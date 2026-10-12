import { useEffect, useMemo, useRef } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { useListening, type ListenPhase } from "../context/ListeningContext";
import { buildListenChunks } from "../lib/listenScript";
import { registerListenScript } from "../lib/listeningScripts";
import type { ListenQueueItem } from "../lib/listeningState";

interface NewsListenControlsProps {
  newsId: number;
  title: string;
  subtitle: string;
  plainLanguage: string | null;
  actionItems: string | null;
  articleLoading: boolean;
  expanded: boolean;
}

function listenLabel(
  phase: ListenPhase,
  isSpeaking: boolean,
  isPaused: boolean,
  item: ListenQueueItem | undefined,
): string {
  if (isSpeaking) {
    return "Пауза";
  }
  if (isPaused) {
    return "Продолжить";
  }
  if (phase === "idle" && item !== undefined && !item.finished && item.chunkIndex > 0) {
    return "Продолжить";
  }
  return "Слушать";
}

/** Listen / queue controls. Guests get a link to sign in; playback stays on the device. */
export function NewsListenControls({
  newsId,
  title,
  subtitle,
  plainLanguage,
  actionItems,
  articleLoading,
  expanded,
}: NewsListenControlsProps): JSX.Element {
  const { user } = useAuth();
  const {
    activeNewsId,
    error,
    pause,
    phase,
    play,
    resume,
    setAutoNext,
    state,
    stop,
    stopIfCurrent,
    toggleQueue,
  } = useListening();
  const chunks: readonly string[] = useMemo(
    (): readonly string[] =>
      buildListenChunks({
        title,
        subtitle,
        plainLanguage,
        actionItems,
      }),
    [actionItems, plainLanguage, subtitle, title],
  );
  const wasExpandedRef: { current: boolean } = useRef<boolean>(expanded);

  useEffect(() => {
    if (user === null) {
      return;
    }
    registerListenScript(newsId, chunks);
  }, [chunks, newsId, user]);

  useEffect(() => {
    if (wasExpandedRef.current && !expanded) {
      stopIfCurrent(newsId);
    }
    wasExpandedRef.current = expanded;
  }, [expanded, newsId, stopIfCurrent]);

  useEffect(() => {
    return (): void => {
      stopIfCurrent(newsId);
    };
  }, [newsId, stopIfCurrent]);

  if (user === null) {
    return (
      <Link className="news-open-link" title="Войдите, чтобы слушать" to="/account">
        Слушать
      </Link>
    );
  }

  const item: ListenQueueItem | undefined = state.items.find(
    (row: ListenQueueItem) => row.newsId === newsId,
  );
  const isCurrent: boolean = state.currentNewsId === newsId;
  const isSpeaking: boolean = isCurrent && phase === "speaking" && activeNewsId === newsId;
  const isPaused: boolean = isCurrent && phase === "paused" && activeNewsId === newsId;
  const label: string = listenLabel(phase, isSpeaking, isPaused, isCurrent ? item : undefined);
  const cardError: string = error !== null && error.newsId === newsId ? error.message : "";

  const onListen = (): void => {
    if (isSpeaking) {
      pause();
      return;
    }
    if (isPaused) {
      resume();
      return;
    }
    play(newsId, chunks);
  };

  return (
    <>
      <button
        aria-busy={articleLoading}
        className={isSpeaking || isPaused ? "news-listen-btn is-active" : "news-listen-btn"}
        disabled={articleLoading || chunks.length === 0}
        onClick={onListen}
        type="button"
      >
        {articleLoading ? "Загрузка…" : label}
      </button>
      <button
        aria-pressed={item !== undefined}
        className={item !== undefined ? "news-listen-btn is-active" : "news-listen-btn"}
        onClick={(): void => {
          toggleQueue(newsId);
        }}
        type="button"
      >
        {item !== undefined ? "В очереди" : "В очередь"}
      </button>
      {isSpeaking || isPaused ? (
        <button className="news-listen-btn" onClick={stop} type="button">
          Стоп
        </button>
      ) : null}
      {isCurrent ? (
        <button
          aria-pressed={state.autoNext}
          className={state.autoNext ? "news-listen-btn is-active" : "news-listen-btn"}
          onClick={(): void => {
            setAutoNext(!state.autoNext);
          }}
          title="Следующая новость из очереди"
          type="button"
        >
          Авто
        </button>
      ) : null}
      {cardError !== "" ? (
        <p className="news-listen-note error" role="alert">
          {cardError}
        </p>
      ) : null}
    </>
  );
}
