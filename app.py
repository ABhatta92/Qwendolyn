import streamlit as st

from qwendolyn.agent.bootstrap import create_agents


st.set_page_config(
    page_title="Qwendolyn",
    page_icon="🤖",
    layout="wide",
)

st.title("🤖 Qwendolyn")
st.caption("Your AI Workforce")


# -----------------------------------------------------------------------------
# Session State
# -----------------------------------------------------------------------------

if "agents" not in st.session_state:
    st.session_state.agents = create_agents()

if "messages" not in st.session_state:
    st.session_state.messages = []


# -----------------------------------------------------------------------------
# Sidebar
# -----------------------------------------------------------------------------

with st.sidebar:

    st.header("Agent")

    agent_name = st.selectbox(
        "Choose an agent",
        [
            "Python",
        ],
    )

    st.divider()

    if st.button(
        "🔄 Reload Agent",
        use_container_width=True,
    ):

        st.session_state.agents = create_agents()

        st.success(
            "Agent reloaded."
        )

    if st.button(
        "🗑️ Clear Conversation",
        use_container_width=True,
    ):

        st.session_state.messages.clear()

        st.rerun()


# -----------------------------------------------------------------------------
# Agent
# -----------------------------------------------------------------------------

for message in st.session_state.messages:

    with st.chat_message(
        message["role"]
    ):

        if message["role"] == "assistant":

            st.caption(
                f"Agent: {message['agent']}"
            )

        st.markdown(
            message["content"]
        )


prompt = st.chat_input(
    "Ask the Python Agent..."
)

if prompt:

    agent = st.session_state.agents[
        agent_name
    ]

    st.session_state.messages.append(
        {
            "role": "user",
            "content": prompt,
        }
    )

    with st.chat_message("user"):

        st.markdown(prompt)

    with st.chat_message("assistant"):

        st.caption(
            f"Agent: {agent_name}"
        )

        with st.spinner(
            "Python Agent working..."
        ):

            try:

                response = agent.run(
                    prompt
                )

            except Exception as ex:

                response = (
                    "### ❌ Task Failed\n\n"
                    f"```text\n{ex}\n```"
                )

            st.markdown(
                response
            )

    st.session_state.messages.append(
        {
            "role": "assistant",
            "agent": agent_name,
            "content": response,
        }
    )