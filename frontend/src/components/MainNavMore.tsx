import { useEffect, useState, type MouseEvent } from "react";
import { Link } from "react-router-dom";
import { UrgentPushToggle } from "./UrgentPushToggle";

export function MainNavMore(): JSX.Element {
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
    return () => {
      document.removeEventListener("keydown", onKeyDown);
    };
  }, [open]);

  const closeMenu = (): void => {
    setOpen(false);
  };

  const onMenuClick = (event: MouseEvent<HTMLDivElement>): void => {
    event.stopPropagation();
  };

  return (
    <div className={`main-nav-more${open ? " is-open" : ""}`}>
      <button
        aria-expanded={open}
        className="main-nav-more-trigger"
        onClick={() => {
          setOpen((prev: boolean) => !prev);
        }}
        type="button"
      >
        Ещё
      </button>
      {open ? (
        <>
          <button
            aria-label="Закрыть меню"
            className="main-nav-more-backdrop"
            onClick={closeMenu}
            type="button"
          />
          <div className="main-nav-more-menu" onClick={onMenuClick} role="menu">
            <UrgentPushToggle />
            <Link onClick={closeMenu} to="/contact">
              Контакты
            </Link>
            <Link onClick={closeMenu} to="/privacy">
              Конфиденциальность
            </Link>
            <Link onClick={closeMenu} to="/impressum">
              Impressum
            </Link>
          </div>
        </>
      ) : null}
    </div>
  );
}
