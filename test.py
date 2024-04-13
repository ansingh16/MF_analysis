import streamlit as st
import pandas as pd

# Function to create and display the DataFrame
def display_dataframe(inputs):
    if inputs:
        st.subheader("Consolidated DataFrame:")
        df = pd.DataFrame(inputs)
        st.write(df)

# Main Streamlit app
def main():
    st.title("Scheme URL and Units Input App")
    
    # Initialize an empty list to store inputs
    if 'inputs' not in st.session_state:
        st.session_state.inputs = []
    
    # Sidebar input fields
    scheme_url = st.sidebar.text_input("Enter Scheme URL:")
    units = st.sidebar.text_input("Enter Units:")
    
    # Check if add button is pressed
    if st.sidebar.button("Add"):
        if scheme_url and units:
            # Add entry to the list of inputs
            st.session_state.inputs.append({'Scheme URL': scheme_url, 'Units': units, 'Checkbox': True})
    
    # Display entries with checkboxes in the sidebar
    st.sidebar.subheader("Entries:")
    for i, input_data in enumerate(st.session_state.inputs):
        checkbox_key = f"checkbox_{i}"
        units_key = f"units_{i}"
        
        print(st.session_state.inputs[i]['Scheme URL'])

        # Place checkbox and text input side by side using columns layout
        col1, col2 = st.sidebar.columns([1, 1])
        st.session_state.inputs[i]['Checkbox'] = col1.checkbox(label=f"Entry {i+1}", key=checkbox_key, value=input_data['Checkbox'])
        st.session_state.inputs[i]['Units'] = col2.text_input(label="Units", key=units_key, value=input_data['Units'])
    
    # Filter out unchecked entries and update the DataFrame
    inputs = [input_data for input_data in st.session_state.inputs if input_data['Checkbox']]
    
    # Display the consolidated DataFrame
    display_dataframe(inputs)

if __name__ == "__main__":
    main()
