import streamlit as st

from qwendolyn.bootstrap import create_agent


st.set_page_config(
    page_title="Qwendolyn",
    layout="wide",
)

st.title("Qwendolyn")

if "agent" not in st.session_state:
    st.session_state.agent = create_agent()

if "messages" not in st.session_state:
    st.session_state.messages = []


col1, col2 = st.columns(2)

with col1:
    developer = st.button("👨‍💻 Developer", use_container_width=True)

with col2:
    analyst = st.button("📊 Analyst", use_container_width=True)


prompt = st.chat_input("Ask Qwendolyn...")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


if prompt:

    persona = "developer" if developer else "analyst"

    st.session_state.messages.append(
        {
            "role": "user",
            "content": prompt,
        }
    )

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):

        with st.spinner("Thinking..."):

            response = st.session_state.agent.run(
                prompt=prompt,
                persona=persona,
            )

            st.markdown(response)

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": response,
        }
    )