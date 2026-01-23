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


def parse_monthly_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Transform monthly USITC data from wide to long format.
    
    USITC monthly data has columns like 'Jan 2024', 'Feb 2024', etc.
    This function converts to long format with year and month columns.
    
    Args:
        df: Wide-format DataFrame with country column and month columns
    
    Returns:
        Long-format DataFrame with columns: country, year, month, value
    """
    df = df.copy()
    
    # Get the country column (first column)
    country_col = df.columns[0]
    
    # Identify month columns (format: 'Mon YYYY' like 'Jan 2024')
    month_map = {
        'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
        'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
    }
    
    month_cols = []
    for col in df.columns[1:]:
        col_str = str(col).strip()
        parts = col_str.split()
        if len(parts) == 2 and parts[0] in month_map:
            month_cols.append(col)
    
    if not month_cols:
        # Fallback: try YYYYMM format
        for col in df.columns[1:]:
            col_str = str(col).strip()
            if len(col_str) == 6 and col_str.isdigit():
                month_cols.append(col)
    
    # Filter to country + month columns
    df_subset = df[[country_col] + month_cols].copy()
    
    # Melt to long format
    df_long = df_subset.melt(
        id_vars=[country_col],
        var_name='period',
        value_name='value'
    )
    df_long = df_long.rename(columns={country_col: 'country'})
    
    # Parse period into year and month
    def parse_period(p):
        p_str = str(p).strip()
        parts = p_str.split()
        if len(parts) == 2 and parts[0] in month_map:
            return int(parts[1]), month_map[parts[0]]
        elif len(p_str) == 6 and p_str.isdigit():
            return int(p_str[:4]), int(p_str[4:])
        return None, None
    
    df_long[['year', 'month']] = df_long['period'].apply(
        lambda x: pd.Series(parse_period(x))
    )
    
    # Drop rows where parsing failed
    df_long = df_long.dropna(subset=['year', 'month'])
    df_long['year'] = df_long['year'].astype(int)
    df_long['month'] = df_long['month'].astype(int)
    
    # Convert value to numeric
    df_long['value'] = pd.to_numeric(
        df_long['value'].astype(str).str.replace(',', '').str.replace('"', ''),
        errors='coerce'
    )
    
    # Filter out non-country rows
    exclude_rows = ['Total:', 'Total', 'Unspecified', 'Transshipment', 'Internat Organization']
    df_long = df_long[~df_long['country'].str.strip().isin(exclude_rows)]
    
    # Convert from billions to actual USD (if needed - check data format)
    # df_long['value'] = df_long['value'] * 1e9
    
    return df_long[['country', 'year', 'month', 'value']]


def aggregate_monthly_to_annual(
    df: pd.DataFrame,
    value_col: str = "value",
    country_col: str = "country",
    year_col: str = "year",
    month_col: str = "month",
) -> pd.DataFrame:
    """
    Aggregate monthly data to annual totals.
    
    Marks incomplete years (< 12 months) with a flag for YTD display.
    
    Args:
        df: Monthly trade data with country, year, month, value columns
        value_col: Name of the value column
        country_col: Name of the country column
        year_col: Name of the year column
        month_col: Name of the month column
    
    Returns:
        DataFrame with annual totals and columns:
        - country, year, value (summed)
        - month_count: number of months with data
        - is_ytd: True if less than 12 months
        - last_month: latest month in the data for that year
    """
    df = df.copy()
    
    # Aggregate by country and year
    agg = df.groupby([country_col, year_col]).agg({
        value_col: 'sum',
        month_col: ['count', 'max']
    }).reset_index()
    
    # Flatten column names
    agg.columns = [country_col, year_col, value_col, 'month_count', 'last_month']
    
    # Flag incomplete years
    agg['is_ytd'] = agg['month_count'] < 12
    
    return agg


def annualize_ytd_value(
    df: pd.DataFrame,
    value_col: str = "value",
    month_count_col: str = "month_count",
) -> pd.DataFrame:
    """
    Annualize YTD values to make them comparable to full-year data.
    
    For incomplete years, scales value to 12-month equivalent.
    
    Args:
        df: DataFrame with aggregated annual data including month_count
        value_col: Name of the value column
        month_count_col: Name of the month count column
    
    Returns:
        DataFrame with added 'value_annualized' column
    """
    df = df.copy()
    df['value_annualized'] = df[value_col] * (12 / df[month_count_col])
    return df


def parse_monthly_wide_format(
    df: pd.DataFrame,
    trade_type: str = "import"
) -> pd.DataFrame:
    """
    Parse monthly data in format: Country, Year, 1, 2, 3, ..., N
    
    This handles USITC data where columns are:
    - Column 0: Country name
    - Column 1: Year
    - Columns 2+: Month numbers (1, 2, 3, ... up to 12)
    
    Args:
        df: Wide-format DataFrame with Country, Year, and month columns
        trade_type: 'import' or 'export'
    
    Returns:
        Long-format DataFrame with columns: country, year, month, value, trade_type
    """
    df = df.copy()
    
    # Identify columns
    country_col = df.columns[0]  # 'Country'
    year_col = df.columns[1]      # 'Year'
    
    # Month columns are the remaining columns (1, 2, 3, ..., N)
    month_cols = [col for col in df.columns[2:] if str(col).isdigit()]
    
    # Melt to long format
    df_long = df.melt(
        id_vars=[country_col, year_col],
        value_vars=month_cols,
        var_name='month',
        value_name='value'
    )
    
    # Rename columns
    df_long = df_long.rename(columns={
        country_col: 'country',
        year_col: 'year'
    })
    
    # Convert types
    df_long['year'] = df_long['year'].astype(int)
    df_long['month'] = df_long['month'].astype(int)
    df_long['value'] = pd.to_numeric(df_long['value'], errors='coerce')
    
    # Add trade type
    df_long['trade_type'] = trade_type
    
    # Filter out non-country rows
    exclude_rows = ['Total:', 'Total', 'Unspecified', 'Transshipment', 'Internat Organization']
    df_long = df_long[~df_long['country'].str.strip().isin(exclude_rows)]
    
    # Drop rows with zero or null values
    df_long = df_long[df_long['value'] > 0]
    df_long = df_long.dropna(subset=['value'])
    
    return df_long[['country', 'year', 'month', 'value', 'trade_type']]
