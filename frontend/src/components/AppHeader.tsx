import { useLocation, useNavigate } from "react-router-dom";
import { ProfileMenu } from "./ProfileMenu";

const FEED_TITLE: string = "Новости простыми словами";

export function AppHeader(): JSX.Element {
  const { pathname } = useLocation();
  const navigate = useNavigate();
  const isFeed: boolean = pathname === "/";

  const handleBackToFeed = (): void => {
    navigate("/", { replace: true });
    window.scrollTo({ top: 0, behavior: "instant" });
  };

  return (
    <header className="app-header">
      <div className="app-header-start">
        {isFeed ? (
          <h1 className="app-header-title">{FEED_TITLE}</h1>
        ) : (
          <button className="app-header-back" onClick={handleBackToFeed} type="button">
            ← Лента
          </button>
        )}
      </div>
      <ProfileMenu />
    </header>
  );
}
