import { Link } from "react-router-dom";
import { UrgentPushToggle } from "./UrgentPushToggle";

export function MainNavMore(): JSX.Element {
  return (
    <details className="main-nav-more">
      <summary className="main-nav-more-trigger">Ещё</summary>
      <div className="main-nav-more-menu">
        <UrgentPushToggle />
        <Link to="/contact">Контакты</Link>
        <Link to="/privacy">Конфиденциальность</Link>
        <Link to="/impressum">Impressum</Link>
      </div>
    </details>
  );
}
