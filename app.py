import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

st.set_page_config(page_title="HS Code Import/Export Analyzer", layout="wide")
st.title("📦 HS Code Import/Export Analyzer")
st.markdown("Upload one or more CSV files containing HS-level trade data.")

uploaded_files = st.file_uploader("Upload your CSV file(s)", type=["csv"], accept_multiple_files=True)

# User options
hs_level = st.selectbox("Select HS Level", ["HS2", "HS4", "HS6"])
metric = st.selectbox("Select Metric", ["value", "netWgt"])
chart_type = st.selectbox("Select Chart Type", ["Stacked Bar Chart (Unified Flows)", "Sunburst Hierarchy"])

def process_and_visualize(df, filename):
    st.subheader(f"📁 {filename}")
    st.write("Detected columns:", df.columns.tolist())

    # Auto-map columns
    col_map = {}
    for col in df.columns:
        cl = col.lower()
        if 'cmd' in cl:
            col_map['cmdCode'] = col
        elif 'partnerdesc' in cl:
            col_map['partnerDesc'] = col
        elif 'flowdesc' in cl:
            col_map['flowDesc'] = col
        elif 'cif' in cl:
            col_map['cifvalue'] = col
        elif 'fob' in cl:
            col_map['fobvalue'] = col
        elif 'wgt' in cl and 'net' in cl:
            col_map['netWgt'] = col
        elif 'refyear' in cl:
            col_map['year'] = col

    required = ['cmdCode', 'partnerDesc', 'flowDesc', 'netWgt', 'year']
    missing = [req for req in required if req not in col_map]
    if missing:
        st.error(f"Missing required columns: {', '.join(missing)}. Skipping file.")
        return

    # Rename and clean
    df = df.rename(columns={v: k for k, v in col_map.items()})
    df = df.loc[:, ~df.columns.duplicated()]
    df['year'] = pd.to_numeric(df['year'], errors='coerce')
    df['value'] = df.get('cifvalue', pd.NA).fillna(df.get('fobvalue', pd.NA))
    df['cmdCode'] = df['cmdCode'].astype(str)
    df['HS2'] = df['cmdCode'].str[:2]
    df['HS4'] = df['cmdCode'].str[:4]
    df['flowDesc'] = df['flowDesc'].str.lower()

    # Ask for HS2 filter
    available_hs2 = df['HS2'].unique()
    selected_hs2 = st.multiselect(f"Select HS2 codes from {filename}:", available_hs2, default=available_hs2[:5])
    df = df[df['HS2'].isin(selected_hs2)]

    if df.empty:
        st.warning("No data available after filtering HS2 codes.")
        return

    # CHART TYPE 1 — Stacked Bar Chart with Unified Import/Export
    if chart_type.startswith("Stacked"):
        df['HS_label'] = df['HS2'] + " → " + df['HS4']
        grouped = df.groupby(['HS_label', 'flowDesc'])[metric].sum().reset_index()
        pivot = grouped.pivot_table(index='HS_label', columns='flowDesc', values=metric, aggfunc='sum').fillna(0)
        pivot = pivot.sort_index()

        fig, ax = plt.subplots(figsize=(14, 7))
        pivot.plot(kind='bar', stacked=True, ax=ax)
        ax.set_title(f"{metric} by HS2 → HS4 (Import & Export Combined)", fontsize=14)
        ax.set_ylabel(metric)
        ax.set_xlabel("HS2 → HS4 Code")
        ax.legend(title="Flow")
        plt.xticks(rotation=45, ha="right")
        st.pyplot(fig)

    # CHART TYPE 2 — Sunburst Chart for HS2 > HS4 + Flow
    elif chart_type.startswith("Sunburst"):
        import plotly.express as px

        grouped = df.groupby(['flowDesc', 'HS2', 'HS4'])[metric].sum().reset_index()
        fig = px.sunburst(
            grouped,
            path=['flowDesc', 'HS2', 'HS4'],
            values=metric,
            title=f"Sunburst of {filename} – Flow → HS2 → HS4",
            color='flowDesc'
        )
        fig.update_traces(insidetextorientation='radial')
        st.plotly_chart(fig, use_container_width=True)

# Process uploaded files
if uploaded_files:
    for file in uploaded_files:
        try:
            df = pd.read_csv(file)
            process_and_visualize(df, file.name)
        except Exception as e:
            st.error(f"Error processing {file.name}: {e}")
