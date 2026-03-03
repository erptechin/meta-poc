import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { GetDataService, RunMetaEtlService } from "../services/platformService";
import "./PlatformData.css";

const WORKSPACE_ID = 1;

function formatDate(iso) {
  if (!iso) return "—";
  try {
    const d = new Date(iso);
    return d.toLocaleString(undefined, {
      dateStyle: "short",
      timeStyle: "short",
    });
  } catch {
    return iso;
  }
}

function formatBudget(value, currency = "INR") {
  if (value == null || value === "" || value === "0") return "—";
  const num = typeof value === "string" ? parseFloat(value, 10) : value;
  if (Number.isNaN(num)) return value;
  return new Intl.NumberFormat(undefined, {
    style: "currency",
    currency: currency,
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(num / 100);
}

function objectiveLabel(obj) {
  if (!obj) return "—";
  const map = {
    OUTCOME_AWARENESS: "Brand awareness",
    OUTCOME_ENGAGEMENT: "Engagement",
    OUTCOME_LEADS: "Lead generation",
    OUTCOME_SALES: "Sales / conversions",
    OUTCOME_TRAFFIC: "Traffic",
  };
  return map[obj] ?? obj;
}

export default function PlatformData() {
  const queryClient = useQueryClient();
  const [expandedCampaigns, setExpandedCampaigns] = useState(true);

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
          Run Meta ETL and view campaigns from your connected Meta ad accounts.
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
          Run Meta ETL and view campaigns from your connected Meta ad accounts.
        </p>
        <div className="platform-data__error">
          Failed to load: {error?.message || "Unknown error"}
        </div>
      </div>
    );
  }

  const storedData = data?.data ?? null;
  const campaigns = Array.isArray(storedData?.campaigns) ? storedData.campaigns : [];
  const hasStoredData = campaigns.length > 0;

  return (
    <div className="platform-data">
      <div className="platform-data__header">
        <div>
          <h2 className="platform-data__title">Platform Data</h2>
          <p className="platform-data__intro">
            Run Meta ETL and view campaigns from your connected Meta ad accounts.
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
          <div className="platform-data__sections">
            <section className="platform-data__section">
              <button
                type="button"
                className="platform-data__section-head"
                onClick={() => setExpandedCampaigns((v) => !v)}
                aria-expanded={expandedCampaigns}
              >
                <span className="platform-data__section-title">Campaigns</span>
                <span className="platform-data__section-count">{campaigns.length}</span>
                <span className="platform-data__section-chevron" aria-hidden>
                  {expandedCampaigns ? "▼" : "▶"}
                </span>
              </button>
              {expandedCampaigns && (
                <div className="platform-data__section-body">
                  <div className="platform-data__table-wrap">
                    <table className="platform-data__table">
                      <thead>
                        <tr>
                          <th>Name</th>
                          <th>Status</th>
                          <th>Objective</th>
                          <th>Daily budget</th>
                          <th>Lifetime budget</th>
                          <th>Created</th>
                        </tr>
                      </thead>
                      <tbody>
                        {campaigns.map((c) => (
                          <tr key={c.id}>
                            <td className="platform-data__cell-name" title={c.name}>
                              {c.name ?? "—"}
                            </td>
                            <td>
                              <span className={`platform-data__badge platform-data__badge--${(c.status || "").toLowerCase()}`}>
                                {c.status ?? "—"}
                              </span>
                            </td>
                            <td>{objectiveLabel(c.objective)}</td>
                            <td>{formatBudget(c.daily_budget)}</td>
                            <td>{formatBudget(c.lifetime_budget)}</td>
                            <td className="platform-data__cell-date">{formatDate(c.created_time)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </section>
          </div>
        ) : (
          <div className="platform-data__placeholder">
            <span className="platform-data__placeholder-icon" aria-hidden>
              📊
            </span>
            <p>No campaigns in DB. Connect Meta in Platform Integration, then click Run ETL to fetch and save.</p>
          </div>
        )}
      </div>
    </div>
  );
}
