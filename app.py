import streamlit as st
from llm import OllamaLLM

st.set_page_config(page_title="Ollama Agent", layout="wide")

st.title("Qwendolyn Prototype")

if "llm" not in st.session_state:
    st.session_state.llm = OllamaLLM()

prompt = st.text_area("Command", height=180)

if st.button("Run"):
    if prompt.strip():
        with st.spinner("Thinking..."):
            try:
                response = st.session_state.llm.invoke(prompt)
                st.subheader("Response")
                st.write(response)
            except Exception as e:
                st.error(str(e))
