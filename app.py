import streamlit as st
import pandas as pd
import plotly.express as px
import os

DATA_FOLDER = "data"  # Folder containing HS2_Import.csv and HS2_Export.csv files

st.set_page_config(page_title="HS Code Import/Export Analyzer", layout="wide")
st.title("📦 HS Code Import/Export Analyzer (Folder Mode)")

# Show importing and exporting country info if present
if 'reporterDesc' in combined_df.columns and 'flowDesc' in combined_df.columns:
    importers = combined_df[combined_df['flowDesc'].str.lower() == 'import']['reporterDesc'].unique()
    exporters = combined_df[combined_df['flowDesc'].str.lower() == 'export']['reporterDesc'].unique()
    st.markdown(f"**📥 Importing Countries:** {', '.join(importers)}")
    st.markdown(f"**📤 Exporting Countries:** {', '.join(exporters)}")
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

# Chart: Sunburst

def render_combined_sunburst(df, metric, hs_level):
    st.markdown(f"### \U0001F310 Sunburst Chart – {metric.upper()} by {hs_level}")
    years = sorted(df['refYear'].dropna().unique())
    cols = st.columns(len(years))
    for idx, year in enumerate(years):
        year_df = df[df['refYear'] == year].copy()
        grouped = year_df.groupby(['countryFlow', 'HS4', 'HS6'])[metric].sum().reset_index()
        path = ['countryFlow', 'HS4'] if hs_level == 'HS4' else ['countryFlow', 'HS4', 'HS6']
        if hs_level == 'HS4':
            grouped = grouped.groupby(['countryFlow', 'HS4'])[metric].sum().reset_index()
        fig = px.sunburst(grouped, path=path, values=metric, color='countryFlow',
                          title=f"{int(year)} ({'USD' if metric == 'value' else 'kg'})")
        fig.update_traces(insidetextorientation='radial')
        with cols[idx]:
            st.plotly_chart(fig, use_container_width=True)

# Chart: Bar (absolute or percentage)
def render_combined_stacked_bar(df, metric, hs_level, show="both"):
    df = df[df[hs_level].str.len() == (4 if hs_level == 'HS4' else 6)]
    grouped = df.groupby(['refYear', 'flowDesc', hs_level])[metric].sum().reset_index()
    grouped['year_flow'] = grouped['refYear'].astype(str) + grouped['flowDesc'].str.lower().map({'export': ' A', 'import': ' B'})
