import streamlit as st
import os

st.set_page_config(page_title="AI Sales & Inventory", layout="wide")

st.title("📦 AI Sales & Inventory Management System")

# Initialize Session State for Data Persistence
if 'data' not in st.session_state:
    st.session_state['data'] = None
if 'processed_data' not in st.session_state:
    st.session_state['processed_data'] = None

st.info("Select a module from the sidebar to begin. Start with 'Data Upload'.")