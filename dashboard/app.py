"""
US Trade Data Analysis Dashboard - The China Story Arc

Narrative-driven Streamlit dashboard exploring how America's supply chain
shifted from China to Mexico, Vietnam, and other emerging partners.

Run with: streamlit run dashboard/app.py
"""

import streamlit as st
import pandas as pd
from pathlib import Path
from streamlit_echarts import st_echarts
import streamlit_antd_components as sac
import streamlit_shadcn_ui as ui

# Page config
st.set_page_config(
    page_title="The China Story Arc",
    page_icon="🌏",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# =============================================================================
# MATERIAL DESIGN DARK THEME PALETTE
# Reference: https://m2.material.io/design/color/dark-theme.html
# =============================================================================
THEME = {
    # Backgrounds
    "background": "#121212",        # 0dp elevation
    "surface_1dp": "#1e1e1e",       # 5% white overlay
    "surface_4dp": "#272727",       # 9% white overlay
    "surface_8dp": "#2d2d2d",       # 12% white overlay
    "surface_16dp": "#353535",      # 15% white overlay
    
    # Brand colors (desaturated for dark theme)
    "primary": "#BB86FC",           # Purple 200
    "primary_variant": "#3700B3",   # Purple 700
    "secondary": "#03DAC6",         # Teal 200
    "error": "#CF6679",             # Desaturated red
    
    # Text emphasis levels
    "text_high": "rgba(255,255,255,0.87)",     # 87% - High emphasis
    "text_medium": "rgba(255,255,255,0.60)",   # 60% - Medium emphasis
    "text_disabled": "rgba(255,255,255,0.38)", # 38% - Disabled
}

# Mobile-first CSS with Material Design colors
st.markdown(f"""
<style>
/* Compact header */
.compact-header h1 {{
    font-size: 1.5rem !important;
    margin: 0 0 0.25rem 0 !important;
    font-weight: 700;
    color: {THEME["text_high"]};
}}
.compact-header p {{
    color: {THEME["text_medium"]};
    font-size: 0.875rem;
    margin: 0;
}}

/* Column spacing */
div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {{
    padding: 0 0.25rem;
}}

/* Smooth transitions */
iframe {{
    transition: opacity 0.3s ease;
}}

/* Hide sidebar */
section[data-testid="stSidebar"] {{
    display: none;
}}

/* Tighter spacing on mobile */
@media (max-width: 768px) {{
    .block-container {{
        padding: 1rem 0.75rem 80px 0.75rem !important;
    }}
    h2 {{
        font-size: 1.1rem !important;
    }}
    h3 {{
        font-size: 1rem !important;
    }}
    /* Make segmented control sticky at bottom on mobile */
    iframe[title="streamlit_antd_components.utils.component_func.sac"] {{
        position: fixed !important;
        bottom: 0 !important;
        left: 0 !important;
        right: 0 !important;
        width: 100vw !important;
        height: 60px !important;
        z-index: 1000 !important;
        background: {THEME["surface_8dp"]} !important;
        padding: 10px 8px !important;
        box-shadow: 0 -2px 10px rgba(0,0,0,0.5) !important;
        border-top: 1px solid {THEME["surface_16dp"]} !important;
    }}
}}

/* Antd segmented control dark theme styling */
.ant-segmented {{
    background: {THEME["surface_4dp"]} !important;
    border-radius: 8px !important;
}}
.ant-segmented-item {{
    color: {THEME["text_medium"]} !important;
}}
.ant-segmented-item-selected {{
    background: {THEME["primary"]} !important;
    color: #000000 !important;
}}
.ant-segmented-item:hover:not(.ant-segmented-item-selected) {{
    color: {THEME["text_high"]} !important;
}}

/* Dividers */
hr {{
    border-color: {THEME["surface_8dp"]} !important;
    opacity: 0.5;
}}

/* Caption text */
.stCaption {{
    color: {THEME["text_medium"]} !important;
}}
</style>
""", unsafe_allow_html=True)

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"

# Era definitions - the narrative structure (colors from Material palette)
ERAS = {
    "Pre-WTO (1995-2001)": {
        "start": 1995,
        "end": 2001,
        "title": "The Baseline",
        "description": "Before China joined WTO. Manufacturing distributed across Japan, Taiwan, and early Chinese SEZs.",
        "key_event": "China WTO accession Dec 2001",
        "color": "#90A4AE"  # Blue Grey 300
    },
    "WTO Boom (2001-2008)": {
        "start": 2001,
        "end": 2008,
        "title": "Rapid Rise",
        "description": "China's share explodes as manufacturing shifts en masse to take advantage of WTO access.",
        "key_event": "Financial Crisis 2008",
        "color": "#CF6679"  # Error/Red (Material dark)
    },
    "Post-Crisis (2009-2017)": {
        "start": 2009,
        "end": 2017,
        "title": "Maturation",
        "description": "China peaks at 21%+. Supply chains deeply integrated. Early nearshoring discussions begin.",
        "key_event": "Trump tariffs announced 2018",
        "color": "#FFB74D"  # Amber 300
    },
    "Trade War Era (2018-Present)": {
        "start": 2018,
        "end": 2024,
        "title": "The Shift Begins",
        "description": "China share declines to 13%. Mexico surpasses China. Vietnam and India emerge as alternatives.",
        "key_event": "Mexico becomes #1 import source 2023",
        "color": "#03DAC6"  # Secondary/Teal 200
    }
}

# Key countries for comparison
FOCUS_COUNTRIES = ["China", "Mexico", "Canada", "Vietnam", "Japan", "Germany", "South Korea", "Taiwan", "India", "Ireland"]

# Country colors using Material Design 300-level variants (optimized for dark backgrounds)
# Reference: https://m2.material.io/design/color/the-color-system.html
COUNTRY_COLORS = {
    "China": "#CF6679",      # Error color - prominent, the story's focus
    "Mexico": "#03DAC6",     # Secondary/Teal 200 - rising star
    "Vietnam": "#BB86FC",    # Primary/Purple 200
    "India": "#FFB74D",      # Amber 300 - warm accent
    "Canada": "#81C784",     # Green 300 - stable partner
    "Japan": "#64B5F6",      # Blue 300 - historical
    "Germany": "#4FC3F7",    # Light Blue 300 - European
    "South Korea": "#7986CB",# Indigo 300 - tech
    "Taiwan": "#F06292",     # Pink 300 - tech
    "Ireland": "#AED581",    # Light Green 300 - pharma
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


def create_winners_losers_echart(df: pd.DataFrame, era_config: dict, top_n: int = 10) -> tuple:
    """Create ECharts horizontal bar charts for winners and losers."""
    imports = df[df["trade_type"] == "import"]
    
    start_data = imports[imports["year"] == era_config["start"]][["country", "share_pct"]]
    end_data = imports[imports["year"] == era_config["end"]][["country", "share_pct"]]
    
    comparison = start_data.merge(
        end_data, on="country", suffixes=("_start", "_end"), how="outer"
    ).fillna(0)
    
    comparison["share_change"] = comparison["share_pct_end"] - comparison["share_pct_start"]
    
    # Winners chart (using Material secondary/teal for gains)
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
            "itemStyle": {"color": THEME["secondary"]},  # Teal 200
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
    
    # Losers chart (using Material error/red for losses)
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
            "itemStyle": {"color": THEME["error"]},  # Desaturated red
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
                "itemStyle": {"color": THEME["text_disabled"]},  # Subtle grey
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
    # Compact Header
    st.markdown("""
    <div class="compact-header">
        <h1>The China Story Arc</h1>
        <p>How America's Supply Chain Shifted · 1995-2024</p>
    </div>
    """, unsafe_allow_html=True)
    
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
    
    # Era selection with antd segmented control
    era_keys = list(ERAS.keys())
    
    # Build segmented items and mapping
    era_items = []
    label_to_key = {}
    for era_key in era_keys:
        name_parts = era_key.split("(")
        era_name = name_parts[0].strip()
        era_items.append(sac.SegmentedItem(label=era_name))
        label_to_key[era_name] = era_key
    
    # Get era from query params or default to Trade War Era
    query_era = st.query_params.get("era", None)
    if query_era and query_era in era_keys:
        default_index = era_keys.index(query_era)
    else:
        default_index = 3  # Default to Trade War Era
    
    # Era selector (sticky on mobile via CSS)
    selected_label = sac.segmented(
        items=era_items,
        index=default_index,
        align="center",
        size="xs",  # Extra small to fit on mobile
        radius="md",
        color="violet",  # Material purple
        bg_color="transparent",
        divider=False,
        use_container_width=True,
        key="era_selector"
    )
    
    # Map label back to full era key and update URL
    selected_era = label_to_key.get(selected_label, era_keys[default_index])
    st.query_params["era"] = selected_era
    era_config = ERAS[selected_era]
    
    # Era context - compact inline description
    st.caption(f"**{era_config['title']}:** {era_config['description']}")
    
    # Get era metrics
    metrics = get_era_metrics(df, era_config)
    top_country = metrics['top_5'].iloc[0] if len(metrics['top_5']) > 0 else {"country": "N/A", "share_pct": 0}
    
    # Metric cards using shadcn
    cols = st.columns(4)
    with cols[0]:
        ui.metric_card(
            title=f"China {era_config['start']}",
            content=f"{metrics['china_start']:.1f}%",
            key="metric_start"
        )
    with cols[1]:
        ui.metric_card(
            title=f"China {era_config['end']}",
            content=f"{metrics['china_end']:.1f}%",
            key="metric_end"
        )
    with cols[2]:
        delta_str = f"{metrics['china_delta']:+.1f}pp"
        ui.metric_card(
            title="Change",
            content=delta_str,
            description=f"{metrics['china_delta']:+.1f} pts",
            key="metric_change"
        )
    with cols[3]:
        ui.metric_card(
            title=f"#1 in {era_config['end']}",
            content=top_country['country'],
            description=f"{top_country['share_pct']:.1f}%",
            key="metric_top"
        )
    
    st.markdown("---")
    
    # Main China Arc Chart (with all focus countries) - ECharts version
    st.subheader("The Full Arc")
    echart_options = create_china_arc_echart(df, selected_era)
    st_echarts(options=echart_options, height="450px")
    
    # Era Comparison - full width
    st.markdown("---")
    st.subheader("China Across Eras")
    comparison_opts = create_era_comparison_echart(df)
    st_echarts(options=comparison_opts, height="300px")
    
    # Winners and Losers
    st.markdown("---")
    st.subheader(f"Winners & Losers: {era_config['start']} → {era_config['end']}")
    
    col1, col2 = st.columns(2)
    winners_opts, losers_opts = create_winners_losers_echart(df, era_config)
    
    with col1:
        st_echarts(options=winners_opts, height="350px")
    
    with col2:
        st_echarts(options=losers_opts, height="350px")
    
    # Trade War Beneficiaries - Growth cards (only for Trade War era)
    if selected_era == "Trade War Era (2018-Present)":
        st.markdown("---")
        st.subheader("Trade War Beneficiaries")
        
        spotlight_countries = ["Vietnam", "Mexico", "India", "Taiwan", "Thailand"]
        imports = df[df["trade_type"] == "import"]
        
        # Build growth data
        growth_data = []
        for country in spotlight_countries:
            share_2018 = imports[(imports["country"] == country) & (imports["year"] == 2018)]["share_pct"]
            share_2024 = imports[(imports["country"] == country) & (imports["year"] == 2024)]["share_pct"]
            
            if len(share_2018) > 0 and len(share_2024) > 0:
                start = share_2018.values[0]
                end = share_2024.values[0]
                growth = ((end - start) / start) * 100 if start > 0 else 0
                growth_data.append({"country": country, "share": end, "growth": growth})
        
        # Display with shadcn metric cards
        growth_cols = st.columns(len(growth_data))
        for i, data in enumerate(growth_data):
            with growth_cols[i]:
                ui.metric_card(
                    title=data["country"],
                    content=f"{data['share']:.1f}%",
                    description=f"+{data['growth']:.0f}% since 2018",
                    key=f"growth_{data['country']}"
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
