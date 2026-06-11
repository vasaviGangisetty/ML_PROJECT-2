import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import datetime
import os
import joblib
from pathlib import Path

# ==========================================
# 1. PREMIUM DESIGN SYSTEM & CONTAINER TARGETING (CSS)
# ==========================================
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');
    
    .stApp { 
        background-color: #060b18; 
        font-family: 'Plus Jakarta Sans', sans-serif; 
        color: #e5e7eb; 
    }
    
    /* Elegant Title Styling */
    .forecast-title { 
        font-size: 2.5rem; 
        font-weight: 800; 
        background: linear-gradient(135deg, #ffffff 40%, #60a5fa 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 5px; 
        letter-spacing: -0.03em;
    }
    .forecast-subtitle { 
        color: #94a3b8; 
        font-size: 1.05rem; 
        margin-bottom: 25px; 
    }

    /* Target Native Streamlit Containers cleanly with Glassmorphic styles */
    div[data-testid="stVerticalBlockBorder"] {
        background: rgba(15, 23, 42, 0.7) !important;
        backdrop-filter: blur(16px) !important;
        border: 1px solid rgba(14, 165, 233, 0.15) !important;
        border-radius: 20px !important;
        padding: 24px !important;
        box-shadow: 0 15px 35px rgba(0, 0, 0, 0.5) !important;
        margin-bottom: 24px !important;
        transition: border-color 0.3s ease, box-shadow 0.3s ease !important;
    }
    div[data-testid="stVerticalBlockBorder"]:hover {
        border-color: rgba(139, 92, 246, 0.4) !important;
        box-shadow: 0 15px 40px rgba(139, 92, 246, 0.15) !important;
    }

    /* Custom KPI Dashboard Cards */
    .kpi-wrapper {
        background: rgba(15, 23, 42, 0.95);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 16px;
        padding: 20px 24px;
        text-align: left;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }
    .kpi-lbl {
        color: #94a3b8;
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin: 0;
    }
    .kpi-val {
        font-size: 28px;
        font-weight: 800;
        margin-top: 6px;
        margin-bottom: 0;
    }
    </style>
    """, unsafe_allow_html=True)

# --- HEADER ---
st.markdown('<h1 class="forecast-title">📈 Predictive Sales Forecasting</h1>', unsafe_allow_html=True)
st.markdown('<p class="forecast-subtitle">Generate statistical multi-horizon forecasts using optimized offline predictive frameworks.</p>', unsafe_allow_html=True)

# ==========================================
# 2. STATE RECOVERY & COMPATIBILITY CHECK
# ==========================================
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed_data"
MODELS_DIR = PROJECT_ROOT / "saved_models"

# 1. Recover Processed Data state from disk if empty
if "processed_data" not in st.session_state:
    if PROCESSED_DATA_DIR.exists():
        processed_files = [f for f in os.listdir(PROCESSED_DATA_DIR) if f.endswith('.csv')]
        if processed_files:
            try:
                st.session_state["processed_data"] = pd.read_csv(PROCESSED_DATA_DIR / processed_files[0])
            except Exception:
                pass

# 2. Recover Model state from disk if empty
if "trained_model" not in st.session_state:
    if MODELS_DIR.exists():
        model_files = [f for f in os.listdir(MODELS_DIR) if f.endswith('.pkl')]
        if model_files:
            try:
                payload = joblib.load(MODELS_DIR / model_files[0])
                if isinstance(payload, dict) and "pipeline" in payload:
                    st.session_state["trained_model"] = payload["pipeline"]
                    st.session_state["model_features"] = payload["features"]
                else:
                    st.session_state["trained_model"] = payload
            except Exception:
                pass

# Safety block if still unresolved
if "processed_data" not in st.session_state or "trained_model" not in st.session_state:
    st.info("💡 Predictive Engine Offline: Please process your data and fit a model inside preceding tabs before initiating forecasts.")
    st.stop()

# Retrieve values
df = st.session_state["processed_data"]
model = st.session_state["trained_model"]
features = st.session_state["model_features"]

# Retrieve column mappings safely
date_col = st.session_state.get("used_date_col", "Date_Parsed")
if date_col not in df.columns:
    date_col = "Date_Parsed" if "Date_Parsed" in df.columns else "Date"

sales_col = st.session_state.get("used_sales_col", "Sales")
if sales_col not in df.columns:
    sales_col = "Sales" if "Sales" in df.columns else df.select_dtypes(include=[np.number]).columns[0]

prod_col = st.session_state.get("used_prod_col", "Product")
reg_col = st.session_state.get("used_reg_col", "Region")

# ==========================================
# 3. FORECAST CONTROL CENTER
# ==========================================
st.sidebar.markdown("### 🎛️ Forecast Configuration")
days_to_predict = st.sidebar.slider("Forecast Horizon (Days)", min_value=7, max_value=120, value=30)

st.sidebar.markdown("---")
st.sidebar.markdown("### 📊 Business Scenarios")
scenario = st.sidebar.selectbox(
    "Simulation Profile",
    options=["Realistic (Base Model)", "Optimistic (+15% Demand Shift)", "Conservative (-15% Supply Constraint)"]
)

multiplier = 1.00
if "Optimistic" in scenario:
    multiplier = 1.15
elif "Conservative" in scenario:
    multiplier = 0.85

st.sidebar.markdown("---")
run_engine = st.sidebar.button("🚀 Run Predictive Engine", use_container_width=True)

if "future_df" not in st.session_state:
    st.session_state["future_df"] = None

if run_engine:
    with st.spinner("Compiling date schedules and applying scenario parameters..."):
        # 1. Synthesize Date Frame
        last_date = pd.to_datetime(df[date_col]).max()
        future_dates = pd.date_range(start=last_date + datetime.timedelta(days=1), periods=days_to_predict)
        
        future_df = pd.DataFrame({'Date': future_dates})
        future_df['Month'] = future_df['Date'].dt.month
        future_df['Year'] = future_df['Date'].dt.year
        future_df['Day'] = future_df['Date'].dt.day
        future_df['Is_Weekend'] = future_df['Date'].dt.dayofweek.apply(lambda x: 1 if x >= 5 else 0)
        
        # Pull festival schedules (Default to Oct-Dec if none)
        future_df['Is_Festival'] = future_df['Month'].apply(lambda x: 1 if x in [10, 11, 12] else 0)
        
        # Align columns to training features structure
        X_future = pd.get_dummies(future_df.drop(columns=['Date']))
        X_future = X_future.reindex(columns=features, fill_value=0)
        
        # 2. Run Inference
        # If model is the scikit-learn Pipeline, it automatically handles standardization scaling
        base_predictions = model.predict(X_future)
        base_predictions = np.clip(base_predictions, 0, None)
        
        future_df['Predicted_Sales'] = base_predictions * multiplier
        st.session_state["future_df"] = future_df

# ==========================================
# 4. VISUALIZATION DASHBOARD
# ==========================================
future_df = st.session_state["future_df"]

if future_df is not None:
    
    # --- KEY DECISION METRICS ---
    col1, col2, col3 = st.columns(3)
    
    total_forecasted = future_df['Predicted_Sales'].sum()
    historical_avg = df[sales_col].mean()
    predicted_avg = future_df['Predicted_Sales'].mean()
    
    if historical_avg > 0:
        avg_growth = ((predicted_avg - historical_avg) / historical_avg) * 100
    else:
        avg_growth = 0.0
        
    with col1:
        st.markdown(f"""
            <div class="kpi-wrapper">
                <p class="kpi-lbl">Forecasted Cumulative Units</p>
                <p class="kpi-val" style="background: linear-gradient(135deg, #38bdf8 0%, #818cf8 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                    {int(total_forecasted):,}
                </p>
            </div>
        """, unsafe_allow_html=True)
    with col2:
        trend_color = "linear-gradient(135deg, #34d399 0%, #059669 100%)" if avg_growth >= 0 else "linear-gradient(135deg, #f87171 0%, #dc2626 100%)"
        st.markdown(f"""
            <div class="kpi-wrapper">
                <p class="kpi-lbl">Target Demand Deviation</p>
                <p class="kpi-val" style="background: {trend_color}; -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                    {avg_growth:+.1f}%
                </p>
            </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
            <div class="kpi-wrapper">
                <p class="kpi-lbl">Confidence Tier</p>
                <p class="kpi-val" style="background: linear-gradient(135deg, #c084fc 0%, #818cf8 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                    Optimal (Pipelines Active)
                </p>
            </div>
        """, unsafe_allow_html=True)

    st.write("")

    # --- MULTI-TAB EXECUTIVE DASHBOARD ---
    tab_trajectory, tab_distribution, tab_manifest = st.tabs([
        "📈 Sales Horizon Trajectory",
        "📊 Categorical Demand Allocation",
        "📋 Forecast Manifest Terminal"
    ])

    with tab_trajectory:
        with st.container(border=True):
            st.subheader("Trajectory Outlook: Historical vs Predicted Timeline")
            st.write("###")
            
            fig = go.Figure()
            hist_slice = df.tail(90).sort_values(by=date_col)
            
            # Historical Trace
            fig.add_trace(go.Scatter(
                x=hist_slice[date_col], 
                y=hist_slice[sales_col], 
                name="Observed History", 
                line=dict(color="#4b5563", width=2)
            ))
            
            # Predicted Trace
            fig.add_trace(go.Scatter(
                x=future_df['Date'], 
                y=future_df['Predicted_Sales'], 
                name="Scenario Outlook", 
                line=dict(color="#0ea5e9", width=4, dash='dot')
            ))
            
            fig.update_layout(
                template="plotly_dark", 
                paper_bgcolor="rgba(0,0,0,0)", 
                plot_bgcolor="rgba(0,0,0,0)", 
                height=450,
                margin=dict(l=10, r=10, t=10, b=10),
                xaxis=dict(showgrid=False),
                yaxis=dict(gridcolor="rgba(255, 255, 255, 0.05)"),
                legend=dict(orientation="h", y=1.1, x=0.5, xanchor="center"),
                font=dict(family="Plus Jakarta Sans", size=11)
            )
            st.plotly_chart(fig, use_container_width=True)

    with tab_distribution:
        col_pie, col_bar = st.columns(2)
        
        with col_pie:
            with st.container(border=True):
                st.subheader("Projected Product Contribution")
                st.write("###")
                
                if prod_col in df.columns:
                    product_weights = df.groupby(prod_col)[sales_col].sum()
                    product_ratios = product_weights / product_weights.sum()
                    
                    predicted_shares = product_ratios * total_forecasted
                    share_df = predicted_shares.reset_index().rename(columns={sales_col: "Projected Units"})
                    
                    # Resolved: Replaced the missing Ice_r variable with a custom electric cybernetic sequence
                    cyber_palette = ["#38bdf8", "#0ea5e9", "#2563eb", "#6366f1", "#8b5cf6", "#d946ef"]
                    
                    fig_pie = px.pie(
                        share_df, 
                        names=prod_col, 
                        values="Projected Units", 
                        hole=0.5,
                        color_discrete_sequence=cyber_palette
                    )
                    fig_pie.update_layout(
                        paper_bgcolor="rgba(0,0,0,0)", 
                        font_color="#e5e7eb",
                        margin=dict(l=10, r=10, t=10, b=10),
                        legend=dict(orientation="h", y=-0.1, x=0.5, xanchor="center"),
                        font=dict(family="Plus Jakarta Sans", size=11)
                    )
                    st.plotly_chart(fig_pie, use_container_width=True)
                else:
                    st.info("Product classifications not found. Complete previous data pipeline steps to project product shares.")

        with col_bar:
            with st.container(border=True):
                st.subheader("Regional Demand Distribution")
                st.write("###")
                
                if reg_col in df.columns:
                    region_weights = df.groupby(reg_col)[sales_col].sum()
                    region_ratios = region_weights / region_weights.sum()
                    
                    predicted_regions = region_ratios * total_forecasted
                    reg_forecast_df = predicted_regions.reset_index().rename(columns={sales_col: "Projected Units"}).sort_values("Projected Units", ascending=True)
                    
                    fig_bar = px.bar(
                        reg_forecast_df, 
                        x="Projected Units", 
                        y=reg_col, 
                        orientation='h',
                        color="Projected Units", 
                        color_continuous_scale="ice"
                    )
                    fig_bar.update_layout(
                        paper_bgcolor="rgba(0,0,0,0)", 
                        plot_bgcolor="rgba(0,0,0,0)", 
                        coloraxis_showscale=False,
                        font_color="#e5e7eb",
                        margin=dict(l=10, r=10, t=10, b=10),
                        xaxis=dict(showgrid=False, color="#4b5563"),
                        yaxis=dict(color="#4b5563"),
                        font=dict(family="Plus Jakarta Sans", size=11)
                    )
                    st.plotly_chart(fig_bar, use_container_width=True)
                else:
                    st.info("Regional classifications not found. Run geographic prep stages to view regional demand forecasts.")

    with tab_manifest:
        with st.container(border=True):
            st.subheader("Forecast Query Terminal")
            st.markdown('<p style="color: #94a3b8; font-size: 0.95rem; margin-top:-10px; margin-bottom:20px;">Filter forecasting scenarios to isolate potential supply chain risks and peak delivery targets.</p>', unsafe_allow_html=True)
            
            query_cols = st.columns(2)
            with query_cols[0]:
                min_predicted = st.number_input("Filter Minimum Projected Sales Units:", min_value=0.0, value=0.0, step=10.0)
            with query_cols[1]:
                search_weekend = st.selectbox("Weekend Schedule Filter:", ["Show All Schedules", "Weekends Only", "Weekdays Only"])
                
            filtered_forecast = future_df.copy()
            filtered_forecast = filtered_forecast[filtered_forecast['Predicted_Sales'] >= min_predicted]
            
            if search_weekend == "Weekends Only":
                filtered_forecast = filtered_forecast[filtered_forecast['Is_Weekend'] == 1]
            elif search_weekend == "Weekdays Only":
                filtered_forecast = filtered_forecast[filtered_forecast['Is_Weekend'] == 0]
                
            show_cols = ['Date', 'Month', 'Is_Festival', 'Is_Weekend', 'Predicted_Sales']
            display_frame = filtered_forecast[show_cols].copy()
            display_frame['Predicted_Sales'] = display_frame['Predicted_Sales'].round(2)
            
            # Render styled Pandas gradient framework inside streamlit
            styled_manifest = (
                display_frame.style
                .format({"Date": lambda x: x.strftime('%Y-%m-%d'), "Predicted_Sales": "{:,.2f}"})
                .background_gradient(subset=["Predicted_Sales"], cmap="Blues")
            )
            st.dataframe(styled_manifest, use_container_width=True)
            
            st.write("")
            csv_manifest = display_frame.to_csv(index=False)
            st.download_button(
                label="💾 Download Compiled Scenario Predictions (.csv)",
                data=csv_manifest,
                file_name=f"sales_scenario_forecast.csv",
                mime="text/csv",
                use_container_width=True
            )

else:
    with st.container(border=True):
        st.markdown("""
            <div style="text-align:center; padding: 60px 40px;">
                <div style="font-size:3.5rem; margin-bottom: 20px;">🔮</div>
                <h3 style="color:#ffffff; margin-bottom: 10px;">Predictive Engine Offline</h3>
                <p style="color:#64748B; max-width: 500px; margin: 0 auto 25px auto;">
                    Configure your predictive horizon scope on the sidebar controller and execute the model solver to generate trajectory dashboards.
                </p>
            </div>
        """, unsafe_allow_html=True)