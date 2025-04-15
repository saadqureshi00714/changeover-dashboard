import pandas as pd
import streamlit as st
import plotly.express as px

# Load the data
event_df = pd.read_excel("C:/Users/SaadQureshi/Documents/oee-changeovers/changeover_event_summary.xlsx")
monthly_df = pd.read_excel("C:/Users/SaadQureshi/Documents/oee-changeovers/monthly_machine_summary.xlsx")

# Page title
st.title("Changeover Summary Dashboard")

# Filter by month
selected_month = st.selectbox("Select Month", sorted(monthly_df['month'].unique()))
filtered_monthly = monthly_df[monthly_df['month'] == selected_month]

# Display bar chart of average changeover time by machine
st.subheader(f"Average Changeover Time (Hours) – {selected_month}")
fig = px.bar(filtered_monthly, x='machine', y='average_changeover_time_hr',
             title="Avg Changeover Time per Machine", text='average_changeover_time_hr')
st.plotly_chart(fig, use_container_width=True)

# Display summary text
st.subheader("Summary Lines")
for line in filtered_monthly['summary_line']:
    st.markdown(f"- {line}")

# Show raw data (optional toggle)
if st.checkbox("Show Raw Event Data"):
    st.write(event_df)
