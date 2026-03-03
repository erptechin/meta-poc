import React, { useEffect } from "react";
import { useSearchParams, useNavigate, useLocation } from "react-router-dom";
import "./CampaignResult.css";

/**
 * Single campaign result page: shows success or failure from path or query.
 * Path: /campaign-result?outcome=success|failure&message=...
 * Legacy paths /campaign-success and /campaign-failure still supported.
 */
export default function CampaignResult() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { pathname } = useLocation();
  const message = searchParams.get("message") || "";
  const outcomeParam = searchParams.get("outcome");
  const isSuccess =
    outcomeParam === "success" ||
    (!outcomeParam && pathname === "/campaign-success");



  useEffect(() => {
    const timeoutId = setTimeout(() => {
      navigate(`/`);
      if (window.opener) {
        window.opener.location.reload();
      }
      window.close();
    }, 4000);

    return () => clearTimeout(timeoutId);
  }, []);

  return (
    <div className="campaign-result">
      <div className="campaign-result__card">
        <div
          className={`campaign-result__icon campaign-result__icon--${isSuccess ? "success" : "failure"}`}
          aria-hidden
        >
          {isSuccess ? "✓" : "✕"}
        </div>
        <h1 className="campaign-result__title">
          {isSuccess ? "Campaign connected" : "Campaign connection failed"}
        </h1>
        <p className="campaign-result__subtitle">
          {isSuccess
            ? "Meta Ads has been linked to your workspace."
            : "Something went wrong while connecting Meta Ads."}
        </p>
        {message && (
          <div
            className={`campaign-result__message campaign-result__message--${isSuccess ? "success" : "failure"}`}
          >
            {decodeURIComponent(message)}
          </div>
        )}
        <div className="campaign-result__actions">
          <button
            type="button"
            className="campaign-result__btn campaign-result__btn--primary"
            onClick={() => navigate("/")}
          >
            Back to Platform Integration
          </button>
        </div>
      </div>
    </div>
  );
}
