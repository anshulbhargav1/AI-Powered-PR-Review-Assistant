import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { App } from "./App";
import { RepositoriesProvider } from "./context/RepositoriesContext";
import "./index.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <BrowserRouter>
      <RepositoriesProvider>
        <App />
      </RepositoriesProvider>
    </BrowserRouter>
  </React.StrictMode>
);
