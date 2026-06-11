import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# --- CLINICAL UI CONFIG ---
st.set_page_config(page_title="Nexus AI | Inventory Lab", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0B0E14; font-family: 'Inter', sans-serif; color: #E0E0E0; }
    
    /* Clinical Card Style */
    .clinical-card {
        background: #161B22;
        padding: 24px;
        border-radius: 10px;
        border: 1px solid #30363D;
        margin-bottom: 20px;
    }
    
    /* Status Colors */
    .critical { color: #F85149; font-weight: bold; }
    .warning { color: #D29922; font-weight: bold; }
    .healthy { color: #3FB950; font-weight: bold; }
    
    /* Metric Labels */
    .label { color: #8B949E; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.05em; }
    .value { color: #58A6FF; font-size: 1.8rem; font-weight: 700; }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<h1 style="color:white; font-weight:800;">📦 Inventory Optimization Lab</h1>', unsafe_allow_html=True)
st.markdown("<p style='color:#8B949E;'>Clinical Analysis of Stock Replenishment and Safety Buffers</p>", unsafe_allow_html=True)

if "processed_data" not in st.session_state:
    st.error("🚨 Data Stream Offline: Please complete data processing first.")
    st.stop()

df = st.session_state["processed_data"]

# --- CLINICAL PARAMETERS ---
with st.sidebar:
    st.header("⚙️ Supply Parameters")
    lead_time = st.number_input("Lead Time (Days)", 1, 30, 7)
    
    # Use a Selectbox instead of a Slider to prevent the Z-Score Error
    service_level_str = st.selectbox(
        "Service Level Confidence", 
        ["90% (Standard)", "95% (High)", "99% (Clinical/Critical)"],
        index=1
    )
    
    # Mapping the selection to Z-Score
    z_mapping = {"90% (Standard)": 1.28, "95% (High)": 1.65, "99% (Clinical/Critical)": 2.33}
    Z = z_mapping[service_level_str]

# --- COMPUTATIONAL ENGINE ---
inv_analysis = df.groupby('Product').agg({
    'Sales': ['mean', 'std'],
    'Stock_Level': 'last'
}).reset_index()

inv_analysis.columns = ['Product', 'Avg_Daily_Sales', 'Sales_Std', 'Current_Stock']

# Apply Formulas
inv_analysis['Safety_Stock'] = Z * inv_analysis['Sales_Std'] * np.sqrt(lead_time)
inv_analysis['Reorder_Point'] = (inv_analysis['Avg_Daily_Sales'] * lead_time) + inv_analysis['Safety_Stock']

def get_clinical_status(row):
    if row['Current_Stock'] < (row['Reorder_Point'] * 0.4): return "🚨 CRITICAL"
    if row['Current_Stock'] <= row['Reorder_Point']: return "⚠️ REORDER"
    return "✅ HEALTHY"

inv_analysis['Status'] = inv_analysis.apply(get_clinical_status, axis=1)

# --- VISUAL DASHBOARD ---
c1, c2, c3, c4 = st.columns(4)
c1.markdown(f'<div class="clinical-card"><p class="label">Total SKUs</p><p class="value">{len(inv_analysis)}</p></div>', unsafe_allow_html=True)
c2.markdown(f'<div class="clinical-card"><p class="label">Critical Alerts</p><p class="value" style="color:#F85149;">{len(inv_analysis[inv_analysis["Status"] == "🚨 CRITICAL"])}</p></div>', unsafe_allow_html=True)
c3.markdown(f'<div class="clinical-card"><p class="label">Replenishment ROP</p><p class="value">{inv_analysis["Reorder_Point"].mean():.1f}</p></div>', unsafe_allow_html=True)
c4.markdown(f'<div class="clinical-card"><p class="label">Target Service Level</p><p class="value">{service_level_str.split()[0]}</p></div>', unsafe_allow_html=True)

# Main Grid
col_l, col_r = st.columns([0.65, 0.35])

with col_l:
    st.markdown('<div class="clinical-card">', unsafe_allow_html=True)
    st.subheader("📋 Optimization Matrix")
    
    # Styling the table for clinical appearance
    def color_status(val):
        color = '#3FB950' if 'HEALTHY' in val else ('#D29922' if 'REORDER' in val else '#F85149')
        return f'color: {color}; font-weight: bold;'

    st.dataframe(
        inv_analysis[['Product', 'Current_Stock', 'Reorder_Point', 'Safety_Stock', 'Status']]
        .style.applymap(color_status, subset=['Status'])
        .format(precision=2),
        use_container_width=True, height=400
    )
    st.markdown('</div>', unsafe_allow_html=True)

with col_r:
    st.markdown('<div class="clinical-card">', unsafe_allow_html=True)
    st.subheader("📊 Inventory Health")
    fig = px.pie(inv_analysis, names='Status', hole=0.5, 
                 color='Status', color_discrete_map={"✅ HEALTHY":"#3FB950", "⚠️ REORDER":"#D29922", "🚨 CRITICAL":"#F85149"})
    fig.update_layout(showlegend=False, paper_bgcolor="rgba(0,0,0,0)", margin=dict(t=0, b=0, l=0, r=0))
    st.plotly_chart(fig, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# --- INDIVIDUAL PRODUCT INSIGHTS ---
st.markdown("### 🧬 SKU Deep Dive")
selected_sku = st.selectbox("Select Product for Analysis", inv_analysis['Product'].unique())
sku_data = inv_analysis[inv_analysis['Product'] == selected_sku].iloc[0]

# Clinical Gauge for Selected SKU
fig_gauge = go.Figure(go.Indicator(
    mode = "gauge+number",
    value = sku_data['Current_Stock'],
    domain = {'x': [0, 1], 'y': [0, 1]},
    title = {'text': f"Stock Level: {selected_sku}", 'font': {'size': 24, 'color': 'white'}},
    gauge = {
        'axis': {'range': [0, sku_data['Reorder_Point'] * 2], 'tickcolor': "white"},
        'bar': {'color': "#58A6FF"},
        'bgcolor': "#161B22",
        'threshold': {
            'line': {'color': "red", 'width': 4},
            'thickness': 0.75,
            'value': sku_data['Reorder_Point']
        },
        'steps': [
            {'range': [0, sku_data['Reorder_Point']], 'color': '#301c1c'},
            {'range': [sku_data['Reorder_Point'], sku_data['Reorder_Point'] * 2], 'color': '#1c3021'}
        ]
    }
))
fig_gauge.update_layout(paper_bgcolor="rgba(0,0,0,0)", font={'color': "white", 'family': "Arial"})
st.plotly_chart(fig_gauge, use_container_width=True)