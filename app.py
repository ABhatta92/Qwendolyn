import json
from pathlib import Path

import streamlit as st

from qwendolyn import config
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
            "Frontend",
        ],
    )

    st.divider()

    if st.button(
        "🔄 Reload Agents",
        use_container_width=True,
    ):

        st.session_state.agents = create_agents()
        st.success("Agents reloaded.")

    if st.button(
        "🗑️ Clear Conversation",
        use_container_width=True,
    ):

        st.session_state.messages.clear()
        st.rerun()


# -----------------------------------------------------------------------------
# Tabs
# -----------------------------------------------------------------------------

agent_tab, runs_tab = st.tabs(
    [
        "💬 Agent",
        "📈 Runs",
    ]
)


# =============================================================================
# Agent
# =============================================================================

with agent_tab:

    for message in st.session_state.messages:

        with st.chat_message(message["role"]):

            if message["role"] == "assistant":

                st.caption(
                    f"Agent: {message['agent']}"
                )

            st.markdown(
                message["content"]
            )

    prompt = st.chat_input(
        f"Ask the {agent_name} Agent..."
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
                f"{agent_name} Agent working..."
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


# =============================================================================
# Runs
# =============================================================================

with runs_tab:

    st.subheader("Run Explorer")

    runs_root = (
        config.LOGS
        / "runs"
    )

    if not runs_root.exists():

        st.info(
            "No runs have been recorded."
        )

        st.stop()

    run_dirs = sorted(
        [
            path
            for path in runs_root.iterdir()
            if path.is_dir()
        ],
        reverse=True,
    )

    if not run_dirs:

        st.info(
            "No runs have been recorded."
        )

        st.stop()

    selected_run = st.selectbox(
        "Run",
        run_dirs,
        format_func=lambda path: path.name,
    )

    metadata_path = (
        selected_run
        / "run.json"
    )

    if metadata_path.exists():

        metadata = json.loads(
            metadata_path.read_text(
                encoding="utf-8"
            )
        )

        c1, c2, c3, c4 = st.columns(4)

        c1.metric(
            "Agent",
            metadata["agent"],
        )

        c2.metric(
            "Iterations",
            metadata["iterations"],
        )

        c3.metric(
            "Success",
            str(metadata["success"]),
        )

        c4.metric(
            "Started",
            metadata["started_at"][:19],
        )

        with st.expander(
            "Objective",
            expanded=True,
        ):

            st.write(
                metadata["objective"]
            )

    artifacts = (
        selected_run
        / "artifacts"
    )

    prompt_files = sorted(
        artifacts.glob(
            "prompt_*.txt"
        )
    )

    if not prompt_files:

        st.info(
            "No iterations found."
        )

        st.stop()

    iterations = [
        path.stem.split("_")[-1]
        for path in prompt_files
    ]

    selected_iteration = st.selectbox(
        "Iteration",
        iterations,
    )

    prefix = (
        f"{selected_iteration}"
    )

    prompt_file = (
        artifacts
        / f"prompt_{prefix}.txt"
    )

    response_file = (
        artifacts
        / f"response_{prefix}.txt"
    )

    execution_file = (
        artifacts
        / f"execution_{prefix}.json"
    )

    script_candidates = sorted(
        artifacts.glob(
            f"script_{prefix}.*"
        )
    )

    prompt_tab, response_tab, script_tab, execution_tab = st.tabs(
        [
            "Prompt",
            "Response",
            "Script",
            "Execution",
        ]
    )

    with prompt_tab:

        if prompt_file.exists():

            st.code(
                prompt_file.read_text(
                    encoding="utf-8"
                ),
                language="text",
            )

    with response_tab:

        if response_file.exists():

            st.code(
                response_file.read_text(
                    encoding="utf-8"
                ),
                language="text",
            )

    with script_tab:

        if script_candidates:

            script = script_candidates[0]

            extension = (
                script.suffix.lstrip(".")
                or "text"
            )

            st.code(
                script.read_text(
                    encoding="utf-8"
                ),
                language=extension,
            )

    with execution_tab:

        if execution_file.exists():

            st.json(
                json.loads(
                    execution_file.read_text(
                        encoding="utf-8"
                    )
                )
            )