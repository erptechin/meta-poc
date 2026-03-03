import React from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { GetDataService } from "../services/platformService";
import "./PlatformData.css";

const WORKSPACE_ID = 1;

export default function PlatformData() {
  const queryClient = useQueryClient();

  const {
    data,
    isLoading,
    isError,
    error,
  } = useQuery({
    queryKey: ["platform-data", WORKSPACE_ID],
    queryFn: () => GetDataService(WORKSPACE_ID),
  });

  if (isLoading) {
    return (
      <div className="platform-data">
        <h2 className="platform-data__title">Platform Data</h2>
        <p className="platform-data__intro">
          Run Meta ETL and view data from your connected Meta ad accounts.
        </p>
        <div className="platform-data__loading">Loading…</div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="platform-data">
        <h2 className="platform-data__title">Platform Data</h2>
        <p className="platform-data__intro">
          Run Meta ETL and view data from your connected Meta ad accounts.
        </p>
        <div className="platform-data__error">
          Failed to load: {error?.message || "Unknown error"}
        </div>
      </div>
    );
  }

  const storedData = data?.data ?? null;
  const isList = Array.isArray(storedData);
  const hasItems = isList ? storedData.length > 0 : storedData != null;

  return (
    <div className="platform-data">
      <div className="platform-data__header">
        <div>
          <h2 className="platform-data__title">Platform Data</h2>
          <p className="platform-data__intro">
            Run Meta ETL and view data from your connected Meta ad accounts.
          </p>
        </div>
        <button
          type="button"
          className="platform-data__refresh-btn"
          onClick={() => queryClient.invalidateQueries({ queryKey: ["platform-data", WORKSPACE_ID] })}
        >
          Refresh
        </button>
      </div>
      <div className="platform-data__content">
        {hasItems ? (
          <pre className="platform-data__json">{JSON.stringify(storedData, null, 2)}</pre>
        ) : (
          <div className="platform-data__placeholder">
            <span className="platform-data__placeholder-icon" aria-hidden>
              📊
            </span>
            <p>No Meta integration. Connect Meta in Platform Integration, then click Refresh.</p>
          </div>
        )}
      </div>
    </div>
  );
}
