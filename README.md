# Qwendolyn

Qwendolyn is a local autonomous data-engineering agent. For each objective it
plans work, executes one of three high-level capabilities, inspects the
result, and continues until it has verified completion or encountered a
failure.

The capabilities are deliberately narrow in number:

- **Filesystem** manages workspace paths and UTF-8 text files.
- **Python** is the workhorse for data engineering and arbitrary workspace code.
- **Database** manages DuckDB SQL, metadata, views, and Parquet interchange.

Every operation returns one `CapabilityResult` contract containing success,
message, data, artifacts, metrics, logs, and error information. The planner
receives those records as evidence; a separate responder produces the final
user-facing summary from the same verified records.

## Install
pip install -r requirements.txt

## Start Ollama
ollama serve

## Pull a model
ollama pull qwen3:8b

## Run
streamlit run app.py
