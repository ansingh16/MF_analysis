import streamlit as st

# Sample data for selection
options = ['Apple', 'Banana', 'Cherry', 'Date', 'Elderberry', 'Fig', 'Grapes', 'Honeydew']

# Create a search box that filters the options
search_term = st.text_input('Search')

# Filter the options based on the search term
filtered_options = [option for option in options if search_term.lower() in option.lower()]

# Display the selectbox with filtered options
selected_option = st.selectbox('Select an option', filtered_options)

st.write(f'You selected: {selected_option}')
