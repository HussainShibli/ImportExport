import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="HS Code Import/Export Analyzer", layout="wide")
st.title("📦 HS Code Import/Export Analyzer")
st.markdown("Upload one or more CSV files containing HS-level trade data. This tool will prepare data for visualization.")

uploaded_files = st.file_uploader("Upload your CSV file(s)", type=["csv"], accept_multiple_files=True)

metric = st.selectbox("Select Metric", ["value", "netWgt"])


def render_combined_sunburst(df, metric):
    st.markdown("### 🌐 Sunburst Chart – HS4 → HS6 Breakdown by Country")
    df['cmdCode'] = df['cmdCode'].astype(str)
    df['HS4'] = df['cmdCode'].str[:4]
    df['HS6'] = df['cmdCode'].str[:6]
    df['value'] = df.get('cifvalue', pd.NA).fillna(df.get('fobvalue', pd.NA))
    df['reporterDesc'] = df.get('reporterDesc', 'Unknown Country').fillna('Unknown Country')
    df['flowDesc'] = df.get('flowDesc', '').str.lower()
    df['countryFlow'] = df['reporterDesc'] + " (" + df['flowDesc'] + ")"

    grouped = df.groupby(['countryFlow', 'HS4', 'HS6'])[metric].sum().reset_index()

    fig = px.sunburst(
        grouped,
        path=['countryFlow', 'HS4', 'HS6'],
        values=metric,
        color='countryFlow',
        title=f"Combined Sunburst – HS4 to HS6 by Country ({'USD' if metric == 'value' else 'kg'})"
    )
    fig.update_traces(insidetextorientation='radial')
    st.plotly_chart(fig, use_container_width=True)

def render_combined_stacked_bar(df, metric):
    st.markdown("### 📊 Percentage Stacked Bar Chart – HS4 Share within Each Country")
    df['cmdCode'] = df['cmdCode'].astype(str)
    df['HS4'] = df['cmdCode'].str[:4]
    df['value'] = df.get('cifvalue', pd.NA).fillna(df.get('fobvalue', pd.NA))
    df['reporterDesc'] = df.get('reporterDesc', 'Unknown Country').fillna('Unknown Country')
    df['flowDesc'] = df.get('flowDesc', '').str.lower()
    df['countryFlow'] = df['reporterDesc'] + " (" + df['flowDesc'] + ")"
    df = df[df['HS4'].str.len() == 4]

    grouped = df.groupby(['countryFlow', 'HS4'])[metric].sum().reset_index()

    pivot = grouped.pivot(index='countryFlow', columns='HS4', values=metric).fillna(0)
    percent_df = pivot.div(pivot.sum(axis=1), axis=0).reset_index().melt(id_vars='countryFlow', var_name='HS4', value_name='percentage')
    percent_df['percentage'] *= 100

    if not percent_df.empty:
        fig = px.bar(
            percent_df,
            x='countryFlow',
            y='percentage',
            color='HS4',
            title=f"Importing and Exporting Countries – HS4 Share (Percentage)",
            labels={'percentage': 'Percentage (%)', 'HS4': 'HS4 Code'},
            text_auto='.1f'
        )
        fig.update_layout(barmode='stack', xaxis_title="Country (Flow)", yaxis_title="Percentage (%)")
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("### 📊 Combined Stacked Bar Chart – HS4 Breakdown for Importing and Exporting Countries")

    df['cmdCode'] = df['cmdCode'].astype(str)
    df['HS4'] = df['cmdCode'].str[:4]
    df['value'] = df.get('cifvalue', pd.NA).fillna(df.get('fobvalue', pd.NA))
    df['reporterDesc'] = df.get('reporterDesc', 'Unknown Country').fillna('Unknown Country')
    df['flowDesc'] = df.get('flowDesc', '').str.lower()
    df['countryFlow'] = df['reporterDesc'] + " (" + df['flowDesc'] + ")"
    df = df[df['HS4'].str.len() == 4]

    grouped = df.groupby(['countryFlow', 'HS4'])[metric].sum().reset_index()

    if not grouped.empty:
        fig = px.bar(
            grouped,
            x='countryFlow',
            y=metric,
            color='HS4',
            title=f"Importing and Exporting Countries – HS4 Composition ({'USD' if metric == 'value' else 'kg'})",
            labels={'value': metric, 'HS4': 'HS4 Code'},
            text_auto='.2s'
        )
        fig.update_layout(barmode='stack', xaxis_title="Country (Flow)", yaxis_title=f"{metric} ({'USD' if metric == 'value' else 'kg'})")
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
        render_combined_sunburst(combined_df, metric)
        render_combined_stacked_bar(combined_df, metric)
