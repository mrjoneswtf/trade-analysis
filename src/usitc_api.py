"""
USITC DataWeb API Client

Fetch US trade data programmatically from the USITC DataWeb API.
API Documentation: https://www.usitc.gov/sites/default/files/applications/dataweb/api/dataweb_query_api.html
"""

import requests
import pandas as pd
from pathlib import Path
from typing import Optional, List, Literal
import json
import logging
import urllib3

# Disable SSL warnings (USITC API sometimes has cert issues)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)

# API Configuration
API_BASE_URL = "https://datawebws.usitc.gov/dataweb"


def _load_token() -> Optional[str]:
    """Load API token from usitc-api-info.md file."""
    project_root = Path(__file__).parent.parent
    token_file = project_root / "usitc-api-info.md"
    
    if token_file.exists():
        content = token_file.read_text()
        lines = content.strip().split("\n")
        for line in lines:
            # Token is typically a long JWT string starting with eyJ
            if line.startswith("eyJ"):
                return line.strip()
    return None


# Basic query template based on USITC documentation
BASIC_QUERY = {
    "savedQueryName": "",
    "savedQueryDesc": "",
    "isOwner": True,
    "runMonthly": False,
    "reportOptions": {
        "tradeType": "Import",
        "classificationSystem": "HTS"
    },
    "searchOptions": {
        "MiscGroup": {
            "districts": {
                "aggregation": "Aggregate District",
                "districtGroups": {"userGroups": []},
                "districts": [],
                "districtsExpanded": [{"name": "All Districts", "value": "all"}],
                "districtsSelectType": "all"
            },
            "importPrograms": {
                "aggregation": None,
                "importPrograms": [],
                "programsSelectType": "all"
            },
            "extImportPrograms": {
                "aggregation": "Aggregate CSC",
                "extImportPrograms": [],
                "extImportProgramsExpanded": [],
                "programsSelectType": "all"
            },
            "provisionCodes": {
                "aggregation": "Aggregate RPCODE",
                "provisionCodesSelectType": "all",
                "rateProvisionCodes": [],
                "rateProvisionCodesExpanded": []
            }
        },
        "commodities": {
            "aggregation": "Aggregate Commodities",
            "codeDisplayFormat": "YES",
            "commoditiesSelectType": "all",
            "commodities": [],
            "commodityGroups": {"userGroups": []}
        },
        "countries": {
            "aggregation": "Individual Countries",
            "countryGroups": {"userGroups": []},
            "countries": [],
            "countriesExpanded": [{"name": "World", "value": "0000"}],
            "countriesSelectType": "all"
        },
        "timeframes": {
            "timeframeSelectType": "fullYears",
            "fullYears": {
                "startYear": "1995",
                "endYear": "2024",
                "timeperiod": "Annual"
            }
        }
    },
    "sortOptions": {
        "sortBy": "VALUE",
        "sortOrder": "DESC"
    }
}


class USITCDataWebAPI:
    """Client for USITC DataWeb API."""
    
    def __init__(self, token: Optional[str] = None):
        """
        Initialize API client.
        
        Args:
            token: API token. If not provided, attempts to load from usitc-api-info.md
        """
        self.token = token or _load_token()
        if not self.token:
            raise ValueError(
                "API token required. Either pass token parameter or create "
                "usitc-api-info.md file with your token."
            )
        
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json; charset=utf-8",
        })
        self.session.verify = False  # USITC sometimes has cert issues
    
    def _make_request(
        self, 
        endpoint: str, 
        method: str = "GET",
        data: Optional[dict] = None,
        max_retries: int = 3,
        retry_delay: int = 5
    ) -> dict:
        """Make API request with retry logic."""
        import time
        
        url = f"{API_BASE_URL}{endpoint}"
        
        for attempt in range(max_retries):
            try:
                if method == "GET":
                    response = self.session.get(url)
                elif method == "POST":
                    response = self.session.post(url, json=data)
                else:
                    raise ValueError(f"Unsupported method: {method}")
                
                # Check for data load mode (503)
                if response.status_code == 503:
                    if attempt < max_retries - 1:
                        print(f"  Server busy (data load mode), retrying in {retry_delay}s...")
                        time.sleep(retry_delay)
                        continue
                    else:
                        raise requests.exceptions.HTTPError(
                            "USITC DataWeb is in data load mode. Try again later."
                        )
                
                response.raise_for_status()
                return response.json()
            
            except requests.exceptions.RequestException as e:
                logger.error(f"API request failed: {e}")
                if hasattr(e, 'response') and e.response is not None:
                    logger.error(f"Response text: {e.response.text[:500]}")
                if attempt < max_retries - 1:
                    print(f"  Request failed, retrying in {retry_delay}s...")
                    time.sleep(retry_delay)
                else:
                    raise
    
    def get_all_countries(self) -> pd.DataFrame:
        """Get list of all available countries and country groups."""
        data = self._make_request("/api/v2/country/getAllCountries")
        if isinstance(data, dict) and "options" in data:
            return pd.DataFrame(data["options"])
        return pd.DataFrame(data)
    
    def get_saved_queries(self) -> List[dict]:
        """Get list of saved queries for your account."""
        return self._make_request("/api/v2/savedQuery/getAllSavedQueries")
    
    def run_trade_query(
        self,
        trade_type: Literal["Import", "Export", "TotExp", "GenImp", "Balance"] = "Import",
        start_year: int = 1995,
        end_year: int = 2024,
        time_period: Literal["Annual", "Monthly", "Quarterly"] = "Annual",
        classification: Literal["HTS", "NAIC", "SITC", "SIC"] = "HTS",
    ) -> pd.DataFrame:
        """
        Run a trade data query.
        
        Args:
            trade_type: Type of trade flow (Import, Export, TotExp, GenImp, Balance)
            start_year: Start year for data
            end_year: End year for data
            time_period: Time aggregation level (Annual, Monthly, Quarterly)
            classification: Commodity classification system
        
        Returns:
            DataFrame with trade data
        """
        # Build query from template
        import copy
        query = copy.deepcopy(BASIC_QUERY)
        
        # Update query parameters
        query["reportOptions"]["tradeType"] = trade_type
        query["reportOptions"]["classificationSystem"] = classification
        query["searchOptions"]["timeframes"]["fullYears"]["startYear"] = str(start_year)
        query["searchOptions"]["timeframes"]["fullYears"]["endYear"] = str(end_year)
        query["searchOptions"]["timeframes"]["fullYears"]["timeperiod"] = time_period
        
        # Set countries to individual (not aggregated)
        query["searchOptions"]["countries"]["aggregation"] = "Individual Countries"
        
        logger.info(f"Running query: {trade_type} {start_year}-{end_year}")
        print(f"Querying USITC API: {trade_type} {start_year}-{end_year}...")
        
        try:
            result = self._make_request("/api/v2/report2/runReport", method="POST", data=query)
            
            # Parse the nested response structure
            df = self._parse_response(result)
            
            logger.info(f"Retrieved {len(df)} rows")
            print(f"Retrieved {len(df)} rows")
            return df
            
        except Exception as e:
            logger.error(f"Query failed: {e}")
            raise
    
    def _parse_response(self, result: dict) -> pd.DataFrame:
        """Parse the nested USITC API response into a DataFrame."""
        try:
            # Navigate the nested structure
            tables = result.get("dto", {}).get("tables", [])
            if not tables:
                return pd.DataFrame()
            
            table = tables[0]
            
            # Get column headers
            columns = []
            for col_group in table.get("column_groups", []):
                for col in col_group.get("columns", []):
                    columns.append(col.get("label", ""))
            
            # Get data rows
            rows = []
            row_groups = table.get("row_groups", [])
            if row_groups:
                for row in row_groups[0].get("rowsNew", []):
                    row_data = []
                    for entry in row.get("rowEntries", []):
                        row_data.append(entry.get("value", ""))
                    rows.append(row_data)
            
            return pd.DataFrame(rows, columns=columns)
            
        except Exception as e:
            logger.error(f"Failed to parse response: {e}")
            # Try to return raw data structure for debugging
            if isinstance(result, dict):
                return pd.DataFrame([{"raw_response": str(result)[:1000]}])
            return pd.DataFrame()
    
    def get_imports_by_country(
        self,
        start_year: int = 1995,
        end_year: int = 2024,
    ) -> pd.DataFrame:
        """
        Get annual import data by country.
        """
        return self.run_trade_query(
            trade_type="Import",
            start_year=start_year,
            end_year=end_year,
            time_period="Annual",
        )
    
    def get_exports_by_country(
        self,
        start_year: int = 1995,
        end_year: int = 2024,
    ) -> pd.DataFrame:
        """
        Get annual export data by country.
        """
        return self.run_trade_query(
            trade_type="TotExp",
            start_year=start_year,
            end_year=end_year,
            time_period="Annual",
        )


def fetch_and_save_trade_data(
    output_dir: Optional[Path] = None,
    start_year: int = 1995,
    end_year: int = 2024,
    token: Optional[str] = None,
) -> dict:
    """
    Fetch imports and exports data and save to CSV files.
    
    Args:
        output_dir: Directory to save files (defaults to data/raw/usitc)
        start_year: Start year
        end_year: End year
        token: API token (optional, will load from file)
    
    Returns:
        Dict with paths to saved files
    """
    if output_dir is None:
        output_dir = Path(__file__).parent.parent / "data" / "raw" / "usitc"
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    api = USITCDataWebAPI(token=token)
    saved_files = {}
    
    # Fetch imports
    print(f"\nFetching imports data ({start_year}-{end_year})...")
    try:
        imports_df = api.get_imports_by_country(start_year, end_year)
        if len(imports_df) > 0:
            imports_path = output_dir / f"imports_by_country_{start_year}_{end_year}.csv"
            imports_df.to_csv(imports_path, index=False)
            saved_files["imports"] = imports_path
            print(f"  Saved: {imports_path} ({len(imports_df)} rows)")
        else:
            print("  No import data returned")
    except Exception as e:
        print(f"  Failed to fetch imports: {e}")
    
    # Fetch exports
    print(f"\nFetching exports data ({start_year}-{end_year})...")
    try:
        exports_df = api.get_exports_by_country(start_year, end_year)
        if len(exports_df) > 0:
            exports_path = output_dir / f"exports_by_country_{start_year}_{end_year}.csv"
            exports_df.to_csv(exports_path, index=False)
            saved_files["exports"] = exports_path
            print(f"  Saved: {exports_path} ({len(exports_df)} rows)")
        else:
            print("  No export data returned")
    except Exception as e:
        print(f"  Failed to fetch exports: {e}")
    
    return saved_files


# CLI entry point
if __name__ == "__main__":
    import sys
    
    print("USITC DataWeb API - Data Fetcher")
    print("=" * 40)
    
    try:
        result = fetch_and_save_trade_data()
        print("\nDownload complete!")
        for name, path in result.items():
            print(f"  {name}: {path}")
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)
