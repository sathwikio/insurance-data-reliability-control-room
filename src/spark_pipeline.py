"""PySpark pipeline: raw runs -> deterministic metrics -> Delta table + Jev input.

The metric columns are computed with UDFs that call src/metrics.py directly,
so the tested Python functions are the single source of truth. Output layout:

    data/delta/pipeline_metrics   Delta table (run facts + metric columns)
    data/jev_input.json            one compact record per run for Jev
"""

import json
import sys
from pathlib import Path

from pyspark.sql import SparkSession, types as T
from pyspark.sql.functions import col

from src import metrics

ROOT = Path(__file__).resolve().parent.parent
RUNS_CSV = ROOT / "data" / "pipeline_runs.csv"
DELTA_PATH = ROOT / "data" / "delta" / "pipeline_metrics"
JEV_INPUT = ROOT / "data" / "jev_input.json"

RUN_SCHEMA = T.StructType([
    T.StructField("run_id", T.StringType(), False),
    T.StructField("pipeline_name", T.StringType(), False),
    T.StructField("domain", T.StringType(), False),
    T.StructField("run_timestamp", T.StringType(), False),
    T.StructField("expected_rows", T.LongType(), False),
    T.StructField("actual_rows", T.LongType(), False),
    T.StructField("failed_rows", T.LongType(), False),
    T.StructField("duration_seconds", T.LongType(), False),
    T.StructField("expected_duration_seconds", T.LongType(), False),
    T.StructField("freshness_delay_minutes", T.LongType(), False),
    T.StructField("schema_drift", T.StringType(), False),
    T.StructField("status", T.StringType(), False),
    T.StructField("error_message", T.StringType(), True),
])


def build_spark() -> SparkSession:
    return (
        SparkSession.builder.master("local[1]")
        .appName("insurance-data-reliability")
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
        .config("spark.ui.enabled", "false")
        .config("spark.sql.shuffle.partitions", "1")
        .getOrCreate()
    )


def load_runs(spark: SparkSession, path: Path = RUNS_CSV):
    return (
        spark.read.schema(RUN_SCHEMA)
        .option("header", "true")
        .csv(str(path))
    )


def with_metrics(runs_df):
    """Add deterministic metric columns using the tested Python functions."""
    from pyspark.sql.functions import udf
    from pyspark.sql.types import BooleanType, DoubleType, StringType

    args = struct_run()

    return runs_df.select(
        "*",
        udf(metrics.failure_rate, DoubleType())(args).alias("failure_rate"),
        udf(metrics.row_count_variance, DoubleType())(args).alias("row_count_variance"),
        udf(metrics.duration_variance, DoubleType())(args).alias("duration_variance"),
        udf(lambda r: metrics.freshness_severity(r["freshness_delay_minutes"]), StringType())(args)
            .alias("freshness_severity"),
        udf(metrics.has_schema_drift, BooleanType())(args).alias("schema_drift_present"),
        udf(metrics.error_present, BooleanType())(args).alias("error_present"),
    )


def struct_run():
    """All columns needed by the metric functions, packed as one struct."""
    from pyspark.sql.functions import struct
    return struct(
        col("expected_rows"), col("actual_rows"), col("failed_rows"),
        col("duration_seconds"), col("expected_duration_seconds"),
        col("freshness_delay_minutes"), col("schema_drift"), col("error_message"),
    )


def write_delta(df, path: Path = DELTA_PATH):
    df.write.format("delta").mode("overwrite").save(str(path))


def export_jev_input(metrics_df, path: Path = JEV_INPUT) -> int:
    """Write one compact decision record per run for the Jev layer."""
    columns = [
        "run_id", "domain", "failure_rate", "row_count_variance",
        "duration_variance", "freshness_delay_minutes", "freshness_severity",
        "schema_drift", "status", "error_present",
    ]
    rows = [row.asDict() for row in metrics_df.orderBy("run_id").select(*columns).collect()]
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as fh:
        json.dump(rows, fh, separators=(",", ":"))
    return len(rows)


def main() -> None:
    spark = build_spark()
    spark.sparkContext.setLogLevel("ERROR")
    try:
        runs_df = load_runs(spark)
        metrics_df = with_metrics(runs_df)
        write_delta(metrics_df)
        count = export_jev_input(metrics_df)
        print(f"delta table written to {DELTA_PATH}")
        print(f"jev input written to {JEV_INPUT} ({count} records)")
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
