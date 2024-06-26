import streamlit as st
from streamlit_navigation_bar import st_navbar
import altair as alt
import pandas as pd

st.set_page_config(initial_sidebar_state="expanded")


def function1():
    st.write("Function 1 executed!")
    st.subheader("Sector Holdings of Scheme")
    # plot an altair chart
    
    # Create some sample data
    data = {'Scheme Name': ['Scheme A', 'Scheme B', 'Scheme C'],
            'Sector Name': ['Sector A', 'Sector B', 'Sector C'],
            'Value': [100, 200, 300]}
    
    df = pd.DataFrame(data)

    # Create an Altair chart
    chart = alt.Chart(df).mark_bar().encode(
        x='Sector Name',
        y='Value',
        color='Scheme Name'
    )
    st.altair_chart(chart,use_container_width=True)

def function2():
    st.write("Function 2 executed!")

def function3():
    st.write("Function 3 executed!")





def main():
    pages = ["function1", "function2", "function3"]

    with open("./styles/sidebar.css", "r") as css_file:
        sidebar_css = css_file.read()

    styles = {
        "nav": {
            "background-color": "#7BD192",
        },
        "div": {
            "max-width": "32rem",
        },
        "span": {
            "border-radius": "0.5rem",
            "padding": "0.4375rem 0.625rem",
            "margin": "0 0.125rem",
        },
        "active": {
            "background-color": "rgba(255, 255, 255, 0.25)",
        },
        "hover": {
            "background-color": "rgba(255, 255, 255, 0.35)",
        },
    }

    with st.sidebar:
        st.write("Sidebar")

    # Render the navigation bar
    navigation = st_navbar(pages, styles=styles)


    # Main content area
    st.title("Welcome to My App!")

    # Execute function based on selected option
    if navigation == 'function1':
        function1()
    elif navigation == 'function2':
        function2()
    elif navigation == 'function3':
        function3()

if __name__ == "__main__":
    main()




