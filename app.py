import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")

st.title("📦 Import/Export Analysis by HS Code Level")

uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)

    # Detect if it's import or export
    flow_type = df['flowDesc'].iloc[0] if 'flowDesc' in df.columns else 'Unknown'

    # User HS level selection
    hs_level = st.radio("Choose HS Code Level:", options=["HS4", "HS6"])

    hs_col = 'cmdCode'
    if hs_level == "HS4":
        df['hs_selected'] = df['cmdCode'].astype(str).str[:4]
    else:
        df['hs_selected'] = df['cmdCode'].astype(str).str[:6]

    df['period'] = df['period'].astype(str)
    df['year'] = df['period'].str[:4]

    group_cols = ['year', 'hs_selected']
    value_cols = ['netWgt', 'cifvalue', 'fobvalue']
    existing_value_cols = [col for col in value_cols if col in df.columns]

    # Aggregate data
    agg_df = df.groupby(group_cols)[existing_value_cols].sum().reset_index()

    # Total value for charting
    agg_df['value'] = agg_df[existing_value_cols[0]]

    # Pivot for stacked bar chart
    pivot_df = agg_df.pivot_table(index='year', columns='hs_selected', values='value', aggfunc='sum').fillna(0)

    # Absolute values
    st.markdown("### 📊 Yearly Absolute Bar Chart – HS Code Breakdown")
    abs_chart = px.bar(
        pivot_df,
        x=pivot_df.index,
        y=pivot_df.columns,
        labels={'value': 'Value', 'year': 'Year'},
        title=f"{flow_type} Value by {hs_level} – Absolute"
    )
    st.plotly_chart(abs_chart, use_container_width=True)

    # Percent stacked bar
    st.markdown("### 📊 Yearly Percentage Stacked Bar Charts – HS Code Share")
    pct_df = pivot_df.div(pivot_df.sum(axis=1), axis=0) * 100
    pct_chart = px.bar(
        pct_df,
        x=pct_df.index,
        y=pct_df.columns,
        labels={'value': 'Percentage', 'year': 'Year'},
        title=f"{flow_type} Share by {hs_level} – Percentage",
    )
    st.plotly_chart(pct_chart, use_container_width=True)

    # Add contextual info
    st.markdown("---")
    st.markdown(f"**Flow Type:** {flow_type}")
    importing = df['rtTitle'].iloc[0] if 'rtTitle' in df.columns else 'N/A'
    exporting = df['ptTitle'].iloc[0] if 'ptTitle' in df.columns else 'N/A'
    st.markdown(f"**Importing Country:** {importing} | **Exporting Country:** {exporting}")
    st.markdown(f"**HS Level Selected:** {hs_level}")
