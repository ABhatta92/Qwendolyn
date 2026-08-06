import streamlit as st

from qwendolyn.agent.bootstrap import create_agent


st.set_page_config(
    page_title="Qwendolyn",
    page_icon="🤖",
    layout="wide",
)

st.title("Qwendolyn")

# -----------------------------------------------------------------------------
# Session State
# -----------------------------------------------------------------------------

if "agent" not in st.session_state:
    st.session_state.agent = create_agent()

if "messages" not in st.session_state:
    st.session_state.messages = []


# -----------------------------------------------------------------------------
# Sidebar
# -----------------------------------------------------------------------------

with st.sidebar:

    st.header("Settings")

    if st.button(
        "🗑️ Clear Conversation",
        use_container_width=True,
    ):
        st.session_state.messages = []
        st.rerun()


# -----------------------------------------------------------------------------
# Conversation History
# -----------------------------------------------------------------------------

for message in st.session_state.messages:

    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# -----------------------------------------------------------------------------
# User Input
# -----------------------------------------------------------------------------

prompt = st.chat_input("Ask Qwendolyn...")


if prompt:

    # Display user message
    st.session_state.messages.append(
        {
            "role": "user",
            "content": prompt,
        }
    )

    with st.chat_message("user"):
        st.markdown(prompt)

    # Run agent
    with st.chat_message("assistant"):

        with st.spinner("Planning and executing..."):

            try:

                response = st.session_state.agent.run(
                    prompt=prompt,
                )

            except Exception as ex:

                response = f"❌ **Task failed**\n\n```text\n{ex}\n```"

            st.markdown(response)

    # Save assistant response
    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": response,
        }
    )
