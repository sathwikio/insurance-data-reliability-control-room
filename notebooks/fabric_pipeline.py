# Microsoft Fabric notebook source
# Insurance Data Reliability Control Room — Microsoft Fabric (Lakehouse) notebook.
#
# Environment: Fabric workspace with a Lakehouse attached (any Spark 3.4+ runtime).
# Upload the two project files into the Lakehouse "Files" section first:
#   data/pipeline_runs.csv    ->  Files/insurance/pipeline_runs.csv
#   data/jev_decisions.json   ->  Files/insurance/jev_decisions.json
# The core transformation logic mirrors notebooks/databricks_pipeline.py and
# src/metrics.py, so both platforms produce the same final analytics table.

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Configuration

# COMMAND ----------

LAKEHOUSE_FILES = "Files/insurance"
SOURCE_CSV = f"{LAKEHOUSE_FILES}/pipeline_runs.csv"
DECISIONS_JSON = f"{LAKEHOUSE_FILES}/jev_decisions.json"
TABLE_METRICS = "pipeline_metrics"
TABLE_FINAL = "pipeline_analytics"

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
# MAGIC ## 3. Lakehouse data load

# COMMAND ----------

from pyspark.sql.types import (
    BooleanType, DoubleType, LongType, StringType, StructField, StructType,
)
from pyspark.sql.functions import struct, udf

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

# Fabric resolves these relative paths against the attached default Lakehouse.
runs_df = (
    spark.read.schema(RUN_SCHEMA)
    .option("header", "true")
    .csv(SOURCE_CSV)
)
display(runs_df.limit(5))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. PySpark transformations — deterministic metric columns

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

# Fabric Lakehouse tables are Delta by default.
metrics_df.write.format("delta").mode("overwrite").saveAsTable(TABLE_METRICS)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 6. Jev result load and join

# COMMAND ----------

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
# MAGIC ## 7. Final analytics table (Power BI-ready)

# COMMAND ----------

final_df.write.format("delta").mode("overwrite").saveAsTable(TABLE_FINAL)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 8. Validation status
# MAGIC
# MAGIC This notebook mirrors the verified Databricks transformation path.
# MAGIC A live Fabric workspace run is not part of this project.
# MAGIC Treat this file as a portability target, not a verified deployment.
