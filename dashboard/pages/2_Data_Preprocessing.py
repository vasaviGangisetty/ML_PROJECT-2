import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

st.set_page_config(
    page_title="Feature Engineering Lab",
    page_icon="⚙️",
    layout="wide"
)

# =========================
# CUSTOM CSS FOR MODERN UI
# =========================
st.markdown("""
<style>
    .stApp {
        background-color: #0d1117;
        color: #c9d1d9;
    }
    .main-title {
        font-size: 38px;
        font-weight: 800;
        background: linear-gradient(135deg, #58a6ff, #bc8cff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 5px;
    }
    .subtitle {
        color: #8b949e;
        font-size: 16px;
        margin-bottom: 25px;
    }
    /* Custom Metric Card Style */
    .metric-container {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 10px;
        padding: 15px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .metric-val {
        font-size: 24px;
        font-weight: 700;
        color: #58a6ff;
        margin: 5px 0 0 0;
    }
    .metric-lbl {
        font-size: 13px;
        color: #8b949e;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin: 0;
    }
</style>
""", unsafe_allow_html=True)

# =========================
# HEADER
# =========================
st.markdown("<div class='main-title'>⚙️ Feature Engineering Lab</div>", unsafe_allow_html=True)
st.markdown("<div class='subtitle'>Advanced preprocessing, seasonal intelligence, and temporal feature extraction</div>", unsafe_allow_html=True)

# =========================
# DATA CHECK
# =========================
if 'data' not in st.session_state or st.session_state["data"] is None:
    st.info("💡 Please upload or load a dataset first to start the Feature Engineering process.")
    st.stop()

df_source = st.session_state["data"].copy()

# =========================
# SIDEBAR SETTINGS & MAPPING
# =========================
st.sidebar.header("🎯 Column Mapping")

# Smart-detect default date and numerical columns
date_cols = list(df_source.columns)
val_cols = list(df_source.columns)

default_date_idx = 0
for i, col in enumerate(date_cols):
    if 'date' in col.lower() or 'time' in col.lower():
        default_date_idx = i
        break

default_val_idx = 0
for i, col in enumerate(val_cols):
    if any(term in col.lower() for term in ['sales', 'revenue', 'value', 'amount', 'target', 'qty']):
        default_val_idx = i
        break

date_col = st.sidebar.selectbox("Date Column", options=date_cols, index=default_date_idx)
sales_col = st.sidebar.selectbox("Sales/Value Column (Optional)", options=val_cols, index=default_val_idx)

st.sidebar.markdown("---")
st.sidebar.header("⚙️ Transformation Parameters")

festival_months = st.sidebar.multiselect(
    "Festival Months",
    options=list(range(1, 13)),
    default=[10, 11, 12],
    format_func=lambda x: ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"][x-1]
)

weekend_detection = st.sidebar.checkbox(
    "Weekend Detection",
    value=True
)

missing_value_fix = st.sidebar.checkbox(
    "Handle Missing Values (ffill + bfill)",
    value=True
)

rolling_window = st.sidebar.slider(
    "Rolling Average Window",
    min_value=3,
    max_value=30,
    value=7
)

# =========================
# PROCESS TRIGGER
# =========================
if st.sidebar.button("Run Feature Engineering", use_container_width=True):
    with st.spinner("Extracting parameters and performing analysis..."):
        df = df_source.copy()

        # Parse Dates
        df["Date_Parsed"] = pd.to_datetime(df[date_col], errors="coerce")
        # Drop rows where dates could not be parsed to prevent downstream errors
        df = df.dropna(subset=["Date_Parsed"])

        # Handle Missing Values if requested
        if missing_value_fix:
            df = df.ffill().bfill()

        # Date Feature Extraction
        df["Year"] = df["Date_Parsed"].dt.year
        df["Month"] = df["Date_Parsed"].dt.month
        df["Month_Name"] = df["Date_Parsed"].dt.strftime("%b")
        df["Quarter"] = df["Date_Parsed"].dt.quarter
        df["Week"] = df["Date_Parsed"].dt.isocalendar().week.astype(int)
        df["Day"] = df["Date_Parsed"].dt.day
        df["Day_of_Week"] = df["Date_Parsed"].dt.day_name()

        # Season Detection Logic
        def get_season(month):
            if month in [12, 1, 2]:
                return "Winter"
            elif month in [3, 4, 5]:
                return "Spring"
            elif month in [6, 7, 8]:
                return "Summer"
            else:
                return "Autumn"

        df["Season"] = df["Month"].apply(get_season)

        # Weekend Flag
        if weekend_detection:
            df["Is_Weekend"] = (df["Date_Parsed"].dt.dayofweek >= 5).astype(int)
        else:
            df["Is_Weekend"] = 0

        # Festival Flag
        df["Is_Festival"] = df["Month"].isin(festival_months).astype(int)

        # Sales/Target Specific Transformations
        if sales_col in df.columns:
            df[sales_col] = pd.to_numeric(df[sales_col], errors="coerce")
            df = df.dropna(subset=[sales_col])

            # Rolling Calculations
            df["Rolling_Avg"] = df[sales_col].rolling(rolling_window, min_periods=1).mean()
            df["Sales_Growth"] = df[sales_col].pct_change().fillna(0) * 100

            # Outlier / Anomaly Detection
            mean_sales = df[sales_col].mean()
            std_sales = df[sales_col].std()
            
            if std_sales > 0:
                df["Anomaly"] = (abs(df[sales_col] - mean_sales) > (2 * std_sales)).astype(int)
            else:
                df["Anomaly"] = 0

        st.session_state["processed_data"] = df
        st.session_state["used_date_col"] = date_col
        st.session_state["used_sales_col"] = sales_col
        st.success("🎉 Preprocessing and Feature Engineering Completed!")

# =========================
# DISPLAY RESULTS
# =========================
# Defensively check if 'processed_data' is present in session state and is not None
if "processed_data" in st.session_state and st.session_state["processed_data"] is not None:
    
    p_df = st.session_state["processed_data"]
    d_col = "Date_Parsed"
    s_col = st.session_state.get("used_sales_col", sales_col)

    # ---------------------
    # HIGH-LEVEL STATISTICS (KPI CARDS)
    # ---------------------
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-container">
            <p class="metric-lbl">Total Samples</p>
            <p class="metric-val">{len(p_df):,}</p>
        </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.markdown(f"""
        <div class="metric-container">
            <p class="metric-lbl">Generated Features</p>
            <p class="metric-val">{len(p_df.columns)}</p>
        </div>
        """, unsafe_allow_html=True)
        
    with col3:
        st.markdown(f"""
        <div class="metric-container">
            <p class="metric-lbl">Festival Periods</p>
            <p class="metric-val">{p_df["Is_Festival"].sum() if "Is_Festival" in p_df.columns else 0:,}</p>
        </div>
        """, unsafe_allow_html=True)
        
    with col4:
        st.markdown(f"""
        <div class="metric-container">
            <p class="metric-lbl">Weekend Records</p>
            <p class="metric-val">{p_df["Is_Weekend"].sum() if "Is_Weekend" in p_df.columns else 0:,}</p>
        </div>
        """, unsafe_allow_html=True)

    st.write("") # Spacing

    # ---------------------
    # ANALYSIS TABS (Clean Structure)
    # ---------------------
    tab_preview, tab_trends, tab_seasonal, tab_correlations = st.tabs([
        "📋 Data Preview & Columns",
        "📈 Trend & Moving Averages",
        "🍂 Seasonal & Anomaly Insights",
        "🔗 Correlation & Export"
    ])

    with tab_preview:
        st.subheader("Engineered Dataset Preview")
        st.dataframe(p_df.head(100), use_container_width=True)
        
        # Schema info
        with st.expander("Explore Column Types & Information"):
            info_df = pd.DataFrame({
                "Data Type": p_df.dtypes.astype(str),
                "Non-Null Count": p_df.notnull().sum(),
                "Null Count": p_df.isnull().sum()
            })
            st.dataframe(info_df, use_container_width=True)

    with tab_trends:
        if s_col in p_df.columns:
            col_l, col_r = st.columns(2)
            
            with col_l:
                st.subheader("Global Trend Analysis")
                trend_df = p_df.groupby(d_col)[s_col].sum().reset_index()
                fig1 = px.line(
                    trend_df,
                    x=d_col,
                    y=s_col,
                    title=f"Aggregated {s_col} Over Time",
                    template="plotly_dark",
                    color_discrete_sequence=["#58a6ff"]
                )
                fig1.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig1, use_container_width=True)

            with col_r:
                st.subheader(f"Rolling Average ({rolling_window}-Day)")
                fig2 = go.Figure()
                fig2.add_trace(go.Scatter(
                    x=p_df[d_col],
                    y=p_df[s_col],
                    name="Raw Value",
                    line=dict(color="rgba(110, 118, 129, 0.4)", width=1.5)
                ))
                fig2.add_trace(go.Scatter(
                    x=p_df[d_col],
                    y=p_df["Rolling_Avg"],
                    name="Rolling Average",
                    line=dict(color="#bc8cff", width=2.5)
                ))
                fig2.update_layout(
                    template="plotly_dark", 
                    plot_bgcolor="rgba(0,0,0,0)", 
                    paper_bgcolor="rgba(0,0,0,0)",
                    legend=dict(orientation="h", y=1.1)
                )
                st.plotly_chart(fig2, use_container_width=True)
        else:
            st.warning("Trend plots are disabled. Please map a numerical target variable to view time-series charts.")

    with tab_seasonal:
        if s_col in p_df.columns:
            col_sl, col_sr = st.columns(2)
            
            with col_sl:
                st.subheader("Seasonal Average Analysis")
                season_df = p_df.groupby("Season")[s_col].mean().reset_index()
                fig4 = px.bar(
                    season_df,
                    x="Season",
                    y=s_col,
                    color="Season",
                    color_discrete_sequence=px.colors.qualitative.Pastel,
                    template="plotly_dark"
                )
                fig4.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", showlegend=False)
                st.plotly_chart(fig4, use_container_width=True)

            with col_sr:
                st.subheader("Outlier/Anomaly Highlights")
                fig3 = px.scatter(
                    p_df,
                    x=d_col,
                    y=s_col,
                    color=p_df["Anomaly"].astype(str),
                    color_discrete_map={"0": "#58a6ff", "1": "#ff7b72"},
                    template="plotly_dark",
                    labels={"color": "Is Anomaly"}
                )
                fig3.update_layout(
                    plot_bgcolor="rgba(0,0,0,0)", 
                    paper_bgcolor="rgba(0,0,0,0)",
                    legend=dict(orientation="h", y=1.1)
                )
                st.plotly_chart(fig3, use_container_width=True)
        else:
            st.warning("Seasonal metrics are unavailable. Please select a numerical column for mapping.")

    with tab_correlations:
        # Correlation Matrix Setup
        st.subheader("Feature Correlation")
        numeric_df = p_df.select_dtypes(include=np.number)
        
        if not numeric_df.empty and len(numeric_df.columns) > 1:
            corr = numeric_df.corr()
            fig_corr = px.imshow(
                corr,
                text_auto=".2f",
                color_continuous_scale="RdBu_r",
                zmin=-1,
                zmax=1,
                template="plotly_dark"
            )
            fig_corr.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_corr, use_container_width=True)
        else:
            st.info("Insufficient numeric features available to generate a correlation matrix.")

        # Download Processed Dataset Section
        st.markdown("---")
        st.subheader("💾 Export Transformations")
        csv = p_df.to_csv(index=False)
        st.download_button(
            label="Download Processed Dataset (.csv)",
            data=csv,
            file_name="processed_dataset.csv",
            mime="text/csv",
            use_container_width=True
        )

        # Dynamic Automated Insights
        if s_col in p_df.columns:
            st.markdown("### 🧠 Automated Features Overview")
            
            # Identify highest/lowest seasons dynamically
            season_means = p_df.groupby("Season")[s_col].mean()
            best_season = season_means.idxmax() if not season_means.empty else "N/A"
            worst_season = season_means.idxmin() if not season_means.empty else "N/A"
            
            # Anomaly percent
            anomaly_pct = (p_df["Anomaly"].mean() * 100) if "Anomaly" in p_df.columns else 0.0

            st.info(
                f"""
                - **Primary Trend Peak**: Highest average metric performance registered during **{best_season}**.
                - **Historical Valley**: Lowest average metrics detected during **{worst_season}**.
                - **Anomalies Detected**: Outliers account for **{anomaly_pct:.2f}%** of the current dataset (exceeding 2 standard deviations).
                - **Integration Readiness**: Data schema contains a mix of temporal, calendar, and flag boundaries, ready for consumption by deep learning / forecasting pipelines.
                """
            )

else:
    # If processed data is not found yet, inform the user to configure variables on the left
    st.info("👈 Configure variables and click **Run Feature Engineering** in the sidebar to generate data transformations.")