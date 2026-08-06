import streamlit as st

from qwendolyn.agent.bootstrap import create_agent


st.set_page_config(
    page_title="Qwendolyn",
    page_icon="🤖",
    layout="wide",
)

st.title("🤖 Qwendolyn")
st.caption("Your autonomous Python data engineer.")


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
        "🔄 Reload Agent",
        use_container_width=True,
    ):
        st.session_state.agent = create_agent()
        st.success("Agent reloaded.")

    if st.button(
        "🗑️ Clear Conversation",
        use_container_width=True,
    ):
        st.session_state.messages.clear()
        st.rerun()


# -----------------------------------------------------------------------------
# Conversation History
# -----------------------------------------------------------------------------

for message in st.session_state.messages:

    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# -----------------------------------------------------------------------------
# Chat Input
# -----------------------------------------------------------------------------

prompt = st.chat_input(
    "Describe the Python task..."
)

if prompt:

    st.session_state.messages.append(
        {
            "role": "user",
            "content": prompt,
        }
    )

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):

        status = st.status(
            "Running...",
            expanded=True,
        )

        try:

            status.write("🧠 Thinking")
            status.write("🐍 Generating Python")
            status.write("▶️ Executing")
            status.write("🔁 Iterating until complete")

            response = st.session_state.agent.run(
                prompt=prompt,
            )

            status.update(
                label="Completed",
                state="complete",
            )

        except Exception as ex:

            response = (
                "### ❌ Execution Failed\n\n"
                f"```text\n{ex}\n```"
            )

            status.update(
                label="Failed",
                state="error",
            )

        st.markdown(response)

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": response,
        }
    )