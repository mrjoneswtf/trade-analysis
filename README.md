# US Trade Data Analysis: Supply Chain Country Shifts

Analyze US import/export data (1995-present) to understand how sourcing countries have shifted over time - tracking patterns like China's rise, NAFTA effects, and the recent "China+1" migration to Vietnam, Mexico, and India.

## Data Sources

| Source | Coverage | URL |
|--------|----------|-----|
| **USITC DataWeb** (Primary) | 1989-Present | https://dataweb.usitc.gov/ |
| **NBER Trade Database** (Historical) | 1972-2001 | https://www.nber.org/research/data/us-imports-1972-2001 |
| **Census Bureau** (Supplementary) | Various | https://www.census.gov/foreign-trade/ |

## Setup

### 1. Create Virtual Environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Download Data

1. Register for a free account at [USITC DataWeb](https://dataweb.usitc.gov/)
2. Download trade data (imports/exports by country, 1995-present)
3. Place downloaded files in `data/raw/usitc/`

## Project Structure

```
Data_Trade-Import-Export/
├── data/
│   ├── raw/                    # Original downloads
│   │   ├── usitc/              # USITC DataWeb exports
│   │   └── nber/               # Historical NBER data
│   ├── processed/              # Cleaned, harmonized datasets
│   ├── reference/              # GDP deflators, country mappings
│   └── exports/                # Final analysis-ready datasets
├── notebooks/
│   ├── 01_data_acquisition.ipynb
│   ├── 02_data_cleaning.ipynb
│   ├── 03_exploratory_analysis.ipynb
│   ├── 04_country_shift_analysis.ipynb
│   └── 05_visualization_report.ipynb
├── src/                        # Python modules
│   ├── data_loader.py          # Data loading utilities
│   ├── transformers.py         # Calculations (shares, growth)
│   ├── classification_mapper.py # Country name standardization
│   └── analysis.py             # HHI, shift detection
├── dashboard/                  # Streamlit app
├── reports/                    # Generated reports
└── requirements.txt
```

## Usage

### Run Jupyter Notebooks

```bash
jupyter lab
```

Open notebooks in order (01 → 05) for the complete analysis workflow.

### Run Dashboard

```bash
streamlit run dashboard/app.py
```

## Key Analyses

1. **Country Share Evolution** - Track top 20 trading partners over time
2. **China Story Arc** - Pre-WTO, WTO boom, trade war, post-COVID
3. **Beneficiary Countries** - Who gained as China share declined?
4. **Concentration Metrics** - HHI index for source diversification
5. **Event Analysis** - Impact of tariffs, COVID, trade agreements

## Historical Periods

| Period | Years | Key Events |
|--------|-------|------------|
| Pre-NAFTA | 1989-1993 | Baseline |
| Pre-WTO China | 1994-2000 | NAFTA in effect |
| China WTO Boom | 2001-2007 | China joins WTO |
| Financial Crisis | 2008-2009 | Global recession |
| Post-Crisis Growth | 2010-2017 | Recovery |
| Trade War | 2018-2019 | US-China tariffs |
| COVID Era | 2020-2021 | Supply chain disruptions |
| Post-COVID | 2022+ | Reshoring, diversification |
