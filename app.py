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
        "🔄 Reinitialize Agent",
        use_container_width=True,
    ):
        st.session_state.agent = create_agent()
        st.success("Agent reinitialized.")

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

prompt = st.chat_input("Give Qwendolyn a task...")


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
            "Planning task...",
            expanded=True,
        )

        try:

            status.write("🧠 Planning")
            status.write("⚙️ Executing capabilities")
            status.write("✅ Verifying outputs")
            status.write("📝 Preparing response")

            response = st.session_state.agent.run(
                prompt=prompt,
            )

            status.update(
                label="Task complete",
                state="complete",
            )

        except Exception as ex:

            status.update(
                label="Task failed",
                state="error",
            )

            response = (
                "❌ **Task failed**\n\n"
                f"```text\n{ex}\n```"
            )

        st.markdown(response)

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": response,
        }
    )