import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px

st.set_page_config(page_title="HS Code Import/Export Analyzer", layout="wide")
st.title("📦 HS Code Import/Export Analyzer")
st.markdown("Upload one or more CSV files containing HS-level trade data. This tool will show Import and Export data by HS2 → HS4 level using multiple visualizations.")

uploaded_files = st.file_uploader("Upload your CSV file(s)", type=["csv"], accept_multiple_files=True)

metric = st.selectbox("Select Metric", ["value", "netWgt"])

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

    # Rename and prepare data
    df = df.rename(columns={v: k for k, v in col_map.items()})
    df = df.loc[:, ~df.columns.duplicated()]
    df['year'] = pd.to_numeric(df['year'], errors='coerce')
    df['value'] = df.get('cifvalue', pd.NA).fillna(df.get('fobvalue', pd.NA))
    df['cmdCode'] = df['cmdCode'].astype(str)
    df['HS2'] = df['cmdCode'].str[:2]
    df['HS4'] = df['cmdCode'].str[:4]
    df['flowDesc'] = df['flowDesc'].str.lower()

    df['HS_label'] = df['HS2'] + " → " + df['HS4']

    # =========================
    # 1. Absolute Stacked Chart
    # =========================
    st.markdown("### 📊 Stacked Bar Chart – Absolute Trade Value")

    grouped = df.groupby(['HS_label', 'flowDesc'])[metric].sum().reset_index()
    pivot = grouped.pivot_table(index='HS_label', columns='flowDesc', values=metric, aggfunc='sum').fillna(0)
    pivot = pivot.sort_index()

    fig1, ax1 = plt.subplots(figsize=(14, 7))
    pivot.plot(kind='bar', stacked=True, ax=ax1)
    ax1.set_title("Absolute Import & Export by HS2 → HS4", fontsize=14)
    ax1.set_ylabel(metric)
    ax1.set_xlabel("HS2 → HS4 Code")
    ax1.legend(title="Flow")
    plt.xticks(rotation=45, ha="right")
    st.pyplot(fig1)

    # ===============================
    # 2. Percentage Stacked Chart
    # ===============================
    st.markdown("### 📊 Percentage Stacked Bar Chart – Share of Trade per HS Code")

    percentage_pivot = pivot.div(pivot.sum(axis=1), axis=0) * 100

    fig2, ax2 = plt.subplots(figsize=(14, 7))
    percentage_pivot.plot(kind='bar', stacked=True, ax=ax2)
    ax2.set_title("Percentage Distribution of Import & Export by HS2 → HS4", fontsize=14)
    ax2.set_ylabel("Percentage (%)")
    ax2.set_xlabel("HS2 → HS4 Code")
    ax2.legend(title="Flow")
    plt.xticks(rotation=45, ha="right")
    st.pyplot(fig2)

    # ======================
    # 3. Sunburst Hierarchy
    # ======================
    st.markdown("### 🌐 Sunburst Chart – Flow → HS2 → HS4")

    sunburst_grouped = df.groupby(['flowDesc', 'HS2', 'HS4'])[metric].sum().reset_index()

    fig3 = px.sunburst(
        sunburst_grouped,
        path=['flowDesc', 'HS2', 'HS4'],
        values=metric,
        title=f"Sunburst Chart for {filename}",
        color='flowDesc'
    )
    fig3.update_traces(insidetextorientation='radial')
    st.plotly_chart(fig3, use_container_width=True)

# Run for each uploaded file
if uploaded_files:
    for file in uploaded_files:
        try:
            df = pd.read_csv(file)
            process_and_visualize(df, file.name)
        except Exception as e:
            st.error(f"Error processing {file.name}: {e}")
