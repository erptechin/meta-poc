"""
google_extractor – Rivery-style ETL for Google Ads API.
Configuration and constants.
"""
import os

REQUEST_TIMEOUT = float(os.getenv("GOOGLE_ADS_REQUEST_TIMEOUT", "30.0"))
# Google Ads API developer token (required for API access; set in .env)
GOOGLE_ADS_DEVELOPER_TOKEN = os.getenv("GOOGLE_ADS_DEVELOPER_TOKEN", "")
