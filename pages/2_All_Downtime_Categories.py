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

# Precompute combined comments for each machine-date
comment_rows = []
for _, row in df.iterrows():
    comment_dict = {'machine': row['machine'], 'date': row['date']}
    for category, cause_list in all_cause_columns.items():
        combined_comment = "; ".join(str(row[c]) for c in cause_list if c in row and pd.notna(row[c]))
        comment_dict[category] = combined_comment
    comment_rows.append(comment_dict)
comments_df = pd.DataFrame(comment_rows)

# Melt data for category-wise plots
melt_cols = list(downtime_labels.keys())
df_melted = df.melt(
    id_vars=['machine', 'date', 'week', 'month'],
    value_vars=melt_cols,
    var_name='downtime_type', value_name='duration_min'
)
df_melted['downtime_type'] = df_melted['downtime_type'].map(downtime_labels)
df_melted['duration_hr'] = df_melted['duration_min'] / 60

# Merge comments from precomputed table
comments_df_long = comments_df.melt(id_vars=['machine', 'date'], var_name='downtime_type', value_name='comments')
df_melted = df_melted.merge(comments_df_long, on=['machine', 'date', 'downtime_type'], how='left')

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

# --- Chart 2: Weekly Downtime Composition (Pie) ---
st.subheader("📆 Weekly Downtime Composition")
df_week = df_melted.groupby('downtime_type', as_index=False)['duration_hr'].sum()
fig2 = px.pie(
    df_week,
    names='downtime_type', values='duration_hr',
    title='Weekly Downtime Distribution by Category'
)
st.plotly_chart(fig2, use_container_width=True)

# --- Chart 3: Monthly Downtime Composition (Pie) ---
st.subheader("🗓️ Monthly Downtime Composition")
df_month = df_melted.groupby('downtime_type', as_index=False)['duration_hr'].sum()
fig3 = px.pie(
    df_month,
    names='downtime_type', values='duration_hr',
    title='Monthly Downtime Distribution by Category'
)
st.plotly_chart(fig3, use_container_width=True)
