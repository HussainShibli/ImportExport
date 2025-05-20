import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="HS Code Import/Export Analyzer", layout="wide")
st.title("📦 HS Code Import/Export Analyzer")
st.markdown("Upload one or more CSV files containing HS-level trade data. This tool will prepare data for visualization.")

uploaded_files = st.file_uploader("Upload your CSV file(s)", type=["csv"], accept_multiple_files=True)

metric = st.selectbox("Select Metric", ["value", "netWgt"])


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


def render_combined_hs4_stacked_bar(df, metric):
    st.markdown("### 📊 Combined Stacked Bar Chart – HS4 Breakdown for Importing and Exporting Countries")

    df['cmdCode'] = df['cmdCode'].astype(str)
    df['HS4'] = df['cmdCode'].str[:4]
    df['value'] = df.get('cifvalue', pd.NA).fillna(df.get('fobvalue', pd.NA))

    df['reporterDesc'] = df.get('reporterDesc', 'Unknown Country').fillna('Unknown Country')
    df['flowDesc'] = df['flowDesc'].str.lower()

    df['countryFlow'] = df['reporterDesc'] + " (" + df['flowDesc'] + ")"

    grouped = df.groupby(['countryFlow', 'HS4'])[metric].sum().reset_index()

    if not grouped.empty:
        fig = px.bar(
            grouped,
            x='countryFlow',
            y=metric,
            color='HS4',
            title=f"Importing and Exporting Countries – HS4 Composition ({metric})",
            labels={'value': metric, 'HS4': 'HS4 Code'},
            text_auto='.2s'
        )
        fig.update_layout(barmode='stack', xaxis_title="Country (Flow)", yaxis_title=metric)
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
        render_combined_hs4_stacked_bar(combined_df, metric)
