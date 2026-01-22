"""
Data transformation utilities for US trade analysis.
Handles calculations for shares, growth rates, and inflation adjustment.
"""

import pandas as pd
import numpy as np
from typing import Optional, List


def calculate_country_shares(
    df: pd.DataFrame,
    value_col: str = "value",
    country_col: str = "country",
    year_col: str = "year",
    trade_type_col: Optional[str] = "trade_type",
) -> pd.DataFrame:
    """
    Calculate each country's share of total trade by year.
    
    Args:
        df: Trade data with value, country, and year columns
        value_col: Name of the value column
        country_col: Name of the country column
        year_col: Name of the year column
        trade_type_col: Optional column for import/export distinction
    
    Returns:
        DataFrame with added 'share' and 'share_pct' columns
    """
    df = df.copy()
    
    # Group columns for total calculation
    group_cols = [year_col]
    if trade_type_col and trade_type_col in df.columns:
        group_cols.append(trade_type_col)
    
    # Calculate yearly totals
    yearly_totals = df.groupby(group_cols)[value_col].transform("sum")
    
    # Calculate shares
    df["share"] = df[value_col] / yearly_totals
    df["share_pct"] = df["share"] * 100
    
    return df


def calculate_yoy_growth(
    df: pd.DataFrame,
    value_col: str = "value",
    country_col: str = "country",
    year_col: str = "year",
    trade_type_col: Optional[str] = "trade_type",
) -> pd.DataFrame:
    """
    Calculate year-over-year growth rates for each country.
    
    Args:
        df: Trade data
        value_col: Name of the value column
        country_col: Name of the country column
        year_col: Name of the year column
        trade_type_col: Optional column for import/export distinction
    
    Returns:
        DataFrame with added 'yoy_growth' and 'yoy_growth_pct' columns
    """
    df = df.copy()
    df = df.sort_values([country_col, year_col])
    
    # Group columns
    group_cols = [country_col]
    if trade_type_col and trade_type_col in df.columns:
        group_cols.append(trade_type_col)
    
    # Calculate YoY growth
    df["prev_value"] = df.groupby(group_cols)[value_col].shift(1)
    df["yoy_growth"] = (df[value_col] - df["prev_value"]) / df["prev_value"]
    df["yoy_growth_pct"] = df["yoy_growth"] * 100
    
    # Clean up
    df = df.drop(columns=["prev_value"])
    
    return df


def calculate_rolling_average(
    df: pd.DataFrame,
    value_col: str = "value",
    country_col: str = "country",
    year_col: str = "year",
    window: int = 3,
) -> pd.DataFrame:
    """
    Calculate rolling average for smoothing trends.
    
    Args:
        df: Trade data
        value_col: Name of the value column
        country_col: Name of the country column
        year_col: Name of the year column
        window: Rolling window size (years)
    
    Returns:
        DataFrame with added rolling average column
    """
    df = df.copy()
    df = df.sort_values([country_col, year_col])
    
    col_name = f"{value_col}_rolling_{window}yr"
    df[col_name] = df.groupby(country_col)[value_col].transform(
        lambda x: x.rolling(window=window, min_periods=1).mean()
    )
    
    return df


def adjust_for_inflation(
    df: pd.DataFrame,
    deflator_df: pd.DataFrame,
    value_col: str = "value",
    year_col: str = "year",
    base_year: int = 2020,
) -> pd.DataFrame:
    """
    Adjust nominal values to real values using GDP deflator.
    
    Args:
        df: Trade data with nominal values
        deflator_df: DataFrame with 'year' and 'deflator' columns
        value_col: Name of the value column
        year_col: Name of the year column
        base_year: Base year for real values (deflator = 100)
    
    Returns:
        DataFrame with added 'value_real' column
    """
    df = df.copy()
    
    # Ensure deflator is indexed properly
    deflator_map = deflator_df.set_index("year")["deflator"].to_dict()
    
    # Get base year deflator
    base_deflator = deflator_map.get(base_year, 100)
    
    # Calculate adjustment factor for each year
    df["deflator"] = df[year_col].map(deflator_map)
    df["value_real"] = df[value_col] * (base_deflator / df["deflator"])
    
    # Clean up
    df = df.drop(columns=["deflator"])
    
    return df


def calculate_share_change(
    df: pd.DataFrame,
    start_year: int,
    end_year: int,
    country_col: str = "country",
    year_col: str = "year",
    share_col: str = "share_pct",
) -> pd.DataFrame:
    """
    Calculate change in market share between two years.
    
    Args:
        df: Trade data with share calculations
        start_year: Starting year for comparison
        end_year: Ending year for comparison
        country_col: Name of the country column
        year_col: Name of the year column
        share_col: Name of the share column
    
    Returns:
        DataFrame with share change by country
    """
    start_shares = df[df[year_col] == start_year].set_index(country_col)[share_col]
    end_shares = df[df[year_col] == end_year].set_index(country_col)[share_col]
    
    result = pd.DataFrame({
        f"share_{start_year}": start_shares,
        f"share_{end_year}": end_shares,
    })
    
    result["share_change"] = result[f"share_{end_year}"] - result[f"share_{start_year}"]
    result["share_change_pct"] = (
        result["share_change"] / result[f"share_{start_year}"] * 100
    )
    
    return result.reset_index().sort_values("share_change", ascending=False)


def aggregate_by_period(
    df: pd.DataFrame,
    periods: dict,
    value_col: str = "value",
    country_col: str = "country",
    year_col: str = "year",
) -> pd.DataFrame:
    """
    Aggregate trade data by named time periods.
    
    Args:
        df: Trade data
        periods: Dict mapping period names to (start_year, end_year) tuples
            e.g., {"Pre-WTO": (1995, 2000), "WTO Boom": (2001, 2008)}
        value_col: Name of the value column
        country_col: Name of the country column
        year_col: Name of the year column
    
    Returns:
        DataFrame aggregated by period and country
    """
    results = []
    
    for period_name, (start, end) in periods.items():
        period_df = df[(df[year_col] >= start) & (df[year_col] <= end)]
        
        agg = period_df.groupby(country_col).agg({
            value_col: ["sum", "mean"],
            year_col: ["min", "max", "count"],
        })
        
        agg.columns = ["total_value", "avg_yearly_value", "start_year", "end_year", "years"]
        agg["period"] = period_name
        agg = agg.reset_index()
        
        results.append(agg)
    
    return pd.concat(results, ignore_index=True)
