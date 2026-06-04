import { FormEvent, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { ApiError } from "../api/client";
import { useAuth } from "../context/AuthContext";

interface LocationState {
  from?: string;
}

export function AccountPage(): JSX.Element {
  const navigate = useNavigate();
  const location = useLocation();
  const redirectState = location.state as LocationState | null | undefined;
  const { initializing, login, logout, register, user } = useAuth();

  const [registerEmail, setRegisterEmail] = useState<string>("");
  const [registerPassword, setRegisterPassword] = useState<string>("");
  const [loginEmail, setLoginEmail] = useState<string>("");
  const [loginPassword, setLoginPassword] = useState<string>("");
  const [registerError, setRegisterError] = useState<string>("");
  const [loginError, setLoginError] = useState<string>("");
  const [registerBusy, setRegisterBusy] = useState<boolean>(false);
  const [loginBusy, setLoginBusy] = useState<boolean>(false);

  const handleRegister = async (evt: FormEvent<HTMLFormElement>): Promise<void> => {
    evt.preventDefault();
    setRegisterError("");
    setRegisterBusy(true);
    try {
      await register({ email: registerEmail, password: registerPassword });
      setRegisterEmail("");
      setRegisterPassword("");
    } catch (err: unknown) {
      if (err instanceof ApiError && err.status === 409) {
        setRegisterError("Этот email уже зарегистрирован. Войдите или используйте другой адрес.");
      } else if (err instanceof ApiError && err.status === 422) {
        setRegisterError("Проверьте формат email и длину пароля (не менее 8 символов).");
      } else if (err instanceof Error) {
        setRegisterError(err.message);
      } else {
        setRegisterError("Не удалось зарегистрироваться.");
      }
    } finally {
      setRegisterBusy(false);
    }
  };

  const handleLogin = async (evt: FormEvent<HTMLFormElement>): Promise<void> => {
    evt.preventDefault();
    setLoginError("");
    setLoginBusy(true);
    try {
      const me = await login({ email: loginEmail, password: loginPassword });
      setLoginEmail("");
      setLoginPassword("");
      if (typeof redirectState?.from === "string" && redirectState.from.startsWith("/")) {
        navigate(redirectState.from, { replace: true });
        return;
      }
      if (me.can_moderate) {
        navigate("/moderation", { replace: true });
      }
    } catch (err: unknown) {
      if (err instanceof ApiError && err.status === 401) {
        setLoginError("Неверный email или пароль.");
      } else if (err instanceof Error) {
        setLoginError(err.message);
      } else {
        setLoginError("Не удалось войти.");
      }
    } finally {
      setLoginBusy(false);
    }
  };

  if (initializing) {
    return (
      <section>
        <p className="loading-inline">Загрузка…</p>
      </section>
    );
  }

  if (user !== null) {
    return (
      <section className="account-page">
        <h1>Аккаунт</h1>
        <p>
          Вы вошли как <strong>{user.email}</strong>.
        </p>
        <p className="muted">
          Скоро здесь появятся персональные функции: умная лента, синхронизация и голосовое прослушивание.
          {user.can_moderate ? " У вашего аккаунта есть доступ к модерации." : ""}
        </p>
        {user.can_moderate ? (
          <p>
            <Link to="/moderation">Очередь модерации</Link>
          </p>
        ) : null}
        <button className="account-logout-wide" onClick={() => void logout()} type="button">
          Выйти из аккаунта
        </button>
        <p className="muted account-editorial-link">
          <Link to="/">На главную</Link>
        </p>
      </section>
    );
  }

  return (
    <section className="account-page">
      <h1>Аккаунт</h1>
      <p className="muted">
        Ленту и новости можно читать без регистрации. Аккаунт понадобится для персонализации и дополнительных функций.
      </p>

      <div className="account-benefits">
        <h2>Зачем регистрироваться</h2>
        <ul>
          <li>
            <strong>Умная лента</strong> — темы и приоритеты под ваши интересы (когда эта функция будет включена).
          </li>
          <li>
            <strong>Один профиль на всех устройствах</strong> — настройки и история не привязаны только к одному телефону.
          </li>
          <li>
            <strong>Голосовое прослушивание</strong> — сохранение прогресса и очереди прослушивания между сессиями
            (в разработке).
          </li>
          <li>
            <strong>Без жёсткой подписки на рассылку</strong> — вход только для функций приложения, спам не обещаем.
          </li>
        </ul>
      </div>

      <div className="account-forms-grid">
        <div className="account-form-card">
          <h2>Регистрация</h2>
          <form autoComplete="on" className="operator-login-form" onSubmit={(e) => void handleRegister(e)}>
            <label className="field-label" htmlFor="reader-register-email">
              Email
            </label>
            <input
              aria-label="Email для регистрации"
              autoComplete="email"
              className="operator-login-field"
              id="reader-register-email"
              inputMode="email"
              maxLength={254}
              name="email"
              onChange={(e) => setRegisterEmail(e.target.value)}
              required
              spellCheck={false}
              type="email"
              value={registerEmail}
            />
            <label className="field-label" htmlFor="reader-register-password">
              Пароль (не менее 8 символов)
            </label>
            <input
              aria-label="Пароль для регистрации"
              autoComplete="new-password"
              className="operator-login-field"
              id="reader-register-password"
              maxLength={256}
              minLength={8}
              name="password"
              onChange={(e) => setRegisterPassword(e.target.value)}
              required
              type="password"
              value={registerPassword}
            />
            {registerError !== "" ? <p className="error">{registerError}</p> : null}
            <button disabled={registerBusy} type="submit">
              {registerBusy ? "Регистрация…" : "Создать аккаунт"}
            </button>
          </form>
        </div>

        <div className="account-form-card">
          <h2>Вход</h2>
          <form autoComplete="on" className="operator-login-form" onSubmit={(e) => void handleLogin(e)}>
            <label className="field-label" htmlFor="reader-login-email">
              Email
            </label>
            <input
              aria-label="Email для входа"
              autoComplete="username"
              className="operator-login-field"
              id="reader-login-email"
              inputMode="email"
              maxLength={254}
              name="email"
              onChange={(e) => setLoginEmail(e.target.value)}
              required
              spellCheck={false}
              type="email"
              value={loginEmail}
            />
            <label className="field-label" htmlFor="reader-login-password">
              Пароль
            </label>
            <input
              aria-label="Пароль для входа"
              autoComplete="current-password"
              className="operator-login-field"
              id="reader-login-password"
              maxLength={256}
              name="password"
              onChange={(e) => setLoginPassword(e.target.value)}
              required
              type="password"
              value={loginPassword}
            />
            {loginError !== "" ? <p className="error">{loginError}</p> : null}
            <button disabled={loginBusy} type="submit">
              {loginBusy ? "Вход…" : "Войти"}
            </button>
          </form>
        </div>
      </div>

      <p className="muted account-editorial-link">
        <Link to="/">На главную</Link>
      </p>
    </section>
  );
}
