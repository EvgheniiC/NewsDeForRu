import React, { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from "react";
import { enqueueOne } from "../analytics/engagementQueue";
import { useAuth } from "./AuthContext";
import { getCardSpeaker } from "../lib/listeningSpeaker";
import type { SpeechPlace } from "../lib/cardTts";
import type { ListenChunk } from "../lib/listenScript";
import { getListenScript, preferListenScript, registerListenScript } from "../lib/listeningScripts";
import {
  LISTENING_STATE_EVENT,
  ensurePlaying,
  enqueueNews,
  markFinished,
  nextUnfinishedId,
  readListeningState,
  removeNews,
  setChunk,
  setPosition,
  writeListeningState,
  type ListenQueueItem,
  type ListeningState,
} from "../lib/listeningState";
import { scheduleListeningSyncFlush } from "../lib/listeningSync";

export type ListenPhase = "idle" | "speaking" | "paused";

interface ListenError {
  newsId: number;
  message: string;
}

export interface ListeningContextValue {
  state: ListeningState;
  phase: ListenPhase;
  activeNewsId: number | null;
  error: ListenError | null;
  play: (newsId: number, chunks: readonly ListenChunk[]) => void;
  pause: () => void;
  resume: () => void;
  stop: () => void;
  stopIfCurrent: (newsId: number) => void;
  toggleQueue: (newsId: number) => void;
  setAutoNext: (enabled: boolean) => void;
}

const ListeningContext: React.Context<ListeningContextValue | null> =
  createContext<ListeningContextValue | null>(null);

function commitListeningState(next: ListeningState): void {
  writeListeningState(next);
  scheduleListeningSyncFlush();
}

export function ListeningProvider({ children }: { children: React.ReactNode }): JSX.Element {
  const { user } = useAuth();
  const userId: number | null = user?.id ?? null;
  const [state, setState] = useState<ListeningState>(() => readListeningState());
  const [phase, setPhase] = useState<ListenPhase>("idle");
  const [activeNewsId, setActiveNewsId] = useState<number | null>(null);
  const [error, setError] = useState<ListenError | null>(null);
  const stateRef: React.MutableRefObject<ListeningState> = useRef<ListeningState>(state);
  const phaseRef: React.MutableRefObject<ListenPhase> = useRef<ListenPhase>(phase);
  const playGenRef: React.MutableRefObject<number> = useRef<number>(0);
  const playRef: React.MutableRefObject<(newsId: number, chunks: readonly ListenChunk[]) => void> = useRef<
    (newsId: number, chunks: readonly ListenChunk[]) => void
  >(() => undefined);

  useEffect((): void => {
    if (state.updatedAt >= stateRef.current.updatedAt) {
      stateRef.current = state;
    }
  }, [state]);

  useEffect((): void => {
    phaseRef.current = phase;
  }, [phase]);

  const rememberPlace = useCallback((): void => {
    if (phaseRef.current === "idle") {
      return;
    }
    const newsId: number | null = stateRef.current.currentNewsId;
    const place: SpeechPlace | null = getCardSpeaker().position();
    if (newsId === null || place === null) {
      return;
    }
    const next: ListeningState = setPosition(
      stateRef.current,
      newsId,
      place.chunkIndex,
      place.charOffset,
      Date.now(),
    );
    stateRef.current = next;
    commitListeningState(next);
    setState(next);
  }, []);

  const stop = useCallback((): void => {
    rememberPlace();
    playGenRef.current += 1;
    getCardSpeaker().stop();
    phaseRef.current = "idle";
    setPhase("idle");
    setActiveNewsId(null);
  }, [rememberPlace]);

  const play = useCallback((newsId: number, chunks: readonly ListenChunk[]): void => {
    const script: readonly ListenChunk[] = preferListenScript(newsId, chunks);
    if (script.length === 0) {
      setError({ newsId, message: "Нечего озвучивать." });
      return;
    }
    const saved: ListenQueueItem | undefined = stateRef.current.items.find(
      (row: ListenQueueItem) => row.newsId === newsId,
    );
    const savedIndex: number = saved !== undefined && !saved.finished ? saved.chunkIndex : 0;
    const hasBody: boolean = script.some((chunk: ListenChunk) => chunk.kind === "pause");
    if (saved !== undefined && !saved.finished && savedIndex >= script.length && !hasBody) {
      return;
    }
    registerListenScript(newsId, script);
    playGenRef.current += 1;
    const generation: number = playGenRef.current;
    const started: ListeningState = ensurePlaying(stateRef.current, newsId, Date.now(), script.length);
    stateRef.current = started;
    commitListeningState(started);
    setState(started);
    setError(null);
    phaseRef.current = "speaking";
    setPhase("speaking");
    setActiveNewsId(newsId);
    const item: ListenQueueItem | undefined = started.items.find(
      (row: ListenQueueItem) => row.newsId === newsId,
    );
    let startIndex: number = item?.chunkIndex ?? 0;
    let startOffset: number = item?.charOffset ?? 0;
    if (startIndex >= script.length) {
      startIndex = 0;
      startOffset = 0;
      const restarted: ListeningState = setPosition(stateRef.current, newsId, 0, 0, Date.now());
      stateRef.current = restarted;
      commitListeningState(restarted);
      setState(restarted);
    }
    enqueueOne(newsId, "listen_start", { chunk_index: startIndex }, true);
    getCardSpeaker().speak(
      script,
      startIndex,
      {
        onChunk: (index: number): void => {
          if (generation !== playGenRef.current) {
            return;
          }
          const next: ListeningState = setChunk(stateRef.current, newsId, index, Date.now());
          stateRef.current = next;
          commitListeningState(next);
          setState(next);
        },
        onEnd: (): void => {
          if (generation !== playGenRef.current) {
            return;
          }
          const finished: ListeningState = markFinished(stateRef.current, newsId, Date.now());
          stateRef.current = finished;
          commitListeningState(finished);
          setState(finished);
          if (!finished.autoNext) {
            phaseRef.current = "idle";
            setPhase("idle");
            setActiveNewsId(null);
            return;
          }
          const nextId: number | null = nextUnfinishedId({ ...finished, currentNewsId: newsId });
          const nextScript: readonly ListenChunk[] | null = nextId === null ? null : getListenScript(nextId);
          if (nextId === null || nextScript === null || nextScript.length === 0) {
            phaseRef.current = "idle";
            setPhase("idle");
            setActiveNewsId(null);
            return;
          }
          playRef.current(nextId, nextScript);
        },
        onError: (message: string): void => {
          if (generation !== playGenRef.current) {
            return;
          }
          phaseRef.current = "idle";
          setPhase("idle");
          setActiveNewsId(null);
          setError({ newsId, message });
        },
      },
      startOffset,
    );
  }, []);

  useEffect((): void => {
    playRef.current = play;
  }, [play]);

  const pause = useCallback((): void => {
    if (phaseRef.current !== "speaking") {
      return;
    }
    rememberPlace();
    getCardSpeaker().pause();
    phaseRef.current = "paused";
    setPhase("paused");
  }, [rememberPlace]);

  const resume = useCallback((): void => {
    if (phaseRef.current !== "paused") {
      return;
    }
    if (getCardSpeaker().position() === null) {
      const newsId: number | null = stateRef.current.currentNewsId;
      const savedScript: readonly ListenChunk[] | null = newsId === null ? null : getListenScript(newsId);
      if (newsId !== null && savedScript !== null) {
        playRef.current(newsId, savedScript);
      }
      return;
    }
    getCardSpeaker().resume();
    phaseRef.current = "speaking";
    setPhase("speaking");
  }, []);

  const stopIfCurrent = useCallback(
    (newsId: number): void => {
      if (stateRef.current.currentNewsId !== newsId || phaseRef.current === "idle") {
        return;
      }
      stop();
    },
    [stop],
  );

  const toggleQueue = useCallback((newsId: number): void => {
    const current: ListeningState = stateRef.current;
    const exists: boolean = current.items.some((item: ListenQueueItem) => item.newsId === newsId);
    if (exists && current.currentNewsId === newsId && phaseRef.current !== "idle") {
      stop();
    }
    const next: ListeningState = exists
      ? removeNews(current, newsId, Date.now())
      : enqueueNews(current, newsId, Date.now());
    stateRef.current = next;
    commitListeningState(next);
    setState(next);
  }, [stop]);

  const setAutoNext = useCallback((enabled: boolean): void => {
    const next: ListeningState = { ...stateRef.current, autoNext: enabled, updatedAt: Date.now() };
    stateRef.current = next;
    commitListeningState(next);
    setState(next);
  }, []);

  useEffect(() => {
    const onChange = (): void => {
      setState(readListeningState());
    };
    window.addEventListener(LISTENING_STATE_EVENT, onChange);
    return (): void => {
      window.removeEventListener(LISTENING_STATE_EVENT, onChange);
    };
  }, []);

  useEffect(() => {
    stop();
    setState(readListeningState());
    setError(null);
  }, [stop, userId]);

  useEffect(() => {
    const onHide = (): void => {
      if (document.visibilityState === "hidden") {
        stop();
      }
    };
    document.addEventListener("visibilitychange", onHide);
    window.addEventListener("pagehide", stop);
    return (): void => {
      document.removeEventListener("visibilitychange", onHide);
      window.removeEventListener("pagehide", stop);
      stop();
    };
  }, [stop]);

  const value: ListeningContextValue = useMemo(
    (): ListeningContextValue => ({
      state,
      phase,
      activeNewsId,
      error,
      play,
      pause,
      resume,
      stop,
      stopIfCurrent,
      toggleQueue,
      setAutoNext,
    }),
    [activeNewsId, error, pause, phase, play, resume, setAutoNext, state, stop, stopIfCurrent, toggleQueue],
  );

  return <ListeningContext.Provider value={value}>{children}</ListeningContext.Provider>;
}

// eslint-disable-next-line react-refresh/only-export-components -- hook paired with ListeningProvider
export function useListening(): ListeningContextValue {
  const value: ListeningContextValue | null = useContext(ListeningContext);
  if (value === null) {
    throw new Error("useListening must be used within ListeningProvider");
  }
  return value;
}
