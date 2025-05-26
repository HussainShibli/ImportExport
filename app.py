import streamlit as st
import pandas as pd
import plotly.express as px
import os

DATA_FOLDER = "data"  # Folder containing HS2_Import.csv and HS2_Export.csv files

st.set_page_config(page_title="HS Code Import/Export Analyzer", layout="wide")
st.title("📦 HS Code Import/Export Analyzer (Folder Mode)")

# Chart toggles
show_sunburst = st.checkbox("Show Sunburst Charts", value=True, key="sunburst")
show_absolute_bar = st.checkbox("Show Absolute Bar Charts", value=True, key="absolute")
show_percentage_bar = st.checkbox("Show Percentage Bar Charts", value=True, key="percentage")
show_ratio_chart = st.checkbox("Show Value-to-Quantity Ratio Chart", value=True, key="ratio")
st.markdown("Select an HS2 code to visualize its Import/Export data from local files.")

# Get available HS2 codes from filenames in folder
def get_hs2_options():
    files = os.listdir(DATA_FOLDER)
    hs2_codes = sorted(set(f.split("_")[0] for f in files if f.endswith(".csv") and "_" in f))
    return hs2_codes

# Preprocessing function to reduce redundancy
def preprocess_dataframe(df):
    df['cmdCode'] = df['cmdCode'].astype(str)
    df['HS2'] = df['cmdCode'].str[:2]
    df['HS4'] = df['cmdCode'].str[:4]
    df['HS6'] = df['cmdCode'].str[:6]
    df['cifvalue'] = pd.to_numeric(df['cifvalue'], errors='coerce')
    df['fobvalue'] = pd.to_numeric(df['fobvalue'], errors='coerce')
    df['value'] = df.apply(
        lambda row: row['fobvalue'] if pd.isna(row['cifvalue']) or row['cifvalue'] == 0 else row['cifvalue'], axis=1)
    df['reporterDesc'] = df['reporterDesc'].fillna('Unknown Country')
    df['flowDesc'] = df['flowDesc'].str.lower()
    df['countryFlow'] = df['reporterDesc'] + " (" + df['flowDesc'] + ")"
    df['refYear'] = pd.to_numeric(df['refYear'], errors='coerce')
    return df

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

def render_combined_sunburst(df, metric, hs_level, selected_year):
    st.markdown(f"### \U0001F310 Sunburst Chart – {metric.upper()} by {hs_level} for {selected_year}")
    year_df = df[df['refYear'] == selected_year].copy()
    grouped = year_df.groupby(['countryFlow', 'HS4', 'HS6'])[metric].sum().reset_index()
    path = ['countryFlow', 'HS4'] if hs_level == 'HS4' else ['countryFlow', 'HS4', 'HS6']
    if hs_level == 'HS4':
        grouped = grouped.groupby(['countryFlow', 'HS4'])[metric].sum().reset_index()
    fig = px.sunburst(grouped, path=path, values=metric, color='countryFlow',
                      title=f"{int(selected_year)} ({'USD' if metric == 'value' else 'kg'})")
    fig.update_traces(insidetextorientation='radial')
    st.plotly_chart(fig, use_container_width=True)

# Chart: Bar (absolute or percentage)
def render_combined_stacked_bar(df, metric, hs_level, show="both", selected_year=None):
    df = df[df[hs_level].notna() & (df[hs_level].str.len() == (4 if hs_level == 'HS4' else 6))]
    if selected_year:
        df = df[df['refYear'] == selected_year]
    grouped = df.groupby(['refYear', 'flowDesc', hs_level], dropna=True)[metric].sum().reset_index()
    flow_order = {'export': 0, 'import': 1}
    grouped['flow_order'] = grouped['flowDesc'].map(flow_order)
    grouped = grouped.sort_values(by=['refYear', 'flow_order', hs_level])
    grouped['year_flow'] = grouped['flowDesc'].str.capitalize() + "<br>" + grouped['refYear'].astype(str)

    if show in ["absolute", "both"]:
        st.markdown(f"### 📊 Absolute Stacked Bar – {metric.upper()} by {hs_level}")
        category_order = grouped['year_flow'].tolist()
        fig = px.bar(grouped, x='year_flow', y=metric, color=hs_level, text_auto='.2s')
        fig.update_layout(
            barmode='stack',
            legend=dict(orientation='h', y=-0.2, x=0.5, xanchor='center'),
            xaxis_title="Year / Flow",
            yaxis_title=f"{metric} ({'USD' if metric == 'value' else 'kg'})",
            margin=dict(b=80),
            height=500,
            xaxis={'type': 'category', 'categoryorder': 'array', 'categoryarray': category_order}
        )
        st.plotly_chart(fig, use_container_width=True)

    if show in ["percentage", "both"]:
        st.markdown(f"### 📊 Percentage Stacked Bar – {metric.upper()} by {hs_level}")
        pivot = grouped.pivot(index='year_flow', columns=hs_level, values=metric).fillna(0)
        percent_df = pivot.div(pivot.sum(axis=1), axis=0).reset_index().melt(id_vars='year_flow', var_name=hs_level, value_name='percentage')
        percent_df['percentage'] *= 100
        fig = px.bar(percent_df, x='year_flow', y='percentage', color=hs_level, text_auto='.1f')
        fig.update_layout(
            barmode='stack',
            legend=dict(orientation='h', y=-0.2, x=0.5, xanchor='center'),
            xaxis_title="Year / Flow",
            yaxis_title="Percentage (%)",
            height=500,
            xaxis={'type': 'category'}
        )
        st.plotly_chart(fig, use_container_width=True)

# Chart: Value / Quantity Ratio using altQty unless it's zero, then use netWgt

def render_ratio_chart(df, hs_level, selected_year=None):
    if selected_year:
        st.markdown(f"### 📈 Value-to-Quantity Ratio for {selected_year} (Value / altQty or netWgt)")
        df = df[(df[hs_level].str.len() == (4 if hs_level == 'HS4' else 6)) & (df['refYear'] == selected_year)].copy()
    else:
        st.markdown("### 📈 Value-to-Quantity Ratio Chart (Combined Years)")
        df = df[(df[hs_level].str.len() == (4 if hs_level == 'HS4' else 6))].copy()

    df['quantity'] = df.apply(
        lambda row: row['altQty'] if pd.notnull(row['altQty']) and row['altQty'] > 0 else row['netWgt'], axis=1)
    df = df[df['quantity'] > 0]
    df['valuePerUnit'] = df['value'] / df['quantity']

    grouped = df.groupby(['refYear', 'flowDesc', hs_level], sort=False)['valuePerUnit'].mean().reset_index()
    flow_order = {'export': 0, 'import': 1}
    grouped['flow_order'] = grouped['flowDesc'].map(flow_order)
    grouped = grouped.sort_values(by=['refYear', 'flow_order', hs_level])

    fig = px.line(
        grouped,
        x='refYear',
        y='valuePerUnit',
        color=hs_level,
        line_group=hs_level,
        facet_col='flowDesc',
        markers=True,
        title="Value per Unit (USD / altQty or netWgt) Over Time",
        labels={'valuePerUnit': 'Value / Quantity', hs_level: f'{hs_level} Code'}
    )
    fig.update_layout(
        legend=dict(orientation='h', y=-0.25, x=0.5, xanchor='center'),
        xaxis_title="Year",
        yaxis_title="USD per Unit",
        height=500,
        xaxis={'type': 'category', 'categoryorder': 'array', 'categoryarray': sorted(grouped['refYear'].unique().tolist())}
    )
    st.plotly_chart(fig, use_container_width=True)

# MAIN APP FLOW
available_hs2 = get_hs2_options()
selected_hs2 = st.selectbox("Select HS2 Code (from folder)", available_hs2)
hs_level = st.radio("Select HS Level", options=["HS4", "HS6"], horizontal=True)

combined_df = load_data_for_hs2(selected_hs2)
    combined_df = preprocess_dataframe(combined_df)

    hs4_options = sorted(set(code for code in combined_df['HS4'].dropna().unique() if len(code) == 4))
    selected_hs4 = st.multiselect("Select HS4 Codes", options=hs4_options, default=hs4_options)

    hs6_candidates = combined_df[combined_df['HS4'].isin(selected_hs4)]['HS6']
    hs6_options = sorted(set(code for code in hs6_candidates.dropna().unique() if len(code) == 6))
    selected_hs6 = st.multiselect("Select HS6 Codes (within selected HS4s)", options=hs6_options, default=hs6_options)

    final_df = combined_df[combined_df['HS4'].isin(selected_hs4) & combined_df['HS6'].isin(selected_hs6)]

    all_years = sorted(final_df['refYear'].dropna().unique())
    if all_years:
        year_cols = st.columns(len(all_years))
        selected_years = []
        for i, y in enumerate(all_years):
            with year_cols[i]:
                if st.toggle(str(y), value=(y == all_years[0])):
                    selected_years.append(y)

        if show_sunburst:
            st.markdown("## 🌐 Sunburst Charts by Year")
            for year in selected_years:
                st.markdown(f"### Year {year}")
                col1, col2 = st.columns(2)
                with col1:
                    render_combined_sunburst(final_df, "value", hs_level, year)
                with col2:
                    render_combined_sunburst(final_df, "netWgt", hs_level, year)

        if show_absolute_bar:
            st.markdown("## 📊 Absolute Stacked Bar Chart (Combined Years)")
            render_combined_stacked_bar(final_df[final_df['refYear'].isin(selected_years)], "value", hs_level, show="absolute")
            render_combined_stacked_bar(final_df[final_df['refYear'].isin(selected_years)], "netWgt", hs_level, show="absolute")

        if show_percentage_bar:
            st.markdown("## 📊 Percentage Stacked Bar Chart (Combined Years)")
            render_combined_stacked_bar(final_df[final_df['refYear'].isin(selected_years)], "value", hs_level, show="percentage")
            render_combined_stacked_bar(final_df[final_df['refYear'].isin(selected_years)], "netWgt", hs_level, show="percentage")

        if show_ratio_chart:
            st.markdown("## 📈 Value to Quantity Ratio Chart (Combined Years)")
            render_ratio_chart(final_df[final_df['refYear'].isin(selected_years)], hs_level)

# ========================= NEW CUSTOM FLOW GRAPH SECTION =========================
st.markdown("---")
st.header("📈 Custom Flow Graph Section")

available_hs2_all = get_hs2_options()
selected_multiple_hs2 = st.multiselect("Select One or More HS2 Codes", available_hs2_all)

if selected_multiple_hs2:
    combined_df_custom = pd.DataFrame()
    for hs2_code in selected_multiple_hs2:
        df = load_data_for_hs2(hs2_code)
        if df is not None:
            combined_df_custom = pd.concat([combined_df_custom, df], ignore_index=True)

    if not combined_df_custom.empty:
        combined_df_custom = preprocess_dataframe(combined_df_custom)

        hs4_all = sorted(set(combined_df_custom['HS4'].dropna().unique()))
        hs4_selected = st.multiselect("Optionally filter HS4 Codes", hs4_all)
        if hs4_selected:
            combined_df_custom = combined_df_custom[combined_df_custom['HS4'].isin(hs4_selected)]

        hs6_all = sorted(set(combined_df_custom['HS6'].dropna().unique()))
        hs6_selected = st.multiselect("Optionally filter HS6 Codes", hs6_all)
        if hs6_selected:
            combined_df_custom = combined_df_custom[combined_df_custom['HS6'].isin(hs6_selected)]

        st.subheader("Select Flow Graph Types to Generate")
sunburst_checked = st.checkbox("🌐 Sunburst Chart")
icicle_checked = st.checkbox("🧊 Icicle Chart")
treemap_checked = st.checkbox("🌲 Treemap")
sankey_checked = st.checkbox("🔀 Sankey Diagram")

if st.button("Generate Selected Graphs"):
            if sunburst_checked:
                st.markdown("### 🌐 Sunburst Chart (All Years Combined)")
                grouped = combined_df_custom.groupby(["flowDesc", "HS2", "HS4", "HS6"])["value"].sum().reset_index()
                fig = px.sunburst(grouped, path=["flowDesc", "HS2", "HS4", "HS6"], values="value", color="flowDesc")
                fig.update_traces(insidetextorientation='radial')
                st.plotly_chart(fig, use_container_width=True)

            if icicle_checked:
                st.markdown("### 🧊 Icicle Chart (All Years Combined)")
                grouped = combined_df_custom.groupby(["flowDesc", "HS2", "HS4", "HS6"])["value"].sum().reset_index()
                fig = px.icicle(grouped, path=["flowDesc", "HS2", "HS4", "HS6"], values="value", color="flowDesc")
                st.plotly_chart(fig, use_container_width=True)

            if treemap_checked:
                st.markdown("### 🌲 Treemap (All Years Combined)")
                grouped = combined_df_custom.groupby(["flowDesc", "HS2", "HS4", "HS6"])["value"].sum().reset_index()
                fig = px.treemap(grouped, path=["flowDesc", "HS2", "HS4", "HS6"], values="value", color="flowDesc")
                st.plotly_chart(fig, use_container_width=True)

            if sankey_checked:
                st.markdown("### 🔀 Sankey Diagram – Flow from HS2 to HS6")
                grouped = combined_df_custom.groupby(["flowDesc", "HS2", "HS4", "HS6"])["value"].sum().reset_index()

                sankey_data = []
                labels = []
                label_map = {}
                index = 0

                for level in ["HS2", "HS4", "HS6"]:
                    unique = grouped[level].unique()
                    for item in unique:
                        if item not in label_map:
                            label_map[item] = index
                            labels.append(item)
                            index += 1

                for _, row in grouped.iterrows():
                    sankey_data.append({
                        "source": label_map[row["HS2"]],
                        "target": label_map[row["HS4"]],
                        "value": row["value"]
                    })
                    sankey_data.append({
                        "source": label_map[row["HS4"]],
                        "target": label_map[row["HS6"]],
                        "value": row["value"]
                    })

                import plotly.graph_objects as go

                fig = go.Figure(data=[go.Sankey(
    arrangement="snap",
    node=dict(
        pad=15,
        thickness=20,
        line=dict(color="gray", width=0.5),
        label=labels,
        color=["#4B8BBE" if label in grouped['HS2'].values else "#306998" if label in grouped['HS4'].values else "#FFE873" for label in labels]
    ),
    link=dict(
        source=[x["source"] for x in sankey_data],
        target=[x["target"] for x in sankey_data],
        value=[x["value"] for x in sankey_data],
        color="rgba(192,192,192,0.4)",
        hovertemplate='From %{source.label} to %{target.label}<br>Value: %{value:,.0f}<extra></extra>'
    )
)])

                fig.update_layout(
    title_text="Sankey Diagram: Flow from HS2 → HS4 → HS6",
    font_size=12,
    margin=dict(l=20, r=20, t=50, b=20),
    height=600
)
                st.plotly_chart(fig, use_container_width=True)

# ========================= END CUSTOM SECTION =========================
