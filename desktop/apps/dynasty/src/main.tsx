import React from "react";
import ReactDOM from "react-dom/client";
import { HashRouter } from "react-router-dom";

import "@nwr/ui/styles.css";
import { OwnerErrorBoundary } from "@nwr/ui";
import "./pages.css";
import { DynastyApp } from "./DynastyApp";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <OwnerErrorBoundary mode="dynasty">
      <HashRouter>
        <DynastyApp />
      </HashRouter>
    </OwnerErrorBoundary>
  </React.StrictMode>,
);
