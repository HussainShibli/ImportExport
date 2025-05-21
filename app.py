import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="HS Code Import/Export Analyzer", layout="wide")
st.title("📦 HS Code Import/Export Analyzer")
st.markdown("Upload one or more CSV files containing HS-level trade data. This tool will prepare data for visualization.")

uploaded_files = st.file_uploader("Upload your CSV file(s)", type=["csv"], accept_multiple_files=True)
metric = st.selectbox("Select Metric", ["value", "netWgt"])

# ✅ Unified HS Level selector
hs_level = st.radio("Select HS Level", options=["HS4", "HS6"], horizontal=True)


def render_combined_sunburst(df, metric, hs_level):
    st.markdown("### 🌐 Sunburst Chart – HS Breakdown by Country and Year")

    df['cmdCode'] = df['cmdCode'].astype(str)
    df['HS4'] = df['cmdCode'].str[:4]
    df['HS6'] = df['cmdCode'].str[:6]
    df['reporterDesc'] = df.get('reporterDesc', 'Unknown Country').fillna('Unknown Country')
    df['flowDesc'] = df.get('flowDesc', '').str.lower()
    df['countryFlow'] = df['reporterDesc'] + " (" + df['flowDesc'] + ")"
    df['year'] = pd.to_numeric(df.get('refYear', pd.NA), errors='coerce')

    years = sorted(df['year'].dropna().unique())
    cols = st.columns(len(years))

    for idx, year in enumerate(years):
        year_df = df[df['year'] == year].copy()
        year_df['flow_order'] = year_df['flowDesc'].map({'import': 0, 'export': 1})
        year_df = year_df.sort_values(by=['flow_order', 'reporterDesc'])

        grouped = year_df.groupby(['countryFlow', 'HS4', 'HS6'])[metric].sum().reset_index()

        if hs_level == 'HS4':
            grouped = grouped.groupby(['countryFlow', 'HS4'])[metric].sum().reset_index()
            path = ['countryFlow', 'HS4']
        else:
            path = ['countryFlow', 'HS4', 'HS6']

        fig = px.sunburst(
            grouped,
            path=path,
            values=metric,
            color='countryFlow',
            title=f"{int(year)} ({'USD' if metric == 'value' else 'kg'})"
        )
        fig.update_traces(insidetextorientation='radial')
        with cols[idx]:
            st.plotly_chart(fig, use_container_width=True)


def render_combined_stacked_bar(df, metric, hs_level):
    st.markdown("### 📊 Combined Absolute Stacked Bar Chart")

    df['cmdCode'] = df['cmdCode'].astype(str)
    df['HS4'] = df['cmdCode'].str[:4]
    df['HS6'] = df['cmdCode'].str[:6]
    df['reporterDesc'] = df.get('reporterDesc', 'Unknown Country').fillna('Unknown Country')
    df['flowDesc'] = df.get('flowDesc', '').str.lower()
    df['countryFlow'] = df['reporterDesc'] + " (" + df['flowDesc'] + ")"
    df['year'] = pd.to_numeric(df.get('refYear', pd.NA), errors='coerce')

    df = df[df[hs_level].str.len() == (4 if hs_level == 'HS4' else 6)]

    grouped = df.groupby(['year', 'flowDesc', hs_level])[metric].sum().reset_index()
    grouped['year_flow'] = grouped['year'].astype(str) + " / " + grouped['flowDesc'].str.capitalize()

    if not grouped.empty:
        fig = px.bar(
            grouped,
            x='year_flow',
            y=metric,
            color=hs_level,
            title=f"{hs_level} Value by Flow and Year",
            labels={metric: "Trade Volume", hs_level: f"{hs_level} Code"},
            text_auto='.2s'
        )
        fig.update_layout(
            barmode='stack',
            xaxis_title="Year – Flow",
            yaxis_title=f"{metric} ({'USD' if metric == 'value' else 'kg'})",
            showlegend=True
        )
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("### 📊 Combined Percentage Stacked Bar Chart")

    grouped = df.groupby(['year', 'flowDesc', hs_level])[metric].sum().reset_index()
    grouped['year_flow'] = grouped['year'].astype(str) + " – " + grouped['flowDesc'].str.capitalize()

    pivot = grouped.pivot(index='year_flow', columns=hs_level, values=metric).fillna(0)
    percent_df = pivot.div(pivot.sum(axis=1), axis=0).reset_index().melt(id_vars='year_flow', var_name=hs_level, value_name='percentage')
    percent_df['percentage'] *= 100

    if not percent_df.empty:
        fig = px.bar(
            percent_df,
            x='year_flow',
            y='percentage',
            color=hs_level,
            title=f"{hs_level} Share by Flow and Year",
            labels={'percentage': 'Percentage (%)', hs_level: f"{hs_level} Code"},
            text_auto='.1f'
        )
        fig.update_layout(
            barmode='stack',
            xaxis_title="Year – Flow",
            yaxis_title="Percentage (%)",
            showlegend=True
        )
        st.plotly_chart(fig, use_container_width=True)


# ========== Main App Logic ==========
if uploaded_files:
    all_data = []
    for file in uploaded_files:
        try:
            df = pd.read_csv(file)
            df['value'] = df.get('cifvalue', pd.NA).fillna(df.get('fobvalue', pd.NA))
            all_data.append(df)
        except Exception as e:
            st.error(f"Error processing {file.name}: {e}")

    if all_data:
        combined_df = pd.concat(all_data, ignore_index=True)
        combined_df['cmdCode'] = combined_df['cmdCode'].astype(str)
        combined_df['HS2'] = combined_df['cmdCode'].str[:2]
        combined_df['HS4'] = combined_df['cmdCode'].str[:4]

        hs2_options = sorted(combined_df['HS2'].dropna().unique())
        selected_hs2 = st.multiselect("Select HS2 Codes", options=hs2_options, default=hs2_options)

        filtered_df = combined_df[combined_df['HS2'].isin(selected_hs2)]

        hs4_list = sorted(filtered_df['HS4'].dropna().unique())
        hs6_list = sorted(filtered_df['cmdCode'].str[:6].dropna().unique())

        selector_options = [f"HS4: {code}" for code in hs4_list] + [f"HS6: {code}" for code in hs6_list]
        selected_codes = st.multiselect("Select HS4/HS6 Codes", options=selector_options, default=selector_options)

        selected_hs4 = [code.split(": ")[1] for code in selected_codes if code.startswith("HS4:")]
        selected_hs6 = [code.split(": ")[1] for code in selected_codes if code.startswith("HS6:")]

        final_df = filtered_df[
            (filtered_df['HS4'].isin(selected_hs4)) |
            (filtered_df['cmdCode'].str[:6].isin(selected_hs6))
        ]

        render_combined_sunburst(final_df, metric, hs_level)
        render_combined_stacked_bar(final_df, metric, hs_level)
