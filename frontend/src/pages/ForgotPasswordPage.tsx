import { FormEvent, useState } from "react";
import { Link } from "react-router-dom";
import { ApiError, authForgotPassword } from "../api/client";

export function ForgotPasswordPage(): JSX.Element {
  const [email, setEmail] = useState<string>("");
  const [error, setError] = useState<string>("");
  const [busy, setBusy] = useState<boolean>(false);
  const [sent, setSent] = useState<boolean>(false);
  const [devLink, setDevLink] = useState<string | null>(null);

  const handleSubmit = async (evt: FormEvent<HTMLFormElement>): Promise<void> => {
    evt.preventDefault();
    setError("");
    setBusy(true);
    setDevLink(null);
    try {
      const response = await authForgotPassword(email.trim().toLowerCase());
      setSent(true);
      if (typeof response.dev_reset_link === "string" && response.dev_reset_link.length > 0) {
        setDevLink(response.dev_reset_link);
      }
    } catch (err: unknown) {
      if (err instanceof ApiError && err.status === 422) {
        setError("Проверьте формат email.");
      } else if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("Не удалось отправить запрос.");
      }
    } finally {
      setBusy(false);
    }
  };

  if (sent) {
    return (
      <section className="account-page">
        <h1>Сброс пароля</h1>
        <p>
          Если аккаунт с этим email зарегистрирован, мы отправили инструкции. Проверьте почту (и папку «Спам»).
        </p>
        {devLink !== null ? (
          <p className="muted">
            Режим разработки (SMTP не настроен):{" "}
            <a href={devLink}>открыть ссылку сброса</a>
          </p>
        ) : null}
        <p className="muted account-editorial-link">
          <Link to="/account">Вернуться ко входу</Link>
        </p>
      </section>
    );
  }

  return (
    <section className="account-page">
      <h1>Забыли пароль?</h1>
      <p className="muted">
        Укажите email, с которым вы регистрировались. Мы пришлём ссылку для нового пароля.
      </p>
      <form autoComplete="on" className="operator-login-form" onSubmit={(e) => void handleSubmit(e)}>
        <label className="field-label" htmlFor="forgot-email">
          Email
        </label>
        <input
          aria-label="Email для сброса пароля"
          autoComplete="email"
          className="operator-login-field"
          id="forgot-email"
          inputMode="email"
          maxLength={254}
          name="email"
          onChange={(e) => setEmail(e.target.value)}
          required
          spellCheck={false}
          type="email"
          value={email}
        />
        {error !== "" ? <p className="error">{error}</p> : null}
        <button disabled={busy} type="submit">
          {busy ? "Отправка…" : "Отправить ссылку"}
        </button>
      </form>
      <p className="muted account-editorial-link">
        <Link to="/account">Назад ко входу</Link>
        {" · "}
        <Link to="/">На главную</Link>
      </p>
    </section>
  );
}
