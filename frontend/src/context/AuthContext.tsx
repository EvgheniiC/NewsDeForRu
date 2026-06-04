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
  authLogin,
  authLogout,
  authMe,
  authRefresh,
  authRegister,
} from "../api/client";
import type {
  UserLoginCredentials,
  UserMe,
  UserRegisterCredentials,
  UserTokenPair,
} from "../types/userAuth";

const ACCESS_KEY: string = "newsfr.auth.access_token";
const REFRESH_KEY: string = "newsfr.auth.refresh_token";

interface AuthState {
  user: UserMe | null;
  initializing: boolean;
  login: (credentials: UserLoginCredentials) => Promise<UserMe>;
  register: (credentials: UserRegisterCredentials) => Promise<UserMe>;
  logout: () => Promise<void>;
  withModerationAccess: <T>(run: (accessToken: string) => Promise<T>) => Promise<T>;
  withPipelineAccess: <T>(run: (accessToken: string) => Promise<T>) => Promise<T>;
}

const AuthContext: React.Context<AuthState | undefined> = createContext<AuthState | undefined>(
  undefined,
);

function persistTokens(pair: UserTokenPair | null): void {
  if (pair === null) {
    localStorage.removeItem(ACCESS_KEY);
    localStorage.removeItem(REFRESH_KEY);
    return;
  }
  localStorage.setItem(ACCESS_KEY, pair.access_token);
  localStorage.setItem(REFRESH_KEY, pair.refresh_token);
}

function readStoredPair(): UserTokenPair | null {
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
    await authLogout(refresh);
  } catch {
    /* ignore */
  }
}

export function AuthProvider(props: Readonly<{ children: React.ReactNode }>): JSX.Element {
  const { children } = props;
  const [user, setUser] = useState<UserMe | null>(null);
  const [initializing, setInitializing] = useState<boolean>(true);
  const tokensRef = useRef<UserTokenPair | null>(null);

  const applyPairState = useCallback((pair: UserTokenPair | null, nextUser: UserMe | null): void => {
    tokensRef.current = pair;
    persistTokens(pair);
    setUser(nextUser);
  }, []);

  const rotatePairWithRefresh = useCallback(async (): Promise<UserTokenPair> => {
    const currentRefresh: string | null = tokensRef.current?.refresh_token ?? null;
    if (currentRefresh === null || currentRefresh === "") {
      throw new ApiError("No refresh token", 401);
    }
    const next: UserTokenPair = await authRefresh(currentRefresh);
    tokensRef.current = next;
    persistTokens(next);
    return next;
  }, []);

  const requestMe = useCallback(async (accessToken: string): Promise<UserMe> => {
    return authMe(accessToken);
  }, []);

  const login = useCallback(
    async (credentials: UserLoginCredentials): Promise<UserMe> => {
      const pair: UserTokenPair = await authLogin(credentials);
      const me: UserMe = await requestMe(pair.access_token);
      applyPairState(pair, me);
      return me;
    },
    [applyPairState, requestMe],
  );

  const register = useCallback(
    async (credentials: UserRegisterCredentials): Promise<UserMe> => {
      const pair: UserTokenPair = await authRegister(credentials);
      const me: UserMe = await requestMe(pair.access_token);
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
          const rotated: UserTokenPair = await rotatePairWithRefresh();
          const me: UserMe = await requestMe(rotated.access_token);
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
      const stored: UserTokenPair | null = readStoredPair();
      if (stored === null) {
        setInitializing(false);
        return;
      }
      tokensRef.current = stored;
      try {
        const meFromAccess: UserMe = await authMe(stored.access_token);
        applyPairState(stored, meFromAccess);
      } catch {
        try {
          const rotated: UserTokenPair = await authRefresh(stored.refresh_token);
          const meAfter: UserMe = await authMe(rotated.access_token);
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

  const value = useMemo<AuthState>(
    () => ({
      user,
      initializing,
      login,
      register,
      logout,
      withModerationAccess,
      withPipelineAccess,
    }),
    [initializing, login, logout, register, user, withModerationAccess, withPipelineAccess],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

// eslint-disable-next-line react-refresh/only-export-components -- hook paired with AuthProvider
export function useAuth(): AuthState {
  const ctx: AuthState | undefined = useContext(AuthContext);
  if (ctx === undefined) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return ctx;
}
