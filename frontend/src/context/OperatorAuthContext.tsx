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
  ApiError,
  logoutStaff,
  refreshStaffSession,
  staffLogin,
  staffMe,
} from "../api/client";
import type {
  OperatorLoginCredentials,
  OperatorMe,
  OperatorTokenPair,
} from "../types/operatorAuth";

const ACCESS_KEY: string = "newsfr.operator.access_token";
const REFRESH_KEY: string = "newsfr.operator.refresh_token";

interface OperatorAuthState {
  user: OperatorMe | null;
  /** True until first hydrate from storage (or absent storage) completes. */
  initializing: boolean;
  login: (credentials: OperatorLoginCredentials) => Promise<OperatorMe>;
  logout: () => Promise<void>;
  /**
   * Run an API callback with a Bearer access token (refresh once on HTTP 401 if possible).
   * Caller must enforce permissions via guards; callbacks should use moderator-only endpoints.
   */
  withModerationAccess: <T>(run: (accessToken: string) => Promise<T>) => Promise<T>;
  /**
   * Same refresh behaviour for endpoints that require `can_run_pipeline` on the account.
   */
  withPipelineAccess: <T>(run: (accessToken: string) => Promise<T>) => Promise<T>;
}

const OperatorAuthContext: React.Context<OperatorAuthState | undefined> =
  createContext<OperatorAuthState | undefined>(undefined);

function persistTokens(pair: OperatorTokenPair | null): void {
  if (pair === null) {
    localStorage.removeItem(ACCESS_KEY);
    localStorage.removeItem(REFRESH_KEY);
    return;
  }
  localStorage.setItem(ACCESS_KEY, pair.access_token);
  localStorage.setItem(REFRESH_KEY, pair.refresh_token);
}

function readStoredPair(): OperatorTokenPair | null {
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
    await logoutStaff(refresh);
  } catch {
    /* ignore logout transport errors */
  }
}

export function OperatorAuthProvider(props: Readonly<{ children: React.ReactNode }>): JSX.Element {
  const { children } = props;
  const [user, setUser] = useState<OperatorMe | null>(null);
  const [initializing, setInitializing] = useState<boolean>(true);
  const tokensRef = useRef<OperatorTokenPair | null>(null);

  const applyPairState = useCallback((pair: OperatorTokenPair | null, nextUser: OperatorMe | null): void => {
    tokensRef.current = pair;
    persistTokens(pair);
    setUser(nextUser);
  }, []);

  const rotatePairWithRefresh = useCallback(async (): Promise<OperatorTokenPair> => {
    const currentRefresh: string | null = tokensRef.current?.refresh_token ?? null;
    if (currentRefresh === null || currentRefresh === "") {
      throw new ApiError("No refresh token", 401);
    }
    const next: OperatorTokenPair = await refreshStaffSession(currentRefresh);
    tokensRef.current = next;
    persistTokens(next);
    return next;
  }, []);

  const requestMe = useCallback(async (accessToken: string): Promise<OperatorMe> => {
    return staffMe(accessToken);
  }, []);

  const login = useCallback(
    async (credentials: OperatorLoginCredentials): Promise<OperatorMe> => {
      const pair: OperatorTokenPair = await staffLogin(credentials);
      const me: OperatorMe = await requestMe(pair.access_token);
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

  const runWithTokenRetry = useCallback(
    async <T,>(run: (accessToken: string) => Promise<T>): Promise<T> => {
      const firstAccess: string | null = tokensRef.current?.access_token ?? null;
      if (firstAccess === null || firstAccess === "") {
        throw new ApiError("Not authenticated", 401);
      }
      try {
        return await run(firstAccess);
      } catch (err: unknown) {
        if (!(err instanceof ApiError) || err.status !== 401) {
          throw err;
        }
        try {
          const rotated: OperatorTokenPair = await rotatePairWithRefresh();
          const me: OperatorMe = await requestMe(rotated.access_token);
          setUser(me);
          return await run(rotated.access_token);
        } catch (second: unknown) {
          applyPairState(null, null);
          throw second instanceof Error ? second : err;
        }
      }
    },
    [applyPairState, requestMe, rotatePairWithRefresh],
  );

  const withModerationAccess = useCallback(
    async <T,>(run: (accessToken: string) => Promise<T>): Promise<T> => {
      if (!user?.can_moderate) {
        throw new ApiError("Moderation is not permitted for this account", 403);
      }
      return runWithTokenRetry(run);
    },
    [runWithTokenRetry, user],
  );

  const withPipelineAccess = useCallback(
    async <T,>(run: (accessToken: string) => Promise<T>): Promise<T> => {
      if (!user?.can_run_pipeline) {
        throw new ApiError("Pipeline runs are not permitted for this account", 403);
      }
      return runWithTokenRetry(run);
    },
    [runWithTokenRetry, user],
  );

  useEffect(() => {
    const hydrate = async (): Promise<void> => {
      const stored: OperatorTokenPair | null = readStoredPair();
      if (stored === null) {
        setInitializing(false);
        return;
      }
      tokensRef.current = stored;
      try {
        const meFromAccess: OperatorMe = await staffMe(stored.access_token);
        applyPairState(stored, meFromAccess);
      } catch {
        try {
          const rotated: OperatorTokenPair = await refreshStaffSession(stored.refresh_token);
          const meAfter: OperatorMe = await staffMe(rotated.access_token);
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

  const value = useMemo<OperatorAuthState>(
    () => ({
      user,
      initializing,
      login,
      logout,
      withModerationAccess,
      withPipelineAccess,
    }),
    [initializing, login, logout, user, withModerationAccess, withPipelineAccess],
  );

  return <OperatorAuthContext.Provider value={value}>{children}</OperatorAuthContext.Provider>;
}

// eslint-disable-next-line react-refresh/only-export-components -- hook paired with OperatorAuthProvider
export function useOperatorAuth(): OperatorAuthState {
  const ctx: OperatorAuthState | undefined = useContext(OperatorAuthContext);
  if (ctx === undefined) {
    throw new Error("useOperatorAuth must be used within OperatorAuthProvider");
  }
  return ctx;
}
