import { Navigate, Outlet, Route, Routes, useLocation } from "react-router-dom";
import { useAuth } from "./context/AuthContext";
import { isMaintenanceExemptPath, isMaintenanceMode } from "./lib/maintenanceMode";
import { AndroidBackButtonListener } from "./mobile/AndroidBackButtonListener";
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
import { AppHeader } from "./components/AppHeader";
import { ImpressumPage } from "./pages/ImpressumPage";
import { ContactPage } from "./pages/ContactPage";
import { MaintenancePage } from "./pages/MaintenancePage";
import { PrivacyPage } from "./pages/PrivacyPage";

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
  const location = useLocation();
  const maintenance: boolean = isMaintenanceMode();
  const showPublicApp: boolean = !maintenance || isMaintenanceExemptPath(location.pathname);

  if (!showPublicApp) {
    return (
      <main className="container">
        <Routes>
          <Route element={<MaintenancePage />} path="*" />
        </Routes>
      </main>
    );
  }

  return (
    <main className="container">
      <DeepLinkListener />
      <AndroidBackButtonListener />
      <PushNotificationListener />
      <AppHeader />
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
