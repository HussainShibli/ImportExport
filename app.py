import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="HS Code Import/Export Analyzer", layout="wide")
st.title("📦 HS Code Import/Export Analyzer")
st.markdown("Upload one or more CSV files containing HS-level trade data. This tool will prepare data for visualization.")

uploaded_files = st.file_uploader("Upload your CSV file(s)", type=["csv"], accept_multiple_files=True)

metric = st.selectbox("Select Metric", ["value", "netWgt"])


def render_combined_stacked_bar(df, metric):
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
        render_combined_stacked_bar(combined_df, metric)
