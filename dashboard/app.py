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

# Page config
st.set_page_config(
    page_title="The China Story Arc",
    page_icon="🌏",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Mobile-first CSS
st.markdown("""
<style>
/* Compact header */
.compact-header h1 {
    font-size: 1.5rem !important;
    margin: 0 0 0.25rem 0 !important;
    font-weight: 700;
    color: rgba(255,255,255,0.87);
}
.compact-header p {
    color: rgba(255,255,255,0.60);
    font-size: 0.875rem;
    margin: 0;
}

/* Era tabs styling */
div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {
    padding: 0 0.25rem;
}

/* Responsive metrics grid */
.metric-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 0.5rem;
    margin: 0.5rem 0;
}
@media (min-width: 768px) {
    .metric-grid {
        grid-template-columns: repeat(4, 1fr);
    }
}
.metric-card {
    background: #1e1e1e;
    border-radius: 0.75rem;
    padding: 0.75rem;
    text-align: center;
    border: 1px solid rgba(255,255,255,0.12);
}
.metric-card .label {
    font-size: 0.7rem;
    color: rgba(255,255,255,0.60);
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 0.25rem;
}
.metric-card .value {
    font-size: 1.25rem;
    font-weight: 700;
    color: rgba(255,255,255,0.87);
}
.metric-card .delta {
    font-size: 0.75rem;
    margin-top: 0.125rem;
}
.metric-card .delta.positive { color: #4ade80; }
.metric-card .delta.negative { color: #CF6679; }

/* Growth cards grid */
.growth-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 0.5rem;
    margin: 0.5rem 0;
}
@media (min-width: 640px) {
    .growth-grid {
        grid-template-columns: repeat(3, 1fr);
    }
}
@media (min-width: 768px) {
    .growth-grid {
        grid-template-columns: repeat(5, 1fr);
    }
}

/* Smooth transitions */
iframe {
    transition: opacity 0.3s ease;
}

/* Hide sidebar on mobile */
@media (max-width: 768px) {
    section[data-testid="stSidebar"] {
        display: none;
    }
}

/* Tighter spacing on mobile */
@media (max-width: 768px) {
    .block-container {
        padding: 1rem 0.75rem !important;
        padding-bottom: 5rem !important;
    }
    h2 {
        font-size: 1.1rem !important;
    }
    h3 {
        font-size: 1rem !important;
    }
}

/* Era navigation buttons */
.era-nav {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    width: 100%;
    background: #1e1e1e;
    margin: 0.5rem 0;
    border-top: 1px solid rgba(255,255,255,0.12);
}

@media (max-width: 768px) {
    .era-nav {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        z-index: 999;
        box-shadow: 0 -4px 12px rgba(0,0,0,0.4);
        margin: 0;
    }
}

.era-btn {
    padding: 0.6rem 0.25rem;
    text-align: center;
    cursor: pointer;
    border: none;
    transition: all 0.2s ease;
    text-decoration: none;
    display: block;
}

.era-btn .name {
    font-size: 0.75rem;
    font-weight: 600;
    display: block;
}

.era-btn .years {
    font-size: 0.65rem;
    opacity: 0.7;
    display: block;
    margin-top: 0.125rem;
}

.era-btn.selected {
    color: white;
}

.era-btn:not(.selected) {
    background: #1e1e1e;
    color: rgba(255,255,255,0.60);
}

.era-btn:not(.selected):hover {
    background: #282828;
    color: rgba(255,255,255,0.87);
}

/* Hide default Streamlit radio on mobile */
@media (max-width: 768px) {
    div[data-testid="stRadio"] {
        display: none !important;
    }
}

/* Hide custom era nav on desktop */
@media (min-width: 769px) {
    .era-nav {
        display: none;
    }
}
</style>
""", unsafe_allow_html=True)

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
    
    # Get era from query params or default to Trade War Era
    era_keys = list(ERAS.keys())
    query_era = st.query_params.get("era", None)
    
    # Determine selected era index
    if query_era and query_era in era_keys:
        default_index = era_keys.index(query_era)
    else:
        default_index = 3  # Trade War Era
    
    # Desktop: Streamlit radio (hidden on mobile via CSS)
    selected_era = st.radio(
        "Select Era",
        era_keys,
        index=default_index,
        horizontal=True,
        label_visibility="collapsed",
        key="era_radio"
    )
    
    # Update query params when radio changes
    st.query_params["era"] = selected_era
    
    era_config = ERAS[selected_era]
    
    # Era context - compact inline description
    st.caption(f"**{era_config['title']}:** {era_config['description']}")
    
    # Mobile: Custom sticky bottom navigation (hidden on desktop via CSS)
    era_buttons_html = []
    for era_key in era_keys:
        era_info = ERAS[era_key]
        # Extract just the era name (before parenthesis) and years
        name_parts = era_key.split("(")
        era_name = name_parts[0].strip()
        era_years = f"{era_info['start']}-{era_info['end']}"
        
        is_selected = era_key == selected_era
        selected_class = "selected" if is_selected else ""
        bg_style = f"background-color: {era_info['color']};" if is_selected else ""
        
        era_buttons_html.append(
            f'<a href="?era={era_key}" target="_self" class="era-btn {selected_class}" style="{bg_style}">'
            f'<span class="name">{era_name}</span>'
            f'<span class="years">{era_years}</span>'
            f'</a>'
        )
    
    st.markdown(
        f'<div class="era-nav">{"".join(era_buttons_html)}</div>',
        unsafe_allow_html=True
    )
    
    # Get era metrics
    metrics = get_era_metrics(df, era_config)
    
    # Responsive metrics grid (2x2 on mobile, 4 col on desktop)
    delta_class = "positive" if metrics['china_delta'] > 0 else "negative"
    top_country = metrics['top_5'].iloc[0] if len(metrics['top_5']) > 0 else {"country": "N/A", "share_pct": 0}
    
    st.markdown(f"""
    <div class="metric-grid">
        <div class="metric-card">
            <div class="label">China {era_config['start']}</div>
            <div class="value">{metrics['china_start']:.1f}%</div>
        </div>
        <div class="metric-card">
            <div class="label">China {era_config['end']}</div>
            <div class="value">{metrics['china_end']:.1f}%</div>
        </div>
        <div class="metric-card">
            <div class="label">Change</div>
            <div class="value">{metrics['china_delta']:+.1f}pp</div>
            <div class="delta {delta_class}">{metrics['china_delta']:+.1f} pts</div>
        </div>
        <div class="metric-card">
            <div class="label">#1 in {era_config['end']}</div>
            <div class="value">{top_country['country']}</div>
            <div class="delta">{top_country['share_pct']:.1f}%</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
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
        
        # Build responsive growth cards
        growth_cards_html = []
        for country in spotlight_countries:
            share_2018 = imports[(imports["country"] == country) & (imports["year"] == 2018)]["share_pct"]
            share_2024 = imports[(imports["country"] == country) & (imports["year"] == 2024)]["share_pct"]
            
            if len(share_2018) > 0 and len(share_2024) > 0:
                start = share_2018.values[0]
                end = share_2024.values[0]
                growth = ((end - start) / start) * 100 if start > 0 else 0
                growth_cards_html.append(
                    f'<div class="metric-card">'
                    f'<div class="label">{country}</div>'
                    f'<div class="value">{end:.1f}%</div>'
                    f'<div class="delta positive">+{growth:.0f}% since 2018</div>'
                    f'</div>'
                )
        
        cards_html = ''.join(growth_cards_html)
        st.markdown(f'<div class="growth-grid">{cards_html}</div>', unsafe_allow_html=True)
    
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
