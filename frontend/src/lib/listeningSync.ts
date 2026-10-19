/** Push and pull the listen queue for the signed-in user. */

import { getUserListening, putUserListening } from "../api/client";
import type { UserListeningPutResponse, UserListeningState } from "../types/userListening";
import {
  chooseListeningState,
  clearListeningState,
  emptyListeningState,
  fromApiListeningState,
  readListeningOwner,
  readListeningState,
  toApiListeningState,
  writeListeningOwner,
  writeListeningState,
  type ListeningState,
} from "./listeningState";

type ListeningSyncFlushHandler = () => Promise<void>;

const FLUSH_MS: number = 850;

let flushTimer: number | null = null;
let flushing: boolean = false;
let flushAgain: boolean = false;
let flushHandler: ListeningSyncFlushHandler | null = null;

export function setListeningSyncFlushHandler(handler: ListeningSyncFlushHandler | null): void {
  flushHandler = handler;
  if (handler !== null) {
    scheduleListeningSyncFlush();
  }
}

export function scheduleListeningSyncFlush(): void {
  if (flushHandler === null) {
    return;
  }
  if (flushing) {
    flushAgain = true;
    return;
  }
  if (flushTimer !== null) {
    return;
  }
  flushTimer = window.setTimeout((): void => {
    flushTimer = null;
    void flushListeningSyncQueue();
  }, FLUSH_MS);
}

export async function flushListeningSyncQueue(): Promise<void> {
  if (flushHandler === null || flushing) {
    flushAgain = true;
    return;
  }
  flushing = true;
  try {
    do {
      flushAgain = false;
      await flushHandler();
    } while (flushAgain);
  } finally {
    flushing = false;
  }
}

export async function flushListeningToServer(accessToken: string): Promise<void> {
  const sent: ListeningState = readListeningState();
  if (sent.updatedAt <= 0 && sent.items.length === 0) {
    return;
  }
  const response: UserListeningPutResponse = await putUserListening(accessToken, toApiListeningState(sent));
  const latest: ListeningState = readListeningState();
  if (latest.updatedAt !== sent.updatedAt) {
    scheduleListeningSyncFlush();
    return;
  }
  if (!response.applied) {
    writeListeningState(chooseListeningState(latest, fromApiListeningState(response.state)));
  }
}

export async function reconcileListening(accessToken: string, userId: number): Promise<void> {
  const owner: number | null = readListeningOwner();
  if (owner !== null && owner !== userId) {
    clearListeningState();
    writeListeningOwner(userId);
  }
  const remote: UserListeningState = await getUserListening(accessToken);
  const local: ListeningState = readListeningState();
  const remoteState: ListeningState = fromApiListeningState(remote);
  if (remoteState.updatedAt > local.updatedAt) {
    writeListeningState(remoteState);
  } else if (local.updatedAt > remoteState.updatedAt) {
    await flushListeningToServer(accessToken);
  } else if (local.items.length === 0 && remoteState.items.length === 0) {
    writeListeningState(emptyListeningState());
  }
  writeListeningOwner(userId);
}

export function configureListeningSync(options: {
  userId: number | null;
  runAuthenticated: ((task: (accessToken: string) => Promise<void>) => Promise<void>) | null;
}): () => void {
  if (options.userId === null || options.runAuthenticated === null) {
    setListeningSyncFlushHandler(null);
    return (): void => undefined;
  }
  const userId: number = options.userId;
  const runAuthenticated: (task: (accessToken: string) => Promise<void>) => Promise<void> =
    options.runAuthenticated;
  setListeningSyncFlushHandler(async (): Promise<void> => {
    await runAuthenticated(async (accessToken: string): Promise<void> => {
      await flushListeningToServer(accessToken);
    });
  });
  void runAuthenticated(async (accessToken: string): Promise<void> => {
    await reconcileListening(accessToken, userId);
  });
  const flushNow = (): void => {
    void flushListeningSyncQueue();
  };
  const onVisibility = (): void => {
    if (document.visibilityState === "hidden") {
      flushNow();
    }
  };
  window.addEventListener("visibilitychange", onVisibility);
  window.addEventListener("pagehide", flushNow);
  return (): void => {
    flushNow();
    setListeningSyncFlushHandler(null);
    window.removeEventListener("visibilitychange", onVisibility);
    window.removeEventListener("pagehide", flushNow);
  };
}
