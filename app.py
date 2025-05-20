import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

st.set_page_config(page_title="HS Code Trade Analyzer", layout="wide")

st.title("📦 HS Code Import/Export Analyzer")

uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)

    # Parse HS codes and time
    df['year'] = pd.to_datetime(df['periodDesc'], errors='coerce').dt.year
    df['HS2'] = df['cmdCode'].astype(str).str[:2]
    df['HS4'] = df['cmdCode'].astype(str).str[:4]
    df['HS6'] = df['cmdCode'].astype(str).str[:6]
    df['flowDesc'] = df['flowDesc'].str.lower()

    df['value'] = df['cifvalue'].fillna(df['fobvalue'])

    st.success("File loaded successfully!")
    hs_level = st.selectbox("Select HS Level", ["HS2", "HS4", "HS6"])
    metric = st.selectbox("Select Metric", ["value", "netWgt"])
    chart_type = st.selectbox("Select Chart Type", ["Grouped", "Stacked", "Diverging", "Faceted"])

    grouped = df.groupby([hs_level, 'year', 'flowDesc', 'partnerDesc']).agg({metric: 'sum'}).reset_index()

    selected_hs_codes = st.multiselect(f"Select {hs_level} codes to compare", grouped[hs_level].unique(), default=grouped[hs_level].unique()[:3])

    for hs_code in selected_hs_codes:
        subset = grouped[grouped[hs_level] == hs_code]
        title = f"{hs_level} {hs_code} - {metric} by Country and Flow"

        st.subheader(title)

        if chart_type == "Grouped":
            fig, ax = plt.subplots(figsize=(12, 6))
            sns.barplot(data=subset, x='partnerDesc', y=metric, hue='flowDesc', ax=ax)
            ax.set_title(title)
            ax.set_xticklabels(ax.get_xticklabels(), rotation=45)
            st.pyplot(fig)

        elif chart_type == "Stacked":
            pivot = subset.pivot_table(index='partnerDesc', columns='flowDesc', values=metric, aggfunc='sum').fillna(0)
            fig, ax = plt.subplots(figsize=(12, 6))
            pivot.plot(kind='bar', stacked=True, ax=ax)
            ax.set_title(title)
            ax.set_xticklabels(ax.get_xticklabels(), rotation=45)
            st.pyplot(fig)

        elif chart_type == "Diverging":
            diverging = subset.copy()
            diverging[metric] = diverging.apply(lambda row: -row[metric] if row['flowDesc'] == 'import' else row[metric], axis=1)
            fig, ax = plt.subplots(figsize=(12, 6))
            sns.barplot(data=diverging, x='partnerDesc', y=metric, hue='flowDesc', ax=ax)
            ax.axhline(0, color='black', linewidth=1)
            ax.set_title(title + " (Diverging)")
            ax.set_xticklabels(ax.get_xticklabels(), rotation=45)
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
                ax.set_xticklabels(ax.get_xticklabels(), rotation=45)
            st.pyplot(g)
