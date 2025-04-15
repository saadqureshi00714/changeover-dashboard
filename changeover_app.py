import pandas as pd
import streamlit as st
import plotly.express as px
import os

# ---------- DATA PROCESSING SECTION ----------

# Load the original Excel file
file_path = "change_over_test.xlsx"
df = pd.read_excel(file_path)
df.columns = df.columns.str.strip().str.lower()

# Convert date and create month
df['date'] = pd.to_datetime(df['date'])
df['month'] = df['date'].dt.to_period('M').astype(str)

# Filter only CNC workshop (optional – remove if not needed)
if 'workshop' in df.columns:
    df = df[df['workshop'].str.upper() == 'CNC']

# Sort for processing
df = df.sort_values(by=['month', 'machine', 'date', 'shift']).reset_index(drop=True)

# Generate changeover event summary
summary_data = []
prev_machine, from_part, to_part, month = None, None, None, None
accumulated_duration = 0

for idx, row in df.iterrows():
    machine = row['machine']
    part_code = row['part code']
    last_part_code = row['last part code']
    duration = row['subtotal.co']
    current_month = row['month']

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

# Append the last changeover
if accumulated_duration > 0:
    summary_data.append({
        'month': month,
        'machine': prev_machine,
        'from product': from_part,
        'to product': to_part,
        'changeover duration (min)': accumulated_duration
    })

# Convert to DataFrame
summary_df = pd.DataFrame(summary_data)

# Calculate monthly summary
monthly_summary = summary_df.groupby(['month', 'machine'], as_index=False).agg(
    total_changeover_time_hr=('changeover duration (min)', lambda x: round(x.sum() / 60, 2)),
    average_changeover_time_hr=('changeover duration (min)', lambda x: round(x.mean() / 60, 2))
)

# ---------- STREAMLIT APP SECTION ----------

st.set_page_config(page_title="Changeover Dashboard", layout="wide")
st.title("📊 Changeover Summary Dashboard")

# Machine filter
machines = sorted(summary_df['machine'].dropna().unique())
selected_machine = st.selectbox("Select a Machine", options=["All"] + machines)

# Filter data
filtered_summary = summary_df.copy()
filtered_monthly = monthly_summary.copy()
if selected_machine != "All":
    filtered_summary = summary_df[summary_df['machine'] == selected_machine]
    filtered_monthly = monthly_summary[monthly_summary['machine'] == selected_machine]

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
    "Download Event Data as Excel",
    data=filtered_summary.to_csv(index=False).encode(),
    file_name="changeover_event_summary.csv",
    mime="text/csv"
)
