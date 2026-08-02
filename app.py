import streamlit as st

from qwendolyn.llm import OllamaLLM
from qwendolyn.utils.logging import get_logger

logger = get_logger("app", log_file="app")

st.title("Qwendolyn")
logger.info("Streamlit app initialized")

if "llm" not in st.session_state:
    logger.info("Creating Ollama LLM session")
    st.session_state.llm = OllamaLLM()

prompt = st.text_area("Prompt")

col1, col2 = st.columns(2)

with col1:
    dev = st.button("👨‍💻 Dev")

with col2:
    analyst = st.button("📊 Analyst")

if dev:
    logger.info("User triggered developer mode")
    response = st.session_state.llm.invoke(prompt, mode="dev")
    st.write(response)

if analyst:
    logger.info("User triggered analyst mode")
    response = st.session_state.llm.invoke(prompt, mode="analyst")
    st.write(response)