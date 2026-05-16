import { Link, Navigate, Outlet, Route, Routes, useLocation } from "react-router-dom";
import { useOperatorAuth } from "./context/OperatorAuthContext";
import { FeedPage } from "./pages/FeedPage";
import { LoginPage } from "./pages/LoginPage";
import { ModerationPage } from "./pages/ModerationPage";
import { NewsDetailsPage } from "./pages/NewsDetailsPage";
import { PrivacyPage } from "./pages/PrivacyPage";

function OperatorNavActions(): JSX.Element {
  const { initializing, logout, user } = useOperatorAuth();

  if (initializing) {
    return <span className="main-nav-muted"> … </span>;
  }

  if (user) {
    return (
      <>
        {user.can_moderate ? <Link to="/moderation">Модерация</Link> : null}
        <button
          className="main-nav-button"
          onClick={() => void logout()}
          type="button"
        >
          Выйти ({user.email})
        </button>
      </>
    );
  }

  return <Link to="/login">Вход оператора</Link>;
}

/** Renders child routes only when the operator can moderate (after session is hydrated). */
function ModeratorRoute(): JSX.Element {
  const { initializing, user } = useOperatorAuth();
  const location = useLocation();

  if (initializing) {
    return (
      <section>
        <p className="loading-inline">Проверка доступа…</p>
      </section>
    );
  }

  if (!user?.can_moderate) {
    return <Navigate replace to="/login" state={{ from: location.pathname }} />;
  }

  return <Outlet />;
}

function App(): JSX.Element {
  return (
    <main className="container">
      <nav className="main-nav">
        <Link to="/">Лента</Link>
        <OperatorNavActions />
        <Link to="/privacy">Конфиденциальность</Link>
      </nav>
      <Routes>
        <Route element={<FeedPage />} path="/" />
        <Route element={<NewsDetailsPage />} path="/news/:id" />
        <Route element={<ModeratorRoute />} path="/moderation">
          <Route index element={<ModerationPage />} />
        </Route>
        <Route element={<LoginPage />} path="/login" />
        <Route element={<PrivacyPage />} path="/privacy" />
      </Routes>
    </main>
  );
}

export default App;
