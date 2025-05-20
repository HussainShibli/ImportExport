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


def render_hs4_share_bar_chart(df, metric):
    st.markdown("### 📊 Percentage Share of HS4 within HS2 – by Country")

    df['cmdCode'] = df['cmdCode'].astype(str)
    df['HS2'] = df['cmdCode'].str[:2]
    df['HS4'] = df['cmdCode'].str[:4]
    df['value'] = df.get('cifvalue', pd.NA).fillna(df.get('fobvalue', pd.NA))

    df['reporterDesc'] = df.get('reporterDesc', 'Unknown Country').fillna('Unknown Country')
    grouped = df.groupby(['reporterDesc', 'HS2', 'HS4'])[metric].sum().reset_index()

    pivot = grouped.pivot_table(index=['HS2', 'HS4'], columns='reporterDesc', values=metric, aggfunc='sum').fillna(0)

    percentage_pivot = pivot.groupby(level=0).apply(lambda x: x.div(x.sum(axis=0), axis=1)) * 100

    for hs2_code in percentage_pivot.index.levels[0]:
        hs4_subset = percentage_pivot.loc[hs2_code]
        fig, ax = plt.subplots(figsize=(12, 6))
        hs4_subset.plot(kind='bar', stacked=True, ax=ax)
        ax.set_title(f"HS4 Share of Total {metric} within HS2 {hs2_code} – by Country")
        ax.set_ylabel("Percentage (%)")
        ax.set_xlabel("HS4 Code")
        ax.legend(title="Country", bbox_to_anchor=(1.05, 1), loc='upper left')
        st.pyplot(fig)


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
        render_hs4_share_bar_chart(combined_df, metric)
