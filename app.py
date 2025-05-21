import streamlit as st
import pandas as pd
import plotly.express as px
import os

DATA_FOLDER = "data"  # <-- Your folder containing the HS2 import/export files

st.set_page_config(page_title="HS Code Import/Export Analyzer", layout="wide")
st.title("📦 HS Code Import/Export Analyzer (Folder Mode)")
st.markdown("Select an HS2 code to visualize its Import/Export data from local files.")

# Get available HS2 codes from filenames in folder
def get_hs2_options():
    files = os.listdir(DATA_FOLDER)
    hs2_codes = sorted(set(f.split("_")[0] for f in files if f.endswith(".csv") and "_" in f))
    return hs2_codes

# Read import/export files for a specific HS2 code
def load_data_for_hs2(hs2_code):
    try:
        imp_file = os.path.join(DATA_FOLDER, f"{hs2_code}_Import.csv")
        exp_file = os.path.join(DATA_FOLDER, f"{hs2_code}_Export.csv")
        df_imp = pd.read_csv(imp_file)
        df_exp = pd.read_csv(exp_file)
        df_imp["flowDesc"] = "import"
        df_exp["flowDesc"] = "export"
        return pd.concat([df_imp, df_exp], ignore_index=True)
    except Exception as e:
        st.error(f"Failed to load data for HS2 {hs2_code}: {e}")
        return None

# Select HS2 file group from dropdown
available_hs2 = get_hs2_options()
selected_hs2 = st.selectbox("Select HS2 Code (from folder)", available_hs2)

# Unified settings
metric = st.selectbox("Select Metric", ["value", "netWgt"])
hs_level = st.radio("Select HS Level", options=["HS4", "HS6"], horizontal=True)

# Load and process the selected HS2 group
combined_df = load_data_for_hs2(selected_hs2)
if combined_df is not None:
    combined_df['cmdCode'] = combined_df['cmdCode'].astype(str)
    combined_df['HS4'] = combined_df['cmdCode'].str[:4]
    combined_df['HS6'] = combined_df['cmdCode'].str[:6]
    combined_df['HS2'] = combined_df['cmdCode'].str[:2]
    combined_df['value'] = combined_df.get('cifvalue', pd.NA).fillna(combined_df.get('fobvalue', pd.NA))
    combined_df['reporterDesc'] = combined_df.get('reporterDesc', 'Unknown Country').fillna('Unknown Country')
    combined_df['flowDesc'] = combined_df['flowDesc'].str.lower()
    combined_df['countryFlow'] = combined_df['reporterDesc'] + " (" + combined_df['flowDesc'] + ")"
    combined_df['year'] = pd.to_numeric(combined_df.get('refYear', pd.NA), errors='coerce')

    # HS4 Selector
    hs4_options = sorted(set(code for code in combined_df['HS4'].dropna().unique() if len(code) == 4))
    selected_hs4 = st.multiselect("Select HS4 Codes", options=hs4_options, default=hs4_options)

    # HS6 Selector
    hs6_candidates = combined_df[combined_df['HS4'].isin(selected_hs4)]['HS6']
    hs6_options = sorted(set(code for code in hs6_candidates.dropna().unique() if len(code) == 6))
    selected_hs6 = st.multiselect("Select HS6 Codes (within selected HS4s)", options=hs6_options, default=hs6_options)

    # Final Filtered Data
    final_df = combined_df[
        (combined_df['HS4'].isin(selected_hs4)) |
        (combined_df['HS6'].isin(selected_hs6))
    ]

    # Render charts
    def render_combined_sunburst(df, metric, hs_level):
        st.markdown("### 🌐 Sunburst Chart – HS Breakdown by Country and Year")
        years = sorted(df['year'].dropna().unique())
        cols = st.columns(len(years))
        for idx, year in enumerate(years):
            year_df = df[df['year'] == year].copy()
            grouped = year_df.groupby(['countryFlow', 'HS4', 'HS6'])[metric].sum().reset_index()
            path = ['countryFlow', 'HS4'] if hs_level == 'HS4' else ['countryFlow', 'HS4', 'HS6']
            if hs_level == 'HS4':
                grouped = grouped.groupby(['countryFlow', 'HS4'])[metric].sum().reset_index()
            fig = px.sunburst(grouped, path=path, values=metric, color='countryFlow', title=f"{int(year)} ({'USD' if metric == 'value' else 'kg'})")
            fig.update_traces(insidetextorientation='radial')
            with cols[idx]:
                st.plotly_chart(fig, use_container_width=True)

    def render_combined_stacked_bar(df, metric, hs_level, show="both"):
        if show in ["absolute", "both"]:
            st.markdown(f"#### Absolute Stacked Bar Chart – {metric.upper()}")
            df = df[df[hs_level].str.len() == (4 if hs_level == 'HS4' else 6)]
            grouped = df.groupby(['year', 'flowDesc', hs_level])[metric].sum().reset_index()
            grouped['year_flow'] = grouped['year'].astype(str) + " / " + grouped['flowDesc'].str.capitalize()
            if not grouped.empty:
                fig = px.bar(grouped, x='year_flow', y=metric, color=hs_level,
                             title=f"{hs_level} Value by Flow and Year", text_auto='.2s')
                fig.update_layout(barmode='stack', xaxis_title="Year – Flow", yaxis_title=f"{metric} ({'USD' if metric == 'value' else 'kg'})")
                st.plotly_chart(fig, use_container_width=True)

        if show in ["percentage", "both"]:
            st.markdown(f"#### Percentage Stacked Bar Chart – {metric.upper()}")
            grouped = df.groupby(['year', 'flowDesc', hs_level])[metric].sum().reset_index()
            grouped['year_flow'] = grouped['year'].astype(str) + " – " + grouped['flowDesc'].str.capitalize()
            pivot = grouped.pivot(index='year_flow', columns=hs_level, values=metric).fillna(0)
            percent_df = pivot.div(pivot.sum(axis=1), axis=0).reset_index().melt(id_vars='year_flow', var_name=hs_level, value_name='percentage')
            percent_df['percentage'] *= 100
            if not percent_df.empty:
                fig = px.bar(percent_df, x='year_flow', y='percentage', color=hs_level,
                             title=f"{hs_level} Share by Flow and Year", text_auto='.1f')
                fig.update_layout(barmode='stack', xaxis_title="Year – Flow", yaxis_title="Percentage (%)")
                st.plotly_chart(fig, use_container_width=True)

st.markdown("## 🌐 Sunburst – Value (USD)")
render_combined_sunburst(final_df, "value", hs_level)

st.markdown("## 🌐 Sunburst – Weight (kg)")
render_combined_sunburst(final_df, "netWgt", hs_level)

st.markdown("## 📊 Absolute Bar Chart – Value (USD)")
render_combined_stacked_bar(final_df, "value", hs_level, show="absolute")

st.markdown("## 📊 Absolute Bar Chart – Weight (kg)")
render_combined_stacked_bar(final_df, "netWgt", hs_level, show="absolute")

st.markdown("## 📊 Percentage Bar Chart – Value (USD)")
render_combined_stacked_bar(final_df, "value", hs_level, show="percentage")

st.markdown("## 📊 Percentage Bar Chart – Weight (kg)")
render_combined_stacked_bar(final_df, "netWgt", hs_level, show="percentage")
