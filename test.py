import pandas as pd
import numpy as np
import altair as alt

# Sample data for two portfolios with allocations to different sectors
portfolio1 = {
    'Technology': 0.2,
    'Healthcare': 0.3,
    'Finance': 0.1,
    'Energy': 0.2,
    'Consumer Goods': 0.2
}

portfolio2 = {
    'Technology': 0.25,
    'Healthcare': 0.25,
    'Finance': 0.15,
    'Energy': 0.2,
    'Consumer Goods': 0.15
}

# Convert dictionaries to pandas DataFrames
df_portfolio1 = pd.DataFrame.from_dict(portfolio1, orient='index', columns=['Portfolio 1'])
df_portfolio2 = pd.DataFrame.from_dict(portfolio2, orient='index', columns=['Portfolio 2'])

# Merge the two DataFrames on sector names
df_merged = pd.merge(df_portfolio1, df_portfolio2, left_index=True, right_index=True, how='outer')

# Fill missing values with 0
df_merged.fillna(0, inplace=True)

# Calculate correlation coefficient
correlation_coefficient = np.corrcoef(df_merged['Portfolio 1'], df_merged['Portfolio 2'])[0, 1]

# Visualization using Altair
df_merged.reset_index(inplace=True)
df_long = df_merged.melt('index')

chart = alt.Chart(df_long).mark_bar().encode(
    x='index:N',
    y='value:Q',
    color='variable:N',
    column='variable:N'
).properties(
    width=200
)

# Display the visualization
chart.show()

# Print the correlation coefficient
print(f'Correlation Coefficient: {correlation_coefficient}')
