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
    all_data['HS2'] = all_data['cmdCode'].str[:2]
    all_data['HS4'] = all_data['cmdCode'].str[:4]
    all_data['HS6'] = all_data['cmdCode'].str[:6]

    all_data['flowDesc'] = all_data['flowDesc'].str.lower()
    all_data['value'] = all_data.get('cifvalue', pd.NA).fillna(all_data.get('fobvalue', pd.NA))

    # Determine reporter country from each file
    all_data['reporterDesc'] = all_data.get('reporterDesc', 'Unknown Country')
    all_data['reporterDesc'] = all_data['reporterDesc'].fillna('Unknown Country')

    # Combine country and flow for root label
    all_data['countryFlow'] = all_data['reporterDesc'] + " (" + all_data['flowDesc'] + ")"

    grouped = all_data.groupby(['countryFlow', 'HS2', 'HS4', 'HS6'])[metric].sum().reset_index()

    fig = px.sunburst(
        grouped,
        path=['countryFlow', 'HS2', 'HS4', 'HS6'],
        values=metric,
        title="🌐 Combined Sunburst Chart – Import & Export by HS2 → HS4 → HS6 (by Country)",
        color='countryFlow'
    )
    fig.update_traces(insidetextorientation='radial')
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
