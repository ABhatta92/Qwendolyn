from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st

from qwendolyn import config


# =============================================================================
# Configuration
# =============================================================================

DB_PATH = (
    Path(config.LOGS)
    / "runs.db"
)


# =============================================================================
# Page
# =============================================================================

st.set_page_config(
    page_title="Qwendolyn Runs",
    page_icon="📊",
    layout="wide",
)

st.title("📊 Qwendolyn Run Explorer")
st.caption("Structured execution history")


# =============================================================================
# Database
# =============================================================================

def get_connection() -> sqlite3.Connection:

    connection = sqlite3.connect(
        DB_PATH
    )

    connection.row_factory = sqlite3.Row

    return connection


def load_runs() -> pd.DataFrame:

    if not DB_PATH.exists():

        return pd.DataFrame()

    with get_connection() as connection:

        return pd.read_sql_query(
            """
            SELECT
                id,
                agent,
                objective,
                started_at,
                finished_at,
                status
            FROM runs
            ORDER BY started_at DESC
            """,
            connection,
        )


def load_events(
    run_id: str,
) -> pd.DataFrame:

    with get_connection() as connection:

        return pd.read_sql_query(
            """
            SELECT
                id,
                timestamp,
                step,
                attempt,
                event_type,
                status,
                duration,
                message,
                stdout,
                stderr
            FROM events
            WHERE run_id = ?
            ORDER BY id ASC
            """,
            connection,
            params=(run_id,),
        )


# =============================================================================
# Helpers
# =============================================================================

def calculate_duration(
    started_at,
    finished_at,
    status=None,
):

    if (
        started_at is None
        or pd.isna(started_at)
    ):
        return None

    try:

        start = pd.to_datetime(
            started_at,
            utc=True,
        )

        if (
            finished_at is None
            or pd.isna(finished_at)
        ):

            if status == "RUNNING":

                now = pd.Timestamp.now(
                    tz="UTC"
                )

                return (
                    now - start
                ).total_seconds()

            return None

        end = pd.to_datetime(
            finished_at,
            utc=True,
        )

        return (
            end - start
        ).total_seconds()

    except (
        TypeError,
        ValueError,
        OverflowError,
    ):

        return None


def format_duration(
    seconds,
) -> str:

    if seconds is None:
        return "—"

    try:

        seconds = float(seconds)

    except (
        TypeError,
        ValueError,
    ):

        return "—"

    if pd.isna(seconds):
        return "—"

    if seconds < 0:
        return "—"

    if seconds < 60:

        return f"{seconds:.1f}s"

    minutes = int(
        seconds // 60
    )

    remaining = int(
        seconds % 60
    )

    if minutes < 60:

        return (
            f"{minutes}m "
            f"{remaining}s"
        )

    hours = minutes // 60

    minutes = minutes % 60

    return (
        f"{hours}h "
        f"{minutes}m "
        f"{remaining}s"
    )


def status_icon(
    status: str | None,
) -> str:

    if status == "SUCCESS":
        return "✅"

    if status == "FAILED":
        return "❌"

    if status == "RUNNING":
        return "🔄"

    return "•"


def safe_text(
    value,
) -> str:

    if value is None:
        return ""

    if pd.isna(value):
        return ""

    return str(value)


# =============================================================================
# Database Check
# =============================================================================

if not DB_PATH.exists():

    st.warning(
        f"No run database found at `{DB_PATH}`."
    )

    st.info(
        "Run Qwendolyn once to create the run database."
    )

    st.stop()


runs = load_runs()


if runs.empty:

    st.info(
        "No runs have been recorded yet."
    )

    st.stop()


# =============================================================================
# Sidebar Filters
# =============================================================================

with st.sidebar:

    st.header("Filters")

    agents = sorted(
        runs["agent"]
        .dropna()
        .unique()
        .tolist()
    )

    selected_agent = st.selectbox(
        "Agent",
        ["All"] + agents,
    )

    statuses = sorted(
        runs["status"]
        .dropna()
        .unique()
        .tolist()
    )

    selected_status = st.selectbox(
        "Status",
        ["All"] + statuses,
    )

    st.divider()

    if st.button(
        "🔄 Refresh",
        use_container_width=True,
    ):

        st.rerun()


# =============================================================================
# Apply Filters
# =============================================================================

filtered_runs = runs.copy()


if selected_agent != "All":

    filtered_runs = filtered_runs[
        filtered_runs["agent"]
        == selected_agent
    ]


if selected_status != "All":

    filtered_runs = filtered_runs[
        filtered_runs["status"]
        == selected_status
    ]


if filtered_runs.empty:

    st.info(
        "No runs match the selected filters."
    )

    st.stop()


# =============================================================================
# Run Selection
# =============================================================================

st.subheader(
    f"Runs ({len(filtered_runs)})"
)


def run_label(
    row,
) -> str:

    icon = status_icon(
        row["status"]
    )

    objective = str(
        row["objective"]
    )

    if len(objective) > 90:

        objective = (
            objective[:87]
            + "..."
        )

    return (
        f"{icon} "
        f"{row['started_at'][:19]} — "
        f"{row['agent']} — "
        f"{objective}"
    )


run_options = filtered_runs.to_dict(
    orient="records"
)


selected_index = st.selectbox(
    "Select run",
    range(
        len(run_options)
    ),
    format_func=lambda index:
        run_label(
            run_options[index]
        ),
)


selected_run = run_options[
    selected_index
]


run_id = selected_run["id"]


# =============================================================================
# Run Overview
# =============================================================================

st.divider()

st.subheader("Run Overview")


duration = calculate_duration(
    selected_run["started_at"],
    selected_run["finished_at"],
    selected_run["status"],
)

events = load_events(
    run_id
)


steps = (
    events["step"]
    .dropna()
    .nunique()
    if not events.empty
    else 0
)


llm_calls = (
    len(
        events[
            events["event_type"]
            == "LLM_CALL"
        ]
    )
    if not events.empty
    else 0
)


executions = (
    len(
        events[
            events["event_type"]
            == "PYTHON_EXECUTION"
        ]
    )
    if not events.empty
    else 0
)


failures = (
    len(
        events[
            events["status"]
            == "FAILED"
        ]
    )
    if not events.empty
    else 0
)


c1, c2, c3, c4, c5 = st.columns(5)


c1.metric(
    "Status",
    selected_run["status"],
)

c2.metric(
    "Duration",
    format_duration(
        duration
    ),
)

c3.metric(
    "Steps",
    steps,
)

c4.metric(
    "LLM Calls",
    llm_calls,
)

c5.metric(
    "Failures",
    failures,
)


st.markdown(
    f"**Agent:** `{selected_run['agent']}`"
)

st.markdown(
    f"**Run ID:** `{run_id}`"
)


with st.expander(
    "Objective",
    expanded=True,
):

    st.write(
        selected_run["objective"]
    )


# =============================================================================
# Timeline
# =============================================================================

st.divider()

st.subheader("Timeline")


if events.empty:

    st.info(
        "No events recorded for this run."
    )

else:

    for _, event in events.iterrows():

        icon = status_icon(
            event["status"]
        )

        timestamp = str(
            event["timestamp"]
        )

        event_type = str(
            event["event_type"]
        )

        step = event["step"]

        attempt = event["attempt"]

        duration_text = ""

        if pd.notna(
            event["duration"]
        ):

            duration_text = (
                f" · "
                f"{format_duration(event['duration'])}"
            )

        location = ""

        if pd.notna(step):

            location = (
                f" · Step {int(step)}"
            )

        if pd.notna(attempt):

            location += (
                f" · Attempt {int(attempt)}"
            )

        message = safe_text(
            event["message"]
        )

        stdout = safe_text(
            event["stdout"]
        )

        stderr = safe_text(
            event["stderr"]
        )

        with st.container(
            border=True
        ):

            c1, c2, c3 = st.columns(
                [1, 3, 2]
            )

            c1.markdown(
                f"### {icon}"
            )

            c2.markdown(
                f"**{event_type}**"
            )

            c3.caption(
                timestamp
            )

            if location or duration_text:

                st.caption(
                    f"{location}"
                    f"{duration_text}"
                )

            if message:

                st.write(
                    message
                )

            # -------------------------------------------------------------
            # Execution evidence
            # -------------------------------------------------------------

            if event_type == "PYTHON_EXECUTION":

                with st.expander(
                    "Execution details",
                    expanded=(
                        event["status"]
                        == "FAILED"
                    ),
                ):

                    if stdout:

                        st.markdown(
                            "**stdout**"
                        )

                        st.code(
                            stdout,
                            language="text",
                        )

                    else:

                        st.caption(
                            "stdout: empty"
                        )

                    if stderr:

                        st.markdown(
                            "**stderr**"
                        )

                        st.code(
                            stderr,
                            language="text",
                        )

                    else:

                        st.caption(
                            "stderr: empty"
                        )


# =============================================================================
# Raw Events
# =============================================================================

st.divider()

with st.expander(
    "Raw Events",
):

    st.dataframe(
        events,
        use_container_width=True,
        hide_index=True,
    )