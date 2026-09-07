import { useLocation, useNavigate } from "react-router-dom";
import { isMaintenanceMode } from "../lib/maintenanceMode";
import { ProfileMenu } from "./ProfileMenu";

const FEED_TITLE: string = "Новости простыми словами";

export function AppHeader(): JSX.Element {
  const { pathname } = useLocation();
  const navigate = useNavigate();
  const maintenance: boolean = isMaintenanceMode();
  const isFeed: boolean = pathname === "/";
  const showBackToFeed: boolean = !isFeed && !maintenance;

  const handleBackToFeed = (): void => {
    navigate("/", { replace: true });
    window.scrollTo({ top: 0, behavior: "instant" });
  };

  return (
    <header className="app-header">
      <div className="app-header-start">
        {showBackToFeed ? (
          <button className="app-header-back" onClick={handleBackToFeed} type="button">
            ← Лента
          </button>
        ) : (
          <h1 className="app-header-title">{FEED_TITLE}</h1>
        )}
      </div>
      <ProfileMenu />
    </header>
  );
}
