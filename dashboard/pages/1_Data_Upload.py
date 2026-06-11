import streamlit as st
import pandas as pd
import plotly.express as px

# -------------------------------
# 1. INITIALIZE SESSION STATE
# -------------------------------
# This keeps our loaded dataset active even when you open collapse boxes, 
# interact with plots, or click buttons.
if "active_df" not in st.session_state:
    st.session_state.active_df = None
if "prev_option" not in st.session_state:
    st.session_state.prev_option = None

# -------------------------------
# 2. COLUMN STANDARDIZER
# -------------------------------
def standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    if df is None:
        return None
    df = df.copy()
    df.columns = (
        df.columns.str.replace(r'^\ufeff', '', regex=True)
        .str.strip()
        .str.lower()
        .str.replace(r'[\.\s\$]', '_', regex=True)
    )

    rename_map = {}
    for col in df.columns:
        if col in ['region', 'reg', 'geography', 'territory']:
            rename_map[col] = 'Region'
        elif col in ['sales', 'units_sold', 'quantity', 'qty', 'units', 'unit_sold']:
            rename_map[col] = 'Sales'
        elif col in ['revenue', 'total_revenue', 'sales_amount', 'amount', 'revenue_usd', 'totalrevenue']:
            rename_map[col] = 'Revenue'
        elif col in ['product', 'item_type', 'item', 'product_category', 'category', 'itemtype']:
            rename_map[col] = 'Product'
        elif col in ['date', 'order_date', 'sale_date', 'ship_date', 'orderdate']:
            rename_map[col] = 'Date'
        elif col in ['stock_level', 'stock', 'inventory', 'units_in_stock', 'stocklevel']:
            rename_map[col] = 'Stock_Level'
    return df.rename(columns=rename_map)

# -------------------------------
# 3. MAKE UNIQUE COLUMNS
# -------------------------------
def make_unique_columns(df: pd.DataFrame) -> pd.DataFrame:
    seen = {}
    new_cols = []
    for col in df.columns:
        if col not in seen:
            seen[col] = 0
            new_cols.append(col)
        else:
            seen[col] += 1
            new_cols.append(f"{col}_{seen[col]}")
    df.columns = new_cols
    return df

# -------------------------------
# 4. DATA LOADER
# -------------------------------
@st.cache_data(ttl=600, show_spinner=False)
def load_data(source):
    try:
        # Automatically detects commas, semicolons, and tabs across different files
        df = pd.read_csv(source, sep=None, engine="python")
        df = make_unique_columns(df) 
        df = standardize_columns(df)
        df = make_unique_columns(df) # Safeguard unique names after renaming
        return df
    except Exception as e:
        st.error(f"Error parsing file: {e}")
        return None

# -------------------------------
# 5. INLINE PREMIUM CSS
# -------------------------------
def inject_css():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

        body, .stApp {
            background: radial-gradient(circle at 50% 0%, #0F172A 0%, #030712 100%);
            font-family: 'Inter', sans-serif;
            color: #F3F4F6;
        }
        .section-card {
            background: rgba(17, 24, 39, 0.65);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 14px;
            padding: 24px;
            margin-bottom: 24px;
            box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.4);
        }
        .hero-title {
            color: #FFFFFF;
            font-size: 2.4rem;
            font-weight: 700;
            letter-spacing: -0.04em;
        }
        .hero-sub {
            color: #9CA3AF;
            font-size: 1.02rem;
            margin-bottom: 0px;
        }
        .badge {
            background: rgba(99, 102, 241, 0.12);
            color: #818CF8;
            border: 1px solid rgba(99, 102, 241, 0.25);
            border-radius: 20px;
            padding: 3px 10px;
            font-size: 0.75rem;
            font-weight: 600;
            letter-spacing: 0.05em;
        }
        div[data-testid="stMetric"] {
            background: rgba(17, 24, 39, 0.7) !important;
            backdrop-filter: blur(8px);
            border: 1px solid rgba(255, 255, 255, 0.06) !important;
            padding: 18px 22px !important;
            border-radius: 12px !important;
            box-shadow: 0 4px 20px -5px rgba(0,0,0,0.3);
            transition: all 0.3s ease !important;
        }
        div[data-testid="stMetric"]:hover {
            transform: translateY(-3px);
            border-color: rgba(99, 102, 241, 0.45) !important;
        }
        [data-testid="stMetricLabel"] p {
            color: #9CA3AF !important;
            font-size: 0.75rem !important;
            font-weight: 600 !important;
            text-transform: uppercase !important;
            letter-spacing: 0.05em !important;
        }
        [data-testid="stMetricValue"] div {
            color: #F9FAFB !important;
            font-size: 1.9rem !important;
            font-weight: 700 !important;
        }
        /* Style standard streamlit expanders */
        .streamlit-expanderHeader {
            background-color: rgba(17, 24, 39, 0.4) !important;
            border: 1px solid rgba(255, 255, 255, 0.05) !important;
            border-radius: 8px !important;
        }
        </style>
    """, unsafe_allow_html=True)

inject_css()

# -------------------------------
# 6. HEADER
# -------------------------------
st.markdown("""
<div style="margin-bottom: 28px;">
    <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 4px;">
        <span class="hero-title">Nexus AI</span>
        <span class="badge">PRO v3.1</span>
    </div>
    <p class="hero-sub">Predictive Sales & Inventory Hub</p>
</div>
""", unsafe_allow_html=True)

# -------------------------------
# 7. DATA INGESTION
# -------------------------------
st.sidebar.markdown("<h3 style='color: #FFFFFF; font-size: 1.15rem; margin-bottom: 12px;'>📥 Data Stream</h3>", unsafe_allow_html=True)
option = st.sidebar.radio("Choose Source", ["Upload CSV", "Network URL", "Sample Benchmarks"])

# Clear loaded data when switching ingestion options to prevent cross-data pollution
if st.session_state.prev_option != option:
    st.session_state.active_df = None
    st.session_state.prev_option = option

if option == "Upload CSV":
    file = st.sidebar.file_uploader("Upload CSV", type="csv", label_visibility="collapsed")
    if file:
        st.session_state.active_df = load_data(file)
    elif not file:
        st.session_state.active_df = None

elif option == "Network URL":
    url = st.sidebar.text_input("Enter CSV URL", placeholder="https://raw.githubusercontent.com/...csv")
    if url:
        st.session_state.active_df = load_data(url)
    elif not url:
        st.session_state.active_df = None

elif option == "Sample Benchmarks":
    # Let users load sample datasets instantly
    if st.sidebar.button("🚀 Load Benchmark"):
        benchmark_df = pd.DataFrame({
            'Date': pd.date_range(start='2023-01-01', periods=365, freq='D'),
            'Region': ['North', 'South', 'East', 'West'] * 91 + ['North'],
            'Product': ['Item A', 'Item B', 'Item C', 'Item D'] * 91 + ['Item A'],
            'Sales': [40, 60, 30, 80] * 91 + [40],
            'Revenue': [4000, 6000, 3000, 8000] * 91 + [4000],
            'Stock_Level': [100, 20, 50, 5] * 91 + [100]
        })
        st.session_state.active_df = standardize_columns(benchmark_df)

# Retrieve active dataset from the session state
df = st.session_state.active_df

# -------------------------------
# 8. ANALYTICS BLOCK
# -------------------------------
if df is not None:
    # Safe modification of dataframe copy
    df = df.copy()

    # Absolute integrity fallback checker
    required_cols = {
        'Region': 'Global',
        'Sales': 0,
        'Revenue': 0,
        'Product': 'Generic Product',
        'Date': pd.to_datetime('today'),
        'Stock_Level': 0
    }
    for col, fallback in required_cols.items():
        if col not in df.columns:
            df[col] = fallback

    # Enforce formatting types safely
    df['Sales'] = pd.to_numeric(df['Sales'], errors='coerce').fillna(0)
    df['Revenue'] = pd.to_numeric(df['Revenue'], errors='coerce').fillna(0)
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')

    # KPIs Row
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Rows Found", f"{len(df):,}")
    m2.metric("Total Revenue", f"${df['Revenue'].sum():,.0f}")
    m3.metric("Geographies", f"{df['Region'].nunique()}")
    m4.metric("Status", "Cleaned")

    st.write("###")

    # Main Visual Layout
    col_l, col_r = st.columns([0.45, 0.55], gap="large")

    with col_l:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown("<h5 style='color:#FFFFFF; margin:0 0 16px 0; font-weight:600; font-size:1rem;'>📋 Data Preview</h5>", unsafe_allow_html=True)
        st.dataframe(df.head(100), height=320, use_container_width=True)
        
        # Byte conversion is compatible across old and new versions of Streamlit
        csv_bytes = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="⬇️ Download Cleaned CSV", 
            data=csv_bytes, 
            file_name="cleaned_data.csv", 
            mime="text/csv",
            use_container_width=True
        )
        st.markdown('</div>', unsafe_allow_html=True)

    with col_r:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown("<h5 style='color:#FFFFFF; margin:0 0 16px 0; font-weight:600; font-size:1rem;'>🌎 Regional Distribution</h5>", unsafe_allow_html=True)
        fig = px.bar(
            df.groupby('Region')['Sales'].sum().reset_index(),
            x='Region', y='Sales', color='Sales',
            color_continuous_scale=["#4F46E5", "#06B6D4"],
            template="plotly_dark"
        )
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', 
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=10, r=10, t=10, b=10),
            height=320, 
            coloraxis_showscale=False,
            xaxis=dict(showgrid=False, linecolor='rgba(255,255,255,0.08)'),
            yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)', linecolor='rgba(255,255,255,0.08)')
        )
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # Advanced Analytics Expander
    with st.expander("📈 Advanced Stream Visualizations"):
        st.markdown("<br>", unsafe_allow_html=True)
        
        # 1. Date sorting is necessary to avoid intersecting/scrambled lines
        df_sorted = df.dropna(subset=['Date']).sort_values('Date')
        if not df_sorted.empty:
            fig_line = px.line(df_sorted, x="Date", y="Revenue", color="Region", template="plotly_dark", markers=True)
            fig_line.update_layout(
                paper_bgcolor='rgba(0,0,0,0)', 
                plot_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(gridcolor='rgba(255,255,255,0.05)'),
                yaxis=dict(gridcolor='rgba(255,255,255,0.05)')
            )
            st.plotly_chart(fig_line, use_container_width=True)
        else:
            st.warning("No valid timestamps found to plot trendlines.")

        # 2. Smart Pie chart - auto-group excess products so the chart doesn't clutter
        top_products = df.groupby('Product')['Sales'].sum().reset_index()
        if len(top_products) > 8:
            top_products = top_products.sort_values('Sales', ascending=False)
            top_8 = top_products.head(8)
            others_sales = top_products.iloc[8:]['Sales'].sum()
            others_row = pd.DataFrame([{'Product': 'Other Products', 'Sales': others_sales}])
            pie_data = pd.concat([top_8, others_row], ignore_index=True)
        else:
            pie_data = top_products

        fig_pie = px.pie(
            pie_data, 
            names="Product", 
            values="Sales", 
            color_discrete_sequence=px.colors.sequential.RdBu,
            template="plotly_dark"
        )
        fig_pie.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_pie, use_container_width=True)

        # 3. Dynamic Scatter
        fig_scatter = px.scatter(
            df, 
            x="Sales", 
            y="Stock_Level", 
            color="Region", 
            size="Revenue", 
            template="plotly_dark"
        )
        fig_scatter.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', 
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(gridcolor='rgba(255,255,255,0.05)'),
            yaxis=dict(gridcolor='rgba(255,255,255,0.05)')
        )
        st.plotly_chart(fig_scatter, use_container_width=True)

    # Footer Processing Action
    st.markdown("---")
    if st.button("Initialize Processing Pipeline ➔"):
        st.session_state['data'] = df
        st.success("Pipeline Synchronized.")
        st.balloons()

else:
    # Elegant custom placeholder replacing plain warning text
    st.markdown("""
        <div class="empty-state">
            <div class="empty-icon">📊</div>
            <h3>System Awaiting Data Ingestion</h3>
            <p>Please select a source in the sidebar to load your dataset (CSV Upload, Network URL, or Sample Benchmark).</p>
        </div>
        """, unsafe_allow_html=True)