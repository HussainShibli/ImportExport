import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="HS Code Import/Export Analyzer", layout="wide")
st.title("📦 HS Code Import/Export Analyzer")
st.markdown("Upload one or more CSV files containing HS-level trade data. This tool will prepare data for visualization.")

uploaded_files = st.file_uploader("Upload your CSV file(s)", type=["csv"], accept_multiple_files=True)

metric = st.selectbox("Select Metric", ["value", "netWgt"])


def render_sunburst_chart(df, metric):
    df['cmdCode'] = df['cmdCode'].astype(str)
    df['HS2'] = df['cmdCode'].str[:2]
    df['HS4'] = df['cmdCode'].str[:4]
    df['HS6'] = df['cmdCode'].str[:6]

    df['flowDesc'] = df['flowDesc'].str.lower()
    df['value'] = df.get('cifvalue', pd.NA).fillna(df.get('fobvalue', pd.NA))

    grouped = df.groupby(['flowDesc', 'HS2', 'HS4', 'HS6'])[metric].sum().reset_index()

    fig = px.sunburst(
        grouped,
        path=['flowDesc', 'HS2', 'HS4', 'HS6'],
        values=metric,
        title="🌐 Sunburst Chart – Import & Export by HS2 → HS4 → HS6",
        color='flowDesc'
    )
    fig.update_traces(insidetextorientation='radial')
    st.plotly_chart(fig, use_container_width=True)


if uploaded_files:
    for file in uploaded_files:
        try:
            df = pd.read_csv(file)
            st.subheader(f"📁 {file.name}")
            st.write("Detected columns:", df.columns.tolist())
            render_sunburst_chart(df, metric)
        except Exception as e:
            st.error(f"Error processing {file.name}: {e}")
