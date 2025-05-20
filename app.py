import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="HS Code Import/Export Analyzer", layout="wide")
st.title("📦 HS Code Import/Export Analyzer")
st.markdown("Upload one or more CSV files containing HS-level trade data. This tool will prepare data for visualization.")

uploaded_files = st.file_uploader("Upload your CSV file(s)", type=["csv"], accept_multiple_files=True)

metric = st.selectbox("Select Metric", ["value", "netWgt"])
level = st.radio("Select HS Level for Bar Charts", options=["HS4", "HS6"], horizontal=True)


def render_combined_sunburst_chart(all_data, metric):
    all_data['cmdCode'] = all_data['cmdCode'].astype(str)
    all_data['HS4'] = all_data['cmdCode'].str[:4]
    all_data['HS6'] = all_data['cmdCode'].str[:6]

    all_data['flowDesc'] = all_data['flowDesc'].str.lower()
    all_data['value'] = all_data.get('cifvalue', pd.NA).fillna(all_data.get('fobvalue', pd.NA))

    all_data['reporterDesc'] = all_data.get('reporterDesc', 'Unknown Country')
    all_data['reporterDesc'] = all_data['reporterDesc'].fillna('Unknown Country')
    all_data['countryFlow'] = all_data['reporterDesc'] + " (" + all_data['flowDesc'] + ")"

    grouped = all_data.groupby(['countryFlow', 'HS4', 'HS6'])[metric].sum().reset_index()

    fig = px.sunburst(
        grouped,
        path=['countryFlow', 'HS4', 'HS6'],
        values=metric,
        title="🌐 Combined Sunburst Chart – Import & Export by HS4 → HS6 (by Country)",
        color='countryFlow'
    )
    fig.update_traces(insidetextorientation='radial')
    st.plotly_chart(fig, use_container_width=True)


def render_bar_charts(df, metric, level):
    st.markdown(f"### 📊 Combined Stacked Bar Chart – {level} Breakdown for Importing and Exporting Countries")

    df['cmdCode'] = df['cmdCode'].astype(str)
    df['HS4'] = df['cmdCode'].str[:4]
    df['HS6'] = df['cmdCode'].str[:6]
    df['value'] = df.get('cifvalue', pd.NA).fillna(df.get('fobvalue', pd.NA))

    df['reporterDesc'] = df.get('reporterDesc', 'Unknown Country').fillna('Unknown Country')
    df['flowDesc'] = df['flowDesc'].str.lower()
    df['countryFlow'] = df['reporterDesc'] + " (" + df['flowDesc'] + ")"

    if level == "HS4":
        df = df[df['HS4'].str.len() == 4]
        selected = st.multiselect("Select HS4 Codes to Display", options=sorted(df['HS4'].unique()), default=[])
        if selected:
            df = df[df['HS4'].isin(selected)]
        grouped = df.groupby(['countryFlow', 'HS4'])[metric].sum().reset_index()
        color_col = 'HS4'
    else:
        df = df[df['HS6'].str.len() == 6]
        selected_hs4 = st.multiselect("Select HS4 Codes to View HS6 Within", options=sorted(df['HS4'].unique()), default=[])
        if selected_hs4:
            df = df[df['HS4'].isin(selected_hs4)]
        grouped = df.groupby(['countryFlow', 'HS6'])[metric].sum().reset_index()
        color_col = 'HS6'

    if not grouped.empty:
        fig = px.bar(
            grouped,
            x='countryFlow',
            y=metric,
            color=color_col,
            title=f"Importing and Exporting Countries – {level} Composition ({'USD' if metric == 'value' else 'kg'})",
            labels={'value': metric, color_col: f'{level} Code'},
            text_auto='.2s'
        )
        fig.update_layout(barmode='stack', xaxis_title="Country (Flow)", yaxis_title=f"{metric} ({'USD' if metric == 'value' else 'kg'})")
        st.plotly_chart(fig, use_container_width=True)


def render_percentage_stacked_bar(df, metric):
    st.markdown("### 📊 Percentage Stacked Bar Chart – HS4 Share within Each Country")

    df['cmdCode'] = df['cmdCode'].astype(str)
    df['HS4'] = df['cmdCode'].str[:4]
    df['value'] = df.get('cifvalue', pd.NA).fillna(df.get('fobvalue', pd.NA))

    df['reporterDesc'] = df.get('reporterDesc', 'Unknown Country').fillna('Unknown Country')
    df['flowDesc'] = df['flowDesc'].str.lower()
    df['countryFlow'] = df['reporterDesc'] + " (" + df['flowDesc'] + ")"

    df = df[df['HS4'].str.len() == 4]
    grouped = df.groupby(['countryFlow', 'HS4'])[metric].sum().reset_index()

    pivot = grouped.pivot_table(index='countryFlow', columns='HS4', values=metric, aggfunc='sum').fillna(0)
    percentage_df = pivot.div(pivot.sum(axis=1), axis=0).reset_index().melt(id_vars='countryFlow', var_name='HS4', value_name='percentage')
    percentage_df['percentage'] *= 100

    if not percentage_df.empty:
        fig = px.bar(
            percentage_df,
            x='countryFlow',
            y='percentage',
            color='HS4',
            title="Importing and Exporting Countries – HS4 Composition (Percentage)",
            labels={'percentage': 'Percentage (%)', 'HS4': 'HS4 Code'},
            text_auto='.1f'
        )
        fig.update_layout(barmode='stack', xaxis_title="Country (Flow)", yaxis_title="Percentage (%)")
        st.plotly_chart(fig, use_container_width=True)


if uploaded_files:
    all_data = []
    for file in uploaded_files:
        try:
            df = pd.read_csv(file)
            all_data.append(df)
        except Exception as e:
            st.error(f"Error processing {file.name}: {e}")

    if all_data:
        combined_df = pd.concat(all_data, ignore_index=True)
        render_combined_sunburst_chart(combined_df, metric)
        render_bar_charts(combined_df, metric, level)
        render_percentage_stacked_bar(combined_df, metric)
