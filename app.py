import streamlit as st
import pandas as pd
import plotly.express as px

st.title("Trade Data Visualizer (Importer vs Exporter)")

uploaded_files = st.file_uploader("Upload two trade CSV files", type="csv", accept_multiple_files=True)

if len(uploaded_files) == 2:
    df1 = pd.read_csv(uploaded_files[0])
    df2 = pd.read_csv(uploaded_files[1])

    # Determine flow direction
    if 'Export' in df1['flowDesc'].iloc[0]:
        df_exports, df_imports = df1, df2
    else:
        df_exports, df_imports = df2, df1

    exp_country = df_exports["reporterDesc"].iloc[0]
    imp_country = df_exports["partnerDesc"].iloc[0]

    # Filter HS6 and enrich
    df_exports = df_exports[df_exports["cmdCode"].astype(str).str.len() == 6].copy()
    df_imports = df_imports[df_imports["cmdCode"].astype(str).str.len() == 6].copy()

    for df in [df_exports, df_imports]:
        df["cmdCode"] = df["cmdCode"].astype(str)
        df["HS6"] = df["cmdCode"]
        df["HS4"] = df["cmdCode"].str[:4]
        df["HS2"] = df["cmdCode"].str[:2]
        df["year"] = df["period"].astype(str).str[:4]

    df_exports["value_export"] = pd.to_numeric(df_exports.get("fobvalue"), errors="coerce")
    df_exports["weight_export"] = pd.to_numeric(df_exports.get("netWgt"), errors="coerce")
    df_imports["value_import"] = pd.to_numeric(df_imports.get("cifvalue"), errors="coerce")
    df_imports["weight_import"] = pd.to_numeric(df_imports.get("netWgt"), errors="coerce")

    df_exports.dropna(subset=["value_export", "weight_export"], inplace=True)
    df_imports.dropna(subset=["value_import", "weight_import"], inplace=True)

    # Comparison
    exports_grouped = df_exports.groupby(["year", "HS2", "HS4", "HS6"])[["value_export", "weight_export"]].sum().reset_index()
    imports_grouped = df_imports.groupby(["year", "HS2", "HS4", "HS6"])[["value_import", "weight_import"]].sum().reset_index()
    df = pd.merge(exports_grouped, imports_grouped, on=["year", "HS2", "HS4", "HS6"], how="outer").fillna(0)

    df_melted = pd.melt(df, id_vars=["year", "HS2", "HS4", "HS6"],
                        value_vars=["value_export", "value_import"],
                        var_name="Source", value_name="TradeValue")
    df_melted["Source"] = df_melted["Source"].map({
        "value_export": f"{exp_country} Report",
        "value_import": f"{imp_country} Report"
    })

    year_list = df_melted["year"].unique()
    selected_year = st.selectbox("Select Year", sorted(year_list))

    df_year = df_melted[df_melted["year"] == selected_year]
    hs2_codes = ", ".join(sorted(df_year["HS2"].unique()))

    # Charts
    st.subheader("Sunburst")
    st.plotly_chart(px.sunburst(df_year, path=["Source", "HS2", "HS4", "HS6"], values="TradeValue",
                                title=f"{exp_country} vs {imp_country} | Sunburst – {selected_year} | HS2: {hs2_codes}"))

    st.subheader("Treemap")
    st.plotly_chart(px.treemap(df_year, path=["Source", "HS2", "HS4", "HS6"], values="TradeValue",
                               title=f"{exp_country} vs {imp_country} | Treemap – {selected_year}"))

    st.subheader("Bar Chart – Trade Value by HS4")
    df_hs4 = df_year.groupby(["HS4", "Source"])["TradeValue"].sum().reset_index()
    st.plotly_chart(px.bar(df_hs4, x="HS4", y="TradeValue", color="Source", barmode="group",
                           title=f"Trade Value by HS4 – {selected_year}"))

else:
    st.info("Please upload exactly 2 CSV files.")
