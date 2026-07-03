import { Link, useLocation } from "react-router-dom";
import { ProfileMenu } from "./ProfileMenu";

const FEED_TITLE: string = "Новости простыми словами";

export function AppHeader(): JSX.Element {
  const { pathname } = useLocation();
  const isFeed: boolean = pathname === "/";

  return (
    <header className="app-header">
      <div className="app-header-start">
        {isFeed ? (
          <h1 className="app-header-title">{FEED_TITLE}</h1>
        ) : (
          <Link className="app-header-back" to="/">
            ← Лента
          </Link>
        )}
      </div>
      <ProfileMenu />
    </header>
  );
}
