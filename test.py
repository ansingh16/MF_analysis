import streamlit as st

# Custom CSS to style the tabs
css = """
<style>
/* Increase the font size of the tabs */
.stTab, .stTab > div > div > div {
    font-size: 20px !important;
}

/* Justify the tabs to the center */
.stTabs {
    justify-content: center !important;
}
</style>
"""

# Apply the custom CSS
st.markdown(css, unsafe_allow_html=True)

# Function to execute when Tab 1 is clicked
def function1():
    st.write("Function 1 executed")

# Function to execute when Tab 2 is clicked
def function2():
    st.write("Function 2 executed")

# Function to execute when Tab 3 is clicked
def function3():
    st.write("Function 3 executed")

# Display the tabs
selected_tab = st.tabs(["Tab 1", "Tab 2", "Tab 3"])

# Execute the corresponding function based on the selected tab
if selected_tab == "Tab 1":
    function1()
elif selected_tab == "Tab 2":
    function2()
elif selected_tab == "Tab 3":
    function3()
