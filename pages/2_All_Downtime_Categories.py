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

# Define downtime categories and their labels with matching lowercase column names
downtime_columns = {
    'subtotal-manpower': 'Manpower',
    'subtotal.pd': 'Planned',
    'subtotal.mb': 'Machine Breakdown',
    'subtotal.cb': 'Tool Breakdown',
    'subtotal.tb': 'Mould/Fixture Breakdown',
    'subtotal.qd': 'Quality Issue',
    'subtotal.wd': 'Warehousing Issue',
    'subtotal.o': 'Other'
}

# Corresponding cause columns for multiple entries
all_cause_columns = {
    'Planned': ['cause.pd1', 'cause.pd2'],
    'Machine Breakdown': ['cause.mb1', 'cause.mb2'],
    'Tool Breakdown': ['cause.cb1', 'cause.cb2'],
    'Mould/Fixture Breakdown': ['cause.tb1', 'cause.tb2'],
    'Quality Issue': ['cause.qd1', 'cause.qd2'],
    'Warehousing Issue': ['end.wd12'],
    'Changeover': ['cause.co'],
    'Other': ['cause.o']
}

# Ensure all expected columns are in the dataframe
available_cols = [col for col in downtime_columns if col in df.columns]
downtime_labels = {col: downtime_columns[col] for col in available_cols}

# Sidebar filters
machines = sorted(df['machine'].dropna().unique())
months = sorted(df['month'].dropna().unique())
weeks = sorted(df['week'].dropna().unique())
selected_machine = st.sidebar.selectbox("Select Machine", ["All"] + machines)
selected_month = st.sidebar.selectbox("Select Month", ["All"] + months)
selected_week = st.sidebar.selectbox("Select Week", ["All"] + weeks)

if selected_machine != "All":
    df = df[df['machine'] == selected_machine]
if selected_month != "All":
    df = df[df['month'] == selected_month]
if selected_week != "All":
    df = df[df['week'] == selected_week]

# Melt data for category-wise plots
melt_cols = list(downtime_labels.keys())
df_melted = df.melt(
    id_vars=['machine', 'date', 'week', 'month'],
    value_vars=melt_cols,
    var_name='downtime_type', value_name='duration_min'
)
df_melted['downtime_type'] = df_melted['downtime_type'].map(downtime_labels)
df_melted['duration_hr'] = df_melted['duration_min'] / 60

# Combine cause columns into a raw comment field

def gather_comments(row):
    category = row['downtime_type']
    date = row['date']
    machine = row['machine']
    comments = []
    for col in all_cause_columns.get(category, []):
        if col in df.columns:
            matched = df.loc[(df['machine'] == machine) & (df['date'] == date), col]
            if not matched.empty:
                comment_val = matched.values[0]
                if pd.notna(comment_val):
                    comments.append(str(comment_val))
    return "; ".join(comments)

df_melted['comments'] = df_melted.apply(gather_comments, axis=1)

# --- Chart 1: Total downtime by category + machine ---
st.subheader("📊 Total Downtime by Category and Machine")
fig1 = px.bar(
    df_melted.groupby(['machine', 'downtime_type'], as_index=False).agg({'duration_hr': 'sum', 'comments': lambda x: ", ".join(set(x.dropna().astype(str)))}),
    x='machine', y='duration_hr', color='downtime_type',
    title='Total Downtime (Hours)',
    labels={'duration_hr': 'Downtime (hr)', 'downtime_type': 'Category'},
    barmode='stack',
    hover_data=['comments']
)
st.plotly_chart(fig1, use_container_width=True)

st.caption("🔤 Comments are shown in original language (Chinese). You can copy and translate using your preferred tool.")

# --- Chart 2: Weekly Trend ---
st.subheader("📈 Weekly Downtime Trend by Category")
fig2 = px.line(
    df_melted.groupby(['week', 'downtime_type'], as_index=False)['duration_hr'].sum(),
    x='week', y='duration_hr', color='downtime_type',
    title='Weekly Downtime Trend (Hours)',
    labels={'duration_hr': 'Downtime (hr)', 'downtime_type': 'Category'}
)
st.plotly_chart(fig2, use_container_width=True)

# --- Chart 3: Monthly Trend ---
st.subheader("📅 Monthly Downtime Trend by Category")
fig3 = px.line(
    df_melted.groupby(['month', 'downtime_type'], as_index=False)['duration_hr'].sum(),
    x='month', y='duration_hr', color='downtime_type',
    title='Monthly Downtime Trend (Hours)',
    labels={'duration_hr': 'Downtime (hr)', 'downtime_type': 'Category'}
)
st.plotly_chart(fig3, use_container_width=True)
