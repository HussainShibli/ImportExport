import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="HS Code Import/Export Analyzer", layout="wide")
st.title("📦 HS Code Import/Export Analyzer")
st.markdown("Upload one or more CSV files containing HS-level trade data. This tool will prepare data for visualization.")

uploaded_files = st.file_uploader("Upload your CSV file(s)", type=["csv"], accept_multiple_files=True)

metric = st.selectbox("Select Metric", ["value", "netWgt"])


def render_combined_sunburst(df, metric):
    st.markdown("### 🌐 Sunburst Chart – HS4 → HS6 Breakdown by Country and Year")
    df['cmdCode'] = df['cmdCode'].astype(str)
    df['HS4'] = df['cmdCode'].str[:4]
    df['HS6'] = df['cmdCode'].str[:6]
    df['value'] = df.get('cifvalue', pd.NA).fillna(df.get('fobvalue', pd.NA))
    df['reporterDesc'] = df.get('reporterDesc', 'Unknown Country').fillna('Unknown Country')
    df['flowDesc'] = df.get('flowDesc', '').str.lower()
    df['countryFlow'] = df['reporterDesc'] + " (" + df['flowDesc'] + ")"
    df['year'] = pd.to_numeric(df.get('refYear', pd.NA), errors='coerce')

    years = df['year'].dropna().unique()
    cols = st.columns(len(years))
    for idx, year in enumerate(sorted(years)):
        year_df = df[df['year'] == year]
        year_df['flow_order'] = year_df['flowDesc'].map({'import': 0, 'export': 1})
        year_df = year_df.sort_values(by=['flow_order', 'reporterDesc'])
        grouped = year_df.groupby(['countryFlow', 'HS4', 'HS6'])[metric].sum().reset_index()
        fig = px.sunburst(
            grouped,
            path=['countryFlow', 'HS4', 'HS6'],
            values=metric,
            color='countryFlow',
            title=f"{int(year)} ({'USD' if metric == 'value' else 'kg'})"
        )
        fig.update_traces(insidetextorientation='radial')
        with cols[idx]:
            st.plotly_chart(fig, use_container_width=True)

def render_combined_stacked_bar(df, metric):
    level = st.radio("Select HS Level for Bar Charts", options=["HS4", "HS6"], horizontal=True)
    df['HS6'] = df['cmdCode'].str[:6]
    st.markdown("### 📊 Combined Absolute Stacked Bar Chart – HS4 Value by Flow and Year")
    df['cmdCode'] = df['cmdCode'].astype(str)
    df['HS4'] = df['cmdCode'].str[:4]
    df['value'] = df.get('cifvalue', pd.NA).fillna(df.get('fobvalue', pd.NA))
    df['reporterDesc'] = df.get('reporterDesc', 'Unknown Country').fillna('Unknown Country')
    df['flowDesc'] = df.get('flowDesc', '').str.lower()
    df['countryFlow'] = df['reporterDesc'] + " (" + df['flowDesc'] + ")"
    df['year'] = pd.to_numeric(df.get('refYear', pd.NA), errors='coerce')
    df = df[df[level].str.len() == (4 if level == 'HS4' else 6)]

    grouped = df.groupby(['year', 'flowDesc', level])[metric].sum().reset_index()
    grouped['year_flow'] = grouped['year'].astype(str) + " / " + grouped['flowDesc'].str.capitalize()

    if not grouped.empty:
        fig = px.bar(
            grouped,
            x='year_flow',
            y=metric,
            color=level,
            title="HS4 Value by Flow and Year",
            labels={metric: metric, level: level + ' Code'},
            text_auto='.2s'
        )
        fig.update_layout(barmode='stack', xaxis_title="Year – Flow", yaxis_title=f"{metric} ({'USD' if metric == 'value' else 'kg'})", showlegend=True)
        st.plotly_chart(fig, use_container_width=True)

    

    st.markdown("### 📊 Combined Percentage Stacked Bar Chart – HS4 Share by Year")
    grouped = df.groupby(['year', 'flowDesc', 'HS4'])[metric].sum().reset_index()
    grouped['year_flow'] = grouped['year'].astype(str) + " – " + grouped['flowDesc'].str.capitalize()

    pivot = grouped.pivot(index='year_flow', columns=level, values=metric).fillna(0)
    percent_df = pivot.div(pivot.sum(axis=1), axis=0).reset_index().melt(id_vars='year_flow', var_name='HS4', value_name='percentage')
    percent_df['percentage'] *= 100

    if not percent_df.empty:
        fig = px.bar(
            percent_df,
            x='year_flow',
            y='percentage',
            color='HS4',
            title="HS4 Share by Flow and Year",
            labels={'percentage': 'Percentage (%)', level: level + ' Code'},
            text_auto='.1f'
        )
        fig.update_layout(barmode='stack', xaxis_title="Year – Flow", yaxis_title="Percentage (%)", showlegend=True)
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

        combined_df['cmdCode'] = combined_df['cmdCode'].astype(str)
        combined_df['HS2'] = combined_df['cmdCode'].str[:2]
        combined_df['HS4'] = combined_df['cmdCode'].str[:4]

        hs2_options = sorted(combined_df['HS2'].unique())
        selected_hs2 = st.multiselect("Select HS2 Codes", options=hs2_options, default=hs2_options)

        filtered_df = combined_df[combined_df['HS2'].isin(selected_hs2)]

        hs4_options = sorted([code for code in filtered_df['HS4'].unique() if len(code) == 4 and not code[:2] == code])
        selected_hs4 = st.multiselect("Select HS4 Codes (within selected HS2s)", options=hs4_options, default=hs4_options)

        hs6_candidates = filtered_df[filtered_df['HS4'].isin(selected_hs4)]['cmdCode'].str[:6].unique()
        hs6_options = sorted([code for code in hs6_candidates if code[:4] != code and code[:2] != code])
        selected_hs6 = st.multiselect("Select HS6 Codes (within selected HS4s)", options=hs6_options, default=hs6_options)

        final_df = filtered_df[(filtered_df['HS4'].isin(selected_hs4)) & (filtered_df['cmdCode'].str[:6].isin(selected_hs6))]
        render_combined_sunburst(final_df, metric)
        render_combined_stacked_bar(final_df, metric)
