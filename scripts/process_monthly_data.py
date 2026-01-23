"""
Process Monthly Import Data (2024-2025)

This script processes manually downloaded USITC monthly data and merges it
with historical annual data to create a complete 1995-2025 dataset.

Usage:
    python scripts/process_monthly_data.py

Input files:
    - data/raw/usitc/imports_monthly_2024.csv (full year, 12 months)
    - data/raw/usitc/imports_monthly_2025.csv (YTD, 10 months Jan-Oct)
    - data/processed/trade_data_1995_2024.csv (existing historical data)

Output:
    - data/processed/trade_data_1995_2025.csv
"""

import sys
from pathlib import Path

# Add src to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import pandas as pd
from data_loader import DATA_RAW, DATA_PROCESSED, DATA_REFERENCE
from classification_mapper import standardize_country_names, add_historical_period
from transformers import (
    parse_monthly_wide_format,
    aggregate_monthly_to_annual,
    calculate_country_shares,
    calculate_yoy_growth,
    adjust_for_inflation,
)


def load_monthly_files() -> pd.DataFrame:
    """Load and combine monthly CSV files."""
    usitc_dir = DATA_RAW / "usitc"
    
    # Load 2024 (full year)
    file_2024 = usitc_dir / "imports_monthly_2024.csv"
    if not file_2024.exists():
        raise FileNotFoundError(f"Missing: {file_2024}")
    
    df_2024 = pd.read_csv(file_2024)
    print(f"Loaded 2024 data: {len(df_2024)} countries, columns: {list(df_2024.columns[:5])}...")
    
    # Load 2025 (YTD)
    file_2025 = usitc_dir / "imports_monthly_2025.csv"
    if not file_2025.exists():
        raise FileNotFoundError(f"Missing: {file_2025}")
    
    df_2025 = pd.read_csv(file_2025)
    print(f"Loaded 2025 data: {len(df_2025)} countries, columns: {list(df_2025.columns[:5])}...")
    
    # Parse to long format
    monthly_2024 = parse_monthly_wide_format(df_2024, trade_type="import")
    monthly_2025 = parse_monthly_wide_format(df_2025, trade_type="import")
    
    print(f"Parsed 2024: {len(monthly_2024)} rows, months 1-{monthly_2024['month'].max()}")
    print(f"Parsed 2025: {len(monthly_2025)} rows, months 1-{monthly_2025['month'].max()}")
    
    # Combine
    monthly_combined = pd.concat([monthly_2024, monthly_2025], ignore_index=True)
    print(f"Combined monthly data: {len(monthly_combined)} rows")
    
    return monthly_combined


def aggregate_to_annual(monthly_df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate monthly data to annual totals."""
    annual = aggregate_monthly_to_annual(
        monthly_df,
        value_col="value",
        country_col="country",
        year_col="year",
        month_col="month"
    )
    
    # Add trade_type back
    annual["trade_type"] = "import"
    
    # Convert from billions to actual USD
    annual["value"] = annual["value"] * 1e9
    
    print(f"\nAggregated to annual: {len(annual)} country-year records")
    
    # Show YTD status
    for year in sorted(annual["year"].unique()):
        year_data = annual[annual["year"] == year]
        months = year_data["month_count"].iloc[0]
        is_ytd = year_data["is_ytd"].iloc[0]
        ytd_note = " (YTD)" if is_ytd else ""
        print(f"  {year}: {months} months{ytd_note}, {len(year_data)} countries")
    
    return annual


def load_historical_data() -> pd.DataFrame:
    """Load existing historical annual data (1995-2023)."""
    # Try to find existing processed data
    historical_file = DATA_PROCESSED / "trade_data_1995_2024.csv"
    
    if not historical_file.exists():
        raise FileNotFoundError(
            f"Historical data not found: {historical_file}\n"
            "Run the data cleaning notebook first to create historical data."
        )
    
    df = pd.read_csv(historical_file)
    print(f"\nLoaded historical data: {len(df)} rows")
    print(f"  Years: {df['year'].min()} - {df['year'].max()}")
    print(f"  Trade types: {df['trade_type'].unique().tolist()}")
    
    return df


def merge_data(historical_df: pd.DataFrame, monthly_annual_df: pd.DataFrame) -> pd.DataFrame:
    """Merge historical and monthly-derived data."""
    # Filter historical to years before monthly data starts
    # Keep 2024 from monthly data (more accurate than old 2024 annual)
    monthly_years = monthly_annual_df["year"].unique()
    historical_cutoff = min(monthly_years) - 1
    
    print(f"\nMerging data:")
    print(f"  Historical: 1995-{historical_cutoff}")
    print(f"  Monthly-derived: {min(monthly_years)}-{max(monthly_years)}")
    
    # Filter historical to pre-2024 and imports only
    historical_filtered = historical_df[
        (historical_df["year"] <= historical_cutoff) & 
        (historical_df["trade_type"] == "import")
    ].copy()
    
    # Add is_ytd flag to historical (all False)
    historical_filtered["is_ytd"] = False
    historical_filtered["month_count"] = 12
    historical_filtered["last_month"] = 12
    
    # Select common columns
    common_cols = ["country", "year", "value", "trade_type", "is_ytd", "month_count", "last_month"]
    
    # Ensure both have the same columns
    for col in common_cols:
        if col not in historical_filtered.columns:
            historical_filtered[col] = None
        if col not in monthly_annual_df.columns:
            monthly_annual_df[col] = None
    
    # Merge
    merged = pd.concat([
        historical_filtered[common_cols],
        monthly_annual_df[common_cols]
    ], ignore_index=True)
    
    print(f"  Merged: {len(merged)} rows")
    print(f"  Years: {merged['year'].min()} - {merged['year'].max()}")
    
    return merged


def process_data(df: pd.DataFrame) -> pd.DataFrame:
    """Apply standard processing: standardization, inflation, shares, growth."""
    print("\nProcessing data...")
    
    # 1. Standardize country names
    df = standardize_country_names(df, country_col="country")
    print(f"  Countries after standardization: {df['country'].nunique()}")
    
    # 2. Apply inflation adjustment
    deflator_df = pd.read_csv(DATA_REFERENCE / "gdp_deflator.csv")
    df = adjust_for_inflation(
        df,
        deflator_df,
        value_col="value",
        year_col="year",
        base_year=2020
    )
    print("  Applied inflation adjustment (base year 2020)")
    
    # 3. Calculate country shares
    df = calculate_country_shares(
        df,
        value_col="value_real",
        country_col="country",
        year_col="year",
        trade_type_col="trade_type"
    )
    print("  Calculated country shares")
    
    # 4. Calculate YoY growth
    df = calculate_yoy_growth(
        df,
        value_col="value_real",
        country_col="country",
        year_col="year",
        trade_type_col="trade_type"
    )
    print("  Calculated year-over-year growth")
    
    # 5. Add historical period
    df = add_historical_period(df, year_col="year")
    print("  Added historical period classification")
    
    return df


def validate_data(df: pd.DataFrame):
    """Validate the processed data."""
    print("\nValidation:")
    
    # Check for key countries
    key_countries = ["China", "Mexico", "Canada", "Japan", "Vietnam", "Taiwan"]
    for country in key_countries:
        country_data = df[df["country"] == country]
        if len(country_data) == 0:
            print(f"  WARNING: No data for {country}")
        else:
            years = sorted(country_data["year"].unique())
            print(f"  {country}: {years[0]}-{years[-1]} ({len(years)} years)")
    
    # Check 2025 data
    data_2025 = df[df["year"] == 2025]
    if len(data_2025) > 0:
        ytd_info = data_2025.iloc[0]
        print(f"\n  2025 data: {len(data_2025)} countries")
        print(f"  2025 is YTD: {ytd_info['is_ytd']} (through month {ytd_info['last_month']})")
        
        # Show top 5 in 2025
        top_2025 = data_2025.nlargest(5, "share_pct")[["country", "share_pct"]]
        print("\n  Top 5 import sources in 2025:")
        for _, row in top_2025.iterrows():
            print(f"    {row['country']}: {row['share_pct']:.1f}%")
    
    # Show China trend
    china_data = df[df["country"] == "China"].sort_values("year")
    if len(china_data) > 0:
        print("\n  China import share trend:")
        for year in [2017, 2018, 2020, 2023, 2024, 2025]:
            row = china_data[china_data["year"] == year]
            if len(row) > 0:
                print(f"    {year}: {row['share_pct'].values[0]:.1f}%")


def save_output(df: pd.DataFrame):
    """Save the processed data."""
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    
    max_year = df["year"].max()
    output_file = DATA_PROCESSED / f"trade_data_1995_{max_year}.csv"
    
    df.to_csv(output_file, index=False)
    
    file_size = output_file.stat().st_size / 1e6
    print(f"\nSaved: {output_file}")
    print(f"  Rows: {len(df):,}")
    print(f"  Size: {file_size:.1f} MB")
    
    return output_file


def main():
    """Main processing pipeline."""
    print("=" * 60)
    print("PROCESSING MONTHLY IMPORT DATA")
    print("=" * 60)
    
    # Step 1: Load monthly files
    monthly_df = load_monthly_files()
    
    # Step 2: Aggregate to annual
    annual_df = aggregate_to_annual(monthly_df)
    
    # Step 3: Load historical data
    historical_df = load_historical_data()
    
    # Step 4: Merge
    merged_df = merge_data(historical_df, annual_df)
    
    # Step 5: Process
    processed_df = process_data(merged_df)
    
    # Step 6: Validate
    validate_data(processed_df)
    
    # Step 7: Save
    output_path = save_output(processed_df)
    
    print("\n" + "=" * 60)
    print("PROCESSING COMPLETE")
    print("=" * 60)
    print(f"\nOutput file: {output_path}")
    print("Run the dashboard to see the updated data:")
    print("  streamlit run dashboard/app.py")
    
    return processed_df


if __name__ == "__main__":
    main()
