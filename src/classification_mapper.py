"""
Classification mapping utilities for harmonizing trade data across time.
Handles country name standardization and commodity code mapping.
"""

import pandas as pd
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

# Standard country name mappings for common variations
COUNTRY_NAME_MAPPINGS: Dict[str, str] = {
    # China variations
    "CHINA, PEOPLES REPUBLIC OF": "China",
    "CHINA": "China",
    "CHINA, P.R.": "China",
    "PEOPLES REPUBLIC OF CHINA": "China",
    
    # Taiwan variations
    "TAIWAN": "Taiwan",
    "TAIWAN, PROVINCE OF CHINA": "Taiwan",
    "CHINESE TAIPEI": "Taiwan",
    
    # Hong Kong
    "HONG KONG": "Hong Kong",
    "HONG KONG SAR": "Hong Kong",
    "HONG KONG, CHINA": "Hong Kong",
    
    # Korea variations
    "KOREA, SOUTH": "South Korea",
    "KOREA, REPUBLIC OF": "South Korea",
    "SOUTH KOREA": "South Korea",
    "REPUBLIC OF KOREA": "South Korea",
    "KOREA, NORTH": "North Korea",
    "KOREA, DEM PEOPLES REP": "North Korea",
    
    # Vietnam
    "VIETNAM": "Vietnam",
    "VIET NAM": "Vietnam",
    "VIETNAM, SOC REP OF": "Vietnam",
    
    # Germany
    "GERMANY": "Germany",
    "GERMANY, FEDERAL REPUBLIC OF": "Germany",
    "GERMANY, WEST": "Germany",
    "GERMANY, EAST": "Germany (East)",
    
    # UK variations
    "UNITED KINGDOM": "United Kingdom",
    "UK": "United Kingdom",
    "GREAT BRITAIN": "United Kingdom",
    
    # Russia/USSR
    "RUSSIA": "Russia",
    "RUSSIAN FEDERATION": "Russia",
    "USSR": "Soviet Union",
    "SOVIET UNION": "Soviet Union",
    
    # Mexico
    "MEXICO": "Mexico",
    
    # Canada
    "CANADA": "Canada",
    
    # Japan
    "JAPAN": "Japan",
    
    # India
    "INDIA": "India",
    
    # Other common ones
    "UNITED STATES": "United States",
    "USA": "United States",
    "U.S.A.": "United States",
}

# USSR successor states (for historical data harmonization)
USSR_SUCCESSOR_STATES = [
    "Russia", "Ukraine", "Belarus", "Kazakhstan", "Uzbekistan",
    "Turkmenistan", "Kyrgyzstan", "Tajikistan", "Azerbaijan",
    "Armenia", "Georgia", "Moldova", "Lithuania", "Latvia", "Estonia"
]

# Yugoslavia successor states
YUGOSLAVIA_SUCCESSOR_STATES = [
    "Slovenia", "Croatia", "Bosnia and Herzegovina", "Serbia",
    "Montenegro", "North Macedonia", "Kosovo"
]


def standardize_country_names(
    df: pd.DataFrame,
    country_col: str = "country",
    custom_mappings: Optional[Dict[str, str]] = None,
) -> pd.DataFrame:
    """
    Standardize country names to consistent format.
    
    Args:
        df: DataFrame with country column
        country_col: Name of the country column
        custom_mappings: Additional custom mappings to apply
    
    Returns:
        DataFrame with standardized country names
    """
    df = df.copy()
    
    # Combine default and custom mappings
    mappings = COUNTRY_NAME_MAPPINGS.copy()
    if custom_mappings:
        mappings.update(custom_mappings)
    
    # Apply mappings (case-insensitive)
    original_countries = df[country_col].unique()
    
    def map_country(name):
        if pd.isna(name):
            return name
        upper_name = str(name).upper().strip()
        for pattern, standard in mappings.items():
            if upper_name == pattern.upper():
                return standard
        return name.strip()  # Return original if no mapping
    
    df[country_col] = df[country_col].apply(map_country)
    
    # Log changes
    new_countries = df[country_col].unique()
    mapped_count = len(original_countries) - len(new_countries)
    if mapped_count > 0:
        logger.info(f"Standardized {mapped_count} country name variations")
    
    return df


def create_country_mapping_report(
    df: pd.DataFrame,
    country_col: str = "country",
) -> pd.DataFrame:
    """
    Create a report of unique country names and their frequencies.
    Useful for identifying unmapped variations.
    
    Args:
        df: DataFrame with country column
        country_col: Name of the country column
    
    Returns:
        DataFrame with country names and counts
    """
    counts = df[country_col].value_counts().reset_index()
    counts.columns = ["country", "record_count"]
    
    # Check if each name is in our standard mappings
    counts["is_mapped"] = counts["country"].apply(
        lambda x: str(x).upper().strip() in 
        {k.upper() for k in COUNTRY_NAME_MAPPINGS.keys()}
    )
    
    return counts


def get_historical_period(year: int) -> str:
    """
    Categorize a year into a historical trade period.
    
    Args:
        year: Year to categorize
    
    Returns:
        Period name string
    """
    if year < 1989:
        return "Pre-DataWeb"
    elif year < 1994:
        return "Pre-NAFTA"
    elif year < 2001:
        return "Pre-WTO China"
    elif year < 2008:
        return "China WTO Boom"
    elif year < 2010:
        return "Financial Crisis"
    elif year < 2018:
        return "Post-Crisis Growth"
    elif year < 2020:
        return "Trade War"
    elif year < 2022:
        return "COVID Era"
    else:
        return "Post-COVID"


def add_historical_period(
    df: pd.DataFrame,
    year_col: str = "year",
) -> pd.DataFrame:
    """
    Add historical period classification to DataFrame.
    
    Args:
        df: DataFrame with year column
        year_col: Name of the year column
    
    Returns:
        DataFrame with added 'period' column
    """
    df = df.copy()
    df["period"] = df[year_col].apply(get_historical_period)
    return df


def create_commodity_crosswalk(
    old_codes: pd.DataFrame,
    new_codes: pd.DataFrame,
    old_code_col: str = "old_code",
    new_code_col: str = "new_code",
) -> Dict[str, str]:
    """
    Create a mapping between old and new commodity codes.
    Placeholder for future implementation with actual HTS concordance tables.
    
    Args:
        old_codes: DataFrame with old classification codes
        new_codes: DataFrame with new classification codes
        old_code_col: Column name for old codes
        new_code_col: Column name for new codes
    
    Returns:
        Dictionary mapping old codes to new codes
    """
    # This would be populated with actual HTS concordance data
    # For now, return empty dict as placeholder
    logger.warning(
        "Commodity crosswalk not yet implemented. "
        "Load HTS concordance tables for full functionality."
    )
    return {}
