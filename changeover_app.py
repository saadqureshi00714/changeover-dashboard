import pandas as pd
import streamlit as st
import plotly.express as px
import os

# ---------- DATA PROCESSING SECTION ----------

# ---------- DATA PROCESSING SECTION ----------

# Load the original Excel file
file_path = "change_over_test.xlsx"
df = pd.read_excel(file_path)
df.columns = df.columns.str.strip().str.lower()

# Convert date and create month
df['date'] = pd.to_datetime(df['date'])
df['month'] = df['date'].dt.to_period('M').astype(str)

# Optional: filter workshop
if 'workshop' in df.columns:
    df = df[df['workshop'].str.upper() == 'CNC']

# Sort data for reference
df = df.sort_values(by=['machine', 'date', 'shift']).reset_index(drop=True)

# Create 'last part code' manually
df['last part code'] = None
for i in range(1, len(df)):
    if df.loc[i, 'machine'] == df.loc[i - 1, 'machine'] and df.loc[i - 1, 'subtotal.co'] == 0:
        df.loc[i, 'last part code'] = df.loc[i - 1, 'part code']

# Now filter and generate changeover summary
df = df.sort_values(by=['month', 'machine', 'date', 'shift']).reset_index(drop=True)

summary_data = []
prev_machine, from_part, to_part, month = None, None, None, None
accumulated_duration = 0

for idx, row in df.iterrows():
    machine = row['machine']
    part_code = row['part code']
    last_part_code = row['last part code']
    duration = row['subtotal.co']
    current_month = row['month']

    if pd.isna(last_part_code):
        continue  # Skip rows where we don't have a previous part reference

    if duration == 720 and machine == prev_machine and last_part_code == from_part and part_code == to_part:
        accumulated_duration += duration
        continue

    if accumulated_duration > 0:
        summary_data.append({
            'month': month,
            'machine': prev_machine,
            'from product': from_part,
            'to product': to_part,
            'changeover duration (min)': accumulated_duration
        })

    prev_machine = machine
    from_part = last_part_code
    to_part = part_code
    accumulated_duration = duration
    month = current_month

# Append the last block
if accumulated_duration > 0:
    summary_data.append({
        'month': month,
        'machine': prev_machine,
        'from product': from_part,
        'to product': to_part,
        'changeover duration (min)': accumulated_duration
    })

summary_df = pd.DataFrame(summary_data)

# Monthly summary (in hours)
monthly_summary = summary_df.groupby(['month', 'machine'], as_index=False).agg(
    total_changeover_time_hr=('changeover duration (min)', lambda x: round(x.sum() / 60, 2)),
    average_changeover_time_hr=('changeover duration (min)', lambda x: round(x.mean() / 60, 2))
)

# ---------- STREAMLIT APP SECTION ----------

st.set_page_config(page_title="Changeover Dashboard", layout="wide")
st.title("📊 Changeover Summary Dashboard")

# Sidebar filters
st.sidebar.header("🔎 Filters")

# Machine filter
machines = sorted(summary_df['machine'].dropna().unique())
selected_machine = st.sidebar.selectbox("Select Machine", options=["All"] + machines)

# Month filter
months = sorted(summary_df['month'].dropna().unique())
selected_month = st.sidebar.selectbox("Select Month", options=["All"] + months)

# Apply filters to summary_df
filtered_summary = summary_df.copy()
filtered_monthly = monthly_summary.copy()

if selected_machine != "All":
    filtered_summary = filtered_summary[filtered_summary['machine'] == selected_machine]
    filtered_monthly = filtered_monthly[filtered_monthly['machine'] == selected_machine]

if selected_month != "All":
    filtered_summary = filtered_summary[filtered_summary['month'] == selected_month]
    filtered_monthly = filtered_monthly[filtered_monthly['month'] == selected_month]

# --- Charts ---
st.subheader("🔁 Total Changeover Time (Hours) by Machine")
fig_total = px.bar(
    filtered_monthly,
    x="machine", y="total_changeover_time_hr",
    color="machine", title="Total Changeover Time per Machine",
    text="total_changeover_time_hr"
)
st.plotly_chart(fig_total, use_container_width=True)

st.subheader("⏱️ Average Changeover Time (Hours) by Machine")
fig_avg = px.bar(
    filtered_monthly,
    x="machine", y="average_changeover_time_hr",
    color="machine", title="Average Changeover Time per Machine",
    text="average_changeover_time_hr"
)
st.plotly_chart(fig_avg, use_container_width=True)

# --- Optional: Show Table ---
st.subheader("📋 Changeover Event Table")
st.dataframe(filtered_summary)

# --- Optional: Download ---
st.download_button(
    "Download Filtered Data as CSV",
    data=filtered_summary.to_csv(index=False).encode(),
    file_name="changeover_filtered_summary.csv",
    mime="text/csv"
)
