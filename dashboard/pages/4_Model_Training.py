import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import joblib
import os
import time
from pathlib import Path

# Machine Learning Stack
from sklearn.model_selection import train_test_split, RandomizedSearchCV
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score, mean_absolute_percentage_error
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge
try:
    from xgboost import XGBRegressor
    HAS_XGB = True
except ImportError:
    HAS_XGB = False

# --- 1. PREMIUM STYLING & NATIVE TARGETING (CSS) ---
st.set_page_config(page_title="Nexus AI | Neural Studio", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');

    .stApp { 
        background-color: #060b18; 
        font-family: 'Plus Jakarta Sans', sans-serif; 
    }
    
    /* 
       HIGH-END STYLING FOR NATIVE CONTAINER BORDERS 
       This targets st.container(border=True) and styles it with glassmorphism, 
       eliminating broken HTML wrapper divs completely.
    */
    div[data-testid="stVerticalBlockBorder"] {
        background: rgba(15, 23, 42, 0.7) !important;
        backdrop-filter: blur(16px) !important;
        border: 1px solid rgba(14, 165, 233, 0.15) !important;
        border-radius: 20px !important;
        padding: 24px !important;
        box-shadow: 0 15px 35px rgba(0, 0, 0, 0.5) !important;
        transition: border-color 0.3s ease, box-shadow 0.3s ease !important;
    }
    div[data-testid="stVerticalBlockBorder"]:hover {
        border-color: rgba(139, 92, 246, 0.4) !important;
        box-shadow: 0 15px 40px rgba(139, 92, 246, 0.15) !important;
    }
    
    /* KPI Metrics Styling */
    div[data-testid="stMetric"] {
        background: rgba(15, 23, 42, 0.9) !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
        padding: 18px 22px !important;
        border-radius: 16px !important;
        box-shadow: inset 0 2px 4px rgba(255,255,255,0.02) !important;
    }
    [data-testid="stMetricLabel"] p { 
        color: #94A3B8 !important; 
        text-transform: uppercase; 
        letter-spacing: 0.1em; 
        font-size: 0.75rem !important; 
        font-weight: 600 !important;
    }
    [data-testid="stMetricValue"] div { 
        background: linear-gradient(135deg, #38bdf8 0%, #818cf8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800 !important; 
    }

    /* Calibration Button styling */
    .stButton>button {
        background: linear-gradient(135deg, #0ea5e9 0%, #6366f1 100%) !important;
        color: #ffffff !important;
        border-radius: 12px !important;
        padding: 0.85rem 1.5rem !important;
        font-weight: 700 !important;
        letter-spacing: 0.05em;
        border: none !important;
        box-shadow: 0 4px 15px rgba(99, 102, 241, 0.2) !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        width: 100%;
    }
    .stButton>button:hover {
        box-shadow: 0 0 25px rgba(14, 165, 233, 0.5) !important;
        transform: translateY(-2px);
    }

    /* Pipeline Step Tracker */
    .pipeline-container {
        display: flex;
        justify-content: space-between;
        margin-bottom: 30px;
        padding: 15px;
        background: rgba(15, 23, 42, 0.5);
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.05);
    }
    .step-badge {
        font-size: 0.8rem;
        font-weight: 600;
        padding: 6px 12px;
        border-radius: 20px;
        background: rgba(255,255,255,0.03);
        color: #64748B;
        border: 1px solid rgba(255,255,255,0.05);
    }
    .step-active {
        background: rgba(14, 165, 233, 0.15);
        color: #38BDF8;
        border-color: rgba(14, 165, 233, 0.3);
        box-shadow: 0 0 10px rgba(14, 165, 233, 0.1);
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DYNAMIC PATHS & DATA PERSISTENCE ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed_data"

df = None

# Recover preprocessed data from session state or fall back to disk
if "processed_data" in st.session_state:
    df = st.session_state["processed_data"].copy()
else:
    if PROCESSED_DATA_DIR.exists():
        processed_files = [f for f in os.listdir(PROCESSED_DATA_DIR) if f.endswith('.csv')]
        if processed_files:
            fallback_file = PROCESSED_DATA_DIR / processed_files[0]
            try:
                df = pd.read_csv(fallback_file)
                st.session_state["processed_data"] = df
                st.toast(f"Synchronized with: {processed_files[0]}", icon="🧠")
            except Exception:
                pass

if df is None:
    st.error("🚨 Neural Sync Warning: No processed dataset resolved. Please run Preprocessing first.")
    st.stop()

# --- 3. PIPELINE PREPARATION (WITH INTERACTIVE COLLINEARITY FILTER) ---
def prepare_ml_data(dataframe, target, test_size_pct=0.2, corr_threshold=0.90):
    drop_vars = [target, "Date", "Month_Name", "Day_of_Week", "Season"]
    X_raw = dataframe.drop(columns=[c for c in drop_vars if c in dataframe.columns], errors="ignore")
    y_raw = dataframe[target]

    # Clean out datetimes to avoid sklearn errors
    datetime_cols = X_raw.select_dtypes(include=['datetime', 'datetime64', 'datetimetz']).columns.tolist()
    X_raw = X_raw.drop(columns=datetime_cols, errors="ignore")

    # Encode categorical fields
    X_enc = pd.get_dummies(X_raw, drop_first=True)
    X_enc = X_enc.select_dtypes(include=[np.number, 'bool'])
    
    # Standardize boolean flags
    bool_cols = X_enc.select_dtypes(include=['bool']).columns
    for col in bool_cols:
        X_enc[col] = X_enc[col].astype(int)
        
    # Standardize numerical empty slots and infinities
    X_enc = X_enc.replace([np.inf, -np.inf], np.nan)
    X_enc = X_enc.fillna(X_enc.mean(numeric_only=True)).fillna(0)
    y_enc = y_raw.fillna(y_raw.mean())
    X_enc = X_enc.astype(float)
    
    # Prune highly correlated redundant features
    corr_matrix = X_enc.corr().abs()
    upper_triangle = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))
    redundant_features = [col for col in upper_triangle.columns if any(upper_triangle[col] > corr_threshold)]
    
    if redundant_features:
        X_enc = X_enc.drop(columns=redundant_features)
        
    return train_test_split(X_enc, y_enc, test_size=test_size_pct, random_state=42), X_enc.columns.tolist(), redundant_features

# --- 4. HEADER NAVIGATION ---
st.markdown('<h1 style="color:white; font-size: 2.8rem; font-weight:800; letter-spacing:-0.04em; background: linear-gradient(to right, #ffffff, #94a3b8); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">Neural Training Studio</h1>', unsafe_allow_html=True)
st.markdown('<p style="color:#64748B; font-size:1.1rem; margin-top:-5px; margin-bottom:25px;">Robust pipeline scaling, collinearity pruning, and optimization tuning.</p>', unsafe_allow_html=True)

step_state = "step-active" if "trained_model" in st.session_state else ""
st.markdown(f"""
    <div class="pipeline-container">
        <span class="step-badge step-active">1. Ingest Data</span>
        <span class="step-badge step-active">2. Collinearity Pruning</span>
        <span class="step-badge step-active">3. Standard Scaling (Pipeline)</span>
        <span class="step-badge {step_state}">4. Global Prediction Ready</span>
    </div>
    """, unsafe_allow_html=True)

# --- 5. SIDEBAR CONFIGURATION ---
available_architectures = ["Random Forest", "Ridge Regression"]
if HAS_XGB:
    available_architectures.insert(1, "XGBoost")

with st.sidebar:
    st.markdown("### 🎛️ Optimization Parameters")
    
    target_col = st.selectbox(
        "Predictive Target", 
        [col for col in ["Sales", "Revenue"] if col in df.columns] or [df.columns[0]]
    )
    
    st.divider()
    model_choice = st.multiselect(
        "Model Architectures", 
        available_architectures, 
        default=available_architectures[:2]
    )
    
    st.markdown("### 🛠️ Advanced Controls")
    corr_filter = st.slider("Collinearity Threshold (Prune redundant variables)", 0.70, 1.00, 0.90, 0.05, 
                            help="Drops redundant features with correlation coefficients above this value.")
    
    hyper_tune = st.checkbox("Enable Fast Hyperparameter CV Tuning", value=True,
                             help="Runs standard Cross-Validation to determine optimized parameter states.")
    
    st.write("---")
    test_size = st.slider("Validation Split (%)", min_value=10, max_value=40, value=20, step=5) / 100
    
    train_trigger = st.button("🚀 INITIATE PIPELINE CALIBRATION")

# Prepare dataset splitting
(X_train, X_test, y_train, y_test), feature_names, dropped_cols = prepare_ml_data(df, target_col, test_size, corr_filter)

# Active Features Summary Display
col_left, col_right = st.columns(2)
with col_left:
    with st.expander(f"🔍 Active Feature Input Matrix ({len(feature_names)} columns)"):
        st.write(", ".join(feature_names))
with col_right:
    with st.expander(f"🗑️ Pruned Redundant Features ({len(dropped_cols)} columns)"):
        if dropped_cols:
            st.write(", ".join(dropped_cols))
        else:
            st.info("No collinear columns exceeded pruning threshold limit.")

# --- 6. MODEL TRAINING LOGIC ---
if train_trigger:
    if not model_choice:
        st.warning("Please configure at least one active machine learning architecture.")
        st.stop()
        
    trained_pipelines = []
    
    with st.status("⚡ Scaling Data and Optimizing Parameters...", expanded=True) as status:
        
        # 1. Random Forest Pipeline
        if "Random Forest" in model_choice:
            st.write("Fitting Random Forest Pipeline (scaling + model)...")
            rf_base_pipe = Pipeline([
                ('scaler', StandardScaler()),
                ('model', RandomForestRegressor(random_state=42, n_jobs=-1))
            ])
            if hyper_tune:
                st.write("Cross-Validating Forest estimators...")
                param_dist = {
                    'model__n_estimators': [100, 200],
                    'model__max_depth': [10, 20, None]
                }
                search = RandomizedSearchCV(rf_base_pipe, param_dist, n_iter=4, cv=3, random_state=42, n_jobs=-1)
                search.fit(X_train, y_train)
                trained_pipelines.append(("Random Forest", search.best_estimator_))
            else:
                rf_base_pipe.fit(X_train, y_train)
                trained_pipelines.append(("Random Forest", rf_base_pipe))

        # 2. XGBoost Pipeline
        if "XGBoost" in model_choice and HAS_XGB:
            st.write("Fitting XGBoost Gradient Boosting Pipeline...")
            xgb_base_pipe = Pipeline([
                ('scaler', StandardScaler()),
                ('model', XGBRegressor(random_state=42, n_jobs=-1))
            ])
            if hyper_tune:
                st.write("Tuning learning rates and depth space...")
                param_dist = {
                    'model__n_estimators': [100, 150],
                    'model__learning_rate': [0.05, 0.1, 0.2],
                    'model__max_depth': [4, 6]
                }
                search = RandomizedSearchCV(xgb_base_pipe, param_dist, n_iter=4, cv=3, random_state=42, n_jobs=-1)
                search.fit(X_train, y_train)
                trained_pipelines.append(("XGBoost", search.best_estimator_))
            else:
                xgb_base_pipe.fit(X_train, y_train)
                trained_pipelines.append(("XGBoost", xgb_base_pipe))
        
        # 3. Ridge Pipeline
        if "Ridge Regression" in model_choice:
            st.write("Fitting Standard Scaled Ridge Regularization...")
            ridge_base_pipe = Pipeline([
                ('scaler', StandardScaler()),
                ('model', Ridge())
            ])
            if hyper_tune:
                st.write("Scanning optimal alpha values...")
                param_dist = {
                    'model__alpha': [0.1, 1.0, 10.0, 100.0]
                }
                search = RandomizedSearchCV(ridge_base_pipe, param_dist, n_iter=4, cv=3, random_state=42, n_jobs=-1)
                search.fit(X_train, y_train)
                trained_pipelines.append(("Ridge Regression", search.best_estimator_))
            else:
                ridge_base_pipe.fit(X_train, y_train)
                trained_pipelines.append(("Ridge Regression", ridge_base_pipe))

        status.update(label="Calibration successful. Pipelines saved.", state="complete")

    # --- 7. EVALUATION PIPELINE ---
    scores = []
    for name, pipeline in trained_pipelines:
        preds = pipeline.predict(X_test)
        scores.append({
            "Architecture": name,
            "R² Score": r2_score(y_test, preds),
            "MAE": mean_absolute_error(y_test, preds),
            "MAPE": mean_absolute_percentage_error(y_test, preds),
            "RMSE": np.sqrt(mean_squared_error(y_test, preds)),
            "Pipeline": pipeline,
            "Predictions": preds
        })

    eval_df = pd.DataFrame(scores).sort_values("R² Score", ascending=False)
    best_run = eval_df.iloc[0]

    # Save complete Pipeline state (both data scaler and model)
    st.session_state["trained_model"] = best_run["Pipeline"]
    st.session_state["model_features"] = feature_names
    
    models_dir = PROJECT_ROOT / "saved_models"
    os.makedirs(models_dir, exist_ok=True)
    
    model_payload = {
        "pipeline": best_run["Pipeline"],
        "features": feature_names,
        "target": target_col,
        "r2_score": best_run["R² Score"]
    }
    joblib.dump(model_payload, models_dir / f"{target_col.lower()}_best_model.pkl")

    # Map long model names to shorter, clean variants to prevent metrics card truncation
    display_names = {
        "Ridge Regression": "Ridge",
        "Random Forest": "Random Forest",
        "XGBoost": "XGBoost"
    }
    short_winning_name = display_names.get(best_run["Architecture"], best_run["Architecture"])

    # RENDERING THE NATIVE HIGH-END CONTAINER
    # Using st.container(border=True) ensures that the layout will render perfectly 
    # and contain the metrics and leaderboard tables natively.
    with st.container(border=True):
        st.subheader("🏁 Calibration Leaderboard")
        st.write("###")
        
        col_a, col_b, col_c, col_d = st.columns(4)
        col_a.metric("BEST PIPELINE RUN", short_winning_name)
        col_b.metric("R² SYSTEM METRIC", f"{best_run['R² Score']:.2%}")
        col_c.metric("ERROR RATE (MAPE)", f"{best_run['MAPE']:.2%}")
        col_d.metric("RMSE METRIC", f"{best_run['RMSE']:.2f}")
        
        st.write("###")
        
        leaderboard_view_df = eval_df[["Architecture", "R² Score", "MAE", "MAPE", "RMSE"]].copy()
        st.dataframe(
            leaderboard_view_df,
            column_config={
                "Architecture": st.column_config.TextColumn("Model Architecture", width="medium"),
                "R² Score": st.column_config.ProgressColumn(
                    "Model Accuracy (R²)", 
                    help="Coefficient of Determination score range [0.0 to 1.0]",
                    format="%.3f", 
                    min_value=0.0, 
                    max_value=1.0
                ),
                "MAE": st.column_config.NumberColumn("Average Deviation (MAE)", format="%,.2f"),
                "MAPE": st.column_config.NumberColumn("MAPE Error %", format="%.2f%%"),
                "RMSE": st.column_config.NumberColumn("Root Mean Square (RMSE)", format="%,.2f")
            },
            hide_index=True,
            use_container_width=True
        )

    st.write("---")

    # --- 8. EXPLAINABILITY & DIAGNOSTICS LAYER ---
    diag_l, diag_r = st.columns(2)

    with diag_l:
        with st.container(border=True):
            st.subheader("🎯 Feature Contribution")
            
            best_pipeline_obj = best_run["Pipeline"]
            best_model_obj = best_pipeline_obj.named_steps['model']
            weights = None
            
            if hasattr(best_model_obj, "feature_importances_"):
                weights = best_model_obj.feature_importances_
            elif hasattr(best_model_obj, "coef_"):
                weights = np.abs(best_model_obj.coef_)
                
            if weights is not None:
                imp_df = pd.DataFrame({"Feature": feature_names, "Importance": weights})
                imp_df = imp_df.sort_values("Importance", ascending=True).tail(12)
                
                fig_imp = px.bar(
                    imp_df, 
                    x="Importance", 
                    y="Feature", 
                    orientation='h', 
                    template="plotly_dark",
                    color="Importance",
                    color_continuous_scale="electric"
                )
                fig_imp.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)", 
                    plot_bgcolor="rgba(0,0,0,0)", 
                    coloraxis_showscale=False,
                    xaxis=dict(gridcolor="rgba(255,255,255,0.05)", title="Computed Feature Contribution"),
                    yaxis=dict(gridcolor="rgba(255,255,255,0.05)", title=""),
                    margin=dict(l=10, r=10, t=10, b=10),
                    font=dict(family="Plus Jakarta Sans", size=11)
                )
                st.plotly_chart(fig_imp, use_container_width=True)
            else:
                st.info("Feature contributions are not dynamically exportable for this algorithm.")

    with diag_r:
        with st.container(border=True):
            st.subheader("📉 Residual Density Parity")
            
            fig_res = px.scatter(
                x=y_test, 
                y=best_run["Predictions"], 
                labels={'x': 'Actual Value Indices', 'y': 'AI Forecast Predictions'}, 
                template="plotly_dark", 
                marginal_x="histogram",
                marginal_y="histogram",
                opacity=0.6
            )
            
            fig_res.update_traces(
                marker=dict(size=8, color='#06b6d4', opacity=0.7, line=dict(width=1, color='#0ea5e9')),
                selector=dict(mode='markers')
            )
            
            fig_res.add_shape(
                type="line", 
                x0=y_test.min(), 
                y0=y_test.min(), 
                x1=y_test.max(), 
                y1=y_test.max(), 
                line=dict(color="#8b5cf6", width=2, dash="dash")
            )
            
            fig_res.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", 
                plot_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
                yaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
                margin=dict(l=10, r=10, t=10, b=10),
                font=dict(family="Plus Jakarta Sans", size=11)
            )
            st.plotly_chart(fig_res, use_container_width=True)

else:
    # Awaiting state screen visualization
    with st.container(border=True):
        st.markdown("""
            <div style="text-align:center; padding: 60px 40px;">
                <div style="font-size:3.5rem; margin-bottom: 20px;">⚡</div>
                <h3 style="color:#ffffff; margin-bottom: 10px;">Calibration Pipeline Idle</h3>
                <p style="color:#64748B; max-width: 500px; margin: 0 auto 25px auto;">
                    The robust scaling and parameter calibration pipeline is currently offline. Configure parameters in the sidebar to initiate model training.
                </p>
            </div>
        """, unsafe_allow_html=True)