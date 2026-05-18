import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { flushEngagementQueueSyncOnUnload } from "./analytics/engagementQueue";
import App from "./App";
import { OperatorAuthProvider } from "./context/OperatorAuthContext";
import { ReaderAuthProvider } from "./context/ReaderAuthContext";
import "./styles.css";

flushEngagementQueueSyncOnUnload();

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <BrowserRouter>
      <OperatorAuthProvider>
        <ReaderAuthProvider>
          <App />
        </ReaderAuthProvider>
      </OperatorAuthProvider>
    </BrowserRouter>
  </React.StrictMode>
);
