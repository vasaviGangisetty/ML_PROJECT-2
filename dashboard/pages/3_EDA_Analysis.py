import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

# --- 1. PREMIUM DARK UI STYLING ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    
    .stApp { 
        background-color: #090d16; 
        font-family: 'Inter', sans-serif; 
        color: #e5e7eb; 
    }
    
    /* Elegant Glowing Title Headers */
    .header-text { 
        font-size: 2.4rem; 
        font-weight: 800; 
        background: linear-gradient(135deg, #ffffff 30%, #a5b4fc 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 4px; 
    }
    .sub-text { 
        color: #9ca3af; 
        font-size: 1rem; 
        margin-bottom: 25px; 
    }

    /* Custom Glassmorphic Premium Card */
    .premium-card {
        background: rgba(17, 24, 39, 0.7);
        padding: 24px;
        border-radius: 14px;
        border: 1px solid rgba(255, 255, 255, 0.06);
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
        margin-bottom: 24px;
    }

    /* Custom KPI Cards */
    .kpi-wrapper {
        background: #111827;
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        padding: 16px 20px;
        text-align: left;
    }
    .kpi-lbl {
        color: #9ca3af;
        font-size: 11px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.75px;
        margin: 0;
    }
    .kpi-val {
        color: #34d399;
        font-size: 24px;
        font-weight: 700;
        margin-top: 4px;
        margin-bottom: 0;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. HEADER ---
st.markdown('<h1 class="header-text">📊 Analytical Explorations</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-text">Interactive telemetry exploring revenue, categorical share, and seasonal trends.</p>', unsafe_allow_html=True)

# --- 3. SESSION STATE CHECK ---
if 'processed_data' not in st.session_state or st.session_state['processed_data'] is None:
    st.error("⚠️ Preprocessing incomplete. Please run and compile the Feature Engineering step before proceeding.")
    st.stop()

df = st.session_state['processed_data'].copy()

# --- 4. ROBUST AUTO-MAPPING CONFIGURATION ---
# Auto-detect matches to guarantee operation without hardcoding strict names
def auto_detect(columns, choices):
    for choice in choices:
        for col in columns:
            if col.lower() == choice.lower():
                return col
    return columns[0] if len(columns) > 0 else None

st.sidebar.markdown("### 🔍 Analytical Model Columns")
rev_col = st.sidebar.selectbox("Revenue Field", df.columns, index=df.columns.get_loc(auto_detect(df.columns, ['revenue', 'sales_amount', 'amount', 'turnover'])) if auto_detect(df.columns, ['revenue', 'sales_amount', 'amount', 'turnover']) in df.columns else 0)
sales_col = st.sidebar.selectbox("Units Sold Field", df.columns, index=df.columns.get_loc(auto_detect(df.columns, ['sales', 'volume', 'quantity', 'units_sold'])) if auto_detect(df.columns, ['sales', 'volume', 'quantity', 'units_sold']) in df.columns else 0)
prod_col = st.sidebar.selectbox("Product Categoric Field", df.columns, index=df.columns.get_loc(auto_detect(df.columns, ['product', 'item', 'category'])) if auto_detect(df.columns, ['product', 'item', 'category']) in df.columns else 0)
reg_col = st.sidebar.selectbox("Geographic Region Field", df.columns, index=df.columns.get_loc(auto_detect(df.columns, ['region', 'territory', 'location', 'country'])) if auto_detect(df.columns, ['region', 'territory', 'location', 'country']) in df.columns else 0)

# Optional dynamic fallback mappings if standard seasonal features are missing
date_parsed_col = "Date_Parsed" if "Date_Parsed" in df.columns else auto_detect(df.columns, ['date', 'timestamp'])
month_name_col = "Month_Name" if "Month_Name" in df.columns else None
season_col = "Season" if "Season" in df.columns else None
festival_col = "Is_Festival" if "Is_Festival" in df.columns else None

# Safe type casting to prevent charts from failing
df[rev_col] = pd.to_numeric(df[rev_col], errors='coerce').fillna(0)
df[sales_col] = pd.to_numeric(df[sales_col], errors='coerce').fillna(0)

# --- 5. TOP-LEVEL KPI METRICS ---
m1, m2, m3, m4 = st.columns(4)

with m1:
    st.markdown(f"""
        <div class="kpi-wrapper">
            <p class="kpi-lbl">Gross Revenue</p>
            <p class="kpi-val">${df[rev_col].sum():,.2f}</p>
        </div>
    """, unsafe_allow_html=True)
with m2:
    st.markdown(f"""
        <div class="kpi-wrapper">
            <p class="kpi-lbl">Total Units Sold</p>
            <p class="kpi-val">{df[sales_col].sum():,.0f}</p>
        </div>
    """, unsafe_allow_html=True)
with m3:
    st.markdown(f"""
        <div class="kpi-wrapper">
            <p class="kpi-lbl">Avg. Order Value</p>
            <p class="kpi-val">${df[rev_col].mean():,.2f}</p>
        </div>
    """, unsafe_allow_html=True)
with m4:
    # Determine Peak Month safely
    if month_name_col in df.columns:
        peak_m = df.groupby(month_name_col)[rev_col].sum().idxmax()
    else:
        peak_m = "N/A"
    st.markdown(f"""
        <div class="kpi-wrapper">
            <p class="kpi-lbl">Peak Sales Month</p>
            <p class="kpi-val" style="color: #60a5fa;">{peak_m}</p>
        </div>
    """, unsafe_allow_html=True)

st.write("###")

# --- 6. REVENUE TRENDING (TIME-SERIES AREA CHART) ---
st.markdown('<div class="premium-card">', unsafe_allow_html=True)
st.subheader("📈 Revenue Performance & Temporal Trends")

granularity = st.segmented_control("Select View Granularity:", ["Daily", "Monthly"], default="Monthly")

if granularity == "Monthly" and month_name_col in df.columns:
    # Safely sort months chronologically instead of alphabetically
    if "Month" in df.columns:
        trend_df = df.groupby(['Month', month_name_col])[rev_col].sum().reset_index().sort_values('Month')
    else:
        trend_df = df.groupby(month_name_col)[rev_col].sum().reindex(
            ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        ).reset_index()
    x_axis = month_name_col
else:
    trend_df = df.groupby(date_parsed_col)[rev_col].sum().reset_index() if date_parsed_col in df.columns else df.reset_index()
    x_axis = date_parsed_col if date_parsed_col in df.columns else df.index

fig_revenue = px.area(trend_df, x=x_axis, y=rev_col, 
                      labels={rev_col: "Revenue ($)", x_axis: "Timeline"},
                      line_shape="spline", 
                      color_discrete_sequence=['#6366f1'])

fig_revenue.update_traces(fillcolor="rgba(99, 102, 241, 0.12)")
fig_revenue.update_layout(
    paper_bgcolor="rgba(0,0,0,0)", 
    plot_bgcolor="rgba(0,0,0,0)", 
    font_color="#9ca3af",
    margin=dict(l=10, r=10, t=30, b=10),
    xaxis=dict(showgrid=False, color="#4b5563"), 
    yaxis=dict(gridcolor="rgba(255, 255, 255, 0.05)", color="#4b5563")
)
st.plotly_chart(fig_revenue, use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)

# --- 7. PRODUCT SEGREGATION & REGIONAL SALES DISTRIBUTION ---
col_left, col_right = st.columns(2)

with col_left:
    st.markdown('<div class="premium-card">', unsafe_allow_html=True)
    st.subheader("📦 Revenue Contribution by Product")
    if prod_col in df.columns:
        fig_prod = px.pie(df, names=prod_col, values=rev_col, hole=0.55,
                          color_discrete_sequence=px.colors.sequential.YlOrRd_r)
        fig_prod.update_traces(textposition='inside', textinfo='percent+label')
        fig_prod.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", 
            font_color="#e5e7eb",
            legend=dict(orientation="h", y=-0.1, x=0.5, xanchor="center"),
            margin=dict(l=10, r=10, t=10, b=10)
        )
        st.plotly_chart(fig_prod, use_container_width=True)
    else:
        st.info("Product column not found. Map field in sidebar config.")
    st.markdown('</div>', unsafe_allow_html=True)

with col_right:
    st.markdown('<div class="premium-card">', unsafe_allow_html=True)
    st.subheader("🌎 Sales Volume by Region")
    if reg_col in df.columns:
        region_sales = df.groupby(reg_col)[sales_col].sum().sort_values(ascending=True).reset_index()
        fig_region = px.bar(region_sales, x=sales_col, y=reg_col, orientation='h',
                            labels={sales_col: "Sales Volume (Units)", reg_col: "Region"},
                            color=sales_col, color_continuous_scale="Darkmint")
        fig_region.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", 
            plot_bgcolor="rgba(0,0,0,0)", 
            coloraxis_showscale=False,
            font_color="#e5e7eb",
            margin=dict(l=10, r=10, t=10, b=10),
            xaxis=dict(showgrid=False, color="#4b5563"),
            yaxis=dict(color="#4b5563")
        )
        st.plotly_chart(fig_region, use_container_width=True)
    else:
        st.info("Region column not found. Map field in sidebar config.")
    st.markdown('</div>', unsafe_allow_html=True)

# --- 8. SEASONAL DISTRIBUTION (BOX PLOT) ---
st.markdown('<div class="premium-card">', unsafe_allow_html=True)
st.subheader("🌦️ Seasonal Sales Volatility & Festival Analysis")

if season_col in df.columns and festival_col in df.columns:
    df_box_input = df.copy()
    df_box_input[festival_col] = df_box_input[festival_col].map({0: "Normal Days", 1: "Festival Season"})
    
    fig_box = px.box(df_box_input, x=season_col, y=sales_col, color=festival_col,
                     labels={sales_col: "Sales (Units)", season_col: "Season", festival_col: "Period Status"},
                     points="outliers", notched=True,
                     color_discrete_map={"Normal Days": "#6b7280", "Festival Season": "#10b981"})
    
    fig_box.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", 
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#e5e7eb",
        legend=dict(orientation="h", y=1.05, x=0.5, xanchor="center"),
        margin=dict(l=10, r=10, t=40, b=10),
        xaxis=dict(showgrid=False, color="#4b5563"),
        yaxis=dict(gridcolor="rgba(255, 255, 255, 0.05)", color="#4b5563")
    )
    st.plotly_chart(fig_box, use_container_width=True)
else:
    st.info("Season or Festival flags not found. Enable Weekend/Seasonal processing in Preprocessing tab.")
st.markdown('</div>', unsafe_allow_html=True)

# --- 9. GRANULAR PIVOT MATRIX ---
st.markdown('<div class="premium-card">', unsafe_allow_html=True)
st.subheader("📑 Sales Breakdown Matrix")
st.markdown('<p style="color: #9ca3af; font-size: 0.9rem; margin-top:-10px; margin-bottom:15px;">Dense crosstab of aggregate items sold and generated gross sales volume.</p>', unsafe_allow_html=True)

if reg_col in df.columns and prod_col in df.columns:
    pivot_df = df.groupby([reg_col, prod_col]).agg({
        sales_col: 'sum',
        rev_col: 'sum'
    }).rename(columns={sales_col: "Total Volume", rev_col: "Total Revenue"}).reset_index()

    # Style table with premium pandas formatting 
    styled_pivot = (
        pivot_df.style
        .format({"Total Volume": "{:,.0f}", "Total Revenue": "${:,.2f}"})
        .background_gradient(subset=["Total Revenue"], cmap="Purples")
    )
    st.dataframe(styled_pivot, use_container_width=True)
else:
    st.info("Product or Region dimensions absent. Matrix calculations paused.")
st.markdown('</div>', unsafe_allow_html=True)