# Databricks notebook source
# Insurance Data Reliability Control Room — deterministic pipeline + Jev decision join.
#
# Environment: Databricks Free Edition (Serverless, Unity Catalog), any recent DBR.
# Upload the two project files before running:
#   data/pipeline_runs.csv    ->  /Volumes/<your-volume>/insurance/pipeline_runs.csv
#   data/jev_decisions.json   ->  /Volumes/<your-volume>/insurance/jev_decisions.json
# The metric functions below are a verbatim mirror of src/metrics.py so the
# notebook produces the same numbers as the local pipeline.

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Configuration

# COMMAND ----------

VOLUME_PATH = "/Volumes/main/default/insurance"  # <-- edit to your volume path
SOURCE_CSV = f"{VOLUME_PATH}/pipeline_runs.csv"
DECISIONS_JSON = f"{VOLUME_PATH}/jev_decisions.json"

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Deterministic metric functions (mirror of src/metrics.py)

# COMMAND ----------

METRIC_PRECISION = 6
FRESHNESS_THRESHOLDS = [(15, "ON_TIME"), (60, "MINOR"), (240, "MAJOR"), (float("inf"), "SEVERE")]


def failure_rate(run):
    expected = run["expected_rows"]
    return round(run["failed_rows"] / expected, METRIC_PRECISION) if expected else 0.0


def row_count_variance(run):
    expected = run["expected_rows"]
    return round((run["actual_rows"] - expected) / expected, METRIC_PRECISION) if expected else 0.0


def duration_variance(run):
    expected = run["expected_duration_seconds"]
    return round((run["duration_seconds"] - expected) / expected, METRIC_PRECISION) if expected else 0.0


def freshness_severity(delay_minutes):
    for threshold, label in FRESHNESS_THRESHOLDS:
        if delay_minutes <= threshold:
            return label
    return "SEVERE"


def has_schema_drift(run):
    return bool(run["schema_drift"]) and run["schema_drift"] != "none"


def error_present(run):
    return bool(run["error_message"])


# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Source data load

# COMMAND ----------

from pyspark.sql.types import (
    LongType, StringType, StructField, StructType,
)
from pyspark.sql.functions import udf, struct
from pyspark.sql.types import BooleanType, DoubleType

RUN_SCHEMA = StructType([
    StructField("run_id", StringType(), False),
    StructField("pipeline_name", StringType(), False),
    StructField("domain", StringType(), False),
    StructField("run_timestamp", StringType(), False),
    StructField("expected_rows", LongType(), False),
    StructField("actual_rows", LongType(), False),
    StructField("failed_rows", LongType(), False),
    StructField("duration_seconds", LongType(), False),
    StructField("expected_duration_seconds", LongType(), False),
    StructField("freshness_delay_minutes", LongType(), False),
    StructField("schema_drift", StringType(), False),
    StructField("status", StringType(), False),
    StructField("error_message", StringType(), True),
])

runs_df = (
    spark.read.schema(RUN_SCHEMA)
    .option("header", "true")
    .csv(SOURCE_CSV)
)
display(runs_df.limit(5))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Transformations — deterministic metric columns

# COMMAND ----------

ARGS = struct(
    "expected_rows", "actual_rows", "failed_rows",
    "duration_seconds", "expected_duration_seconds",
    "freshness_delay_minutes", "schema_drift", "error_message",
)

metrics_df = runs_df.select(
    "*",
    udf(failure_rate, DoubleType())(ARGS).alias("failure_rate"),
    udf(row_count_variance, DoubleType())(ARGS).alias("row_count_variance"),
    udf(duration_variance, DoubleType())(ARGS).alias("duration_variance"),
    udf(lambda r: freshness_severity(r["freshness_delay_minutes"]), StringType())(ARGS)
        .alias("freshness_severity"),
    udf(has_schema_drift, BooleanType())(ARGS).alias("schema_drift_present"),
    udf(error_present, BooleanType())(ARGS).alias("error_present"),
)
display(metrics_df)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5. Delta table write (deterministic layer)

# COMMAND ----------

metrics_df.write.format("delta").mode("overwrite").saveAsTable("main.default.pipeline_metrics")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 6. Jev result load and join

# COMMAND ----------

from pyspark.sql.functions import col

DECISION_SCHEMA = StructType([
    StructField("run_id", StringType(), False),
    StructField("decision", StringType(), False),
    StructField("confidence", DoubleType(), True),
])

decisions_df = (
    spark.read.schema(DECISION_SCHEMA)
    .option("multiLine", "true")
    .json(DECISIONS_JSON)
)

# Guard: every source run must have exactly one valid Jev decision.
metric_ids = {row.run_id for row in metrics_df.select("run_id").collect()}
decision_rows = decisions_df.collect()
assert {r.run_id for r in decision_rows} == metric_ids, "decision coverage mismatch"
assert len(decision_rows) == len({r.run_id for r in decision_rows}), "duplicate run_id in decisions"
assert {r.decision for r in decision_rows} <= {"HEALTHY", "WATCH", "INVESTIGATE", "BLOCK"}, "bad label"

final_df = metrics_df.join(
    decisions_df
        .withColumnRenamed("decision", "jev_decision")
        .withColumnRenamed("confidence", "jev_confidence"),
    on="run_id",
    how="inner",
)
display(final_df)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 7. Final analytics table

# COMMAND ----------

final_df.write.format("delta").mode("overwrite").saveAsTable("main.default.pipeline_analytics")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 8. Useful SQL queries (dashboard-ready)

# COMMAND ----------

# MAGIC %sql
# MAGIC -- KPI cards
# MAGIC SELECT
# MAGIC   COUNT(*)                                              AS total_pipeline_runs,
# MAGIC   ROUND(AVG(CASE WHEN jev_decision = 'HEALTHY' THEN 1.0 ELSE 0.0 END), 4) AS healthy_share,
# MAGIC   SUM(CASE WHEN jev_decision IN ('WATCH', 'INVESTIGATE') THEN 1 ELSE 0 END) AS requires_attention,
# MAGIC   SUM(CASE WHEN jev_decision = 'BLOCK' THEN 1 ELSE 0 END) AS blocked_pipelines
# MAGIC FROM main.default.pipeline_analytics;

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Decision distribution (bar chart)
# MAGIC SELECT jev_decision, COUNT(*) AS runs
# MAGIC FROM main.default.pipeline_analytics
# MAGIC GROUP BY jev_decision
# MAGIC ORDER BY runs DESC;

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Domain distribution (bar chart)
# MAGIC SELECT domain, jev_decision, COUNT(*) AS runs
# MAGIC FROM main.default.pipeline_analytics
# MAGIC GROUP BY domain, jev_decision
# MAGIC ORDER BY domain, jev_decision;

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Freshness trend (line chart over run timestamp)
# MAGIC SELECT run_timestamp, freshness_delay_minutes, jev_decision
# MAGIC FROM main.default.pipeline_analytics
# MAGIC ORDER BY run_timestamp;

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Pipeline health table (dashboard filter source)
# MAGIC SELECT
# MAGIC   run_id, pipeline_name, domain, run_timestamp, status,
# MAGIC   jev_decision, jev_confidence,
# MAGIC   failure_rate, row_count_variance, duration_variance,
# MAGIC   freshness_delay_minutes, freshness_severity, schema_drift
# MAGIC FROM main.default.pipeline_analytics
# MAGIC ORDER BY run_timestamp DESC;

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Severe runs detail (investigation queue)
# MAGIC SELECT run_id, pipeline_name, failure_rate, row_count_variance,
# MAGIC        freshness_severity, schema_drift, error_message, jev_decision, jev_confidence
# MAGIC FROM main.default.pipeline_analytics
# MAGIC WHERE jev_decision IN ('INVESTIGATE', 'BLOCK')
# MAGIC ORDER BY jev_confidence ASC;

# COMMAND ----------

# MAGIC %md
# MAGIC ## 9. Dashboard hook
# MAGIC
# MAGIC Build the Databricks dashboard against `main.default.pipeline_analytics`
# MAGIC following `docs/dashboard-spec.md`: four KPI cards (query 1), decision
# MAGIC distribution (query 2), domain distribution (query 3), freshness trend
# MAGIC (query 4), and the pipeline health table (query 5).
