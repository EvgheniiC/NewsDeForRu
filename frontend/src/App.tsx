import { Link, Route, Routes } from "react-router-dom";
import { FeedPage } from "./pages/FeedPage";
import { ModerationPage } from "./pages/ModerationPage";
import { NewsDetailsPage } from "./pages/NewsDetailsPage";
import { PrivacyPage } from "./pages/PrivacyPage";

function App(): JSX.Element {
  return (
    <main className="container">
      <nav className="main-nav">
        <Link to="/">Лента</Link>
        <Link to="/moderation">Модерация</Link>
        <Link to="/privacy">Конфиденциальность</Link>
      </nav>
      <Routes>
        <Route element={<FeedPage />} path="/" />
        <Route element={<NewsDetailsPage />} path="/news/:id" />
        <Route element={<ModerationPage />} path="/moderation" />
        <Route element={<PrivacyPage />} path="/privacy" />
      </Routes>
    </main>
  );
}

export default App;
