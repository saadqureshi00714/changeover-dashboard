import pandas as pd
import streamlit as st
import plotly.express as px
import os

# ---------- STREAMLIT PASSWORD PROTECTION ----------

def check_password():
    def password_entered():
        if st.session_state["password"] == "ottimo123":
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input("Enter Password", type="password", on_change=password_entered, key="password")
        st.stop()
    elif not st.session_state["password_correct"]:
        st.text_input("Enter Password", type="password", on_change=password_entered, key="password")
        st.error("😕 Incorrect password")
        st.stop()

check_password()

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
    changeover_date = row['date']
    shift = row['shift']

    if pd.isna(last_part_code):
        continue

    if duration == 720 and machine == prev_machine and last_part_code == from_part and part_code == to_part:
        accumulated_duration += duration
        continue

    if accumulated_duration > 0:
        summary_data.append({
            'month': month,
            'machine': prev_machine,
            'from product': from_part,
            'to product': to_part,
            'changeover duration (hr)': round(accumulated_duration / 60, 1),
            'date': last_date,
            'shift': last_shift
        })

    prev_machine = machine
    from_part = last_part_code
    to_part = part_code
    accumulated_duration = duration
    month = current_month
    last_date = changeover_date
    last_shift = shift

if accumulated_duration > 0:
    summary_data.append({
        'month': month,
        'machine': prev_machine,
        'from product': from_part,
        'to product': to_part,
        'changeover duration (hr)': round(accumulated_duration / 60, 1),
        'date': last_date,
        'shift': last_shift
    })

summary_df = pd.DataFrame(summary_data)

# Add hover info
summary_df['hover_info'] = (
    "From: " + summary_df['from product'].astype(str) +
    "<br>To: " + summary_df['to product'].astype(str) +
    "<br>Date: " + summary_df['date'].astype(str) +
    "<br>Shift: " + summary_df['shift'].astype(str) +
    "<br>Duration: " + summary_df['changeover duration (hr)'].astype(str) + " hr"
)

# Monthly summary (in hours)
monthly_summary = summary_df.groupby(['month', 'machine'], as_index=False).agg(
    total_changeover_time_hr=('changeover duration (hr)', 'sum'),
    average_changeover_time_hr=('changeover duration (hr)', 'mean')
)

# ---------- STREAMLIT APP SECTION ----------

st.set_page_config(page_title="Changeover Dashboard", layout="wide")
st.title("📊 Changeover Summary Dashboard")

st.sidebar.header("🔎 Filters")

machines = sorted(summary_df['machine'].dropna().unique())
selected_machine = st.sidebar.selectbox("Select Machine", options=["All"] + machines)

months = sorted(summary_df['month'].dropna().unique())
selected_month = st.sidebar.selectbox("Select Month", options=["All"] + months)

# Filter data
filtered_summary = summary_df.copy()
filtered_monthly = monthly_summary.copy()

if selected_machine != "All":
    filtered_summary = filtered_summary[filtered_summary['machine'] == selected_machine]
    filtered_monthly = filtered_monthly[filtered_monthly['machine'] == selected_machine]

if selected_month != "All":
    filtered_summary = filtered_summary[filtered_summary['month'] == selected_month]
    filtered_monthly = filtered_monthly[filtered_monthly['month'] == selected_month]

# --- Monthly Charts ---
st.subheader("🔁 Total Changeover Time (Hours) by Machine")
fig_total = px.bar(
    filtered_monthly,
    x="machine", y="total_changeover_time_hr",
    color="machine",
    title="Total Changeover Time per Machine",
    text=filtered_monthly['total_changeover_time_hr'].round(1).astype(str) + " hr",
    hover_name="machine",
    hover_data={"total_changeover_time_hr": True}
)
st.plotly_chart(fig_total, use_container_width=True)

st.subheader("⏱️ Average Changeover Time (Hours) by Machine")
fig_avg = px.bar(
    filtered_monthly,
    x="machine", y="average_changeover_time_hr",
    color="machine",
    title="Average Changeover Time per Machine",
    text=filtered_monthly['average_changeover_time_hr'].round(1).astype(str) + " hr",
    hover_name="machine",
    hover_data={"average_changeover_time_hr": True}
)
st.plotly_chart(fig_avg, use_container_width=True)

# --- Detailed Event Chart ---
st.subheader("🔍 Product-Level Changeovers")
fig_product = px.bar(
    filtered_summary,
    x="machine", y="changeover duration (hr)",
    color="machine",
    title="Changeover Durations by Product Change",
    text=filtered_summary['changeover duration (hr)'].round(1).astype(str) + " hr",
    hover_name="machine",
    hover_data={"hover_info": True},
)
st.plotly_chart(fig_product, use_container_width=True)

# --- Show Table ---
st.subheader("📋 Changeover Event Table")
st.dataframe(filtered_summary)

# --- Download ---
st.download_button(
    "Download Filtered Data as CSV",
    data=filtered_summary.to_csv(index=False).encode(),
    file_name="changeover_filtered_summary.csv",
    mime="text/csv"
)
