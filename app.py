import streamlit as st
import pandas as pd
import plotly.express as px
import os

DATA_FOLDER = "data"  # Folder containing HS2_Import.csv and HS2_Export.csv files

st.set_page_config(page_title="HS Code Import/Export Analyzer", layout="wide")
st.title("📦 HS Code Import/Export Analyzer (Folder Mode)")

# Chart toggles (for old section)
show_sunburst = st.checkbox("Show Sunburst Charts", value=True, key="sunburst")
show_absolute_bar = st.checkbox("Show Absolute Bar Charts", value=True, key="absolute")
show_percentage_bar = st.checkbox("Show Percentage Bar Charts", value=True, key="percentage")
show_ratio_chart = st.checkbox("Show Value-to-Quantity Ratio Chart", value=True, key="ratio")
st.markdown("Select a hierarchy of HS codes to visualize flow graphs.")

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

def render_hierarchy_sunburst(df, metric):
    st.markdown(f"### 🌐 Sunburst Chart – {metric.upper()} by HS Hierarchy")
    grouped = df.groupby(["flowDesc", "HS2", "HS4", "HS6"])[metric].sum().reset_index()
    fig = px.sunburst(grouped, path=["flowDesc", "HS2", "HS4", "HS6"], values=metric, color="flowDesc",
                      title=f"Sunburst of {metric.upper()} by Flow and HS Codes")
    fig.update_traces(insidetextorientation='radial')
    st.plotly_chart(fig, use_container_width=True)

# New Flow Graph Section
st.markdown("---")
st.header("📈 Custom Flow Graph Explorer")

# Chart type toggles
enable_sunburst = st.checkbox("Enable Sunburst", value=True)
enable_icicle = st.checkbox("Enable Icicle Chart", value=False)
enable_treemap = st.checkbox("Enable Treemap", value=False)

# MAIN APP FLOW
available_hs2 = get_hs2_options()
selected_hs2 = st.multiselect("Select HS2 Codes (from folder)", available_hs2)

combined_df = pd.DataFrame()
for hs2 in selected_hs2:
    df = load_data_for_hs2(hs2)
    if df is not None:
        combined_df = pd.concat([combined_df, df], ignore_index=True)

if not combined_df.empty:
    required_columns = ['cmdCode', 'cifvalue', 'fobvalue', 'reporterDesc', 'flowDesc', 'refYear', 'netWgt']
    missing_columns = [col for col in required_columns if col not in combined_df.columns]
    if missing_columns:
        st.error(f"\u274C Missing required columns: {', '.join(missing_columns)}")
        st.stop()

    combined_df['cmdCode'] = combined_df['cmdCode'].astype(str)
    combined_df['HS6'] = combined_df['cmdCode'].str[:6]
    combined_df['HS4'] = combined_df['cmdCode'].str[:4]
    combined_df['HS2'] = combined_df['cmdCode'].str[:2]
    combined_df['cifvalue'] = pd.to_numeric(combined_df['cifvalue'], errors='coerce')
    combined_df['fobvalue'] = pd.to_numeric(combined_df['fobvalue'], errors='coerce')
    combined_df['value'] = combined_df.apply(
        lambda row: row['fobvalue'] if pd.isna(row['cifvalue']) or row['cifvalue'] == 0 else row['cifvalue'], axis=1
    )

    hs2_options = sorted(set(combined_df['HS2'].dropna().unique()))
    selected_hs2_filter = st.multiselect("Filter to Specific HS2 Codes (Optional)", hs2_options)

    filtered_df = combined_df[combined_df['HS2'].isin(selected_hs2_filter)] if selected_hs2_filter else combined_df

    hs4_options = sorted(set(filtered_df['HS4'].dropna().unique()))
    selected_hs4 = st.multiselect("Filter to Specific HS4 Codes (Optional)", hs4_options)
    if selected_hs4:
        filtered_df = filtered_df[filtered_df['HS4'].isin(selected_hs4)]

    hs6_options = sorted(set(filtered_df['HS6'].dropna().unique()))
    selected_hs6 = st.multiselect("Filter to Specific HS6 Codes (Optional)", hs6_options)
    if selected_hs6:
        filtered_df = filtered_df[filtered_df['HS6'].isin(selected_hs6)]

    if st.button("Generate Flow Graphs"):
        if enable_sunburst:
            render_hierarchy_sunburst(filtered_df, "value")
            render_hierarchy_sunburst(filtered_df, "netWgt")
