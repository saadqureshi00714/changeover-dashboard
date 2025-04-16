import pandas as pd
import streamlit as st
import plotly.express as px

st.set_page_config(page_title="All Downtime Categories", layout="wide")
st.title("🛑 All Downtime Categories")

# Load and prepare data
file_path = "change_over_test.xlsx"
df = pd.read_excel(file_path)
df.columns = df.columns.str.strip().str.lower()

# Convert date and extract week + month
df['date'] = pd.to_datetime(df['date'])
df['week'] = df['date'].dt.isocalendar().week.astype(str)
df['month'] = df['date'].dt.to_period('M').astype(str)

# Filter only valid machines if needed
df = df[df['machine'].notna()]

# Define downtime categories and their labels
downtime_columns = {
    'subtotal.manpower': 'Manpower',
    'subtotal.pd': 'Planned',
    'subtotal.mb': 'Machine Breakdown',
    'subtotal.cb': 'Tool Breakdown',
    'subtotal.tb': 'Mould/Fixture Breakdown',
    'subtotal.qd': 'Quality Issue',
    'subtotal.wd': 'Warehousing Issue',
    'subtotal.o': 'Other'
}

# Sidebar filters
machines = sorted(df['machine'].dropna().unique())
selected_machine = st.sidebar.selectbox("Select Machine", ["All"] + machines)

if selected_machine != "All":
    df = df[df['machine'] == selected_machine]

# Melt data for category-wise plots
df_melted = df.melt(
    id_vars=['machine', 'date', 'week', 'month'],
    value_vars=list(downtime_columns.keys()),
    var_name='downtime_type', value_name='duration_min'
)
df_melted['downtime_type'] = df_melted['downtime_type'].map(downtime_columns)
df_melted['duration_hr'] = df_melted['duration_min'] / 60

# --- Chart 1: Total downtime by category + machine ---
st.subheader("📊 Total Downtime by Category and Machine")
fig1 = px.bar(
    df_melted.groupby(['machine', 'downtime_type'], as_index=False)['duration_hr'].sum(),
    x='machine', y='duration_hr', color='downtime_type',
    title='Total Downtime (Hours)',
    labels={'duration_hr': 'Downtime (hr)', 'downtime_type': 'Category'},
    barmode='stack'
)
st.plotly_chart(fig1, use_container_width=True)

# --- Chart 2: Weekly Trend ---
st.subheader("📈 Weekly Downtime Trend by Category")
fig2 = px.line(
    df_melted.groupby(['week', 'downtime_type'], as_index=False)['duration_hr'].sum(),
    x='week', y='duration_hr', color='downtime_type',
    title='Weekly Downtime Trend',
    labels={'duration_hr': 'Downtime (hr)', 'downtime_type': 'Category'}
)
st.plotly_chart(fig2, use_container_width=True)

# --- Chart 3: Monthly Trend ---
st.subheader("📅 Monthly Downtime Trend by Category")
fig3 = px.line(
    df_melted.groupby(['month', 'downtime_type'], as_index=False)['duration_hr'].sum(),
    x='month', y='duration_hr', color='downtime_type',
    title='Monthly Downtime Trend',
    labels={'duration_hr': 'Downtime (hr)', 'downtime_type': 'Category'}
)
st.plotly_chart(fig3, use_container_width=True)
