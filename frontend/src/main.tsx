import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { flushEngagementQueueSyncOnUnload } from "./analytics/engagementQueue";
import App from "./App";
import "./styles.css";

flushEngagementQueueSyncOnUnload();

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>
);
