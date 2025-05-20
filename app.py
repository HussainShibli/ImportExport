import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px

# Upload files in Colab
from google.colab import files
uploaded = files.upload()

# Load data
import io
file_name = list(uploaded.keys())[0]
df = pd.read_csv(io.BytesIO(uploaded[file_name]))

# Preprocessing
df['year'] = pd.to_datetime(df['periodDesc'], errors='coerce').dt.year
df['HS2'] = df['cmdCode'].astype(str).str[:2]
df['HS4'] = df['cmdCode'].astype(str).str[:4]
df['HS6'] = df['cmdCode'].astype(str).str[:6]

df['flowDesc'] = df['flowDesc'].str.lower()
df['value'] = df['cifvalue'].fillna(df['fobvalue'])  # Use whichever is available

# Let user choose HS level and chart type
hs_level = 'HS2'  # or 'HS4', 'HS6'
metric = 'value'  # or 'netWgt'
chart_type = 'grouped'  # Options: grouped, stacked, diverging, faceted

grouped = df.groupby([hs_level, 'year', 'flowDesc', 'partnerDesc']).agg({metric: 'sum'}).reset_index()

# Choose HS codes to visualize
hs_codes_to_plot = grouped[hs_level].unique()[:5]  # limit for readability

for hs_code in hs_codes_to_plot:
    subset = grouped[grouped[hs_level] == hs_code]
    title = f"{hs_level} {hs_code} - Import vs Export by Country"
    
    if chart_type == 'grouped':
        plt.figure(figsize=(12, 6))
        sns.barplot(data=subset, x='partnerDesc', y=metric, hue='flowDesc')
        plt.title(title)
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()

    elif chart_type == 'stacked':
        pivoted = subset.pivot_table(index='partnerDesc', columns='flowDesc', values=metric, aggfunc='sum').fillna(0)
        pivoted[['import', 'export']].plot(kind='bar', stacked=True, figsize=(12, 6), title=title)
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()

    elif chart_type == 'diverging':
        diverging = subset.copy()
        diverging[metric] = diverging.apply(lambda row: -row[metric] if row['flowDesc'] == 'import' else row[metric], axis=1)
        plt.figure(figsize=(12, 6))
        sns.barplot(data=diverging, x='partnerDesc', y=metric, hue='flowDesc')
        plt.axhline(0, color='black', linewidth=0.8)
        plt.title(title + " (Diverging)")
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()

    elif chart_type == 'faceted':
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
        plt.tight_layout()
        plt.show()
