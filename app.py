import streamlit as st
import pandas as pd
import plotly.express as px
import os

DATA_FOLDER = "data"  # Folder containing HS2_Import.csv and HS2_Export.csv files

st.set_page_config(page_title="HS Code Import/Export Analyzer", layout="wide")
st.title("\U0001F4E6 HS Code Import/Export Analyzer (Folder Mode)")
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
    grouped['year_flow'] = grouped['refYear'].astype(str) + " / " + grouped['flowDesc'].str.capitalize()

    if show in ["absolute", "both"]:
        st.markdown(f"### \U0001F4CA Absolute Stacked Bar – {metric.upper()} by {hs_level}")
        fig = px.bar(grouped, x='year_flow', y=metric, color=hs_level, text_auto='.2s')
        fig.update_layout(barmode='stack', xaxis_title="Year – Flow", yaxis_title=f"{metric} ({'USD' if metric == 'value' else 'kg'})")
        st.plotly_chart(fig, use_container_width=True)

    if show in ["percentage", "both"]:
        st.markdown(f"### \U0001F4CA Percentage Stacked Bar – {metric.upper()} by {hs_level}")
        pivot = grouped.pivot(index='year_flow', columns=hs_level, values=metric).fillna(0)
        percent_df = pivot.div(pivot.sum(axis=1), axis=0).reset_index().melt(id_vars='year_flow', var_name=hs_level, value_name='percentage')
        percent_df['percentage'] *= 100
        fig = px.bar(percent_df, x='year_flow', y='percentage', color=hs_level, text_auto='.1f')
        fig.update_layout(barmode='stack', xaxis_title="Year – Flow", yaxis_title="Percentage (%)")
        st.plotly_chart(fig, use_container_width=True)

# Chart: Value / Quantity Ratio using altQty unless it's zero, then use netWgt

def render_ratio_chart(df, hs_level):
    st.markdown("### \U0001F4C8 Value-to-Quantity Ratio Over Time (Value / altQty or netWgt)")
    df = df[df[hs_level].str.len() == (4 if hs_level == 'HS4' else 6)].copy()

    df['quantity'] = df.apply(
        lambda row: row['altQty'] if pd.notnull(row['altQty']) and row['altQty'] > 0
        else row['netWgt'], axis=1
    )
    df = df[df['quantity'] > 0]

    df['valuePerUnit'] = df['value'] / df['quantity']
    grouped = df.groupby(['refYear', 'flowDesc', hs_level])['valuePerUnit'].mean().reset_index()
    fig = px.line(grouped, x='refYear', y='valuePerUnit', color=hs_level, line_group=hs_level,
                  facet_col='flowDesc', markers=True,
                  title="Value per Unit (USD / altQty or netWgt) Over Time",
                  labels={'valuePerUnit': 'Value / Quantity', hs_level: f'{hs_level} Code'})
    fig.update_layout(xaxis_title="Year", yaxis_title="USD per Unit", height=500)
    st.plotly_chart(fig, use_container_width=True)

# MAIN APP FLOW
available_hs2 = get_hs2_options()
selected_hs2 = st.selectbox("Select HS2 Code (from folder)", available_hs2)
hs_level = st.radio("Select HS Level", options=["HS4", "HS6"], horizontal=True)

combined_df = load_data_for_hs2(selected_hs2)
if combined_df is not None:
    required_columns = ['cmdCode', 'cifvalue', 'fobvalue', 'Reporter', 'flowDesc', 'Year', 'netWgt']
    missing_columns = [col for col in required_columns if col not in combined_df.columns]
    if missing_columns:
        st.error(f"❌ Missing required columns: {', '.join(missing_columns)}")
        st.stop()

    combined_df['cmdCode'] = combined_df['cmdCode'].astype(str)
    combined_df['HS4'] = combined_df['cmdCode'].str[:4]
    combined_df['HS6'] = combined_df['cmdCode'].str[:6]
    combined_df['HS2'] = combined_df['cmdCode'].str[:2]
    combined_df['value'] = combined_df['cifvalue'].fillna(combined_df['fobvalue']).fillna(0)
    combined_df['reporterDesc'] = combined_df['Reporter'].fillna('Unknown Country')
    combined_df['flowDesc'] = combined_df['flowDesc'].str.lower()
    combined_df['countryFlow'] = combined_df['reporterDesc'] + " (" + combined_df['flowDesc'] + ")"
    combined_df['refYear'] = pd.to_numeric(combined_df['Year'], errors='coerce')

    hs4_options = sorted(set(code for code in combined_df['HS4'].dropna().unique() if len(code) == 4))
    selected_hs4 = st.multiselect("Select HS4 Codes", options=hs4_options, default=hs4_options)

    hs6_candidates = combined_df[combined_df['HS4'].isin(selected_hs4)]['HS6']
    hs6_options = sorted(set(code for code in hs6_candidates.dropna().unique() if len(code) == 6))
    selected_hs6 = st.multiselect("Select HS6 Codes (within selected HS4s)", options=hs6_options, default=hs6_options)

    final_df = combined_df[
        (combined_df['HS4'].isin(selected_hs4)) |
        (combined_df['HS6'].isin(selected_hs6))
    ]

    # Render all graphs in desired order
    render_combined_sunburst(final_df, "value", hs_level)
    render_combined_sunburst(final_df, "netWgt", hs_level)

    render_combined_stacked_bar(final_df, "value", hs_level, show="absolute")
    render_combined_stacked_bar(final_df, "netWgt", hs_level, show="absolute")

    render_combined_stacked_bar(final_df, "value", hs_level, show="percentage")
    render_combined_stacked_bar(final_df, "netWgt", hs_level, show="percentage")

    render_ratio_chart(final_df, hs_level)
