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
chart_type = st.selectbox("Select Chart Type", ["Grouped", "Stacked", "Diverging", "Faceted"])

def process_and_visualize(df, filename):
    st.subheader(f"📁 {filename}")

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

    # Rename columns
    df = df.rename(columns={v: k for k, v in col_map.items()})
    df = df.loc[:, ~df.columns.duplicated()]

    # Year already present as int
    df['year'] = pd.to_numeric(df['year'], errors='coerce')

    # Handle value column
    df['value'] = df.get('cifvalue', pd.NA).fillna(df.get('fobvalue', pd.NA))

    try:
        if isinstance(df['cmdCode'], pd.Series):
            df['cmdCode'] = df['cmdCode'].astype(str)
            df['HS2'] = df['cmdCode'].str[:2]
            df['HS4'] = df['cmdCode'].str[:4]
            df['HS6'] = df['cmdCode'].str[:6]
        else:
            st.error(f"'cmdCode' is not a valid Series. Found: {type(df['cmdCode'])}")
            return
    except Exception as e:
        st.error(f"Error processing HS code levels: {e}")
        return

    df['flowDesc'] = df['flowDesc'].str.lower()

    # Group
    try:
        grouped = df.groupby([hs_level, 'year', 'flowDesc', 'partnerDesc'])[metric].sum().reset_index()
    except Exception as e:
        st.error(f"Failed to group data: {e}")
        return

    # HS code filter
    available_codes = grouped[hs_level].unique()
    selected_codes = st.multiselect(f"Select {hs_level} codes from {filename}:", available_codes, default=available_codes[:3])

    for code in selected_codes:
        subset = grouped[grouped[hs_level] == code]
        title = f"{hs_level} {code} – {metric} by country and flow"
        st.markdown(f"#### 📊 {title}")

        if subset.empty:
            st.warning(f"No data available for {hs_level} {code}")
            continue

        if chart_type == "Grouped":
            fig, ax = plt.subplots(figsize=(12, 6))
            sns.barplot(data=subset, x='partnerDesc', y=metric, hue='flowDesc', ax=ax)
            ax.set_title(title)
            ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha="right")
            st.pyplot(fig)

        elif chart_type == "Stacked":
            pivot = subset.pivot_table(index='partnerDesc', columns='flowDesc', values=metric, aggfunc='sum').fillna(0)
            fig, ax = plt.subplots(figsize=(12, 6))
            pivot.plot(kind='bar', stacked=True, ax=ax)
            ax.set_title(title)
            ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha="right")
            st.pyplot(fig)

        elif chart_type == "Diverging":
            diverging = subset.copy()
            diverging[metric] = diverging.apply(lambda row: -row[metric] if row['flowDesc'] == 'import' else row[metric], axis=1)
            fig, ax = plt.subplots(figsize=(12, 6))
            sns.barplot(data=diverging, x='partnerDesc', y=metric, hue='flowDesc', ax=ax)
            ax.axhline(0, color='black', linewidth=1)
            ax.set_title(title)
            ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha="right")
            st.pyplot(fig)

        elif chart_type == "Faceted":
            g = sns.catplot(
                data=subset,
                x='partnerDesc',
                y=metric,
                hue='flowDesc',
                col='year',
                kind='bar',
                col_wrap=3,
                height=4,
                aspect=1.5,
                sharey=False
            )
            g.set_titles(col_template="Year: {col_name}")
            g.fig.suptitle(title, y=1.02)
            for ax in g.axes.flatten():
                ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha="right")
            st.pyplot(g)

# Process each file
if uploaded_files:
    for file in uploaded_files:
        try:
            df = pd.read_csv(file)
            process_and_visualize(df, file.name)
        except Exception as e:
            st.error(f"Error processing {file.name}: {e}")
