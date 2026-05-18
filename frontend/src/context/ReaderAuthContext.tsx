import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import {
  logoutReader,
  readerLogin,
  readerMe,
  readerRegister,
  refreshReaderSession,
} from "../api/client";
import type {
  ReaderLoginCredentials,
  ReaderMe,
  ReaderRegisterCredentials,
  ReaderTokenPair,
} from "../types/readerAuth";

const ACCESS_KEY: string = "newsfr.reader.access_token";
const REFRESH_KEY: string = "newsfr.reader.refresh_token";

interface ReaderAuthState {
  user: ReaderMe | null;
  initializing: boolean;
  login: (credentials: ReaderLoginCredentials) => Promise<ReaderMe>;
  register: (credentials: ReaderRegisterCredentials) => Promise<ReaderMe>;
  logout: () => Promise<void>;
}

const ReaderAuthContext: React.Context<ReaderAuthState | undefined> =
  createContext<ReaderAuthState | undefined>(undefined);

function persistTokens(pair: ReaderTokenPair | null): void {
  if (pair === null) {
    localStorage.removeItem(ACCESS_KEY);
    localStorage.removeItem(REFRESH_KEY);
    return;
  }
  localStorage.setItem(ACCESS_KEY, pair.access_token);
  localStorage.setItem(REFRESH_KEY, pair.refresh_token);
}

function readStoredPair(): ReaderTokenPair | null {
  const access: string | null = localStorage.getItem(ACCESS_KEY);
  const refresh: string | null = localStorage.getItem(REFRESH_KEY);
  if (access !== null && access.length > 0 && refresh !== null && refresh.length > 0) {
    return {
      access_token: access,
      refresh_token: refresh,
      token_type: "bearer",
    };
  }
  return null;
}

async function revokeRemoteRefreshQuietly(refresh: string): Promise<void> {
  try {
    await logoutReader(refresh);
  } catch {
    /* ignore */
  }
}

export function ReaderAuthProvider(props: Readonly<{ children: React.ReactNode }>): JSX.Element {
  const { children } = props;
  const [user, setUser] = useState<ReaderMe | null>(null);
  const [initializing, setInitializing] = useState<boolean>(true);
  const tokensRef = useRef<ReaderTokenPair | null>(null);

  const applyPairState = useCallback((pair: ReaderTokenPair | null, nextUser: ReaderMe | null): void => {
    tokensRef.current = pair;
    persistTokens(pair);
    setUser(nextUser);
  }, []);

  const requestMe = useCallback(async (accessToken: string): Promise<ReaderMe> => {
    return readerMe(accessToken);
  }, []);

  const login = useCallback(
    async (credentials: ReaderLoginCredentials): Promise<ReaderMe> => {
      const pair: ReaderTokenPair = await readerLogin(credentials);
      const me: ReaderMe = await requestMe(pair.access_token);
      applyPairState(pair, me);
      return me;
    },
    [applyPairState, requestMe],
  );

  const register = useCallback(
    async (credentials: ReaderRegisterCredentials): Promise<ReaderMe> => {
      const pair: ReaderTokenPair = await readerRegister(credentials);
      const me: ReaderMe = await requestMe(pair.access_token);
      applyPairState(pair, me);
      return me;
    },
    [applyPairState, requestMe],
  );

  const logout = useCallback(async (): Promise<void> => {
    const refresh: string | null = tokensRef.current?.refresh_token ?? null;
    if (refresh !== null && refresh !== "") {
      await revokeRemoteRefreshQuietly(refresh);
    }
    applyPairState(null, null);
  }, [applyPairState]);

  useEffect(() => {
    const hydrate = async (): Promise<void> => {
      const stored: ReaderTokenPair | null = readStoredPair();
      if (stored === null) {
        setInitializing(false);
        return;
      }
      tokensRef.current = stored;
      try {
        const meFromAccess: ReaderMe = await readerMe(stored.access_token);
        applyPairState(stored, meFromAccess);
      } catch {
        try {
          const rotated: ReaderTokenPair = await refreshReaderSession(stored.refresh_token);
          const meAfter: ReaderMe = await readerMe(rotated.access_token);
          applyPairState(rotated, meAfter);
        } catch {
          persistTokens(null);
          tokensRef.current = null;
          setUser(null);
        }
      } finally {
        setInitializing(false);
      }
    };
    void hydrate();
  }, [applyPairState]);

  const value = useMemo<ReaderAuthState>(
    () => ({
      user,
      initializing,
      login,
      register,
      logout,
    }),
    [initializing, login, logout, register, user],
  );

  return <ReaderAuthContext.Provider value={value}>{children}</ReaderAuthContext.Provider>;
}

// eslint-disable-next-line react-refresh/only-export-components -- hook paired with ReaderAuthProvider
export function useReaderAuth(): ReaderAuthState {
  const ctx: ReaderAuthState | undefined = useContext(ReaderAuthContext);
  if (ctx === undefined) {
    throw new Error("useReaderAuth must be used within ReaderAuthProvider");
  }
  return ctx;
}
