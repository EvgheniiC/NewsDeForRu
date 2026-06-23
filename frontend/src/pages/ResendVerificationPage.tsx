import { FormEvent, useState } from "react";
import { Link } from "react-router-dom";
import { ApiError, authResendVerification } from "../api/client";

export function ResendVerificationPage(): JSX.Element {
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
      const response = await authResendVerification(email.trim().toLowerCase());
      setSent(true);
      if (typeof response.dev_verification_link === "string" && response.dev_verification_link.length > 0) {
        setDevLink(response.dev_verification_link);
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
        <h1>Подтверждение email</h1>
        <div className="account-form-card account-form-single">
          <p>
            Если аккаунт с этим email зарегистрирован и ещё не подтверждён, мы отправили новую ссылку. Проверьте
            почту (и папку «Спам»).
          </p>
          {devLink !== null ? (
            <p className="muted">
              Режим разработки (SMTP не настроен):{" "}
              <a href={devLink}>открыть ссылку подтверждения</a>
            </p>
          ) : null}
        </div>
        <p className="muted account-editorial-link">
          <Link to="/account">Вернуться ко входу</Link>
        </p>
      </section>
    );
  }

  return (
    <section className="account-page">
      <h1>Подтверждение email</h1>
      <div className="account-form-card account-form-single">
        <p className="muted">
          Укажите email, с которым вы регистрировались. Мы пришлём новую ссылку для подтверждения аккаунта.
        </p>
        <form autoComplete="on" className="operator-login-form" onSubmit={(e) => void handleSubmit(e)}>
          <label className="field-label" htmlFor="resend-verification-email">
            Email
          </label>
          <input
            aria-label="Email для повторной отправки подтверждения"
            autoComplete="email"
            className="operator-login-field"
            id="resend-verification-email"
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
      </div>
      <p className="muted account-editorial-link">
        <Link to="/account">Назад ко входу</Link>
        {" · "}
        <Link to="/">На главную</Link>
      </p>
    </section>
  );
}
