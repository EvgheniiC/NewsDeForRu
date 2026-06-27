import { Link, Navigate, Outlet, Route, Routes, useLocation } from "react-router-dom";
import { useAuth } from "./context/AuthContext";
import { DeepLinkListener } from "./mobile/DeepLinkListener";
import { PushNotificationListener } from "./mobile/PushNotificationListener";
import { AccountPage } from "./pages/AccountPage";
import { ForgotPasswordPage } from "./pages/ForgotPasswordPage";
import { ResetPasswordPage } from "./pages/ResetPasswordPage";
import { VerifyEmailPage } from "./pages/VerifyEmailPage";
import { ResendVerificationPage } from "./pages/ResendVerificationPage";
import { FeedPage } from "./pages/FeedPage";
import { LoginPage } from "./pages/LoginPage";
import { ModerationPage } from "./pages/ModerationPage";
import { NewsDetailsPage } from "./pages/NewsDetailsPage";
import { AnalyticsConsentBanner } from "./components/AnalyticsConsentBanner";
import { MainNavMore } from "./components/MainNavMore";
import { ImpressumPage } from "./pages/ImpressumPage";
import { ContactPage } from "./pages/ContactPage";
import { PrivacyPage } from "./pages/PrivacyPage";

function NavAuthActions(): JSX.Element {
  const { initializing, logout, user } = useAuth();

  if (initializing) {
    return <span className="main-nav-muted"> … </span>;
  }

  if (user) {
    return (
      <>
        <Link to="/account">Аккаунт</Link>
        {user.can_moderate ? <Link to="/moderation">Модерация</Link> : null}
        <button className="main-nav-button" onClick={() => void logout()} type="button">
          Выйти ({user.email})
        </button>
      </>
    );
  }

  return <Link to="/account">Войти</Link>;
}

/** Renders child routes only when the user can moderate (after session is hydrated). */
function ModeratorRoute(): JSX.Element {
  const { initializing, user } = useAuth();
  const location = useLocation();

  if (initializing) {
    return (
      <section>
        <p className="loading-inline">Проверка доступа…</p>
      </section>
    );
  }

  if (!user?.can_moderate) {
    return <Navigate replace to="/account" state={{ from: location.pathname }} />;
  }

  return <Outlet />;
}

function App(): JSX.Element {
  return (
    <main className="container">
      <DeepLinkListener />
      <PushNotificationListener />
      <nav className="main-nav">
        <div className="main-nav-start">
          <Link to="/">Лента</Link>
          <MainNavMore />
        </div>
        <div className="main-nav-end">
          <NavAuthActions />
        </div>
      </nav>
      <AnalyticsConsentBanner />
      <Routes>
        <Route element={<FeedPage />} path="/" />
        <Route element={<NewsDetailsPage />} path="/news/:id" />
        <Route element={<ModeratorRoute />} path="/moderation">
          <Route index element={<ModerationPage />} />
        </Route>
        <Route element={<LoginPage />} path="/login" />
        <Route element={<AccountPage />} path="/account" />
        <Route element={<ForgotPasswordPage />} path="/account/forgot" />
        <Route element={<ResetPasswordPage />} path="/account/reset" />
        <Route element={<VerifyEmailPage />} path="/account/verify" />
        <Route element={<ResendVerificationPage />} path="/account/resend-verification" />
        <Route element={<PrivacyPage />} path="/privacy" />
        <Route element={<ContactPage />} path="/contact" />
        <Route element={<ImpressumPage />} path="/impressum" />
      </Routes>
    </main>
  );
}

export default App;
