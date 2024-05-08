import streamlit as st
import pandas as pd

# Sample DataFrame containing mutual fund names
df_names = pd.read_parquet('mstar_funds.parquet')

names = df_names['Name'].to_list()
names.extend([' '])
# read mstar mf names

selected_mutual_funds = st.sidebar.selectbox("Select Mutual Funds:", names, index=len(names) - 1)

col1, col2 = st.sidebar.columns([0.8, 0.2])

include_mf = col1.checkbox(label=f"{selected_mutual_funds}", key=1, value=True)
include_units = col2.text_input(label="Units", key=2, value=1)

