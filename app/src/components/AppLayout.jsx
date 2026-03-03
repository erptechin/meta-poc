import React from "react";
import { Outlet, NavLink } from "react-router-dom";
import "./AppLayout.css";

export default function AppLayout() {
  return (
    <div className="app-layout">
      <header className="app-layout__header">
        <nav className="app-layout__nav" aria-label="Main">
          <NavLink
            to="/platform-integration"
            className={({ isActive }) =>
              `app-layout__link ${isActive ? "app-layout__link--active" : ""}`
            }
            end
          >
            Platform Integration
          </NavLink>
          <NavLink
            to="/platform-data"
            className={({ isActive }) =>
              `app-layout__link ${isActive ? "app-layout__link--active" : ""}`
            }
          >
            Platform Data
          </NavLink>
        </nav>
      </header>
      <main className="app-layout__main">
        <Outlet />
      </main>
    </div>
  );
}
