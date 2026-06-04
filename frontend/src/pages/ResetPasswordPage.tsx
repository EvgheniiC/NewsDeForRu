import { FormEvent, useMemo, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { ApiError, authResetPassword } from "../api/client";

export function ResetPasswordPage(): JSX.Element {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const token: string = useMemo(() => searchParams.get("token")?.trim() ?? "", [searchParams]);

  const [password, setPassword] = useState<string>("");
  const [confirm, setConfirm] = useState<string>("");
  const [error, setError] = useState<string>("");
  const [busy, setBusy] = useState<boolean>(false);
  const [done, setDone] = useState<boolean>(false);

  if (token === "") {
    return (
      <section className="account-page">
        <h1>Сброс пароля</h1>
        <p className="error">Ссылка недействительна или устарела. Запросите сброс пароля снова.</p>
        <p>
          <Link to="/account/forgot">Забыли пароль?</Link>
        </p>
      </section>
    );
  }

  const handleSubmit = async (evt: FormEvent<HTMLFormElement>): Promise<void> => {
    evt.preventDefault();
    setError("");
    if (password.length < 8) {
      setError("Пароль должен быть не короче 8 символов.");
      return;
    }
    if (password !== confirm) {
      setError("Пароли не совпадают.");
      return;
    }
    setBusy(true);
    try {
      await authResetPassword(token, password);
      setDone(true);
    } catch (err: unknown) {
      if (err instanceof ApiError && err.status === 400) {
        setError("Ссылка недействительна или истекла. Запросите новую.");
      } else if (err instanceof ApiError && err.status === 422) {
        setError("Пароль должен быть не короче 8 символов.");
      } else if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("Не удалось сменить пароль.");
      }
    } finally {
      setBusy(false);
    }
  };

  if (done) {
    return (
      <section className="account-page">
        <h1>Пароль обновлён</h1>
        <p>Теперь можно войти с новым паролем.</p>
        <button onClick={() => navigate("/account", { replace: true })} type="button">
          Перейти ко входу
        </button>
      </section>
    );
  }

  return (
    <section className="account-page">
      <h1>Новый пароль</h1>
      <form autoComplete="on" className="operator-login-form" onSubmit={(e) => void handleSubmit(e)}>
        <label className="field-label" htmlFor="reset-password">
          Новый пароль (не менее 8 символов)
        </label>
        <input
          aria-label="Новый пароль"
          autoComplete="new-password"
          className="operator-login-field"
          id="reset-password"
          maxLength={256}
          minLength={8}
          name="password"
          onChange={(e) => setPassword(e.target.value)}
          required
          type="password"
          value={password}
        />
        <label className="field-label" htmlFor="reset-password-confirm">
          Повторите пароль
        </label>
        <input
          aria-label="Повтор пароля"
          autoComplete="new-password"
          className="operator-login-field"
          id="reset-password-confirm"
          maxLength={256}
          minLength={8}
          name="password_confirm"
          onChange={(e) => setConfirm(e.target.value)}
          required
          type="password"
          value={confirm}
        />
        {error !== "" ? <p className="error">{error}</p> : null}
        <button disabled={busy} type="submit">
          {busy ? "Сохранение…" : "Сохранить пароль"}
        </button>
      </form>
      <p className="muted account-editorial-link">
        <Link to="/account/forgot">Запросить новую ссылку</Link>
      </p>
    </section>
  );
}
