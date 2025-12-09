"""Visualization utilities for F1 Analytics.

This module provides clean interfaces for creating charts and visualizations,
separating presentation logic from business logic.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Optional


def render_bar_chart(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    title: Optional[str] = None,
    color: Optional[str] = None
) -> go.Figure:
    """Create a bar chart with proper configuration.

    Args:
        df: DataFrame with data to plot
        x_col: Column name for x-axis
        y_col: Column name for y-axis
        title: Optional chart title
        color: Optional color scheme

    Returns:
        Plotly figure object
    """
    fig = px.bar(df, x=x_col, y=y_col, title=title, color=color)
    fig.update_layout(
        xaxis_title=x_col.replace('_', ' ').title(),
        yaxis_title=y_col.replace('_', ' ').title(),
        hovermode='x unified'
    )
    return fig


def render_line_chart(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    title: Optional[str] = None,
    color: Optional[str] = None
) -> go.Figure:
    """Create a line chart with proper configuration.

    Args:
        df: DataFrame with data to plot
        x_col: Column name for x-axis
        y_col: Column name for y-axis
        title: Optional chart title
        color: Optional color for grouping lines

    Returns:
        Plotly figure object
    """
    fig = px.line(df, x=x_col, y=y_col, title=title, color=color, markers=True)
    fig.update_layout(
        xaxis_title=x_col.replace('_', ' ').title(),
        yaxis_title=y_col.replace('_', ' ').title(),
        hovermode='x unified'
    )
    return fig


def render_scatter_plot(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    title: Optional[str] = None,
    color: Optional[str] = None,
    size: Optional[str] = None
) -> go.Figure:
    """Create a scatter plot with proper configuration.

    Args:
        df: DataFrame with data to plot
        x_col: Column name for x-axis
        y_col: Column name for y-axis
        title: Optional chart title
        color: Optional color for grouping points
        size: Optional size for bubble chart

    Returns:
        Plotly figure object
    """
    fig = px.scatter(df, x=x_col, y=y_col, title=title, color=color, size=size)
    fig.update_layout(
        xaxis_title=x_col.replace('_', ' ').title(),
        yaxis_title=y_col.replace('_', ' ').title(),
        hovermode='closest'
    )
    return fig


def display_visualization(
    df: pd.DataFrame,
    viz_type: str,
    title: Optional[str] = None
) -> None:
    """Display visualization based on type.

    Automatically selects appropriate columns and renders the visualization.

    Args:
        df: DataFrame with data to visualize
        viz_type: Type of visualization ("Table", "Bar Chart", "Line Chart", "Scatter Plot")
        title: Optional title for the visualization
    """
    if df.empty:
        st.warning("No data to display")
        return

    if viz_type == "Table":
        st.dataframe(df, use_container_width=True)

    elif viz_type == "Bar Chart":
        # Use first column as x-axis, last column as y-axis
        x_col = df.columns[0]
        y_col = df.columns[-1]
        fig = render_bar_chart(df, x_col, y_col, title)
        st.plotly_chart(fig, use_container_width=True)

    elif viz_type == "Line Chart":
        x_col = df.columns[0]
        y_col = df.columns[-1]
        fig = render_line_chart(df, x_col, y_col, title)
        st.plotly_chart(fig, use_container_width=True)

    elif viz_type == "Scatter Plot":
        if len(df.columns) < 2:
            st.error("Scatter plot requires at least 2 columns")
            return

        # Use first two numeric columns
        x_col = df.columns[1] if len(df.columns) > 1 else df.columns[0]
        y_col = df.columns[2] if len(df.columns) > 2 else df.columns[-1]
        fig = render_scatter_plot(df, x_col, y_col, title)
        st.plotly_chart(fig, use_container_width=True)
