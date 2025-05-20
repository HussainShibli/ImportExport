import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="HS Code Import/Export Analyzer", layout="wide")
st.title("📦 HS Code Import/Export Analyzer")
st.markdown("Upload one or more CSV files containing HS-level trade data. This tool will prepare data for visualization.")

uploaded_files = st.file_uploader("Upload your CSV file(s)", type=["csv"], accept_multiple_files=True)

metric = st.selectbox("Select Metric", ["value", "netWgt"])
level = st.radio("Select HS Level for Bar Charts", options=["HS4", "HS6"], horizontal=True)


def render_sunbursts_by_year(df, metric):
    df['cmdCode'] = df['cmdCode'].astype(str)
    df['HS4'] = df['cmdCode'].str[:4]
    df['HS6'] = df['cmdCode'].str[:6]
    df['flowDesc'] = df.get('flowDesc', '').str.lower()
    df['value'] = df.get('cifvalue', pd.NA).fillna(df.get('fobvalue', pd.NA))
    df['reporterDesc'] = df.get('reporterDesc', 'Unknown Country').fillna('Unknown Country')
    df['countryFlow'] = df['reporterDesc'] + " (" + df['flowDesc'] + ")"
    df['year'] = pd.to_numeric(df.get('refYear', pd.NA), errors='coerce')

    years = df['year'].dropna().unique()
    for year in sorted(years):
        st.markdown(f"#### 🌐 Sunburst Chart – {int(year)}")
        subset = df[df['year'] == year]
        grouped = subset.groupby(['countryFlow', 'HS4', 'HS6'])[metric].sum().reset_index()
        fig = px.sunburst(
            grouped,
            path=['countryFlow', 'HS4', 'HS6'],
            values=metric,
            title=f"{int(year)}",
            color='countryFlow'
        )
        fig.update_traces(insidetextorientation='radial')
        st.plotly_chart(fig, use_container_width=True)


def render_yearly_import_export_bars(df, metric):
    st.markdown("### 📊 Yearly Import and Export Totals")
    df['value'] = df.get('cifvalue', pd.NA).fillna(df.get('fobvalue', pd.NA))
    df['flowDesc'] = df.get('flowDesc', '').str.lower()
    df['year'] = pd.to_numeric(df.get('refYear', pd.NA), errors='coerce')
    if 'year' in df.columns and 'flowDesc' in df.columns:
        grouped = df.groupby(['year', 'flowDesc'])[metric].sum().reset_index()
    else:
        st.warning("Missing 'year' or 'flowDesc' column in data. Cannot plot yearly import/export totals.")
        return

    fig = px.bar(
        grouped,
        x='year',
        y=metric,
        color='flowDesc',
        barmode='group',
        text_auto='.2s',
        labels={'value': metric, 'flowDesc': 'Flow', 'year': 'Year'},
        title=f"Import and Export Totals by Year ({'USD' if metric == 'value' else 'kg'})"
    )
    fig.update_layout(xaxis_title="Year", yaxis_title=f"{metric} ({'USD' if metric == 'value' else 'kg'})")
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
        render_sunbursts_by_year(combined_df, metric)
        render_yearly_import_export_bars(combined_df, metric)
