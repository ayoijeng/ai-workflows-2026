"""Streamlit interface for the Data Cleaning Agent."""

import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from data_cleaning_agent import LightweightDataCleaningAgent
from streamlit_helpers import (
    categorical_summary_table,
    column_quality_table,
    compare_metrics,
    compute_quality_metrics,
    correlation_heatmap,
    distribution_chart,
    missing_values_chart,
    numeric_summary_table,
    render_metric_row,
    scatter_chart,
)

load_dotenv()

st.set_page_config(
    page_title="Data Cleaning Agent",
    page_icon="🧹",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    div[data-testid="stMetricValue"] { font-size: 1.4rem; }
    .block-container { padding-top: 1.5rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

if "df_cleaned" not in st.session_state:
    st.session_state.df_cleaned = None
if "cleaning_done" not in st.session_state:
    st.session_state.cleaning_done = False


def reset_cleaning_state() -> None:
    st.session_state.df_cleaned = None
    st.session_state.cleaning_done = False


# --- Sidebar ---
with st.sidebar:
    st.header("Upload & Clean")
    uploaded_file = st.file_uploader("Upload a CSV file", type=["csv"])

    user_instructions = st.text_area(
        "Custom cleaning instructions (optional)",
        placeholder="e.g. Drop columns with >40% missing values and remove duplicate rows",
        height=100,
    )

    clean_clicked = st.button("Clean Data", type="primary", use_container_width=True)

    if st.session_state.cleaning_done and st.session_state.df_cleaned is not None:
        st.divider()
        csv = st.session_state.df_cleaned.to_csv(index=False)
        st.download_button(
            "Download Cleaned CSV",
            data=csv,
            file_name="cleaned_data.csv",
            mime="text/csv",
            use_container_width=True,
        )

    st.divider()
    st.caption("Upload a CSV to explore data quality, run EDA, and clean with AI.")


# --- Main content ---
st.title("🧹 Data Cleaning Agent")
st.caption("Explore your data, review quality issues, and clean it with an AI-powered agent.")

if uploaded_file is None:
    st.info("Upload a CSV file in the sidebar to get started.")
    st.stop()

# New upload resets cleaned output
upload_key = f"{uploaded_file.name}:{uploaded_file.size}"
if st.session_state.get("upload_key") != upload_key:
    st.session_state.upload_key = upload_key
    reset_cleaning_state()

df_raw = pd.read_csv(uploaded_file)
raw_metrics = compute_quality_metrics(df_raw)

st.success(f"Loaded **{uploaded_file.name}** — {raw_metrics['rows']:,} rows × {raw_metrics['columns']} columns")

render_metric_row(raw_metrics)

if raw_metrics["constant_cols"]:
    st.warning(
        f"Constant columns detected (single unique value): {', '.join(raw_metrics['constant_cols'])}"
    )

# --- Run cleaning ---
if clean_clicked:
    with st.spinner("AI agent is analyzing and cleaning your data..."):
        try:
            llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
            agent = LightweightDataCleaningAgent(model=llm, log=True)
            kwargs = {"data_raw": df_raw}
            if user_instructions.strip():
                kwargs["user_instructions"] = user_instructions.strip()
            agent.invoke_agent(**kwargs)
            st.session_state.df_cleaned = agent.get_data_cleaned()
            st.session_state.cleaning_done = True
            st.toast("Data cleaning complete!", icon="✅")
        except Exception as exc:
            st.error(f"Cleaning failed: {exc}")
            reset_cleaning_state()

# --- Tabs ---
tab_preview, tab_quality, tab_eda, tab_viz, tab_clean = st.tabs(
    ["📋 Preview", "🔍 Data Quality", "📊 EDA", "📈 Visualizations", "✨ Clean & Compare"]
)

with tab_preview:
    st.subheader("Data Preview")
    preview_rows = st.slider("Rows to preview", min_value=5, max_value=50, value=10, step=5)
    st.dataframe(df_raw.head(preview_rows), use_container_width=True, hide_index=True)

    st.subheader("Column Types")
    dtype_df = pd.DataFrame(
        {"Column": df_raw.columns, "Type": [str(dtype) for dtype in df_raw.dtypes]}
    )
    st.dataframe(dtype_df, use_container_width=True, hide_index=True)

with tab_quality:
    st.subheader("Column-Level Quality")
    st.dataframe(
        column_quality_table(df_raw),
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("Missing Values")
    missing_chart = missing_values_chart(df_raw)
    if missing_chart:
        st.altair_chart(missing_chart, use_container_width=True)
    else:
        st.success("No missing values found.")

    col_a, col_b = st.columns(2)
    with col_a:
        st.metric("Duplicate rows", f"{raw_metrics['duplicate_rows']:,}")
        st.metric("Numeric columns", raw_metrics["numeric_cols"])
    with col_b:
        st.metric("Missing cell rate", f"{raw_metrics['missing_pct']}%")
        st.metric("Categorical columns", raw_metrics["categorical_cols"])

with tab_eda:
    st.subheader("Numeric Summary")
    numeric_summary = numeric_summary_table(df_raw)
    if numeric_summary is not None:
        st.dataframe(numeric_summary, use_container_width=True)
    else:
        st.info("No numeric columns detected.")

    st.subheader("Categorical Value Counts (Top 5 per column)")
    cat_summary = categorical_summary_table(df_raw)
    if cat_summary is not None:
        st.dataframe(cat_summary, use_container_width=True, hide_index=True)
    else:
        st.info("No categorical columns detected.")

    st.subheader("Correlation Matrix")
    corr_chart = correlation_heatmap(df_raw)
    if corr_chart:
        st.altair_chart(corr_chart, use_container_width=True)
    else:
        st.info("Need at least two numeric columns for a correlation matrix.")

with tab_viz:
    st.subheader("Explore Columns")

    all_columns = df_raw.columns.tolist()
    numeric_columns = df_raw.select_dtypes(include="number").columns.tolist()

    col_left, col_right = st.columns(2)

    with col_left:
        dist_col = st.selectbox("Distribution column", all_columns, key="dist_col")
        dist_chart = distribution_chart(df_raw, dist_col)
        if dist_chart:
            st.altair_chart(dist_chart, use_container_width=True)

    with col_right:
        if len(numeric_columns) >= 2:
            x_col = st.selectbox("Scatter X", numeric_columns, index=0, key="scatter_x")
            y_col = st.selectbox(
                "Scatter Y",
                numeric_columns,
                index=min(1, len(numeric_columns) - 1),
                key="scatter_y",
            )
            color_options = ["None"] + all_columns
            color_col = st.selectbox("Color by (optional)", color_options, key="scatter_color")
            color_col = None if color_col == "None" else color_col
            scatter = scatter_chart(df_raw, x_col, y_col, color_col)
            if scatter:
                st.altair_chart(scatter, use_container_width=True)
        else:
            st.info("Select at least two numeric columns for a scatter plot.")

with tab_clean:
    st.subheader("AI Data Cleaning")

    if not st.session_state.cleaning_done or st.session_state.df_cleaned is None:
        st.info("Click **Clean Data** in the sidebar to run the AI cleaning agent.")
        st.markdown(
            """
            The agent will:
            1. Analyze your dataset structure and quality issues
            2. Generate custom Python cleaning code
            3. Execute the code and retry on errors (up to 3 attempts)
            """
        )
    else:
        df_cleaned = st.session_state.df_cleaned
        cleaned_metrics = compute_quality_metrics(df_cleaned)

        st.success("Cleaning complete! Review the before/after comparison below.")

        st.subheader("Before vs After")
        comparison = compare_metrics(raw_metrics, cleaned_metrics)
        st.dataframe(comparison, use_container_width=True, hide_index=True)

        st.subheader("Quality Metrics")
        metric_cols = st.columns(2)
        with metric_cols[0]:
            st.markdown("**Before cleaning**")
            render_metric_row(raw_metrics)
        with metric_cols[1]:
            st.markdown("**After cleaning**")
            render_metric_row(cleaned_metrics)

        st.subheader("Missing Values Comparison")
        compare_cols = st.columns(2)
        with compare_cols[0]:
            st.caption("Before")
            before_missing = missing_values_chart(df_raw)
            if before_missing:
                st.altair_chart(before_missing, use_container_width=True)
            else:
                st.success("No missing values.")
        with compare_cols[1]:
            st.caption("After")
            after_missing = missing_values_chart(df_cleaned)
            if after_missing:
                st.altair_chart(after_missing, use_container_width=True)
            else:
                st.success("No missing values.")

        st.subheader("Cleaned Data Preview")
        st.dataframe(df_cleaned.head(10), use_container_width=True, hide_index=True)
