"""
US Trade Data Analysis Dashboard - The China Story Arc

Narrative-driven Streamlit dashboard exploring how America's supply chain
shifted from China to Mexico, Vietnam, and other emerging partners.

Run with: streamlit run dashboard/app.py
"""

import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
from streamlit_echarts import st_echarts

# Page config
st.set_page_config(
    page_title="The China Story Arc",
    page_icon="🌏",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"

# Era definitions - the narrative structure
ERAS = {
    "Pre-WTO (1995-2001)": {
        "start": 1995,
        "end": 2001,
        "title": "The Baseline",
        "description": "Before China joined WTO. Manufacturing distributed across Japan, Taiwan, and early Chinese SEZs.",
        "key_event": "China WTO accession Dec 2001",
        "color": "#6b7280"
    },
    "WTO Boom (2001-2008)": {
        "start": 2001,
        "end": 2008,
        "title": "Rapid Rise",
        "description": "China's share explodes as manufacturing shifts en masse to take advantage of WTO access.",
        "key_event": "Financial Crisis 2008",
        "color": "#dc2626"
    },
    "Post-Crisis (2009-2017)": {
        "start": 2009,
        "end": 2017,
        "title": "Maturation",
        "description": "China peaks at 21%+. Supply chains deeply integrated. Early nearshoring discussions begin.",
        "key_event": "Trump tariffs announced 2018",
        "color": "#f59e0b"
    },
    "Trade War Era (2018-Present)": {
        "start": 2018,
        "end": 2024,
        "title": "The Shift Begins",
        "description": "China share declines to 13%. Mexico surpasses China. Vietnam and India emerge as alternatives.",
        "key_event": "Mexico becomes #1 import source 2023",
        "color": "#10b981"
    }
}

# Key countries for comparison
FOCUS_COUNTRIES = ["China", "Mexico", "Canada", "Vietnam", "Japan", "Germany", "South Korea", "Taiwan", "India", "Ireland"]
BENEFICIARY_COUNTRIES = ["Vietnam", "Mexico", "India", "Taiwan", "South Korea", "Thailand", "Malaysia", "Indonesia"]

# Hardcoded colors for each country
COUNTRY_COLORS = {
    "China": "#dc2626",      # Red (prominent)
    "Mexico": "#2563eb",     # Blue
    "Canada": "#16a34a",     # Green
    "Vietnam": "#9333ea",    # Purple
    "Japan": "#ea580c",      # Orange
    "Germany": "#0891b2",    # Cyan
    "South Korea": "#4f46e5",# Indigo
    "Taiwan": "#be185d",     # Pink
    "India": "#ca8a04",      # Yellow
    "Ireland": "#65a30d",    # Lime
}


@st.cache_data
def load_data() -> pd.DataFrame:
    """Load processed trade data."""
    trade_path = DATA_PROCESSED / "trade_data_1995_2024.csv"
    
    if trade_path.exists():
        df = pd.read_csv(trade_path)
        return df
    return None


def get_china_share(df: pd.DataFrame, year: int) -> float:
    """Get China's import share for a specific year."""
    china_data = df[(df["country"] == "China") & 
                    (df["year"] == year) & 
                    (df["trade_type"] == "import")]
    if len(china_data) > 0:
        return china_data["share_pct"].values[0]
    return 0.0


def get_era_metrics(df: pd.DataFrame, era_config: dict) -> dict:
    """Calculate key metrics for an era."""
    imports = df[df["trade_type"] == "import"]
    era_data = imports[(imports["year"] >= era_config["start"]) & 
                       (imports["year"] <= era_config["end"])]
    
    china_start = get_china_share(imports, era_config["start"])
    china_end = get_china_share(imports, era_config["end"])
    
    # Get top countries at end of era
    end_year_data = era_data[era_data["year"] == era_config["end"]]
    top_5 = end_year_data.nlargest(5, "share_pct")[["country", "share_pct"]]
    
    return {
        "china_start": china_start,
        "china_end": china_end,
        "china_delta": china_end - china_start,
        "top_5": top_5
    }


def create_china_arc_echart(df: pd.DataFrame, selected_era: str) -> dict:
    """Create ECharts config for the main China trajectory chart."""
    imports = df[df["trade_type"] == "import"]
    
    # Get unique years for x-axis
    years = sorted(imports["year"].unique().tolist())
    
    # Build mark areas for era shading
    mark_area_data = []
    for era_name, era_config in ERAS.items():
        opacity = 0.3 if era_name == selected_era else 0.1
        mark_area_data.append([
            {
                "name": era_config["title"] if era_name == selected_era else "",
                "xAxis": str(era_config["start"]),
                "itemStyle": {"color": era_config["color"], "opacity": opacity}
            },
            {"xAxis": str(era_config["end"])}
        ])
    
    # Build mark points for key events on China's line
    events = [
        (2001, "WTO Entry"),
        (2008, "Financial Crisis"),
        (2018, "Trade War"),
        (2020, "COVID-19"),
        (2023, "Mexico #1")
    ]
    mark_points = []
    china_data = imports[imports["country"] == "China"].sort_values("year")
    for year, label in events:
        share_row = china_data[china_data["year"] == year]
        if len(share_row) > 0:
            share = share_row["share_pct"].values[0]
            mark_points.append({
                "name": label,
                "coord": [str(year), round(share, 1)],
                "value": label,
                "symbol": "pin",
                "symbolSize": 40,
                "label": {
                    "show": True,
                    "position": "top",
                    "formatter": label,
                    "fontSize": 10
                }
            })
    
    # Build series for each country
    series = []
    
    # Add other countries first (behind China)
    for country in FOCUS_COUNTRIES:
        if country != "China":
            country_data = imports[imports["country"] == country].sort_values("year")
            if len(country_data) > 0:
                # Create data aligned to years
                data_dict = dict(zip(country_data["year"].astype(str), country_data["share_pct"].round(1)))
                data = [data_dict.get(str(y), None) for y in years]
                
                color = COUNTRY_COLORS.get(country, "#6b7280")
                series.append({
                    "name": country,
                    "type": "line",
                    "data": data,
                    "smooth": True,
                    "symbol": "none",
                    "lineStyle": {"width": 1.5, "color": color, "opacity": 0.6},
                    "itemStyle": {"color": color},
                    "emphasis": {"focus": "series", "lineStyle": {"width": 3, "opacity": 1}},
                    "z": 1,
                })
    
    # Add China line last (on top, prominent)
    china_data_dict = dict(zip(china_data["year"].astype(str), china_data["share_pct"].round(1)))
    china_values = [china_data_dict.get(str(y), None) for y in years]
    
    series.append({
        "name": "China",
        "type": "line",
        "data": china_values,
        "smooth": True,
        "symbol": "circle",
        "symbolSize": 6,
        "lineStyle": {"width": 3, "color": COUNTRY_COLORS["China"]},
        "itemStyle": {"color": COUNTRY_COLORS["China"]},
        "emphasis": {"focus": "series", "lineStyle": {"width": 4}},
        "z": 10,
        "markArea": {"silent": True, "data": mark_area_data},
        "markPoint": {"data": mark_points, "symbolSize": 35}
    })
    
    return {
        "title": {
            "text": "China's Import Share: The Rise and Shift",
            "left": "center",
            "textStyle": {"fontSize": 16, "fontWeight": "bold"}
        },
        "tooltip": {
            "trigger": "axis",
            "axisPointer": {"type": "cross"},
            "formatter": None  # Use default formatter
        },
        "legend": {
            "data": FOCUS_COUNTRIES,
            "bottom": 0,
            "type": "scroll",
            "textStyle": {"fontSize": 11}
        },
        "grid": {
            "left": "3%",
            "right": "4%",
            "bottom": "15%",
            "top": "15%",
            "containLabel": True
        },
        "xAxis": {
            "type": "category",
            "data": [str(y) for y in years],
            "name": "Year",
            "nameLocation": "middle",
            "nameGap": 30,
            "boundaryGap": False
        },
        "yAxis": {
            "type": "value",
            "name": "Share of US Imports (%)",
            "nameLocation": "middle",
            "nameGap": 45,
            "min": 0,
            "max": 25
        },
        "series": series,
        "animation": True,
        "animationDuration": 1500,
        "animationEasing": "cubicOut"
    }


def create_era_composition_echart(df: pd.DataFrame, era_config: dict, top_n: int = 8) -> dict:
    """Create ECharts stacked area chart for era composition."""
    imports = df[df["trade_type"] == "import"]
    era_data = imports[(imports["year"] >= era_config["start"]) & 
                       (imports["year"] <= era_config["end"])]
    
    # Get top countries for this era
    top_countries = era_data.groupby("country")["value_real"].sum().nlargest(top_n).index.tolist()
    
    # Prepare data
    era_data = era_data.copy()
    era_data["country_group"] = era_data["country"].apply(
        lambda x: x if x in top_countries else "Other"
    )
    
    grouped = era_data.groupby(["year", "country_group"])["share_pct"].sum().reset_index()
    years = sorted(grouped["year"].unique().tolist())
    countries = grouped["country_group"].unique().tolist()
    
    # Color palette
    colors = ["#66c2a5", "#fc8d62", "#8da0cb", "#e78ac3", "#a6d854", "#ffd92f", "#e5c494", "#b3b3b3", "#1f78b4"]
    
    # Build series for each country
    series = []
    for i, country in enumerate(countries):
        country_data = grouped[grouped["country_group"] == country].sort_values("year")
        data_dict = dict(zip(country_data["year"], country_data["share_pct"].round(1)))
        values = [data_dict.get(y, 0) for y in years]
        
        series.append({
            "name": country,
            "type": "line",
            "stack": "Total",
            "areaStyle": {"opacity": 0.8},
            "emphasis": {"focus": "series"},
            "data": values,
            "smooth": True,
            "itemStyle": {"color": colors[i % len(colors)]}
        })
    
    return {
        "title": {
            "text": f"Import Composition: {era_config['start']}-{era_config['end']}",
            "left": "center",
            "textStyle": {"fontSize": 14}
        },
        "tooltip": {"trigger": "axis", "axisPointer": {"type": "cross"}},
        "legend": {
            "data": countries,
            "bottom": 0,
            "type": "scroll",
            "textStyle": {"fontSize": 10}
        },
        "grid": {"left": "3%", "right": "4%", "bottom": "15%", "top": "15%", "containLabel": True},
        "xAxis": {"type": "category", "data": [str(y) for y in years], "boundaryGap": False},
        "yAxis": {"type": "value", "name": "Share (%)", "max": 100},
        "series": series,
        "animation": True,
        "animationDuration": 1000
    }


def create_winners_losers_echart(df: pd.DataFrame, era_config: dict, top_n: int = 10) -> tuple:
    """Create ECharts horizontal bar charts for winners and losers."""
    imports = df[df["trade_type"] == "import"]
    
    start_data = imports[imports["year"] == era_config["start"]][["country", "share_pct"]]
    end_data = imports[imports["year"] == era_config["end"]][["country", "share_pct"]]
    
    comparison = start_data.merge(
        end_data, on="country", suffixes=("_start", "_end"), how="outer"
    ).fillna(0)
    
    comparison["share_change"] = comparison["share_pct_end"] - comparison["share_pct_start"]
    
    # Winners chart
    winners = comparison.nlargest(top_n, "share_change")
    winners_opts = {
        "title": {"text": "Gained Share", "left": "center", "textStyle": {"fontSize": 14}},
        "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}},
        "grid": {"left": "25%", "right": "15%", "top": "15%", "bottom": "10%"},
        "xAxis": {"type": "value", "name": "Share Change (pp)"},
        "yAxis": {
            "type": "category",
            "data": winners["country"].tolist()[::-1],
            "axisLabel": {"fontSize": 11}
        },
        "series": [{
            "type": "bar",
            "data": winners["share_change"].round(1).tolist()[::-1],
            "itemStyle": {"color": "#10b981"},
            "label": {
                "show": True,
                "position": "right",
                "formatter": "+{c}pp",
                "fontSize": 10
            }
        }],
        "animation": True,
        "animationDuration": 800
    }
    
    # Losers chart
    losers = comparison.nsmallest(top_n, "share_change")
    losers_opts = {
        "title": {"text": "Lost Share", "left": "center", "textStyle": {"fontSize": 14}},
        "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}},
        "grid": {"left": "25%", "right": "15%", "top": "15%", "bottom": "10%"},
        "xAxis": {"type": "value", "name": "Share Change (pp)"},
        "yAxis": {
            "type": "category",
            "data": losers["country"].tolist()[::-1],
            "axisLabel": {"fontSize": 11}
        },
        "series": [{
            "type": "bar",
            "data": losers["share_change"].round(1).tolist()[::-1],
            "itemStyle": {"color": "#dc2626"},
            "label": {
                "show": True,
                "position": "left",
                "formatter": "{c}pp",
                "fontSize": 10
            }
        }],
        "animation": True,
        "animationDuration": 800
    }
    
    return winners_opts, losers_opts


def create_beneficiary_spotlight_echart(df: pd.DataFrame, countries: list) -> dict:
    """Create ECharts line chart for beneficiary countries."""
    imports = df[df["trade_type"] == "import"]
    spotlight = imports[imports["country"].isin(countries)].copy()
    
    years = sorted(spotlight["year"].unique().tolist())
    
    # Colors for beneficiary countries
    colors = ["#10b981", "#3b82f6", "#f59e0b", "#8b5cf6", "#ec4899"]
    
    series = []
    for i, country in enumerate(countries):
        country_data = spotlight[spotlight["country"] == country].sort_values("year")
        data_dict = dict(zip(country_data["year"], country_data["share_pct"].round(1)))
        values = [data_dict.get(y, None) for y in years]
        
        series.append({
            "name": country,
            "type": "line",
            "data": values,
            "smooth": True,
            "symbol": "circle",
            "symbolSize": 6,
            "lineStyle": {"width": 2},
            "itemStyle": {"color": colors[i % len(colors)]},
            "emphasis": {"focus": "series"}
        })
    
    # Add trade war shading to first series as markArea
    if series:
        series[0]["markArea"] = {
            "silent": True,
            "data": [[
                {"xAxis": "2018", "itemStyle": {"color": "rgba(16, 185, 129, 0.1)"}},
                {"xAxis": "2024"}
            ]]
        }
    
    return {
        "title": {
            "text": "Emerging Beneficiaries: Who Gained from the Shift?",
            "left": "center",
            "textStyle": {"fontSize": 14}
        },
        "tooltip": {"trigger": "axis"},
        "legend": {
            "data": countries,
            "bottom": 0,
            "type": "scroll",
            "textStyle": {"fontSize": 11}
        },
        "grid": {"left": "3%", "right": "4%", "bottom": "15%", "top": "15%", "containLabel": True},
        "xAxis": {"type": "category", "data": [str(y) for y in years], "boundaryGap": False},
        "yAxis": {"type": "value", "name": "Share (%)"},
        "series": series,
        "animation": True,
        "animationDuration": 1000
    }


def create_era_comparison_echart(df: pd.DataFrame) -> dict:
    """Create ECharts grouped bar chart comparing China's share across eras."""
    imports = df[df["trade_type"] == "import"]
    
    era_data = []
    for era_name, config in ERAS.items():
        start_share = get_china_share(imports, config["start"])
        end_share = get_china_share(imports, config["end"])
        era_data.append({
            "era": era_name.split("(")[0].strip(),
            "start": round(start_share, 1),
            "end": round(end_share, 1),
            "color": config["color"]
        })
    
    df_eras = pd.DataFrame(era_data)
    eras = df_eras["era"].tolist()
    
    return {
        "title": {
            "text": "China's Share: Start vs End of Each Era",
            "left": "center",
            "textStyle": {"fontSize": 14}
        },
        "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}},
        "legend": {
            "data": ["Era Start", "Era End"],
            "top": "bottom",
            "textStyle": {"fontSize": 11}
        },
        "grid": {"left": "3%", "right": "4%", "bottom": "15%", "top": "15%", "containLabel": True},
        "xAxis": {"type": "category", "data": eras},
        "yAxis": {"type": "value", "name": "Share (%)", "max": 25},
        "series": [
            {
                "name": "Era Start",
                "type": "bar",
                "data": df_eras["start"].tolist(),
                "itemStyle": {"color": "#94a3b8"},
                "label": {"show": True, "position": "top", "formatter": "{c}%", "fontSize": 10}
            },
            {
                "name": "Era End",
                "type": "bar",
                "data": [
                    {"value": row["end"], "itemStyle": {"color": row["color"]}}
                    for _, row in df_eras.iterrows()
                ],
                "label": {"show": True, "position": "top", "formatter": "{c}%", "fontSize": 10}
            }
        ],
        "animation": True,
        "animationDuration": 800
    }


def main():
    # Header
    st.title("🌏 The China Story Arc")
    st.markdown("### How America's Supply Chain Shifted (1995-2024)")
    
    # Load data
    df = load_data()
    
    if df is None:
        st.error(
            "No processed data found. Please run the data processing notebooks first:\n\n"
            "1. Place your data in `data/raw/usitc/`\n"
            "2. Run `02_data_cleaning.ipynb`\n\n"
            "Then refresh this page."
        )
        return
    
    # Sidebar - Era Selection
    st.sidebar.header("Navigate the Story")
    
    selected_era = st.sidebar.radio(
        "Select Era",
        list(ERAS.keys()),
        index=3  # Default to Trade War Era
    )
    
    era_config = ERAS[selected_era]
    
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"### {era_config['title']}")
    st.sidebar.markdown(era_config["description"])
    st.sidebar.info(f"📌 **Key Event:** {era_config['key_event']}")
    
    # Get era metrics
    metrics = get_era_metrics(df, era_config)
    
    # Era Summary Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "China Share (Start)",
            f"{metrics['china_start']:.1f}%",
            help=f"China's share of US imports in {era_config['start']}"
        )
    
    with col2:
        st.metric(
            "China Share (End)",
            f"{metrics['china_end']:.1f}%",
            help=f"China's share of US imports in {era_config['end']}"
        )
    
    with col3:
        delta_color = "normal" if metrics['china_delta'] > 0 else "inverse"
        st.metric(
            "Change",
            f"{metrics['china_delta']:+.1f}pp",
            delta=f"{metrics['china_delta']:+.1f} percentage points",
            delta_color=delta_color
        )
    
    with col4:
        if len(metrics['top_5']) > 0:
            top_country = metrics['top_5'].iloc[0]
            st.metric(
                f"#1 in {era_config['end']}",
                top_country['country'],
                f"{top_country['share_pct']:.1f}%"
            )
    
    st.markdown("---")
    
    # Main China Arc Chart (with all focus countries) - ECharts version
    st.subheader("The Full Arc")
    echart_options = create_china_arc_echart(df, selected_era)
    st_echarts(options=echart_options, height="450px")
    
    # Era Deep Dive
    st.markdown("---")
    st.subheader(f"Era Deep Dive: {selected_era}")
    
    col1, col2 = st.columns(2)
    
    with col1:
        composition_opts = create_era_composition_echart(df, era_config)
        st_echarts(options=composition_opts, height="400px")
    
    with col2:
        comparison_opts = create_era_comparison_echart(df)
        st_echarts(options=comparison_opts, height="350px")
    
    # Winners and Losers
    st.markdown("---")
    st.subheader(f"Winners & Losers: {era_config['start']} → {era_config['end']}")
    
    col1, col2 = st.columns(2)
    winners_opts, losers_opts = create_winners_losers_echart(df, era_config)
    
    with col1:
        st_echarts(options=winners_opts, height="350px")
    
    with col2:
        st_echarts(options=losers_opts, height="350px")
    
    # Beneficiary Spotlight (only for Trade War era)
    if selected_era == "Trade War Era (2018-Present)":
        st.markdown("---")
        st.subheader("Beneficiary Spotlight: The China+1 Winners")
        
        spotlight_countries = ["Vietnam", "Mexico", "India", "Taiwan", "Thailand"]
        spotlight_opts = create_beneficiary_spotlight_echart(df, spotlight_countries)
        st_echarts(options=spotlight_opts, height="400px")
        
        # Growth metrics
        imports = df[df["trade_type"] == "import"]
        
        st.markdown("#### Growth Since Trade War Began (2018)")
        cols = st.columns(len(spotlight_countries))
        
        for i, country in enumerate(spotlight_countries):
            share_2018 = imports[(imports["country"] == country) & (imports["year"] == 2018)]["share_pct"]
            share_2024 = imports[(imports["country"] == country) & (imports["year"] == 2024)]["share_pct"]
            
            if len(share_2018) > 0 and len(share_2024) > 0:
                start = share_2018.values[0]
                end = share_2024.values[0]
                growth = ((end - start) / start) * 100 if start > 0 else 0
                
                with cols[i]:
                    st.metric(
                        country,
                        f"{end:.1f}%",
                        f"+{growth:.0f}% growth"
                    )
    
    # Data Explorer (collapsed)
    with st.expander("📊 Data Explorer"):
        imports = df[df["trade_type"] == "import"]
        era_data = imports[(imports["year"] >= era_config["start"]) & 
                          (imports["year"] <= era_config["end"])]
        
        st.dataframe(
            era_data[["country", "year", "value_real", "share_pct", "yoy_growth_pct"]]
            .sort_values(["year", "share_pct"], ascending=[True, False]),
            use_container_width=True,
            height=400
        )
        
        csv = era_data.to_csv(index=False)
        st.download_button(
            "Download Era Data (CSV)",
            csv,
            f"trade_data_{era_config['start']}_{era_config['end']}.csv",
            "text/csv"
        )
    
    # Footer
    st.markdown("---")
    st.caption(
        "Data source: USITC DataWeb | "
        "Values adjusted for inflation (2020 base year) | "
        "Analysis covers US imports by country of origin"
    )


if __name__ == "__main__":
    main()
