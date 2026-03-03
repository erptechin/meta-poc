import React from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { GetDataService, RunMetaEtlService } from "../services/platformService";
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

  const runEtlMutation = useMutation({
    mutationFn: () => RunMetaEtlService(WORKSPACE_ID),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["platform-data", WORKSPACE_ID] });
    },
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
  const hasStoredData =
    storedData &&
    typeof storedData === "object" &&
    (([storedData.ad_accounts, storedData.campaigns, storedData.adsets, storedData.ads].some(
      (arr) => Array.isArray(arr) && arr.length > 0
    )));

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
          onClick={() => runEtlMutation.mutate()}
          disabled={runEtlMutation.isPending}
        >
          {runEtlMutation.isPending ? "Running ETL…" : "Run ETL"}
        </button>
      </div>
      <div className="platform-data__content">
        {hasStoredData ? (
          <pre className="platform-data__json">{JSON.stringify(storedData, null, 2)}</pre>
        ) : (
          <div className="platform-data__placeholder">
            <span className="platform-data__placeholder-icon" aria-hidden>
              📊
            </span>
            <p>No data in DB. Connect Meta in Platform Integration, then click Run ETL to fetch and save.</p>
          </div>
        )}
      </div>
    </div>
  );
}
