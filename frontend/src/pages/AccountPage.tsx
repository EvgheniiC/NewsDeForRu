import { FormEvent, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { ApiError } from "../api/client";
import { PasswordField } from "../components/PasswordField";
import { useAuth } from "../context/AuthContext";

interface LocationState {
  from?: string;
}

interface FeedRedirectState {
  verificationPendingEmail: string;
  devVerificationLink?: string | null;
}

type AuthFormMode = "login" | "register";

export function AccountPage(): JSX.Element {
  const navigate = useNavigate();
  const location = useLocation();
  const redirectState = location.state as LocationState | null | undefined;
  const { initializing, login, logout, register, user } = useAuth();

  const [registerEmail, setRegisterEmail] = useState<string>("");
  const [registerPassword, setRegisterPassword] = useState<string>("");
  const [registerPasswordConfirm, setRegisterPasswordConfirm] = useState<string>("");
  const [loginEmail, setLoginEmail] = useState<string>("");
  const [loginPassword, setLoginPassword] = useState<string>("");
  const [registerError, setRegisterError] = useState<string>("");
  const [loginError, setLoginError] = useState<string>("");
  const [registerBusy, setRegisterBusy] = useState<boolean>(false);
  const [loginBusy, setLoginBusy] = useState<boolean>(false);
  const [formMode, setFormMode] = useState<AuthFormMode>("login");
  const showLoginForm = (): void => {
    setFormMode("login");
    setRegisterError("");
  };

  const showRegisterForm = (): void => {
    setFormMode("register");
    setLoginError("");
  };

  const handleRegister = async (evt: FormEvent<HTMLFormElement>): Promise<void> => {
    evt.preventDefault();
    setRegisterError("");
    if (registerPassword.length < 8) {
      setRegisterError("Пароль должен быть не короче 8 символов.");
      return;
    }
    if (registerPassword !== registerPasswordConfirm) {
      setRegisterError("Пароли не совпадают.");
      return;
    }
    setRegisterBusy(true);
    try {
      const registeredEmail: string = registerEmail.trim().toLowerCase();
      const response = await register({ email: registeredEmail, password: registerPassword });
      const devVerificationLink: string | null =
        typeof response.dev_verification_link === "string" && response.dev_verification_link.length > 0
          ? response.dev_verification_link
          : null;
      const redirectState: FeedRedirectState = {
        verificationPendingEmail: registeredEmail,
        devVerificationLink,
      };
      navigate("/", { replace: true, state: redirectState });
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
      } else if (err instanceof ApiError && err.status === 403) {
        setLoginError("Подтвердите email — проверьте почту или запросите ссылку повторно.");
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
        <div className="account-form-card account-form-single account-session-card">
          <p className="account-session-label">Вы вошли как</p>
          <p className="account-session-email">{user.email}</p>
          <p className="muted account-session-note">
            Скоро здесь появятся персональные функции: умная лента, синхронизация и голосовое прослушивание.
            {user.can_moderate ? " У вашего аккаунта есть доступ к модерации." : ""}
          </p>
          {user.can_moderate ? (
            <p className="account-session-link">
              <Link to="/moderation">Очередь модерации</Link>
            </p>
          ) : null}
          <button className="account-logout-wide" onClick={() => void logout()} type="button">
            Выйти из аккаунта
          </button>
        </div>
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

      {formMode === "register" ? (
        <div className="account-benefits">
          <h2>Зачем регистрироваться</h2>
          <ul>
            <li>
              <strong>Умная лента</strong> — темы и приоритеты под ваши интересы (когда эта функция будет включена).
            </li>
            <li>
              <strong>Один профиль на всех устройствах</strong> — настройки и история не привязаны только к одному
              телефону.
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
      ) : null}

      <div className="account-form-card account-form-single">
        {formMode === "login" ? (
          <>
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
              <p className="account-forgot-link">
                <Link to="/account/forgot">Забыли пароль?</Link>
                {" · "}
                <Link to="/account/resend-verification">Подтвердить email</Link>
              </p>
            </form>
            <p className="account-mode-toggle">
              <button onClick={showRegisterForm} type="button">
                Ещё не зарегистрировались?
              </button>
            </p>
          </>
        ) : (
          <>
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
              <PasswordField
                autoComplete="new-password"
                id="reader-register-password"
                label="Пароль (не менее 8 символов)"
                minLength={8}
                name="password"
                onChange={setRegisterPassword}
                required
                value={registerPassword}
              />
              <PasswordField
                autoComplete="new-password"
                id="reader-register-password-confirm"
                label="Подтвердите пароль"
                minLength={8}
                name="password_confirm"
                onChange={setRegisterPasswordConfirm}
                required
                value={registerPasswordConfirm}
              />
              {registerError !== "" ? <p className="error">{registerError}</p> : null}
              <button disabled={registerBusy} type="submit">
                {registerBusy ? "Регистрация…" : "Создать аккаунт"}
              </button>
            </form>
            <p className="account-mode-toggle">
              <button onClick={showLoginForm} type="button">
                Уже есть аккаунт? Войти
              </button>
            </p>
          </>
        )}
      </div>

      <p className="muted account-editorial-link">
        <Link to="/">На главную</Link>
      </p>
    </section>
  );
}
