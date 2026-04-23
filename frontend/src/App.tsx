import { Link, Route, Routes } from "react-router-dom";
import { FeedPage } from "./pages/FeedPage";
import { ModerationPage } from "./pages/ModerationPage";
import { NewsDetailsPage } from "./pages/NewsDetailsPage";

function App(): JSX.Element {
  return (
    <main className="container">
      <nav className="main-nav">
        <Link to="/">Лента</Link>
        <Link to="/moderation">Модерация</Link>
      </nav>
      <Routes>
        <Route element={<FeedPage />} path="/" />
        <Route element={<NewsDetailsPage />} path="/news/:id" />
        <Route element={<ModerationPage />} path="/moderation" />
      </Routes>
    </main>
  );
}

export default App;
