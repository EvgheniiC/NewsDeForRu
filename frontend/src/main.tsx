import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { flushEngagementQueueSyncOnUnload } from "./analytics/engagementQueue";
import App from "./App";
import { AuthProvider } from "./context/AuthContext";
import { LegalLocaleProvider } from "./context/LegalLocaleContext";
import "./styles.css";

flushEngagementQueueSyncOnUnload();

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <BrowserRouter>
      <AuthProvider>
        <LegalLocaleProvider>
          <App />
        </LegalLocaleProvider>
      </AuthProvider>
    </BrowserRouter>
  </React.StrictMode>
);
