import streamlit as st

st.set_page_config(page_title="AI Sales & Inventory", layout="wide")

st.title("🚀 AI Sales Forecasting & Inventory Optimization")

st.markdown("""
### Welcome to the Business Intelligence Suite
Use the sidebar to navigate through the workflow:
1. **Upload Data**: Load your CSV or use sample datasets.
2. **Preprocessing**: Clean and add seasonal/festival features.
3. **EDA**: Explore revenue and product trends.
4. **Forecasting**: Predict future sales and festival impacts.
5. **Inventory**: Calculate Reorder Points and Safety Stock.
6. **Reports**: Download PDF/Excel summaries.
""")

# Initialize session state to store data across pages
if 'raw_data' not in st.session_state:
    st.session_state['raw_data'] = None
if 'processed_data' not in st.session_state:
    st.session_state['processed_data'] = None