import React, { useEffect } from "react";
import { useSearchParams, useNavigate, useLocation } from "react-router-dom";
import "./IntegrationResult.css";

/**
 * Platform integration result page: shows success or failure from path or query.
 * Path: /integration-result?outcome=success|failure&message=...
 * Legacy paths /platform-integration-success and /platform-integration-failure supported.
 */
export default function IntegrationResult() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { pathname } = useLocation();
  const message = searchParams.get("message") || "";
  const outcomeParam = searchParams.get("outcome");
  const isSuccess =
    outcomeParam === "success" ||
    (!outcomeParam && pathname === "/platform-integration-success");

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
    <div className="integration-result">
      <div className="integration-result__card">
        <div
          className={`integration-result__icon integration-result__icon--${isSuccess ? "success" : "failure"}`}
          aria-hidden
        >
          {isSuccess ? "✓" : "✕"}
        </div>
        <h1 className="integration-result__title">
          {isSuccess ? "Platform connected" : "Platform connection failed"}
        </h1>
        <p className="integration-result__subtitle">
          {isSuccess
            ? "Meta Ads has been linked to your workspace."
            : "Something went wrong while connecting Meta Ads."}
        </p>
        {message && (
          <div
            className={`integration-result__message integration-result__message--${isSuccess ? "success" : "failure"}`}
          >
            {decodeURIComponent(message)}
          </div>
        )}
        <div className="integration-result__actions">
          <button
            type="button"
            className="integration-result__btn integration-result__btn--primary"
            onClick={() => navigate("/platform-integration")}
          >
            Back to Platform Integration
          </button>
        </div>
      </div>
    </div>
  );
}
