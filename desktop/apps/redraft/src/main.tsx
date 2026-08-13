import React from "react";
import ReactDOM from "react-dom/client";
import { HashRouter } from "react-router-dom";

import "@nwr/ui/styles.css";
import { OwnerErrorBoundary } from "@nwr/ui";
import "./redraft.css";
import { RedraftApp } from "./RedraftApp";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <OwnerErrorBoundary mode="redraft">
      <HashRouter><RedraftApp /></HashRouter>
    </OwnerErrorBoundary>
  </React.StrictMode>,
);
