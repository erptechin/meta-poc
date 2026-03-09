import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { GetDataService, RunMetaEtlService } from "../services/platformService";
import "./PlatformData.css";

const WORKSPACE_ID = 1;

function formatDate(iso) {
  if (!iso) return "—";
  try {
    const d = new Date(iso);
    return d.toLocaleDateString(undefined, { dateStyle: "short" });
  } catch {
    return iso;
  }
}

function formatNum(n) {
  if (n == null || n === "") return "—";
  const num = typeof n === "string" ? parseFloat(n, 10) : n;
  if (Number.isNaN(num)) return "—";
  return new Intl.NumberFormat(undefined, { maximumFractionDigits: 2 }).format(num);
}

function formatCurrency(value) {
  if (value == null || value === "") return "—";
  const num = typeof value === "string" ? parseFloat(value, 10) : value;
  if (Number.isNaN(num)) return "—";
  return new Intl.NumberFormat(undefined, {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(num);
}

export default function PlatformData() {
  const queryClient = useQueryClient();
  const [expanded, setExpanded] = useState(true);
  const [reportDate, setReportDate] = useState("");
  const [reportDateFrom, setReportDateFrom] = useState("");
  const [reportDateTo, setReportDateTo] = useState("");

  const queryParams = {};
  if (reportDate) queryParams.reportDate = reportDate;
  if (reportDateFrom) queryParams.reportDateFrom = reportDateFrom;
  if (reportDateTo) queryParams.reportDateTo = reportDateTo;

  const {
    data,
    isLoading,
    isError,
    error,
  } = useQuery({
    queryKey: ["platform-data", WORKSPACE_ID, queryParams],
    queryFn: () => GetDataService(WORKSPACE_ID, queryParams),
  });

  const runEtlMutation = useMutation({
    mutationFn: () => RunMetaEtlService(WORKSPACE_ID, reportDate || null),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["platform-data", WORKSPACE_ID] });
    },
  });

  if (isLoading) {
    return (
      <div className="platform-data">
        <h2 className="platform-data__title">Platform Data</h2>
        <p className="platform-data__intro">
          Run Meta ETL and view campaign insights by report date.
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
          Run Meta ETL and view campaign insights by report date.
        </p>
        <div className="platform-data__error">
          Failed to load: {error?.message || "Unknown error"}
        </div>
      </div>
    );
  }

  const rows = Array.isArray(data?.data) ? data.data : [];
  const hasData = rows.length > 0;

  return (
    <div className="platform-data">
      <div className="platform-data__header">
        <div>
          <h2 className="platform-data__title">Platform Data</h2>
          <p className="platform-data__intro">
            Fetch data by report date. Run ETL to pull Meta campaign insights for a date and save to DB.
          </p>
        </div>
        <div className="platform-data__actions">
          <div className="platform-data__filters">
            <label>
              <span>Report date</span>
              <input
                type="date"
                value={reportDate}
                onChange={(e) => setReportDate(e.target.value)}
                title="Filter by single date"
              />
            </label>
            <label>
              <span>From</span>
              <input
                type="date"
                value={reportDateFrom}
                onChange={(e) => setReportDateFrom(e.target.value)}
              />
            </label>
            <label>
              <span>To</span>
              <input
                type="date"
                value={reportDateTo}
                onChange={(e) => setReportDateTo(e.target.value)}
              />
            </label>
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
      </div>
      <div className="platform-data__content">
        {hasData ? (
          <div className="platform-data__sections">
            <section className="platform-data__section">
              <button
                type="button"
                className="platform-data__section-head"
                onClick={() => setExpanded((v) => !v)}
                aria-expanded={expanded}
              >
                <span className="platform-data__section-title">By report date</span>
                <span className="platform-data__section-count">{rows.length}</span>
                <span className="platform-data__section-chevron" aria-hidden>
                  {expanded ? "▼" : "▶"}
                </span>
              </button>
              {expanded && (
                <div className="platform-data__section-body">
                  <div className="platform-data__table-wrap">
                    <table className="platform-data__table">
                      <thead>
                        <tr>
                          <th>Report date</th>
                          <th>Campaign</th>
                          <th>Impressions</th>
                          <th>Clicks</th>
                          <th>Spend</th>
                          <th>CPM</th>
                          <th>CPC</th>
                          <th>CTR</th>
                        </tr>
                      </thead>
                      <tbody>
                        {rows.map((r, i) => (
                          <tr key={r.id ?? i}>
                            <td className="platform-data__cell-date">{formatDate(r.report_date)}</td>
                            <td className="platform-data__cell-name" title={r.campaign_name}>
                              {r.campaign_name ?? "—"}
                            </td>
                            <td>{formatNum(r.impressions)}</td>
                            <td>{formatNum(r.clicks)}</td>
                            <td>{formatCurrency(r.amount_spent)}</td>
                            <td>{formatNum(r.cpm)}</td>
                            <td>{formatCurrency(r.cpc)}</td>
                            <td>{r.ctr != null ? `${formatNum(r.ctr)}%` : "—"}</td>
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
            <p>No data yet. Connect Meta in Platform Integration, then click Run ETL to fetch insights for a date (default: yesterday).</p>
          </div>
        )}
      </div>
    </div>
  );
}
