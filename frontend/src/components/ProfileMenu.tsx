import { useEffect, useState, type MouseEvent } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { registerAndroidBackPressHandler } from "../mobile/androidBackPress";
import { UrgentPushToggle } from "./UrgentPushToggle";

function profileInitials(email: string): string {
  const trimmed: string = email.trim();
  if (trimmed.length === 0) {
    return "?";
  }
  return trimmed[0].toUpperCase();
}

function GuestAvatarIcon(): JSX.Element {
  return (
    <svg aria-hidden className="profile-menu-guest-icon" fill="none" viewBox="0 0 24 24">
      <circle cx="12" cy="8" r="4" stroke="currentColor" strokeWidth="1.75" />
      <path
        d="M5 20c0-3.314 3.134-6 7-6s7 2.686 7 6"
        stroke="currentColor"
        strokeLinecap="round"
        strokeWidth="1.75"
      />
    </svg>
  );
}

export function ProfileMenu(): JSX.Element {
  const { initializing, logout, user } = useAuth();
  const [open, setOpen] = useState<boolean>(false);

  useEffect(() => {
    if (!open) {
      return;
    }

    const onKeyDown = (event: KeyboardEvent): void => {
      if (event.key === "Escape") {
        setOpen(false);
      }
    };

    document.addEventListener("keydown", onKeyDown);
    const removeBackHandler: () => void = registerAndroidBackPressHandler((): boolean => {
      setOpen(false);
      return true;
    });

    return (): void => {
      document.removeEventListener("keydown", onKeyDown);
      removeBackHandler();
    };
  }, [open]);

  const closeMenu = (): void => {
    setOpen(false);
  };

  const onMenuClick = (event: MouseEvent<HTMLDivElement>): void => {
    event.stopPropagation();
  };

  const menuLabel: string = user ? "Меню аккаунта" : "Меню";

  return (
    <div className={`profile-menu${open ? " is-open" : ""}`}>
      <button
        aria-expanded={open}
        aria-haspopup="menu"
        aria-label={menuLabel}
        className="profile-menu-trigger"
        disabled={initializing}
        onClick={() => {
          setOpen((prev: boolean) => !prev);
        }}
        type="button"
      >
        <span aria-hidden className="profile-menu-avatar">
          {initializing ? "…" : user ? profileInitials(user.email) : <GuestAvatarIcon />}
        </span>
      </button>
      {open ? (
        <>
          <button
            aria-label="Закрыть меню"
            className="profile-menu-backdrop"
            onClick={closeMenu}
            type="button"
          />
          <div className="profile-menu-panel" onClick={onMenuClick} role="menu">
            {!initializing && user ? (
              <>
                <p className="profile-menu-user">{user.email}</p>
                <Link className="profile-menu-link" onClick={closeMenu} role="menuitem" to="/account">
                  Аккаунт
                </Link>
                {user.can_moderate ? (
                  <Link className="profile-menu-link" onClick={closeMenu} role="menuitem" to="/moderation">
                    Модерация
                  </Link>
                ) : null}
                <button
                  className="profile-menu-link profile-menu-action"
                  onClick={() => {
                    closeMenu();
                    void logout();
                  }}
                  role="menuitem"
                  type="button"
                >
                  Выйти
                </button>
                <hr className="profile-menu-divider" />
              </>
            ) : !initializing ? (
              <>
                <Link className="profile-menu-link" onClick={closeMenu} role="menuitem" to="/account">
                  Войти
                </Link>
                <hr className="profile-menu-divider" />
              </>
            ) : null}
            <UrgentPushToggle />
            <Link className="profile-menu-link" onClick={closeMenu} role="menuitem" to="/contact">
              Контакты
            </Link>
            <Link className="profile-menu-link" onClick={closeMenu} role="menuitem" to="/privacy">
              Конфиденциальность
            </Link>
            <Link className="profile-menu-link" onClick={closeMenu} role="menuitem" to="/impressum">
              Impressum
            </Link>
          </div>
        </>
      ) : null}
    </div>
  );
}
