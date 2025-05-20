import streamlit as st
import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt

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

    all_data['reporterDesc'] = all_data.get('reporterDesc', 'Unknown Country')
    all_data['reporterDesc'] = all_data['reporterDesc'].fillna('Unknown Country')
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


def render_stacked_bar_charts(df, metric):
    st.markdown("### 📊 Stacked Bar Chart – HS2 Trade Value by Country and Flow")

    grouped = df.groupby(['reporterDesc', 'flowDesc', 'HS2'])[metric].sum().reset_index()
    pivot_abs = grouped.pivot_table(index='HS2', columns=['reporterDesc', 'flowDesc'], values=metric, aggfunc='sum').fillna(0)

    fig1, ax1 = plt.subplots(figsize=(14, 7))
    pivot_abs.plot(kind='bar', stacked=True, ax=ax1)
    ax1.set_title("Absolute Trade Value by HS2", fontsize=14)
    ax1.set_ylabel(metric)
    ax1.set_xlabel("HS2 Code")
    ax1.legend(title="Country / Flow", bbox_to_anchor=(1.05, 1), loc='upper left')
    st.pyplot(fig1)

    st.markdown("### 📊 Percentage Stacked Bar Chart – Share by HS2")

    pivot_pct = pivot_abs.div(pivot_abs.sum(axis=1), axis=0) * 100
    fig2, ax2 = plt.subplots(figsize=(14, 7))
    pivot_pct.plot(kind='bar', stacked=True, ax=ax2)
    ax2.set_title("Percentage Share by HS2", fontsize=14)
    ax2.set_ylabel("Percentage (%)")
    ax2.set_xlabel("HS2 Code")
    ax2.legend(title="Country / Flow", bbox_to_anchor=(1.05, 1), loc='upper left')
    st.pyplot(fig2)


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
        render_stacked_bar_charts(combined_df, metric)
