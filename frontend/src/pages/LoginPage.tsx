import { Navigate, useLocation } from "react-router-dom";

interface LocationState {
  from?: string;
}

/** Legacy `/login` URL — redirects to unified account page. */
export function LoginPage(): JSX.Element {
  const location = useLocation();
  const state = location.state as LocationState | null | undefined;
  const target: string =
    typeof state?.from === "string" && state.from.startsWith("/") ? "/account" : "/account";
  return <Navigate replace state={state ?? undefined} to={target} />;
}
