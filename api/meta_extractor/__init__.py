"""
Rivery-style ETL for Meta Marketing API.
"""
from .config import META_API_VERSION, GRAPH_BASE_URL
from .extractor import extract_all, extract_ad_accounts, extract_campaigns, extract_ads, extract_ad_sets
from .transformer import transform
from .loader import load_to_store, load_to_dict
from .main import run_pipeline

__all__ = [
    "META_API_VERSION",
    "GRAPH_BASE_URL",
    "extract_all",
    "extract_ad_accounts",
    "extract_campaigns",
    "extract_ads",
    "extract_ad_sets",
    "transform",
    "load_to_store",
    "load_to_dict",
    "run_pipeline",
]
