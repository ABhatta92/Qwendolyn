import streamlit as st

from qwendolyn.bootstrap import create_agent

st.title("Qwendolyn")

if "agent" not in st.session_state:
    st.session_state.agent = create_agent()

prompt = st.text_area("Prompt")

if st.button("Run"):

    response = st.session_state.agent.run(prompt)

    st.write(response)