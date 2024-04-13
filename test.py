import streamlit as st

input = st.text_input("text", key="text")
st.session_state['text1'] = []
def clear_text():
    if "text" in st.session_state:
        test2 = st.session_state["text"]
        st.session_state["text"] = ""
        st.session_state.text1.append(test2) 
    
st.button("clear text input", on_click=clear_text)
st.write(st.session_state.text1)