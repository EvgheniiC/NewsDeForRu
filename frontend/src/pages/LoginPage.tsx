import { FormEvent, useState } from "react";
import { Link, Navigate, useLocation, useNavigate } from "react-router-dom";
import { ApiError } from "../api/client";
import { useOperatorAuth } from "../context/OperatorAuthContext";

interface LocationState {
  from?: string;
}

export function LoginPage(): JSX.Element {
  const navigate = useNavigate();
  const location = useLocation();
  const state = location.state as LocationState | null | undefined;

  const { initializing, login, user } = useOperatorAuth();

  const [email, setEmail] = useState<string>("");
  const [password, setPassword] = useState<string>("");
  const [error, setError] = useState<string>("");
  const [busy, setBusy] = useState<boolean>(false);

  if (!initializing && user) {
    const defaultHome: string = user.can_moderate ? "/moderation" : "/";
    return <Navigate replace to={defaultHome} />;
  }

  const handleSubmit = async (evt: FormEvent<HTMLFormElement>): Promise<void> => {
    evt.preventDefault();
    setError("");
    setBusy(true);
    try {
      const me = await login({ email, password });
      const nextPath: string =
        typeof state?.from === "string" && state.from.startsWith("/")
          ? state.from
          : me.can_moderate
            ? "/moderation"
            : "/";
      navigate(nextPath, { replace: true });
    } catch (submissionError: unknown) {
      if (submissionError instanceof ApiError && submissionError.status === 401) {
        setError("Неверный email или пароль.");
      } else if (submissionError instanceof Error) {
        setError(submissionError.message);
      } else {
        setError("Не удалось войти.");
      }
    } finally {
      setBusy(false);
    }
  };

  return (
    <section>
      <h1>Вход для операторов</h1>
      <p className="muted">
        Публичная лента не требует входа; эта страница только для модерации и запуска pipeline.
      </p>
      <form autoComplete="on" className="operator-login-form" onSubmit={(e) => void handleSubmit(e)}>
        <label className="field-label" htmlFor="operator-email-input">
          Email
        </label>
        <input
          aria-label="Email оператора"
          autoComplete="username"
          className="operator-login-field"
          inputMode="email"
          maxLength={254}
          name="email"
          onChange={(e) => setEmail(e.target.value)}
          required
          spellCheck={false}
          type="email"
          value={email}
        />
        <label className="field-label" htmlFor="operator-password-input">
          Пароль
        </label>
        <input
          aria-label="Пароль оператора"
          autoComplete="current-password"
          className="operator-login-field"
          maxLength={256}
          name="password"
          onChange={(e) => setPassword(e.target.value)}
          required
          type="password"
          value={password}
        />
        {error !== "" ? <p className="error">{error}</p> : null}
        <div className="operator-login-actions">
          <button disabled={busy} type="submit">
            {busy ? "Вход…" : "Войти"}
          </button>
          <Link to="/">На главную</Link>
        </div>
      </form>
    </section>
  );
}
