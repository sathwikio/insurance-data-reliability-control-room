"""Insurance Data Reliability Control Room — local dashboard.

Reads the final analytics dataset (data/final_analytics.csv) produced by
src/build_final.py. Two layers are shown side by side and never merged:
deterministic metrics and the Jev decision layer.

Run: .venv/bin/python -m streamlit run dashboard/app.py
"""

from pathlib import Path

import pandas as pd
import streamlit as st

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "final_analytics.csv"

ATTENTION = ("WATCH", "INVESTIGATE")

TABLE_COLUMNS = [
    "run_id", "pipeline_name", "domain", "run_timestamp", "status",
    "jev_decision", "jev_confidence", "failure_rate", "row_count_variance",
    "duration_variance", "freshness_delay_minutes", "freshness_severity",
    "schema_drift",
]

METRIC_COLUMNS = [
    "expected_rows", "actual_rows", "failed_rows", "failure_rate",
    "row_count_variance", "duration_seconds", "expected_duration_seconds",
    "duration_variance", "freshness_delay_minutes", "freshness_severity",
    "schema_drift", "schema_drift_present", "error_present",
]


@st.cache_data
def load_data() -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH)
    df["run_timestamp"] = pd.to_datetime(df["run_timestamp"])
    return df.sort_values("run_timestamp").reset_index(drop=True)


def render_kpis(df: pd.DataFrame) -> None:
    total = len(df)
    healthy = int((df.jev_decision == "HEALTHY").sum())
    attention = int(df.jev_decision.isin(ATTENTION).sum())
    blocked = int((df.jev_decision == "BLOCK").sum())

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total pipeline runs", f"{total:,}")
    col2.metric("Healthy %", f"{healthy / total:.0%}" if total else "n/a")
    col3.metric("Requires attention", f"{attention:,}")
    col4.metric("Blocked pipelines", f"{blocked:,}")


def render_filters(df: pd.DataFrame) -> pd.DataFrame:
    with st.sidebar:
        st.header("Filters")
        domains = st.multiselect("Domain", sorted(df.domain.unique()))
        decisions = st.multiselect("Jev decision", ["HEALTHY", "WATCH", "INVESTIGATE", "BLOCK"])
        drift_only = st.checkbox("Schema drift only")

    filtered = df.copy()
    if domains:
        filtered = filtered[filtered.domain.isin(domains)]
    if decisions:
        filtered = filtered[filtered.jev_decision.isin(decisions)]
    if drift_only:
        filtered = filtered[filtered.schema_drift_present]
    return filtered


def render_distribution(df: pd.DataFrame) -> None:
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Decision distribution")
        st.bar_chart(df.jev_decision.value_counts())
    with col2:
        st.subheader("Domain distribution")
        st.bar_chart(df.domain.value_counts())


def render_trend(df: pd.DataFrame) -> None:
    st.subheader("Freshness and duration trend")
    metric = st.radio(
        "Trend metric",
        ["Freshness delay (minutes)", "Duration variance"],
        horizontal=True,
    )
    trend = df.set_index("run_timestamp")
    if metric.startswith("Freshness"):
        st.line_chart(trend["freshness_delay_minutes"])
    else:
        st.line_chart(trend["duration_variance"])


def render_table(df: pd.DataFrame) -> None:
    st.subheader("Pipeline health table")
    st.dataframe(
        df[TABLE_COLUMNS].set_index("run_id"),
        width="stretch",
        height=280,
    )


def render_detail(df: pd.DataFrame) -> None:
    st.subheader("Pipeline detail view")
    run_id = st.selectbox("Run", df.run_id.sort_values().tolist())
    run = df[df.run_id == run_id].iloc[0]

    left, right = st.columns([3, 1])
    with left:
        st.markdown("**Deterministic metrics**")
        details = {
            "pipeline": run.pipeline_name,
            "domain": run.domain,
            "run timestamp": str(run.run_timestamp),
            "status": run.status,
            **{c: str(run[c]) for c in METRIC_COLUMNS},
        }
        st.table(pd.DataFrame({"field": details.keys(), "value": details.values()})
                 .set_index("field"))
    with right:
        st.markdown("**Jev decision**")
        st.metric(label="Decision", value=run.jev_decision)
        st.metric(
            label="Confidence",
            value=(f"{run.jev_confidence:.2f}" if pd.notna(run.jev_confidence) else "n/a"),
        )
        if pd.notna(run.error_message):
            st.caption(f"Error: {run.error_message}")


def main() -> None:
    st.set_page_config(page_title="Insurance Data Reliability Control Room", layout="wide")
    st.title("Insurance Data Reliability Control Room")
    st.caption("Deterministic pipeline metrics with the Jev decision layer")

    df = load_data()
    if df.empty:
        st.error("final_analytics.csv is empty or missing — run src.build_final first.")
        return

    filtered = render_filters(df)
    if filtered.empty:
        st.warning("No runs match the current filters.")
        return

    render_kpis(filtered)
    st.divider()
    render_distribution(filtered)
    st.divider()
    render_trend(filtered)
    st.divider()
    render_table(filtered)
    st.divider()
    render_detail(filtered)


main()
