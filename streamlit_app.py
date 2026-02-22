import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import io

st.set_page_config(page_title="Restaurant Dashboard", layout="wide")
st.title("🍽️ Restaurant Analytics Dashboard")

# Sidebar - Google Sheets input
st.sidebar.header("📊 Data Source")
sheet_url = st.sidebar.text_input(
    "Paste Google Sheets URL", 
    "https://docs.google.com/spreadsheets/d/18INCpIytaYX9BSZRB5RisUj5EJb9CXkG/edit?gid=984125391"
)

if st.sidebar.button("🔄 Load Data", type="primary"):
    with st.spinner("Loading..."):
        try:
            # Convert to CSV export
            csv_url = sheet_url.replace("/edit", "/export?format=csv")
            df = pd.read_csv(csv_url)
            st.session_state.df = df
            st.sidebar.success(f"✅ Loaded {len(df)} rows, {len(df.columns)} columns")
            st.sidebar.json(df.dtypes.to_dict())
        except Exception as e:
            st.sidebar.error(f"❌ Error: {str(e)}")
            st.sidebar.info("💡 Make sheet 'Anyone with link can VIEW'")

if 'df' not in st.session_state:
    st.info("""
    👆 **Paste your Google Sheets URL in sidebar** and click "Load Data"
    
    **Your sheet must be public:** Share → "Anyone with link" → "Viewer"
    """)
    st.stop()

df = st.session_state.df.copy()
st.subheader("📋 Data Preview")
st.dataframe(df.head(10))

# Auto-detect datetime and numeric columns
st.subheader("🔍 Auto-Analysis")
date_cols = df.select_dtypes(include=['object']).columns[df.select_dtypes(include=['object']).apply(
    lambda x: pd.to_datetime(x, errors='coerce').notna().sum() > len(x)*0.5)]
num_cols = df.select_dtypes(include=[np.number]).columns.tolist()

if date_cols.empty or not num_cols:
    st.error("No suitable date/numeric columns found. Please check your data format.")
    st.stop()

# Use first date and numeric columns
df['date'] = pd.to_datetime(df[date_cols[0]], errors='coerce')
df['value'] = df[num_cols[0]]
df['date_only'] = df['date'].dt.date
df['hour'] = df['date'].dt.hour

filtered_df = df.dropna(subset=['date_only', 'value'])

# HEATMAPS
st.header("📈 Interactive Heatmaps")
col1, col2 = st.columns(2)

with col1:
    st.subheader("Hourly Heatmap")
    heatmap_data = filtered_df.groupby(['date_only', 'hour'])['value'].sum().reset_index()
    fig = px.density_heatmap(
        heatmap_data.head(1000), 
        x='hour', y='date_only', z='value',
        color_continuous_scale='Viridis',
        title="Activity by Hour"
    )
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("Daily Heatmap")
    daily_data = filtered_df.groupby('date_only')['value'].sum().reset_index()
    fig2 = px.density_heatmap(
        daily_data.tail(31).set_index('date_only').T,
        color_continuous_scale='Reds',
        title="Daily Trends (Last 30 days)"
    )
    st.plotly_chart(fig2, use_container_width=True)

# KPIs
st.header("📊 Key Metrics")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Records", f"{len(filtered_df):,}")
col2.metric("Total Value", f"₹{filtered_df['value'].sum():,.0f}")
col3.metric("Peak Hour", filtered_df.groupby('hour')['value'].sum().idxmax())
col4.metric("Peak Day", filtered_df.groupby('date_only')['value'].sum().idxmax().strftime('%Y-%m-%d'))

# Growth metrics
daily_metrics = filtered_df.groupby('date_only')['value'].sum().reset_index()
daily_metrics['dod'] = daily_metrics['value'].pct_change() * 100
st.subheader("📈 Day-over-Day Growth")
st.line_chart(daily_metrics.set_index('date_only')[['value', 'dod']])