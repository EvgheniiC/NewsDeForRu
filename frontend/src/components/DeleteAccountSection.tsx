import { FormEvent, useState } from "react";
import { ApiError } from "../api/client";
import { useAuth } from "../context/AuthContext";
import { PasswordField } from "./PasswordField";

interface DeleteAccountSectionProps {
  onDeleted: () => void;
}

export function DeleteAccountSection(props: Readonly<DeleteAccountSectionProps>): JSX.Element {
  const { onDeleted } = props;
  const { deleteAccount, user } = useAuth();
  const [confirming, setConfirming] = useState<boolean>(false);
  const [password, setPassword] = useState<string>("");
  const [error, setError] = useState<string>("");
  const [busy, setBusy] = useState<boolean>(false);

  const cancelConfirm = (): void => {
    setConfirming(false);
    setPassword("");
    setError("");
  };

  const handleSubmit = async (evt: FormEvent<HTMLFormElement>): Promise<void> => {
    evt.preventDefault();
    setError("");
    if (password.length < 1) {
      setError("Введите пароль, чтобы подтвердить удаление.");
      return;
    }
    setBusy(true);
    try {
      await deleteAccount(password);
      onDeleted();
    } catch (err: unknown) {
      if (err instanceof ApiError && err.status === 400) {
        setError("Неверный пароль.");
      } else if (err instanceof ApiError && (err.status === 401 || err.status === 403)) {
        setError("Сессия истекла. Войдите снова и повторите удаление.");
      } else if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("Не удалось удалить аккаунт.");
      }
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="account-form-card account-form-single account-danger-zone">
      <h2>Удаление аккаунта</h2>
      <p className="muted">
        Удаление необратимо: email, хеш пароля и сессии будут стёрты. Тем же адресом можно
        зарегистрироваться заново.
        {user?.can_moderate ? " У этого аккаунта есть доступ к модерации — он тоже будет потерян." : ""}
      </p>
      {!confirming ? (
        <button
          className="account-delete-open"
          onClick={() => {
            setConfirming(true);
            setError("");
          }}
          type="button"
        >
          Удалить аккаунт
        </button>
      ) : (
        <form className="operator-login-form" onSubmit={(e) => void handleSubmit(e)}>
          <PasswordField
            autoComplete="current-password"
            id="account-delete-password"
            label="Пароль для подтверждения"
            name="password"
            onChange={setPassword}
            required
            value={password}
          />
          {error !== "" ? <p className="error">{error}</p> : null}
          <div className="account-delete-actions">
            <button className="account-delete-confirm" disabled={busy} type="submit">
              {busy ? "Удаление…" : "Удалить навсегда"}
            </button>
            <button disabled={busy} onClick={cancelConfirm} type="button" className="account-delete-cancel">
              Отмена
            </button>
          </div>
        </form>
      )}
    </div>
  );
}
