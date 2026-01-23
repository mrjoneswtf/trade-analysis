"""
US Trade Data Analysis Dashboard - The China Story Arc

Scrollytelling narrative exploring how America's supply chain
shifted from China to Mexico, Vietnam, and other emerging partners.

Run with: streamlit run dashboard/app.py
"""

import streamlit as st
import pandas as pd
from pathlib import Path
from streamlit_echarts import st_echarts
import streamlit_shadcn_ui as ui

# Page config
st.set_page_config(
    page_title="The China Story Arc",
    page_icon="🌏",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# =============================================================================
# MATERIAL DESIGN DARK THEME PALETTE
# Reference: https://m2.material.io/design/color/dark-theme.html
# =============================================================================
THEME = {
    # Backgrounds
    "background": "#121212",
    "surface_1dp": "#1e1e1e",
    "surface_4dp": "#272727",
    "surface_8dp": "#2d2d2d",
    "surface_16dp": "#353535",
    
    # Brand colors
    "primary": "#BB86FC",
    "primary_variant": "#3700B3",
    "secondary": "#03DAC6",
    "error": "#CF6679",
    
    # Text emphasis
    "text_high": "rgba(255,255,255,0.87)",
    "text_medium": "rgba(255,255,255,0.60)",
    "text_disabled": "rgba(255,255,255,0.38)",
}

# =============================================================================
# CSS - Editorial layout with 800px max-width
# =============================================================================
st.markdown(f"""
<style>
/* Editorial max-width container */
.block-container {{
    max-width: 800px !important;
    margin: 0 auto !important;
    padding: 2rem 1rem !important;
}}

/* Compact header */
.compact-header h1 {{
    font-size: 2rem !important;
    margin: 0 0 0.25rem 0 !important;
    font-weight: 700;
    color: {THEME["text_high"]};
}}
.compact-header p {{
    color: {THEME["text_medium"]};
    font-size: 1rem;
    margin: 0 0 1.5rem 0;
}}

/* Era Sections */
.era-section {{
    padding: 2.5rem 0;
    border-bottom: 1px solid {THEME["surface_8dp"]};
}}
.era-title {{
    font-size: 1.5rem;
    color: {THEME["text_high"]};
    margin-bottom: 0.75rem;
    font-weight: 600;
}}
.era-hook {{
    font-size: 1.2rem;
    font-style: italic;
    color: {THEME["primary"]};
    margin-bottom: 1.25rem;
    line-height: 1.4;
}}
.era-context {{
    color: {THEME["text_medium"]};
    line-height: 1.7;
    margin-bottom: 1.5rem;
    font-size: 1rem;
}}
.era-takeaway {{
    font-weight: 500;
    color: {THEME["text_high"]};
    border-left: 3px solid {THEME["primary"]};
    padding-left: 1rem;
    margin-top: 1.5rem;
    line-height: 1.5;
}}
.key-event {{
    background: {THEME["surface_4dp"]};
    padding: 0.875rem 1rem;
    border-radius: 8px;
    margin: 1.25rem 0;
    font-size: 0.95rem;
}}
.key-event strong {{
    color: {THEME["secondary"]};
}}

/* Hide sidebar */
section[data-testid="stSidebar"] {{
    display: none;
}}

/* Dividers */
hr {{
    border-color: {THEME["surface_8dp"]} !important;
    margin: 0 !important;
}}

/* Caption text */
.stCaption {{
    color: {THEME["text_medium"]} !important;
}}

/* Smooth transitions */
iframe {{
    transition: opacity 0.3s ease;
}}

/* Mobile adjustments */
@media (max-width: 768px) {{
    .block-container {{
        padding: 1rem 0.75rem !important;
    }}
    .compact-header h1 {{
        font-size: 1.5rem !important;
    }}
    .compact-header p {{
        font-size: 0.875rem;
    }}
    .era-title {{
        font-size: 1.25rem;
    }}
    .era-hook {{
        font-size: 1.05rem;
    }}
    .era-section {{
        padding: 1.5rem 0;
    }}
}}

/* Era metrics grid - responsive 2x3 (mobile) to 3x2 (desktop) */
.era-metrics-grid {{
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 0.5rem;
    margin-bottom: 1rem;
}}

/* Desktop: 3 columns with reordering */
@media (min-width: 769px) {{
    .era-metrics-grid {{
        grid-template-columns: repeat(3, 1fr);
    }}
    /* Reorder: 1,2,5 on row 1; 3,4,6 on row 2 */
    .era-metrics-grid > .metric-cell:nth-child(1) {{ order: 1; }}
    .era-metrics-grid > .metric-cell:nth-child(2) {{ order: 2; }}
    .era-metrics-grid > .metric-cell:nth-child(3) {{ order: 4; }}
    .era-metrics-grid > .metric-cell:nth-child(4) {{ order: 5; }}
    .era-metrics-grid > .metric-cell:nth-child(5) {{ order: 3; }}
    .era-metrics-grid > .metric-cell:nth-child(6) {{ order: 6; }}
}}

/* Metric cell styling */
.metric-cell {{
    background: {THEME["surface_4dp"]};
    border-radius: 8px;
    padding: 0.875rem 1rem;
}}
.metric-cell .label {{
    font-size: 0.75rem;
    color: {THEME["text_medium"]};
    margin-bottom: 0.25rem;
}}
.metric-cell .value {{
    font-size: 1.1rem;
    font-weight: 600;
    color: {THEME["text_high"]};
}}
</style>
""", unsafe_allow_html=True)

# =============================================================================
# DATA PATHS
# =============================================================================
PROJECT_ROOT = Path(__file__).parent.parent
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"

# =============================================================================
# ERA DEFINITIONS
# =============================================================================
ERAS = {
    "pre-wto": {
        "start": 1995,
        "end": 2001,
        "title": "Pre-WTO",
        "years": "1995-2001",
        "color": "#90A4AE"
    },
    "wto-boom": {
        "start": 2001,
        "end": 2008,
        "title": "WTO Boom",
        "years": "2001-2008",
        "color": "#CF6679"
    },
    "post-crisis": {
        "start": 2009,
        "end": 2017,
        "title": "Post-Crisis",
        "years": "2009-2017",
        "color": "#FFB74D"
    },
    "trade-war": {
        "start": 2018,
        "end": 2025,  # Dynamic - will use latest available year
        "title": "Trade War",
        "years": "2018-Present",
        "color": "#03DAC6"
    }
}

# =============================================================================
# ERA CONTENT - Narrative copy for each era
# =============================================================================
ERA_CONTENT = {
    "pre-wto": {
        "hook": "Before the flood: When 'Made in China' was just getting started",
        "context": "In the mid-1990s, Japan and Canada dominated US imports. China was a rising player, but still accounted for less than 7% of goods entering American ports. That was about to change.",
        "key_event": "Dec 2001: China joins the World Trade Organization",
        "takeaway": "China doubled its share in six years, setting the stage for an unprecedented manufacturing migration."
    },
    "wto-boom": {
        "hook": "The decade that rewired global manufacturing",
        "context": "WTO membership gave China permanent normal trade relations with the US. American companies rushed to offshore production. Container ships couldn't be built fast enough.",
        "key_event": "2007: China becomes the #1 source of US imports",
        "takeaway": "In seven years, China went from third place to first, capturing more import share than any country in modern history."
    },
    "post-crisis": {
        "hook": "Peak China: The plateau before the storm",
        "context": "After the 2008 financial crisis, China's rise continued but slowed. By 2015, it held over 21% of US imports. Supply chains were deeply entrenched. Early whispers of \"reshoring\" began.",
        "key_event": "2015: China hits all-time high of 21.6% import share",
        "takeaway": "China's dominance seemed unshakeable—but beneath the surface, costs were rising and alternatives were emerging."
    },
    "trade-war": {
        "hook": "The great unwinding accelerates",
        "context": "Section 301 tariffs began the shift in 2018. COVID-19 exposed fragility. Now, 2025's aggressive tariff expansion is accelerating the exodus from China at unprecedented speed.",
        "key_events": [
            "2018: Section 301 tariffs enacted",
            "2020: COVID exposes supply chain fragility",
            "2023: Mexico overtakes China as #1",
            "2025: 'Liberation Day' tariffs reach 145% on some goods"
        ],
        "chapter_2": {
            "title": "Chapter 2: The 2025 Acceleration",
            "text": "In just 10 months of 2025, China's import share plunged from 13% to under 10%—a drop that previously took years. Taiwan nearly doubled its share (semiconductors), while Vietnam and Mexico consolidated their positions as the go-to alternatives."
        },
        "takeaway": "The 'China+1' strategy is now standard practice. What began as tariff policy has become a structural rewiring of global supply chains."
    }
}

# =============================================================================
# FOCUS COUNTRIES AND COLORS
# =============================================================================
HERO_COUNTRIES = ["China", "Mexico", "Canada", "Japan", "Vietnam"]

COUNTRY_COLORS = {
    "China": "#CF6679",
    "Mexico": "#03DAC6",
    "Vietnam": "#BB86FC",
    "India": "#FFB74D",
    "Canada": "#81C784",
    "Japan": "#64B5F6",
    "Germany": "#4FC3F7",
    "South Korea": "#7986CB",
    "Taiwan": "#F06292",
    "Ireland": "#AED581",
    "Thailand": "#A1887F",
}


def get_data_file_mtime() -> float:
    """Get modification time of latest data file for cache busting."""
    for year in [2025, 2024]:
        trade_path = DATA_PROCESSED / f"trade_data_1995_{year}.csv"
        if trade_path.exists():
            return trade_path.stat().st_mtime
    return 0.0


@st.cache_data
def load_data(_cache_key: float = None) -> pd.DataFrame:
    """Load processed trade data. Tries 2025 file first, falls back to 2024."""
    # Try loading the most recent data file
    for year in [2025, 2024]:
        trade_path = DATA_PROCESSED / f"trade_data_1995_{year}.csv"
        if trade_path.exists():
            df = pd.read_csv(trade_path)
            return df
    
    # Fallback: try the old path
    trade_path = DATA_PROCESSED / "trade_data_1995_2024.csv"
    if trade_path.exists():
        return pd.read_csv(trade_path)
    return None


def get_china_share(df: pd.DataFrame, year: int) -> float:
    """Get China's import share for a specific year."""
    china_data = df[(df["country"] == "China") & 
                    (df["year"] == year) & 
                    (df["trade_type"] == "import")]
    if len(china_data) > 0:
        return china_data["share_pct"].values[0]
    return 0.0


def get_era_metrics(df: pd.DataFrame, era_key: str) -> dict:
    """Calculate key metrics for an era including top non-China partner."""
    config = ERAS[era_key]
    imports = df[df["trade_type"] == "import"]
    
    # Cap era end year at actual data range
    data_max_year = imports["year"].max()
    era_end_year = min(config["end"], data_max_year)
    
    # China metrics
    china_start = get_china_share(imports, config["start"])
    china_end = get_china_share(imports, era_end_year)
    
    # Get top countries at end of era
    end_year_data = imports[imports["year"] == era_end_year]
    top_4 = end_year_data.nlargest(4, "share_pct")["country"].tolist()
    top_1 = top_4[0] if top_4 else "N/A"
    top_234 = "/".join(top_4[1:4]) if len(top_4) > 1 else "N/A"
    
    # Find top non-China partner at end of era
    non_china = end_year_data[end_year_data["country"] != "China"]
    if len(non_china) > 0:
        top_partner = non_china.nlargest(1, "share_pct").iloc[0]
        partner_name = top_partner["country"]
        partner_end = top_partner["share_pct"]
        
        # Get partner's start share
        partner_start_data = imports[
            (imports["country"] == partner_name) & 
            (imports["year"] == config["start"])
        ]["share_pct"]
        partner_start = partner_start_data.values[0] if len(partner_start_data) > 0 else 0.0
    else:
        partner_name = "N/A"
        partner_start = 0.0
        partner_end = 0.0
    
    return {
        "china_start": china_start,
        "china_end": china_end,
        "china_delta": china_end - china_start,
        "partner_name": partner_name,
        "partner_start": partner_start,
        "partner_end": partner_end,
        "partner_delta": partner_end - partner_start,
        "top_1": top_1,
        "top_234": top_234
    }


def create_hero_chart(df: pd.DataFrame) -> dict:
    """Create ECharts config for the hero chart - static overview."""
    imports = df[df["trade_type"] == "import"]
    years = sorted(imports["year"].unique().tolist())
    data_max_year = max(years)
    
    # Build subtle era shading (cap at actual data range)
    mark_area_data = []
    for era_key, config in ERAS.items():
        era_end = min(config["end"], data_max_year)
        mark_area_data.append([
            {
                "xAxis": str(config["start"]),
                "itemStyle": {"color": config["color"], "opacity": 0.08}
            },
            {"xAxis": str(era_end)}
        ])
    
    # Build series for top 5 countries
    series = []
    for country in HERO_COUNTRIES:
        country_data = imports[imports["country"] == country].sort_values("year")
        if len(country_data) > 0:
            data_dict = dict(zip(country_data["year"].astype(str), country_data["share_pct"].round(1)))
            data = [data_dict.get(str(y), None) for y in years]
            
            color = COUNTRY_COLORS.get(country, "#6b7280")
            is_china = country == "China"
            
            series_config = {
                "name": country,
                "type": "line",
                "data": data,
                "smooth": True,
                "symbol": "circle" if is_china else "none",
                "symbolSize": 4 if is_china else 0,
                "lineStyle": {
                    "width": 3 if is_china else 2,
                    "color": color,
                    "opacity": 1 if is_china else 0.7
                },
                "itemStyle": {"color": color},
                "z": 10 if is_china else 1,
            }
            
            # Add era shading to China's line
            if is_china:
                series_config["markArea"] = {"silent": True, "data": mark_area_data}
            
            series.append(series_config)
    
    return {
        "tooltip": {
            "trigger": "axis",
            "axisPointer": {"type": "cross"}
        },
        "legend": {
            "data": HERO_COUNTRIES,
            "bottom": 0,
            "textStyle": {"fontSize": 11}
        },
        "grid": {
            "left": "3%",
            "right": "4%",
            "bottom": "12%",
            "top": "5%",
            "containLabel": True
        },
        "xAxis": {
            "type": "category",
            "data": [str(y) for y in years],
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


def create_chapter2_chart(df: pd.DataFrame) -> dict:
    """Create focused 2018-2025 chart for Chapter 2 section."""
    imports = df[df["trade_type"] == "import"]
    
    # Filter to Trade War era (2018+)
    trade_war_imports = imports[imports["year"] >= 2018]
    years = sorted(trade_war_imports["year"].unique().tolist())
    max_year = max(years)
    
    # Key Trade War players
    chapter2_countries = ["China", "Mexico", "Vietnam", "Taiwan"]
    
    # Build series
    series = []
    for country in chapter2_countries:
        country_data = trade_war_imports[trade_war_imports["country"] == country].sort_values("year")
        if len(country_data) > 0:
            data_dict = dict(zip(country_data["year"].astype(str), country_data["share_pct"].round(1)))
            data = [data_dict.get(str(y), None) for y in years]
            
            color = COUNTRY_COLORS.get(country, "#6b7280")
            is_china = country == "China"
            
            series.append({
                "name": country,
                "type": "line",
                "data": data,
                "smooth": True,
                "symbol": "circle",
                "symbolSize": 6 if is_china else 4,
                "lineStyle": {
                    "width": 3 if is_china else 2,
                    "color": color,
                    "opacity": 1 if is_china else 0.8
                },
                "itemStyle": {"color": color},
                "z": 10 if is_china else 1,
            })
    
    # X-axis labels with YTD marker for latest year
    x_labels = []
    for y in years:
        if y == max_year:
            x_labels.append(f"{y}*")  # Mark YTD
        else:
            x_labels.append(str(y))
    
    return {
        "tooltip": {
            "trigger": "axis",
            "backgroundColor": THEME["surface_8dp"],
            "borderColor": THEME["surface_16dp"],
            "textStyle": {"color": THEME["text_high"]}
        },
        "legend": {
            "data": chapter2_countries,
            "bottom": 0,
            "textStyle": {"fontSize": 10, "color": THEME["text_medium"]}
        },
        "grid": {
            "left": "8%",
            "right": "5%",
            "bottom": "18%",
            "top": "8%",
            "containLabel": True
        },
        "xAxis": {
            "type": "category",
            "data": x_labels,
            "boundaryGap": False,
            "axisLabel": {"fontSize": 10, "color": THEME["text_medium"]},
            "axisLine": {"lineStyle": {"color": THEME["surface_16dp"]}}
        },
        "yAxis": {
            "type": "value",
            "name": "Import Share (%)",
            "nameLocation": "middle",
            "nameGap": 35,
            "nameTextStyle": {"fontSize": 10, "color": THEME["text_medium"]},
            "min": 0,
            "max": 25,
            "axisLabel": {"fontSize": 10, "color": THEME["text_medium"]},
            "splitLine": {"lineStyle": {"color": THEME["surface_16dp"], "opacity": 0.3}}
        },
        "series": series,
        "animation": True,
        "animationDuration": 800,
        "animationEasing": "cubicOut"
    }


def create_winners_losers_echart(df: pd.DataFrame, era_key: str, top_n: int = 8) -> tuple:
    """Create ECharts horizontal bar charts for winners and losers."""
    config = ERAS[era_key]
    imports = df[df["trade_type"] == "import"]
    
    # Cap era end year at actual data range
    data_max_year = imports["year"].max()
    era_end_year = min(config["end"], data_max_year)
    
    start_data = imports[imports["year"] == config["start"]][["country", "share_pct"]]
    end_data = imports[imports["year"] == era_end_year][["country", "share_pct"]]
    
    comparison = start_data.merge(
        end_data, on="country", suffixes=("_start", "_end"), how="outer"
    ).fillna(0)
    comparison["share_change"] = comparison["share_pct_end"] - comparison["share_pct_start"]
    
    # Winners
    winners = comparison.nlargest(top_n, "share_change")
    winners_opts = {
        "title": {"text": "Gained Share", "left": "center", "textStyle": {"fontSize": 14}},
        "tooltip": {"trigger": "axis"},
        "grid": {"right": "30%", "left": "15%", "top": "15%", "bottom": "10%"},
        "xAxis": {"type": "value"},
        "yAxis": {
            "type": "category",
            "data": winners["country"].tolist()[::-1],
            "axisLabel": {"fontSize": 11},
            "position": "right"
        },
        "series": [{
            "type": "bar",
            "data": winners["share_change"].round(1).tolist()[::-1],
            "itemStyle": {"color": THEME["secondary"]},
            "label": {"show": True, "position": "left", "formatter": "+{c}pp", "fontSize": 10, "color": THEME["text_high"]},
        }],
        "animation": True
    }
    
    # Losers
    losers = comparison.nsmallest(top_n, "share_change")
    losers_opts = {
        "title": {"text": "Lost Share", "left": "center", "textStyle": {"fontSize": 14}},
        "tooltip": {"trigger": "axis"},
        "grid": {"left": "30%", "right": "15%", "top": "15%", "bottom": "10%"},
        "xAxis": {"type": "value"},
        "yAxis": {
            "type": "category",
            "data": losers["country"].tolist()[::-1],
            "axisLabel": {"fontSize": 11}
        },
        "series": [{
            "type": "bar",
            "data": losers["share_change"].round(1).tolist()[::-1],
            "itemStyle": {"color": THEME["error"]},
            "label": {"show": True, "position": "right", "formatter": "{c}pp", "fontSize": 10, "color": THEME["text_high"]},
        }],
        "animation": True
    }
    
    return winners_opts, losers_opts


def render_header(df: pd.DataFrame):
    """Render the page header with dynamic year range."""
    max_year = df["year"].max() if df is not None else 2024
    st.markdown(f"""
    <div class="compact-header">
        <h1>The China Story Arc</h1>
        <p>How America's Supply Chain Shifted · 1995-{max_year}</p>
    </div>
    """, unsafe_allow_html=True)


def render_hero_chart(df: pd.DataFrame):
    """Render the hero chart showing full trajectory."""
    chart_opts = create_hero_chart(df)
    st_echarts(options=chart_opts, height="400px")


def render_era_section(df: pd.DataFrame, era_key: str):
    """Render a single era section with narrative content."""
    config = ERAS[era_key]
    content = ERA_CONTENT[era_key]
    metrics = get_era_metrics(df, era_key)
    
    # Era title
    st.markdown(f"""
    <div class="era-section" id="{era_key}">
        <h2 class="era-title">{config['title']} ({config['years']})</h2>
        <p class="era-hook">"{content['hook']}"</p>
        <p class="era-context">{content['context']}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Metrics - 6 cards in CSS Grid (2x3 mobile, 3x2 desktop with reordering)
    partner = metrics['partner_name']
    china_delta_sign = "+" if metrics['china_delta'] >= 0 else ""
    partner_delta_sign = "+" if metrics['partner_delta'] >= 0 else ""
    
    # Cards in mobile order: 1-China Share, 2-China Change, 3-Partner Share, 
    # 4-Partner Change, 5-#1 Country, 6-#2/#3/#4
    # CSS reorders on desktop to: Row1(1,2,5) Row2(3,4,6)
    st.markdown(f"""
    <div class="era-metrics-grid">
        <div class="metric-cell">
            <div class="label">China Share</div>
            <div class="value">{metrics['china_start']:.1f}% → {metrics['china_end']:.1f}%</div>
        </div>
        <div class="metric-cell">
            <div class="label">China Change</div>
            <div class="value">{china_delta_sign}{metrics['china_delta']:.1f}pp</div>
        </div>
        <div class="metric-cell">
            <div class="label">{partner} Share</div>
            <div class="value">{metrics['partner_start']:.1f}% → {metrics['partner_end']:.1f}%</div>
        </div>
        <div class="metric-cell">
            <div class="label">{partner} Change</div>
            <div class="value">{partner_delta_sign}{metrics['partner_delta']:.1f}pp</div>
        </div>
        <div class="metric-cell">
            <div class="label">#1 Country</div>
            <div class="value">{metrics['top_1']}</div>
        </div>
        <div class="metric-cell">
            <div class="label">#2/#3/#4</div>
            <div class="value">{metrics['top_234']}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Key event(s)
    if era_key == "trade-war":
        # Multiple events for trade war era
        events_html = ""
        for event in content["key_events"]:
            events_html += f'<div class="key-event">📅 <strong>KEY EVENT:</strong> {event}</div>'
        st.markdown(events_html, unsafe_allow_html=True)
        
        # Chapter 2 subsection (if present)
        if "chapter_2" in content:
            ch2 = content["chapter_2"]
            
            # Chapter 2 title with underline accent
            st.markdown(f"""
            <h4 style="color: {THEME['secondary']}; margin: 2rem 0 1rem 0; font-size: 1.1rem; 
                padding-bottom: 0.5rem; border-bottom: 2px solid {THEME['secondary']};">
                {ch2['title']}
            </h4>
            """, unsafe_allow_html=True)
            
            # Embed the focused 2018-2025 chart
            chapter2_chart = create_chapter2_chart(df)
            st_echarts(options=chapter2_chart, height="280px")
            
            # Chapter 2 narrative in styled box
            st.markdown(f"""
            <div style="margin: 0.5rem 0 2rem 0; padding: 1rem 1.25rem; background: {THEME['surface_4dp']}; 
                border-radius: 8px; border-left: 4px solid {THEME['secondary']};">
                <p style="color: {THEME['text_disabled']}; margin: 0 0 0.75rem 0; font-size: 0.85rem; font-style: italic;">
                    * 2025 data through October (YTD)
                </p>
                <p style="color: {THEME['text_high']}; margin: 0; line-height: 1.6;">{ch2['text']}</p>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="key-event">
            📅 <strong>KEY EVENT:</strong> {content['key_event']}
        </div>
        """, unsafe_allow_html=True)
    
    # Takeaway
    st.markdown(f"""
    <p class="era-takeaway">{content['takeaway']}</p>
    """, unsafe_allow_html=True)


def render_trade_war_expanded(df: pd.DataFrame):
    """Render expanded Trade War section with Winners/Losers and Beneficiaries."""
    # Get the actual end year from data
    imports = df[df["trade_type"] == "import"]
    end_year = imports["year"].max()
    
    # Winners and Losers charts
    st.subheader(f"Winners & Losers: 2018 → {end_year}")
    
    col1, col2 = st.columns(2)
    winners_opts, losers_opts = create_winners_losers_echart(df, "trade-war")
    
    with col1:
        st_echarts(options=winners_opts, height="350px")
    with col2:
        st_echarts(options=losers_opts, height="350px")
    
    # Beneficiaries cards
    st.subheader("Trade War Beneficiaries")
    
    spotlight_countries = ["Vietnam", "Mexico", "India", "Taiwan", "Thailand"]
    imports = df[df["trade_type"] == "import"]
    latest_year = imports["year"].max()
    
    growth_data = []
    for country in spotlight_countries:
        share_2018 = imports[(imports["country"] == country) & (imports["year"] == 2018)]["share_pct"]
        share_latest = imports[(imports["country"] == country) & (imports["year"] == latest_year)]["share_pct"]
        
        if len(share_2018) > 0 and len(share_latest) > 0:
            start = share_2018.values[0]
            end = share_latest.values[0]
            growth = ((end - start) / start) * 100 if start > 0 else 0
            growth_data.append({"country": country, "share": end, "growth": growth})
    
    # Display beneficiary cards - responsive grid
    cols = st.columns(len(growth_data))
    for i, data in enumerate(growth_data):
        with cols[i]:
            ui.metric_card(
                title=data["country"],
                content=f"{data['share']:.1f}%",
                description=f"+{data['growth']:.0f}% since 2018",
                key=f"beneficiary_{data['country']}"
            )


def render_data_explorer(df: pd.DataFrame):
    """Render the data explorer expander."""
    with st.expander("📊 Data Explorer"):
        imports = df[df["trade_type"] == "import"]
        
        st.dataframe(
            imports[["country", "year", "value_real", "share_pct", "yoy_growth_pct"]]
            .sort_values(["year", "share_pct"], ascending=[True, False]),
            use_container_width=True,
            height=400
        )
        
        csv = imports.to_csv(index=False)
        st.download_button(
            "Download Full Dataset (CSV)",
            csv,
            "trade_data_1995_2024.csv",
            "text/csv"
        )


def render_footer(df: pd.DataFrame):
    """Render the footer with data source info and YTD note if applicable."""
    st.markdown("---")
    
    # Build footer text
    footer_parts = [
        "Data source: USITC DataWeb",
        "Values adjusted for inflation (2020 base year)",
        "Analysis covers US imports by country of origin"
    ]
    
    # Check for YTD data
    if 'is_ytd' in df.columns and df['is_ytd'].any():
        ytd_years = df[df['is_ytd']]['year'].unique()
        for year in ytd_years:
            ytd_data = df[(df['year'] == year) & (df['is_ytd'])]
            if 'last_month' in df.columns:
                # Use max last_month across all countries for that year
                max_month = int(ytd_data['last_month'].max())
                month_names = ['', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                              'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
                month_name = month_names[max_month] if max_month <= 12 else ''
                footer_parts.append(f"{year} data through {month_name}")
    
    st.caption(" | ".join(footer_parts))


def main():
    """Main function - linear narrative flow."""
    # Load data with cache busting based on file modification time
    df = load_data(_cache_key=get_data_file_mtime())
    
    if df is None:
        st.error(
            "No processed data found. Please run the data processing notebooks first:\n\n"
            "1. Place your data in `data/raw/usitc/`\n"
            "2. Run `02_data_cleaning.ipynb`\n\n"
            "Then refresh this page."
        )
        return
    
    # Header
    render_header(df)
    
    # Hero Chart - Full trajectory overview
    render_hero_chart(df)
    
    st.markdown("---")
    
    # Era 1: Pre-WTO
    render_era_section(df, "pre-wto")
    
    st.markdown("---")
    
    # Era 2: WTO Boom
    render_era_section(df, "wto-boom")
    
    st.markdown("---")
    
    # Era 3: Post-Crisis
    render_era_section(df, "post-crisis")
    
    st.markdown("---")
    
    # Era 4: Trade War - EXPANDED with additional charts
    render_era_section(df, "trade-war")
    
    st.markdown("")  # Spacing
    
    # Trade War expanded content
    render_trade_war_expanded(df)
    
    st.markdown("---")
    
    # Data Explorer
    render_data_explorer(df)
    
    # Footer
    render_footer(df)


if __name__ == "__main__":
    main()
