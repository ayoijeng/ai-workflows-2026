"""Helpers for data quality, EDA, and visualizations in the Streamlit app."""

from __future__ import annotations

from typing import Any

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st


def compute_quality_metrics(df: pd.DataFrame) -> dict[str, Any]:
    """Return high-level data quality metrics for a DataFrame."""
    total_cells = df.size
    missing_cells = int(df.isna().sum().sum())
    duplicate_rows = int(df.duplicated().sum())
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    categorical_cols = df.select_dtypes(include=["object", "category", "string"]).columns.tolist()
    datetime_cols = df.select_dtypes(include=["datetime", "datetimetz"]).columns.tolist()
    constant_cols = [col for col in df.columns if df[col].nunique(dropna=False) <= 1]

    return {
        "rows": len(df),
        "columns": len(df.columns),
        "missing_cells": missing_cells,
        "missing_pct": round((missing_cells / total_cells * 100) if total_cells else 0, 2),
        "duplicate_rows": duplicate_rows,
        "duplicate_pct": round((duplicate_rows / len(df) * 100) if len(df) else 0, 2),
        "numeric_cols": len(numeric_cols),
        "categorical_cols": len(categorical_cols),
        "datetime_cols": len(datetime_cols),
        "constant_cols": constant_cols,
        "memory_mb": round(df.memory_usage(deep=True).sum() / 1024**2, 2),
    }


def column_quality_table(df: pd.DataFrame) -> pd.DataFrame:
    """Build a per-column quality summary table."""
    rows = []
    for col in df.columns:
        series = df[col]
        missing = int(series.isna().sum())
        rows.append(
            {
                "Column": col,
                "Type": str(series.dtype),
                "Non-Null": int(series.notna().sum()),
                "Missing": missing,
                "Missing %": round((missing / len(df) * 100) if len(df) else 0, 2),
                "Unique": int(series.nunique(dropna=True)),
                "Unique %": round((series.nunique(dropna=True) / len(df) * 100) if len(df) else 0, 2),
            }
        )
    return pd.DataFrame(rows)


def missing_values_chart(df: pd.DataFrame) -> alt.Chart | None:
    """Bar chart of missing value counts by column."""
    missing = df.isna().sum().reset_index()
    missing.columns = ["column", "missing_count"]
    missing = missing[missing["missing_count"] > 0].sort_values("missing_count", ascending=False)

    if missing.empty:
        return None

    return (
        alt.Chart(missing)
        .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
        .encode(
            x=alt.X("missing_count:Q", title="Missing values"),
            y=alt.Y("column:N", sort="-x", title="Column"),
            color=alt.Color("missing_count:Q", scale=alt.Scale(scheme="orangered"), legend=None),
            tooltip=["column", "missing_count"],
        )
        .properties(height=max(200, 28 * len(missing)), title="Missing Values by Column")
    )


def numeric_summary_table(df: pd.DataFrame) -> pd.DataFrame | None:
    """Descriptive statistics for numeric columns."""
    numeric_df = df.select_dtypes(include="number")
    if numeric_df.empty:
        return None
    return numeric_df.describe().T.round(2)


def categorical_summary_table(df: pd.DataFrame, top_n: int = 5) -> pd.DataFrame | None:
    """Top value counts for categorical columns."""
    cat_df = df.select_dtypes(include=["object", "category", "string"])
    if cat_df.empty:
        return None

    rows = []
    for col in cat_df.columns:
        counts = cat_df[col].value_counts(dropna=False).head(top_n)
        for value, count in counts.items():
            display_value = "<missing>" if pd.isna(value) else str(value)
            rows.append({"Column": col, "Value": display_value, "Count": int(count)})

    return pd.DataFrame(rows)


def correlation_heatmap(df: pd.DataFrame) -> alt.Chart | None:
    """Correlation heatmap for numeric columns."""
    numeric_df = df.select_dtypes(include="number")
    if numeric_df.shape[1] < 2:
        return None

    corr = numeric_df.corr().round(2)
    melted = corr.reset_index().melt(id_vars="index", var_name="column", value_name="correlation")
    melted = melted.rename(columns={"index": "row"})

    return (
        alt.Chart(melted)
        .mark_rect()
        .encode(
            x=alt.X("column:N", title=None),
            y=alt.Y("row:N", title=None),
            color=alt.Color(
                "correlation:Q",
                scale=alt.Scale(scheme="redblue", domain=[-1, 1]),
                title="Correlation",
            ),
            tooltip=["row", "column", "correlation"],
        )
        .properties(
            width=max(300, 40 * numeric_df.shape[1]),
            height=max(300, 40 * numeric_df.shape[1]),
            title="Numeric Correlation Matrix",
        )
    )


def distribution_chart(df: pd.DataFrame, column: str) -> alt.Chart | None:
    """Histogram for a numeric column or bar chart for categorical."""
    series = df[column].dropna()
    if series.empty:
        return None

    if pd.api.types.is_numeric_dtype(df[column]):
        chart_df = df[[column]].dropna()
        return (
            alt.Chart(chart_df)
            .mark_bar(opacity=0.85)
            .encode(
                x=alt.X(f"{column}:Q", bin=alt.Bin(maxbins=30), title=column),
                y=alt.Y("count()", title="Count"),
                tooltip=["count()"],
            )
            .properties(height=320, title=f"Distribution: {column}")
        )

    value_counts = (
        df[column]
        .fillna("<missing>")
        .astype(str)
        .value_counts()
        .head(15)
        .reset_index()
    )
    value_counts.columns = ["value", "count"]

    return (
        alt.Chart(value_counts)
        .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
        .encode(
            x=alt.X("count:Q", title="Count"),
            y=alt.Y("value:N", sort="-x", title=column),
            color=alt.Color("count:Q", scale=alt.Scale(scheme="teals"), legend=None),
            tooltip=["value", "count"],
        )
        .properties(height=max(280, 24 * len(value_counts)), title=f"Top Values: {column}")
    )


def scatter_chart(df: pd.DataFrame, x_col: str, y_col: str, color_col: str | None = None) -> alt.Chart | None:
    """Scatter plot for two numeric columns."""
    if not pd.api.types.is_numeric_dtype(df[x_col]) or not pd.api.types.is_numeric_dtype(df[y_col]):
        return None

    chart_df = df[[x_col, y_col]].dropna()
    if chart_df.empty:
        return None

    encoding: dict[str, Any] = {
        "x": alt.X(f"{x_col}:Q", title=x_col),
        "y": alt.Y(f"{y_col}:Q", title=y_col),
        "tooltip": [x_col, y_col],
    }
    if color_col and color_col in df.columns:
        chart_df = df[[x_col, y_col, color_col]].dropna()
        encoding["color"] = alt.Color(f"{color_col}:N", title=color_col)

    return (
        alt.Chart(chart_df)
        .mark_circle(size=60, opacity=0.7)
        .encode(**encoding)
        .properties(height=360, title=f"{y_col} vs {x_col}")
    )


def render_metric_row(metrics: dict[str, Any], prefix: str = "") -> None:
    """Render a row of KPI metrics."""
    cols = st.columns(5)
    labels = [
        ("Rows", f"{metrics['rows']:,}"),
        ("Columns", str(metrics["columns"])),
        ("Missing", f"{metrics['missing_pct']}%"),
        ("Duplicates", f"{metrics['duplicate_rows']:,}"),
        ("Memory", f"{metrics['memory_mb']} MB"),
    ]
    for col, (label, value) in zip(cols, labels):
        col.metric(f"{prefix}{label}" if prefix else label, value)


def compare_metrics(before: dict[str, Any], after: dict[str, Any]) -> pd.DataFrame:
    """Build a before/after comparison table for quality metrics."""
    return pd.DataFrame(
        {
            "Metric": ["Rows", "Columns", "Missing %", "Duplicate rows", "Memory (MB)"],
            "Before": [
                before["rows"],
                before["columns"],
                before["missing_pct"],
                before["duplicate_rows"],
                before["memory_mb"],
            ],
            "After": [
                after["rows"],
                after["columns"],
                after["missing_pct"],
                after["duplicate_rows"],
                after["memory_mb"],
            ],
            "Change": [
                after["rows"] - before["rows"],
                after["columns"] - before["columns"],
                round(after["missing_pct"] - before["missing_pct"], 2),
                after["duplicate_rows"] - before["duplicate_rows"],
                round(after["memory_mb"] - before["memory_mb"], 2),
            ],
        }
    )
