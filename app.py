import streamlit as st

from qwendolyn.llm import OllamaLLM

st.title("Qwendolyn")

if "llm" not in st.session_state:
    st.session_state.llm = OllamaLLM()

prompt = st.text_area("Prompt")

col1, col2 = st.columns(2)

with col1:
    dev = st.button("👨‍💻 Dev")

with col2:
    analyst = st.button("📊 Analyst")

if dev:
    response = st.session_state.llm.invoke(prompt, mode="dev")
    st.write(response)

if analyst:
    response = st.session_state.llm.invoke(prompt, mode="analyst")
    st.write(response)