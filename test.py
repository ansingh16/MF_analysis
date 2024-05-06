import streamlit as st
import mstarpy
import pandas as pd

if 'dummy_data' not in st.session_state.keys():
    response = mstarpy.search_funds(term="Quant Momentum", field=["Name",'fundShareClassId'], country="in", pageSize=100, currency="INR")
    df = pd.DataFrame(response)
    print(df)
    st.session_state['dummy_data'] = df
else:
    dummy_data = st.session_state['dummy_data']

def checkbox_container(data):
    cols = st.columns(10)
    if cols[1].button('Select All'):
        for i in data.Name:
            st.session_state['dynamic_checkbox_' + i] = True
        st.experimental_rerun()
    if cols[2].button('UnSelect All'):
        for i in data.Name:
            st.session_state['dynamic_checkbox_' + i] = False
        st.experimental_rerun()
    for i in data.Name:
        st.checkbox(i, key='dynamic_checkbox_' + i)

def get_selected_checkboxes():
    return [i.replace('dynamic_checkbox_','') for i in st.session_state.keys() if i.startswith('dynamic_checkbox_') and st.session_state[i]]


checkbox_container(st.session_state.dummy_data)
st.write('You selected:')
st.write(get_selected_checkboxes())