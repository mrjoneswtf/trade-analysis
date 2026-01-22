# US Trade Data Analysis Package
"""
Utilities for analyzing US import/export data to understand
supply chain country shifts over time.
"""

from .data_loader import load_usitc_data, load_all_trade_data
from .transformers import (
    calculate_country_shares,
    calculate_yoy_growth,
    adjust_for_inflation,
)
from .classification_mapper import standardize_country_names
from .analysis import (
    calculate_hhi,
    detect_structural_breaks,
    analyze_country_shifts,
)
from .usitc_api import USITCDataWebAPI, fetch_and_save_trade_data

__version__ = "0.1.0"
