import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { ApiError, authVerifyEmail } from "../api/client";
import { useAuth } from "../context/AuthContext";

export function VerifyEmailPage(): JSX.Element {
  const navigate = useNavigate();
  const { establishSession } = useAuth();
  const [searchParams] = useSearchParams();
  const token: string = useMemo(() => searchParams.get("token")?.trim() ?? "", [searchParams]);

  const [error, setError] = useState<string>("");
  const [busy, setBusy] = useState<boolean>(token !== "");
  const [done, setDone] = useState<boolean>(false);

  useEffect(() => {
    if (token === "") {
      return;
    }

    const verify = async (): Promise<void> => {
      setBusy(true);
      setError("");
      try {
        const pair = await authVerifyEmail(token);
        await establishSession(pair);
        setDone(true);
      } catch (err: unknown) {
        if (err instanceof ApiError && err.status === 400) {
          setError("Ссылка недействительна или истекла. Запросите новую.");
        } else if (err instanceof Error) {
          setError(err.message);
        } else {
          setError("Не удалось подтвердить email.");
        }
      } finally {
        setBusy(false);
      }
    };

    void verify();
  }, [establishSession, token]);

  if (token === "") {
    return (
      <section className="account-page">
        <h1>Подтверждение email</h1>
        <p className="error">Ссылка недействительна или устарела.</p>
        <p>
          <Link to="/account/resend-verification">Отправить письмо повторно</Link>
        </p>
      </section>
    );
  }

  if (busy) {
    return (
      <section className="account-page">
        <h1>Подтверждение email</h1>
        <p className="loading-inline">Проверяем ссылку…</p>
      </section>
    );
  }

  if (done) {
    return (
      <section className="account-page">
        <h1>Email подтверждён</h1>
        <p>Аккаунт активирован. Можно пользоваться персональными функциями.</p>
        <button onClick={() => navigate("/account", { replace: true })} type="button">
          Перейти в аккаунт
        </button>
      </section>
    );
  }

  return (
    <section className="account-page">
      <h1>Подтверждение email</h1>
      <p className="error">{error}</p>
      <p>
        <Link to="/account/resend-verification">Отправить письмо повторно</Link>
      </p>
      <p className="muted account-editorial-link">
        <Link to="/account">Назад ко входу</Link>
      </p>
    </section>
  );
}
