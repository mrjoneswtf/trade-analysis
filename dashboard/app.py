"""
US Trade Data Analysis Dashboard - The China Story Arc

Narrative-driven Streamlit dashboard exploring how America's supply chain
shifted from China to Mexico, Vietnam, and other emerging partners.

Run with: streamlit run dashboard/app.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

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


def create_china_arc_chart(df: pd.DataFrame, selected_era: str, compare_countries: list = None) -> go.Figure:
    """Create the main China trajectory chart with era shading and comparison countries."""
    imports = df[df["trade_type"] == "import"]
    china_data = imports[imports["country"] == "China"].sort_values("year")
    
    fig = go.Figure()
    
    # Add era shading
    for era_name, era_config in ERAS.items():
        opacity = 0.3 if era_name == selected_era else 0.1
        fig.add_vrect(
            x0=era_config["start"], x1=era_config["end"],
            fillcolor=era_config["color"],
            opacity=opacity,
            layer="below",
            line_width=0,
            annotation_text=era_config["title"] if era_name == selected_era else "",
            annotation_position="top left",
            annotation_font_size=12
        )
    
    # Add comparison countries first (so they appear behind China)
    if compare_countries:
        for country in compare_countries:
            if country != "China":
                country_data = imports[imports["country"] == country].sort_values("year")
                if len(country_data) > 0:
                    fig.add_trace(go.Scatter(
                        x=country_data["year"],
                        y=country_data["share_pct"],
                        mode="lines",
                        name=country,
                        line=dict(width=1.5),
                        opacity=0.5,
                        hovertemplate=f"<b>{country}</b><br>%{{x}}: %{{y:.1f}}%<extra></extra>"
                    ))
    
    # Add China line last (on top, prominent)
    fig.add_trace(go.Scatter(
        x=china_data["year"],
        y=china_data["share_pct"],
        mode="lines+markers",
        name="China",
        line=dict(color="#dc2626", width=3),
        marker=dict(size=6),
        hovertemplate="<b>China</b><br>%{x}: %{y:.1f}%<extra></extra>"
    ))
    
    # Add key event markers
    events = [
        (2001, "WTO Entry"),
        (2008, "Financial Crisis"),
        (2018, "Trade War"),
        (2020, "COVID-19"),
        (2023, "Mexico #1")
    ]
    
    for year, label in events:
        share = get_china_share(imports, year)
        fig.add_annotation(
            x=year, y=share + 1.5,
            text=label,
            showarrow=True,
            arrowhead=2,
            arrowsize=0.5,
            arrowwidth=1,
            ax=0, ay=-30,
            font=dict(size=10)
        )
    
    # Show legend only if there are comparison countries
    show_legend = compare_countries and len([c for c in compare_countries if c != "China"]) > 0
    
    fig.update_layout(
        title="China's Import Share: The Rise and Shift",
        xaxis_title="Year",
        yaxis_title="Share of US Imports (%)",
        hovermode="x unified",
        showlegend=show_legend,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        height=400,
        margin=dict(t=60, b=40)
    )
    
    fig.update_yaxes(range=[0, 25])
    
    return fig


def create_era_composition_chart(df: pd.DataFrame, era_config: dict, top_n: int = 8) -> go.Figure:
    """Create stacked area chart for era composition."""
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
    
    # Custom color sequence emphasizing China
    colors = px.colors.qualitative.Set2
    
    fig = px.area(
        grouped,
        x="year",
        y="share_pct",
        color="country_group",
        title=f"Import Composition: {era_config['start']}-{era_config['end']}",
        color_discrete_sequence=colors
    )
    
    fig.update_layout(
        xaxis_title="Year",
        yaxis_title="Share of Total Imports (%)",
        legend_title="Country",
        height=400,
        margin=dict(t=60, b=40)
    )
    
    return fig


def create_winners_losers_chart(df: pd.DataFrame, era_config: dict, top_n: int = 10) -> tuple:
    """Create charts showing winners and losers in share change."""
    imports = df[df["trade_type"] == "import"]
    
    start_data = imports[imports["year"] == era_config["start"]][["country", "share_pct"]]
    end_data = imports[imports["year"] == era_config["end"]][["country", "share_pct"]]
    
    comparison = start_data.merge(
        end_data, on="country", suffixes=("_start", "_end"), how="outer"
    ).fillna(0)
    
    comparison["share_change"] = comparison["share_pct_end"] - comparison["share_pct_start"]
    
    # Winners
    winners = comparison.nlargest(top_n, "share_change")
    fig_winners = go.Figure(go.Bar(
        x=winners["share_change"],
        y=winners["country"],
        orientation="h",
        marker_color="#10b981",
        text=winners["share_change"].apply(lambda x: f"+{x:.1f}pp"),
        textposition="outside"
    ))
    fig_winners.update_layout(
        title="Gained Share",
        xaxis_title="Share Change (pp)",
        yaxis=dict(autorange="reversed"),
        height=350,
        margin=dict(l=100, r=60, t=40, b=40)
    )
    
    # Losers
    losers = comparison.nsmallest(top_n, "share_change")
    fig_losers = go.Figure(go.Bar(
        x=losers["share_change"],
        y=losers["country"],
        orientation="h",
        marker_color="#dc2626",
        text=losers["share_change"].apply(lambda x: f"{x:.1f}pp"),
        textposition="outside"
    ))
    fig_losers.update_layout(
        title="Lost Share",
        xaxis_title="Share Change (pp)",
        yaxis=dict(autorange="reversed"),
        height=350,
        margin=dict(l=100, r=60, t=40, b=40)
    )
    
    return fig_winners, fig_losers


def create_beneficiary_spotlight(df: pd.DataFrame, countries: list) -> go.Figure:
    """Create chart highlighting beneficiary countries during Trade War era."""
    imports = df[df["trade_type"] == "import"]
    spotlight = imports[imports["country"].isin(countries)].copy()
    
    fig = px.line(
        spotlight,
        x="year",
        y="share_pct",
        color="country",
        title="Emerging Beneficiaries: Who Gained from the Shift?",
        markers=True
    )
    
    # Add Trade War shading
    fig.add_vrect(
        x0=2018, x1=2024,
        fillcolor="#10b981",
        opacity=0.1,
        layer="below",
        line_width=0
    )
    
    fig.update_layout(
        xaxis_title="Year",
        yaxis_title="Share of US Imports (%)",
        legend_title="Country",
        height=400,
        hovermode="x unified"
    )
    
    return fig


def create_era_comparison_chart(df: pd.DataFrame) -> go.Figure:
    """Create bar chart comparing China's share across eras."""
    imports = df[df["trade_type"] == "import"]
    
    era_data = []
    for era_name, config in ERAS.items():
        start_share = get_china_share(imports, config["start"])
        end_share = get_china_share(imports, config["end"])
        era_data.append({
            "era": era_name.split("(")[0].strip(),
            "start": start_share,
            "end": end_share,
            "color": config["color"]
        })
    
    df_eras = pd.DataFrame(era_data)
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        name="Era Start",
        x=df_eras["era"],
        y=df_eras["start"],
        marker_color="#94a3b8",
        text=df_eras["start"].apply(lambda x: f"{x:.1f}%"),
        textposition="outside"
    ))
    
    fig.add_trace(go.Bar(
        name="Era End",
        x=df_eras["era"],
        y=df_eras["end"],
        marker_color=df_eras["color"],
        text=df_eras["end"].apply(lambda x: f"{x:.1f}%"),
        textposition="outside"
    ))
    
    fig.update_layout(
        title="China's Share: Start vs End of Each Era",
        xaxis_title="Era",
        yaxis_title="Share of US Imports (%)",
        barmode="group",
        height=350,
        legend=dict(orientation="h", yanchor="bottom", y=1.02)
    )
    
    return fig


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
    
    # Compare countries
    st.sidebar.markdown("---")
    compare_countries = st.sidebar.multiselect(
        "Compare Countries",
        FOCUS_COUNTRIES,
        default=["China", "Mexico", "Vietnam"]
    )
    
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
    
    # Main China Arc Chart (with comparison countries)
    st.subheader("The Full Arc")
    fig_arc = create_china_arc_chart(df, selected_era, compare_countries)
    st.plotly_chart(fig_arc, use_container_width=True)
    
    # Era Deep Dive
    st.markdown("---")
    st.subheader(f"Era Deep Dive: {selected_era}")
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig_composition = create_era_composition_chart(df, era_config)
        st.plotly_chart(fig_composition, use_container_width=True)
    
    with col2:
        fig_comparison = create_era_comparison_chart(df)
        st.plotly_chart(fig_comparison, use_container_width=True)
    
    # Winners and Losers
    st.markdown("---")
    st.subheader(f"Winners & Losers: {era_config['start']} → {era_config['end']}")
    
    col1, col2 = st.columns(2)
    fig_winners, fig_losers = create_winners_losers_chart(df, era_config)
    
    with col1:
        st.plotly_chart(fig_winners, use_container_width=True)
    
    with col2:
        st.plotly_chart(fig_losers, use_container_width=True)
    
    # Beneficiary Spotlight (only for Trade War era)
    if selected_era == "Trade War Era (2018-Present)":
        st.markdown("---")
        st.subheader("Beneficiary Spotlight: The China+1 Winners")
        
        spotlight_countries = ["Vietnam", "Mexico", "India", "Taiwan", "Thailand"]
        fig_spotlight = create_beneficiary_spotlight(df, spotlight_countries)
        st.plotly_chart(fig_spotlight, use_container_width=True)
        
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
