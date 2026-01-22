"""
Analysis functions for US trade supply chain shifts.
Includes concentration metrics, structural break detection, and shift analysis.
"""

import pandas as pd
import numpy as np
from typing import List, Tuple, Optional, Dict
import logging

logger = logging.getLogger(__name__)


def calculate_hhi(
    df: pd.DataFrame,
    value_col: str = "value",
    country_col: str = "country",
    year_col: str = "year",
    trade_type_col: Optional[str] = "trade_type",
) -> pd.DataFrame:
    """
    Calculate Herfindahl-Hirschman Index (HHI) for import/export concentration.
    
    HHI ranges from 0 to 10,000:
    - < 1,500: Unconcentrated (diverse sources)
    - 1,500 - 2,500: Moderately concentrated
    - > 2,500: Highly concentrated
    
    Args:
        df: Trade data with value, country, and year columns
        value_col: Name of the value column
        country_col: Name of the country column
        year_col: Name of the year column
        trade_type_col: Optional column for import/export distinction
    
    Returns:
        DataFrame with HHI by year (and trade type if specified)
    """
    # Calculate market shares
    group_cols = [year_col]
    if trade_type_col and trade_type_col in df.columns:
        group_cols.append(trade_type_col)
    
    # Get yearly totals
    yearly_totals = df.groupby(group_cols)[value_col].sum().reset_index()
    yearly_totals.columns = group_cols + ["total"]
    
    # Merge and calculate shares
    df_shares = df.merge(yearly_totals, on=group_cols)
    df_shares["share"] = df_shares[value_col] / df_shares["total"]
    df_shares["share_squared"] = (df_shares["share"] * 100) ** 2
    
    # Sum squared shares to get HHI
    hhi = df_shares.groupby(group_cols)["share_squared"].sum().reset_index()
    hhi.columns = group_cols + ["hhi"]
    
    # Add concentration category
    def categorize_hhi(h):
        if h < 1500:
            return "Unconcentrated"
        elif h < 2500:
            return "Moderate"
        else:
            return "Concentrated"
    
    hhi["concentration"] = hhi["hhi"].apply(categorize_hhi)
    
    return hhi


def detect_structural_breaks(
    series: pd.Series,
    window: int = 5,
    threshold: float = 2.0,
) -> List[int]:
    """
    Detect structural breaks in a time series using rolling statistics.
    
    A simple approach: identify points where the value deviates significantly
    from the rolling mean (more than threshold * rolling std).
    
    Args:
        series: Time series to analyze (indexed by year)
        window: Rolling window size
        threshold: Number of standard deviations for break detection
    
    Returns:
        List of years where structural breaks were detected
    """
    rolling_mean = series.rolling(window=window, center=True).mean()
    rolling_std = series.rolling(window=window, center=True).std()
    
    # Calculate z-scores
    z_scores = (series - rolling_mean) / rolling_std
    
    # Find breaks (absolute z-score exceeds threshold)
    breaks = series.index[abs(z_scores) > threshold].tolist()
    
    return breaks


def analyze_country_shifts(
    df: pd.DataFrame,
    start_year: int,
    end_year: int,
    value_col: str = "value",
    country_col: str = "country",
    year_col: str = "year",
    top_n: int = 20,
) -> Dict[str, pd.DataFrame]:
    """
    Comprehensive analysis of country-level trade shifts between two years.
    
    Args:
        df: Trade data
        start_year: Beginning of comparison period
        end_year: End of comparison period
        value_col: Name of the value column
        country_col: Name of the country column
        year_col: Name of the year column
        top_n: Number of top countries to include
    
    Returns:
        Dictionary with analysis results:
        - 'summary': Overall shift summary
        - 'gainers': Countries that gained share
        - 'losers': Countries that lost share
        - 'rankings': Rank changes
    """
    results = {}
    
    # Get data for start and end years
    start_data = df[df[year_col] == start_year].copy()
    end_data = df[df[year_col] == end_year].copy()
    
    # Calculate totals and shares
    start_total = start_data[value_col].sum()
    end_total = end_data[value_col].sum()
    
    start_data["share"] = start_data[value_col] / start_total * 100
    end_data["share"] = end_data[value_col] / end_total * 100
    
    # Merge for comparison
    comparison = start_data[[country_col, value_col, "share"]].merge(
        end_data[[country_col, value_col, "share"]],
        on=country_col,
        how="outer",
        suffixes=(f"_{start_year}", f"_{end_year}")
    ).fillna(0)
    
    # Calculate changes
    comparison["value_change"] = (
        comparison[f"value_{end_year}"] - comparison[f"value_{start_year}"]
    )
    comparison["share_change"] = (
        comparison[f"share_{end_year}"] - comparison[f"share_{start_year}"]
    )
    comparison["value_growth_pct"] = (
        comparison["value_change"] / comparison[f"value_{start_year}"] * 100
    ).replace([np.inf, -np.inf], np.nan)
    
    # Add rankings
    comparison[f"rank_{start_year}"] = comparison[f"value_{start_year}"].rank(
        ascending=False, method="min"
    )
    comparison[f"rank_{end_year}"] = comparison[f"value_{end_year}"].rank(
        ascending=False, method="min"
    )
    comparison["rank_change"] = (
        comparison[f"rank_{start_year}"] - comparison[f"rank_{end_year}"]
    )
    
    # Sort by end year value for top countries
    comparison = comparison.sort_values(f"value_{end_year}", ascending=False)
    
    # Summary stats
    results["summary"] = pd.DataFrame({
        "metric": [
            f"Total Trade {start_year}",
            f"Total Trade {end_year}",
            "Absolute Growth",
            "Percent Growth",
            "Countries in Start",
            "Countries in End",
        ],
        "value": [
            start_total,
            end_total,
            end_total - start_total,
            (end_total - start_total) / start_total * 100,
            len(start_data),
            len(end_data),
        ]
    })
    
    # Top gainers (by share change)
    results["gainers"] = comparison.nlargest(top_n, "share_change")[
        [country_col, f"share_{start_year}", f"share_{end_year}", 
         "share_change", "value_growth_pct"]
    ].reset_index(drop=True)
    
    # Top losers (by share change)
    results["losers"] = comparison.nsmallest(top_n, "share_change")[
        [country_col, f"share_{start_year}", f"share_{end_year}", 
         "share_change", "value_growth_pct"]
    ].reset_index(drop=True)
    
    # Ranking changes
    results["rankings"] = comparison.head(top_n)[
        [country_col, f"rank_{start_year}", f"rank_{end_year}", "rank_change"]
    ].reset_index(drop=True)
    
    return results


def calculate_trade_balance(
    imports_df: pd.DataFrame,
    exports_df: pd.DataFrame,
    value_col: str = "value",
    country_col: str = "country",
    year_col: str = "year",
) -> pd.DataFrame:
    """
    Calculate trade balance (exports - imports) by country and year.
    
    Args:
        imports_df: Import data
        exports_df: Export data
        value_col: Name of the value column
        country_col: Name of the country column
        year_col: Name of the year column
    
    Returns:
        DataFrame with trade balance calculations
    """
    # Aggregate by country and year
    imports_agg = imports_df.groupby([country_col, year_col])[value_col].sum().reset_index()
    imports_agg.columns = [country_col, year_col, "imports"]
    
    exports_agg = exports_df.groupby([country_col, year_col])[value_col].sum().reset_index()
    exports_agg.columns = [country_col, year_col, "exports"]
    
    # Merge
    balance = imports_agg.merge(exports_agg, on=[country_col, year_col], how="outer").fillna(0)
    
    # Calculate balance
    balance["trade_balance"] = balance["exports"] - balance["imports"]
    balance["total_trade"] = balance["exports"] + balance["imports"]
    balance["balance_ratio"] = balance["trade_balance"] / balance["total_trade"]
    
    return balance


def identify_emerging_partners(
    df: pd.DataFrame,
    lookback_years: int = 10,
    growth_threshold: float = 100,
    min_final_share: float = 1.0,
    value_col: str = "value",
    country_col: str = "country",
    year_col: str = "year",
) -> pd.DataFrame:
    """
    Identify countries that have emerged as significant trade partners.
    
    Criteria:
    - Growth rate above threshold over lookback period
    - Final year share above minimum threshold
    
    Args:
        df: Trade data
        lookback_years: Number of years to look back
        growth_threshold: Minimum growth percentage to qualify
        min_final_share: Minimum share in final year (percent)
        value_col: Name of the value column
        country_col: Name of the country column
        year_col: Name of the year column
    
    Returns:
        DataFrame with emerging partner countries
    """
    max_year = df[year_col].max()
    min_year = max_year - lookback_years
    
    # Filter to lookback period
    period_df = df[df[year_col] >= min_year].copy()
    
    # Get start and end values
    start_values = period_df[period_df[year_col] == min_year].set_index(country_col)[value_col]
    end_values = period_df[period_df[year_col] == max_year].set_index(country_col)[value_col]
    
    # Calculate final year shares
    end_total = end_values.sum()
    end_shares = end_values / end_total * 100
    
    # Calculate growth
    growth = ((end_values - start_values) / start_values * 100).replace([np.inf, -np.inf], np.nan)
    
    # Combine
    emerging = pd.DataFrame({
        "start_value": start_values,
        "end_value": end_values,
        "growth_pct": growth,
        "end_share": end_shares,
    }).reset_index()
    
    # Filter by criteria
    emerging = emerging[
        (emerging["growth_pct"] >= growth_threshold) & 
        (emerging["end_share"] >= min_final_share)
    ].sort_values("growth_pct", ascending=False)
    
    return emerging
