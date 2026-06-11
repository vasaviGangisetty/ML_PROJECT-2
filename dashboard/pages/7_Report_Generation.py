import streamlit as st
import pandas as pd
import numpy as np
import datetime
import os
import plotly.graph_objects as go
import plotly.express as px
from pathlib import Path

# ==========================================
# 1. PREMIUM BRANDING SYSTEM & CSS
# ==========================================
st.set_page_config(page_title="Nexus AI | Executive Reporter", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap');
    
    .stApp { 
        background-color: #030308; 
        font-family: 'Plus Jakarta Sans', sans-serif; 
        color: #f3f4f6; 
    }
    
    /* Live Pulsing Operational Indicator */
    .pulse-indicator {
        display: inline-block;
        width: 8px;
        height: 8px;
        background-color: var(--theme-color, #6366f1);
        border-radius: 50%;
        margin-right: 8px;
        box-shadow: 0 0 0 0 rgba(99, 102, 241, 0.7);
        animation: pulse 1.6s infinite;
        vertical-align: middle;
    }
    @keyframes pulse {
        0% {
            transform: scale(0.95);
            box-shadow: 0 0 0 0 rgba(99, 102, 241, 0.7);
        }
        70% {
            transform: scale(1);
            box-shadow: 0 0 0 6px rgba(99, 102, 241, 0);
        }
        100% {
            transform: scale(0.95);
            box-shadow: 0 0 0 0 rgba(99, 102, 241, 0);
        }
    }

    /* Style Specific Native Containers Safely via Stable Keys */
    .st-key-config-panel, .st-key-preview-panel {
        background: radial-gradient(100% 100% at 0% 0%, rgba(15, 23, 42, 0.75) 0%, rgba(15, 23, 42, 0.3) 100%) !important;
        backdrop-filter: blur(16px) !important;
        -webkit-backdrop-filter: blur(16px) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 16px !important;
        padding: 24px !important;
        box-shadow: 0 15px 35px rgba(0, 0, 0, 0.4) !important;
        position: relative !important;
        overflow: hidden !important;
    }
    
    /* Gradient Panel Top Borders */
    .st-key-config-panel::before, .st-key-preview-panel::before {
        content: "" !important;
        position: absolute !important;
        top: 0 !important;
        left: 0 !important;
        right: 0 !important;
        height: 3px !important;
        background: var(--gradient-theme, linear-gradient(90deg, #6366f1, #38bdf8)) !important;
        z-index: 10 !important;
    }

    /* Keep Panel Heights Uniform & Spacious for Charts */
    .st-key-config-panel, .st-key-preview-panel {
        min-height: 850px !important;
    }

    /* Elegant document-sheet preview inside the dark layout */
    .document-sheet {
        background-color: #060810;
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 35px;
        color: #e2e8f0;
        box-shadow: inset 0 0 30px rgba(0,0,0,0.7);
        max-height: 730px;
        overflow-y: auto;
    }
    
    .doc-meta {
        font-size: 11px;
        font-family: 'JetBrains Mono', monospace;
        color: #64748b;
        text-transform: uppercase;
        border-bottom: 1px solid rgba(255, 255, 255, 0.08);
        padding-bottom: 8px;
        margin-bottom: 18px;
    }
    
    .doc-section-header {
        font-size: 12px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.6px;
        color: var(--theme-color, #38bdf8);
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        padding-bottom: 4px;
        margin-top: 24px;
        margin-bottom: 12px;
    }
    
    .kpi-container {
        display: flex;
        gap: 12px;
        margin-top: 14px;
        margin-bottom: 14px;
    }
    
    .doc-mini-kpi {
        flex: 1;
        background: rgba(255, 255, 255, 0.02);
        border: 1px solid rgba(255, 255, 255, 0.04);
        border-radius: 6px;
        padding: 10px;
        text-align: center;
    }
    
    .doc-mini-lbl {
        font-size: 9px;
        color: #94a3b8;
        text-transform: uppercase;
        margin: 0;
    }
    
    .doc-mini-val {
        font-size: 16px;
        font-weight: 700;
        color: #f8fafc;
        margin: 2px 0 0 0;
    }
    
    /* Document download visual card */
    .download-card {
        background: rgba(255, 255, 255, 0.02);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 8px;
        padding: 14px;
        margin-bottom: 12px;
        transition: border-color 0.2s ease;
    }
    .download-card:hover {
        border-color: var(--theme-color);
    }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. DYNAMIC THEME ENGINE & HIGHLIGHTS
# ==========================================
st.sidebar.markdown("### 🎨 Brand Customization")
theme_selection = st.sidebar.selectbox(
    "Report Highlight Theme",
    options=["Classic Indigo", "Emerald Mint", "Royal Amethyst", "Cyberpunk Amber"]
)

# Theme Mapping configurations
theme_mapping = {
    "Classic Indigo": {
        "color": "#6366f1", 
        "grad": "linear-gradient(90deg, #6366f1, #38bdf8)",
        "scale": ["#1e1b4b", "#312e81", "#3730a3", "#4f46e5", "#6366f1", "#818cf8", "#a5b4fc"]
    },
    "Emerald Mint": {
        "color": "#10b981", 
        "grad": "linear-gradient(90deg, #10b981, #34d399)",
        "scale": ["#022c22", "#064e3b", "#0f766e", "#14b8a6", "#10b981", "#34d399", "#6ee7b7"]
    },
    "Royal Amethyst": {
        "color": "#8b5cf6", 
        "grad": "linear-gradient(90deg, #8b5cf6, #bc8cff)",
        "scale": ["#2e1065", "#4c1d95", "#5b21b6", "#6d28d9", "#7c3aed", "#8b5cf6", "#a78bfa"]
    },
    "Cyberpunk Amber": {
        "color": "#f59e0b", 
        "grad": "linear-gradient(90deg, #f59e0b, #fbbf24)",
        "scale": ["#451a03", "#78350f", "#92400e", "#b45309", "#d97706", "#f59e0b", "#fcd34d"]
    }
}

theme_color = theme_mapping[theme_selection]["color"]
theme_grad = theme_mapping[theme_selection]["grad"]
theme_scale = theme_mapping[theme_selection]["scale"]

# Inject styling variables dynamically into DOM
st.markdown(f"""
    <style>
    :root {{
        --theme-color: {theme_color};
        --gradient-theme: {theme_grad};
    }}
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 3. HEADER
# ==========================================
col_head_l, col_head_r = st.columns([3, 1])
with col_head_l:
    st.markdown('<h1 style="font-weight: 800; font-size: 2.3rem; letter-spacing:-1px; margin-bottom: 4px;">📄 Executive Report Compiler</h1>', unsafe_allow_html=True)
    st.markdown('<p style="color: #94a3b8; font-size: 1.0rem; margin-bottom: 25px;">Consolidate raw metrics and forecasts into styled, sign-off-ready briefs.</p>', unsafe_allow_html=True)
with col_head_r:
    st.markdown('<div style="text-align: right; padding-top: 15px;">', unsafe_allow_html=True)
    st.markdown(f'<span class="pulse-indicator"></span><span style="font-size: 12px; font-weight: 600; color: {theme_color}; text-transform: uppercase; letter-spacing: 1px;">Live Compiling</span>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# 4. DATA RESOLUTION & FALLBACK TELEMETRY
# ==========================================
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed_data"

df = None

def generate_mock_data():
    np.random.seed(42)
    dates = pd.date_range(start="2026-01-01", periods=60)
    products = ["Alpha SKU-100", "Beta SKU-200", "Gamma SKU-300", "Delta SKU-400", "Epsilon SKU-500"]
    data = []
    for prod in products:
        base_demand = np.random.randint(40, 90)
        for dt in dates:
            sales = max(0, int(base_demand + np.random.normal(0, 8)))
            revenue = sales * np.random.randint(20, 45)
            data.append({
                "Date_Parsed": dt,
                "Product": prod,
                "Sales": sales,
                "Revenue": revenue,
                "Region": np.random.choice(["North Zone", "South Zone", "East Zone", "West Zone"]),
                "Anomaly": 1 if np.random.rand() > 0.96 else 0
            })
    return pd.DataFrame(data)

# Resolve data from memory, then try disk, then fall back to mock
if "processed_data" in st.session_state and st.session_state["processed_data"] is not None:
    df = st.session_state["processed_data"].copy()
else:
    if PROCESSED_DATA_DIR.exists():
        processed_files = [f for f in os.listdir(PROCESSED_DATA_DIR) if f.endswith('.csv')]
        if processed_files:
            try:
                df = pd.read_csv(PROCESSED_DATA_DIR / processed_files[0])
                st.session_state["processed_data"] = df
                st.toast("Active dataset loaded.", icon="📊")
            except: pass

if df is None:
    df = generate_mock_data()
    st.info("💡 Running compiler in telemetry simulation mode. Run pre-processing inside preceding tabs to sync standard variables.")

# ==========================================
# 5. DYNAMIC FIELD SEGREGATION
# ==========================================
def auto_detect_col(columns, keywords):
    for key in keywords:
        for col in columns:
            if col.lower() == key.lower():
                return col
    return None

date_col = auto_detect_col(df.columns, ['date_parsed', 'date', 'timestamp'])
rev_col = auto_detect_col(df.columns, ['revenue', 'sales_amount', 'amount', 'turnover'])
sales_col = auto_detect_col(df.columns, ['sales', 'volume', 'quantity', 'units_sold'])
reg_col = auto_detect_col(df.columns, ['region', 'territory', 'location', 'country'])
prod_col = auto_detect_col(df.columns, ['product', 'item', 'category'])

# Robust standard fallbacks
if not rev_col:
    rev_col = df.select_dtypes(include=[np.number]).columns[0]
if not sales_col:
    sales_col = df.select_dtypes(include=[np.number]).columns[1] if len(df.select_dtypes(include=[np.number]).columns) > 1 else rev_col

# Format configurations
df[rev_col] = pd.to_numeric(df[rev_col], errors='coerce').fillna(0)
df[sales_col] = pd.to_numeric(df[sales_col], errors='coerce').fillna(0)

# Base Calculations
total_rev = df[rev_col].sum()
total_sales = df[sales_col].sum()
anomaly_count = df["Anomaly"].sum() if "Anomaly" in df.columns else 0

# ==========================================
# 6. CONFIGURATION SIDEBAR: DYNAMIC PRESETS
# ==========================================
st.sidebar.markdown("### 📋 Executive Templates")
report_preset = st.sidebar.selectbox(
    "Select Report Configuration",
    options=["Financial Summary Report", "Operational Stock & Audit", "Statistical Deviation Analysis"]
)

# Map templates to pre-populated values
presets = {
    "Financial Summary Report": {
        "title": "Quarterly Financial Performance Brief",
        "brief": "Consolidated financial performance reflects healthy conversion margins and robust revenue pathways. Operating metrics exceed baseline benchmarks with positive demand signals across key regional zones. Volume and revenue indices remain closely aligned with strategic corporate parameters.",
        "line": True, "bar": True, "anom": False, "matrix": True
    },
    "Operational Stock & Audit": {
        "title": "Supply Chain & Stock Replenishment Audit",
        "brief": "Inventory optimization assessments indicate balanced product flow rates. Statistical reorder limits successfully buffered temporal demand spikes during peak windows. No major out-of-stock events were flagged across core warehousing regions.",
        "line": False, "bar": True, "anom": True, "matrix": True
    },
    "Statistical Deviation Analysis": {
        "title": "Operational Volatility & Anomaly Log",
        "brief": "Deep-dives into transactional data highlight minimal high-volatility events. Statistical regression and validation checking mapped several brief demand variations. All outlier signals are classified as controlled occurrences and are detailed below.",
        "line": True, "bar": False, "anom": True, "matrix": False
    }
}

active_preset = presets[report_preset]

st.sidebar.markdown("---")
st.sidebar.markdown("### 🎛️ Customize Content")
report_title = st.sidebar.text_input("Report Header Title", value=active_preset["title"])
author_name = st.sidebar.text_input("Author Profile Designation", value="Director of Operations")
include_briefing = st.sidebar.checkbox("Include Executive Narrative", value=True)
include_line_chart = st.sidebar.checkbox("Include Sales Trendline Graph", value=active_preset["line"])
include_bar_chart = st.sidebar.checkbox("Include SKU Volume Distribution", value=active_preset["bar"])
include_anomalies = st.sidebar.checkbox("Include Safety Threshold Alerts", value=active_preset["anom"])
include_matrix = st.sidebar.checkbox("Include Geographic Matrix Grid", value=active_preset["matrix"])

# ==========================================
# 7. EXECUTOR WORKSPACE & PREVIEW SPLIT
# ==========================================
col_ctrl, col_prev = st.columns([1, 1.25])

with col_ctrl:
    with st.container(key="config-panel"):
        st.subheader("📝 Briefing Composition")
        st.markdown('<p style="color: #94a3b8; font-size: 0.9rem; margin-top:-5px; margin-bottom:15px;">Annotate the generated graphics with tactical business annotations.</p>', unsafe_allow_html=True)
        
        briefing_text = st.text_area(
            "Narrative Summary Notes",
            value=active_preset["brief"],
            height=200,
            help="Your written briefings will propagate dynamically to the preview sheets on the right."
        )
        
        st.write("###")
        st.subheader("💾 Multi-Format Report Exporters")
        
        # Format 1: Self-Contained Print-Ready HTML Export Code
        # This provides a clean light theme output (standard for physical/PDF printing) with inline CSS
        date_str = datetime.date.today().strftime('%B %d, %Y')
        html_report_payload = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{report_title}</title>
    <style>
        body {{ font-family: 'Helvetica Neue', Arial, sans-serif; color: #1e293b; background: #ffffff; padding: 45px; line-height: 1.6; max-width: 850px; margin: 0 auto; }}
        h1 {{ font-size: 26px; font-weight: 800; color: #0f172a; margin-bottom: 5px; }}
        .meta {{ font-size: 12px; color: #64748b; border-bottom: 2px solid #e2e8f0; padding-bottom: 15px; margin-bottom: 30px; }}
        .section-header {{ font-size: 14px; font-weight: 700; text-transform: uppercase; color: {theme_color}; border-bottom: 1px solid #e2e8f0; padding-bottom: 5px; margin-top: 35px; margin-bottom: 15px; }}
        .kpi-row {{ display: flex; gap: 15px; margin-top: 20px; margin-bottom: 20px; }}
        .kpi-card {{ flex: 1; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 15px; text-align: center; }}
        .kpi-lbl {{ font-size: 10px; color: #64748b; text-transform: uppercase; margin: 0; }}
        .kpi-val {{ font-size: 20px; font-weight: 700; color: #0f172a; margin: 5px 0 0 0; }}
        p {{ font-size: 13px; color: #334155; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
        th {{ background: #f1f5f9; text-align: left; padding: 8px; font-size: 11px; text-transform: uppercase; color: #475569; border: 1px solid #cbd5e1; }}
        td {{ padding: 8px; font-size: 12px; border: 1px solid #cbd5e1; color: #334155; }}
        @media print {{
            body {{ padding: 20px; }}
            .kpi-card {{ border: 1px solid #94a3b8; }}
        }}
    </style>
</head>
<body>
    <h1>{report_title}</h1>
    <div class="meta">Compiled on {date_str} | Author: {author_name} | Generated via Nexus AI</div>
    
    <div class="section-header">1. Executive Narrative & Assessment</div>
    <p>{briefing_text}</p>
    
    <div class="section-header">2. Strategic KPI Benchmarks</div>
    <div class="kpi-row">
        <div class="kpi-card">
            <p class="kpi-lbl">Volume Dispatched</p>
            <p class="kpi-val">{total_sales:,.0f}</p>
        </div>
        <div class="kpi-card">
            <p class="kpi-lbl">Net Revenue</p>
            <p class="kpi-val">${total_rev:,.2f}</p>
        </div>
        <div class="kpi-card">
            <p class="kpi-lbl">Avg Basket Yield</p>
            <p class="kpi-val">${(total_rev / total_sales if total_sales > 0 else 0):,.2f}</p>
        </div>
    </div>
</body>
</html>
"""

        # Format 2: Standard Markdown Document
        markdown_payload = f"""# {report_title}
**Date:** {date_str}  
**Author Profile:** {author_name}  

## 1. Executive Narrative & Assessment
{briefing_text}

## 2. High-Level Performance Metrics
- **Cumulative Volume:** {total_sales:,.0f} units
- **Consolidated Net Turnover:** ${total_rev:,.2f}
- **Average Basket Unit Yield:** ${(total_rev / total_sales if total_sales > 0 else 0):,.2f}
"""

        # Rendering Export Cards
        st.markdown('<div class="download-card">', unsafe_allow_html=True)
        st.markdown(f"##### 🌐 Standard Print-Ready HTML Report")
        st.caption("Perfect layout optimized for light-theme browsers and saving cleanly to physical PDF documents via standard printing (Ctrl+P).")
        st.download_button(
            label="📄 Export Print-Ready HTML",
            data=html_report_payload,
            file_name=f"{report_title.replace(' ', '_')}_{datetime.date.today()}.html",
            mime="text/html",
            use_container_width=True
        )
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="download-card">', unsafe_allow_html=True)
        st.markdown(f"##### 📝 Markdown Brief Document")
        st.caption("A clean raw markdown blueprint formatted for quick copying into emails, Slack, or corporate slide decks.")
        st.download_button(
            label="📄 Export Markdown Document",
            data=markdown_payload,
            file_name=f"{report_title.replace(' ', '_')}_{datetime.date.today()}.md",
            mime="text/markdown",
            use_container_width=True
        )
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="download-card">', unsafe_allow_html=True)
        st.markdown(f"##### 📊 Full Structured CSV Audit Ledger")
        st.caption("The underlying tabular dataset with all compiled variables for auditing purposes.")
        csv_data = df.to_csv(index=False)
        st.download_button(
            label="💾 Export Tabular CSV Ledger",
            data=csv_data,
            file_name=f"telemetry_source_data_{datetime.date.today()}.csv",
            mime="text/csv",
            use_container_width=True
        )
        st.markdown('</div>', unsafe_allow_html=True)

# --- LIVE PAPER PREVIEWER (RIGHT PANEL) ---
with col_prev:
    with st.container(key="preview-panel"):
        st.subheader("🖥️ Document Layout Preview")
        st.markdown('<p style="color: #94a3b8; font-size: 0.9rem; margin-top:-5px; margin-bottom:15px;">Visually renders dynamically customized layouts in real time.</p>', unsafe_allow_html=True)
        
        # Open Simulated Document Sheet
        st.markdown(f"""
            <div class="document-sheet">
                <div class="doc-meta">
                    Nexus Intelligence System • Standard Executive Layout • Confidential
                </div>
                <h2 style="font-size: 18px; font-weight: 800; color: #ffffff; margin-top: 0; margin-bottom: 4px;">
                    {report_title}
                </h2>
                <div style="font-size: 11px; color: #94a3b8; margin-bottom: 20px;">
                    <b>Compiled:</b> {datetime.date.today().strftime('%Y-%m-%d')} &nbsp;|&nbsp; <b>Author:</b> {author_name}
                </div>
        """, unsafe_allow_html=True)

        # Briefing segment
        if include_briefing:
            st.markdown(f"""
                <div class="doc-section-header">1. Strategic Briefing & Context</div>
                <p style="font-size: 11.5px; color: #cbd5e1; line-height: 1.6; margin: 0; padding-bottom: 10px;">
                    {briefing_text}
                </p>
            """, unsafe_allow_html=True)

        # KPIs Inline summaries
        st.markdown(f"""
            <div class="doc-section-header">2. High-Level Performance Benchmarks</div>
            <div class="kpi-container">
                <div class="doc-mini-kpi">
                    <p class="doc-mini-lbl">Volume Dispatched</p>
                    <p class="doc-mini-val">{total_sales:,.0f}</p>
                </div>
                <div class="doc-mini-kpi">
                    <p class="doc-mini-lbl">Net Revenue</p>
                    <p class="doc-mini-val">${total_rev:,.2f}</p>
                </div>
                <div class="doc-mini-kpi">
                    <p class="doc-mini-lbl">Avg Basket Yield</p>
                    <p class="doc-mini-val">${(total_rev / total_sales if total_sales > 0 else 0):,.2f}</p>
                </div>
            </div>
        """, unsafe_allow_html=True)

        # Chronological Revenue Line Chart
        if include_line_chart:
            st.markdown('<div class="doc-section-header">3. Temporal Outflow Trajectory</div>', unsafe_allow_html=True)
            if date_col and date_col in df.columns:
                trend_agg = df.groupby(date_col)[rev_col].sum().reset_index()
                
                # Plotly line setup
                fig_line = go.Figure()
                fig_line.add_trace(go.Scatter(
                    x=trend_agg[date_col],
                    y=trend_agg[rev_col],
                    fill='tozeroy',
                    # Converts hex colors to RGB for transparency fill logic
                    fillcolor=f"rgba({','.join([str(int(theme_color[i:i+2], 16)) for i in (1, 3, 5)])}, 0.08)",
                    line=dict(color=theme_color, width=2.5, shape='spline'),
                    hoverinfo='skip'
                ))
                fig_line.update_layout(
                    template="plotly_dark",
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    height=130,
                    margin=dict(l=10, r=10, t=5, b=5),
                    xaxis=dict(showgrid=False, color="#4b5563", showticklabels=False),
                    yaxis=dict(gridcolor="rgba(255, 255, 255, 0.04)", showticklabels=False)
                )
                st.plotly_chart(fig_line, use_container_width=True, config={'displayModeBar': False})
            else:
                st.caption("Missing chronological metrics to map the timeline trend.")

        # Product Categorical Bar Chart
        if include_bar_chart:
            st.markdown('<div class="doc-section-header">4. SKU Allocation Breakdown</div>', unsafe_allow_html=True)
            if prod_col and prod_col in df.columns:
                prod_totals = df.groupby(prod_col)[sales_col].sum().reset_index().sort_values(sales_col, ascending=True)
                
                # Plotly Horizontal Bar
                fig_bar = go.Figure()
                fig_bar.add_trace(go.Bar(
                    y=prod_totals[prod_col],
                    x=prod_totals[sales_col],
                    orientation='h',
                    marker=dict(
                        color=prod_totals[sales_col],
                        colorscale=[[0, theme_scale[0]], [1, theme_color]],
                        line=dict(color='rgba(255, 255, 255, 0.1)', width=1)
                    )
                ))
                fig_bar.update_layout(
                    template="plotly_dark",
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    height=140,
                    margin=dict(l=10, r=10, t=5, b=5),
                    xaxis=dict(showgrid=False, color="#4b5563", showticklabels=False),
                    yaxis=dict(gridcolor="rgba(255, 255, 255, 0.04)", color="#94a3b8")
                )
                st.plotly_chart(fig_bar, use_container_width=True, config={'displayModeBar': False})
            else:
                st.caption("Missing categoric attributes to generate product distribution charts.")

        # Anomaly / Audit Log Segment
        if include_anomalies:
            anom_count = int(df['Anomaly'].sum()) if "Anomaly" in df.columns else 0
            anom_status = "STABLE STATUS" if anom_count == 0 else "DEVIATION DETECTED"
            anom_color = "#10b981" if anom_count == 0 else "#f87171"
            st.markdown(f"""
                <div class="doc-section-header">5. Volatility Limits & Anomalies</div>
                <div style="background: rgba(255, 255, 255, 0.02); border: 1px solid rgba(255, 255, 255, 0.05); border-radius: 6px; padding: 12px; font-size: 11px; color: #cbd5e1; line-height: 1.5; margin-bottom: 12px;">
                    Automated testing reports <b style="color: {anom_color};">{anom_count} anomalous deviations</b> exceeding standard safety limits during this timeline. Operational safety indices are evaluated as <b><span style="color: {anom_color};">{anom_status}</span></b>.
                </div>
            """, unsafe_allow_html=True)

        # Geographic Matrix Grid Table
        if include_matrix:
            st.markdown('<div class="doc-section-header">6. Segmented Regional Outflow Matrix</div>', unsafe_allow_html=True)
            if reg_col and reg_col in df.columns:
                regional_df = df.groupby(reg_col)[[sales_col, rev_col]].sum().reset_index()
                st.dataframe(
                    regional_df,
                    column_config={
                        reg_col: st.column_config.TextColumn("Region Segment"),
                        sales_col: st.column_config.NumberColumn("Volume Units"),
                        rev_col: st.column_config.NumberColumn("Turnover ($)")
                    },
                    hide_index=True,
                    use_container_width=True,
                    height=140
                )
            else:
                st.caption("No regional segment columns detected in standard dataframe coordinates.")

        # Close simulated document sheet safely
        st.markdown("""
            </div>
        """, unsafe_allow_html=True)