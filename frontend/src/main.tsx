import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { flushEngagementQueueSyncOnUnload } from "./analytics/engagementQueue";
import App from "./App";
import { AuthProvider } from "./context/AuthContext";
import "./styles.css";

flushEngagementQueueSyncOnUnload();

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <BrowserRouter>
      <AuthProvider>
        <App />
      </AuthProvider>
    </BrowserRouter>
  </React.StrictMode>
);
