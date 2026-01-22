"""
Data loading utilities for US trade data analysis.
Handles USITC DataWeb exports and other data sources.
"""

import pandas as pd
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_RAW = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
DATA_REFERENCE = PROJECT_ROOT / "data" / "reference"
DATA_EXPORTS = PROJECT_ROOT / "data" / "exports"


def load_usitc_data(
    filename: str,
    data_dir: Optional[Path] = None,
) -> pd.DataFrame:
    """
    Load a USITC DataWeb export file (CSV or Excel).
    
    Args:
        filename: Name of the file to load
        data_dir: Directory containing the file (defaults to data/raw/usitc)
    
    Returns:
        DataFrame with trade data
    """
    if data_dir is None:
        data_dir = DATA_RAW / "usitc"
    
    filepath = data_dir / filename
    
    if not filepath.exists():
        raise FileNotFoundError(f"Data file not found: {filepath}")
    
    logger.info(f"Loading USITC data from {filepath}")
    
    if filepath.suffix.lower() == ".csv":
        df = pd.read_csv(filepath)
    elif filepath.suffix.lower() in [".xlsx", ".xls"]:
        df = pd.read_excel(filepath)
    else:
        raise ValueError(f"Unsupported file format: {filepath.suffix}")
    
    logger.info(f"Loaded {len(df):,} rows, {len(df.columns)} columns")
    return df


def load_all_trade_data(
    pattern: str = "*.csv",
    data_dir: Optional[Path] = None,
) -> pd.DataFrame:
    """
    Load and concatenate all trade data files matching a pattern.
    
    Args:
        pattern: Glob pattern for files to load
        data_dir: Directory to search (defaults to data/raw/usitc)
    
    Returns:
        Combined DataFrame with all trade data
    """
    if data_dir is None:
        data_dir = DATA_RAW / "usitc"
    
    files = list(data_dir.glob(pattern))
    
    if not files:
        raise FileNotFoundError(f"No files matching '{pattern}' in {data_dir}")
    
    logger.info(f"Found {len(files)} files to load")
    
    dfs = []
    for filepath in files:
        try:
            if filepath.suffix.lower() == ".csv":
                df = pd.read_csv(filepath)
            else:
                df = pd.read_excel(filepath)
            dfs.append(df)
            logger.info(f"  Loaded {filepath.name}: {len(df):,} rows")
        except Exception as e:
            logger.warning(f"  Failed to load {filepath.name}: {e}")
    
    if not dfs:
        raise ValueError("No files could be loaded successfully")
    
    combined = pd.concat(dfs, ignore_index=True)
    logger.info(f"Combined dataset: {len(combined):,} rows")
    
    return combined


def load_reference_data(filename: str) -> pd.DataFrame:
    """
    Load reference data (deflators, country mappings, etc.)
    
    Args:
        filename: Name of reference file
    
    Returns:
        DataFrame with reference data
    """
    filepath = DATA_REFERENCE / filename
    
    if not filepath.exists():
        raise FileNotFoundError(f"Reference file not found: {filepath}")
    
    if filepath.suffix.lower() == ".csv":
        return pd.read_csv(filepath)
    elif filepath.suffix.lower() in [".xlsx", ".xls"]:
        return pd.read_excel(filepath)
    else:
        raise ValueError(f"Unsupported file format: {filepath.suffix}")


def save_processed_data(
    df: pd.DataFrame,
    filename: str,
    output_dir: Optional[Path] = None,
) -> Path:
    """
    Save processed data to the processed directory.
    
    Args:
        df: DataFrame to save
        filename: Output filename
        output_dir: Output directory (defaults to data/processed)
    
    Returns:
        Path to saved file
    """
    if output_dir is None:
        output_dir = DATA_PROCESSED
    
    output_dir.mkdir(parents=True, exist_ok=True)
    filepath = output_dir / filename
    
    if filepath.suffix.lower() == ".csv":
        df.to_csv(filepath, index=False)
    elif filepath.suffix.lower() == ".parquet":
        df.to_parquet(filepath, index=False)
    else:
        df.to_csv(filepath, index=False)
    
    logger.info(f"Saved {len(df):,} rows to {filepath}")
    return filepath
