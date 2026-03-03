"""
meta_extractor – Rivery-style ETL for Meta (Facebook) Marketing API.
Configuration and constants.
"""
import os

META_API_VERSION = os.getenv("META_API_VERSION", "v23.0")
GRAPH_BASE_URL = f"https://graph.facebook.com/{META_API_VERSION}"

# Default fields for extraction
AD_ACCOUNT_FIELDS = "id,account_id,name,account_status,currency,timezone_name"
CAMPAIGN_FIELDS = "id,name,status,objective,daily_budget,lifetime_budget,created_time,updated_time"
ADSET_FIELDS = "id,name,status,daily_budget,lifetime_budget,targeting,created_time,updated_time"
AD_FIELDS = "id,name,status,creative{id,name},created_time,updated_time"

# Timeouts and limits
REQUEST_TIMEOUT = 30.0
MAX_PAGES_PER_REQUEST = 25
