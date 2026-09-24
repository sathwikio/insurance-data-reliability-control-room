"""Join Jev decisions to the deterministic pipeline metrics (Phase C).

Final analytics table preserves both layers explicitly:

    deterministic metric columns  ->  jev_decision, jev_confidence

Inputs:
    data/delta/pipeline_metrics   (Phase A Delta table)
    data/jev_decisions.json       (Phase B Jev output)

Outputs:
    data/delta/pipeline_analytics   final Delta table
    data/final_analytics.csv        portable CSV export

The module refuses to produce output unless every source run has exactly one
valid Jev decision.
"""

from pathlib import Path

from pyspark.sql import functions as F
from pyspark.sql import types as T

ROOT = Path(__file__).resolve().parent.parent
METRICS_DELTA = ROOT / "data" / "delta" / "pipeline_metrics"
DECISIONS_JSON = ROOT / "data" / "jev_decisions.json"
FINAL_DELTA = ROOT / "data" / "delta" / "pipeline_analytics"
FINAL_CSV = ROOT / "data" / "final_analytics.csv"

ALLOWED_DECISIONS = ("HEALTHY", "WATCH", "INVESTIGATE", "BLOCK")

DECISION_SCHEMA = T.StructType(
    [
        T.StructField("run_id", T.StringType(), False),
        T.StructField("decision", T.StringType(), False),
        T.StructField("confidence", T.DoubleType(), True),
    ]
)


def load_decisions(spark, path: Path = DECISIONS_JSON):
    return spark.read.schema(DECISION_SCHEMA).option("multiLine", "true").json(str(path))


def validate_decisions(metrics_df, decisions_df) -> None:
    """Fail loudly unless the Jev layer covers every run exactly once."""
    metric_ids = {row.run_id for row in metrics_df.select("run_id").collect()}
    decision_rows = decisions_df.collect()
    decision_ids = [row.run_id for row in decision_rows]

    if len(decision_rows) != len(decision_ids) or set(metric_ids) != set(decision_ids):
        missing = metric_ids - set(decision_ids)
        extra = set(decision_ids) - metric_ids
        raise ValueError(
            f"decision coverage mismatch (missing={missing or '{}'}, extra={extra or '{}}'})"
        )

    bad_labels = {row.decision for row in decision_rows} - set(ALLOWED_DECISIONS)
    if bad_labels:
        raise ValueError(f"decisions outside allowed labels: {bad_labels}")


def join_final(metrics_df, decisions_df):
    """Deterministic metrics + Jev decision, joined one-to-one on run_id."""
    return metrics_df.join(
        decisions_df.withColumnRenamed("decision", "jev_decision").withColumnRenamed(
            "confidence", "jev_confidence"
        ),
        on="run_id",
        how="inner",
    ).withColumn(
        "jev_confidence",
        F.coalesce(F.col("jev_confidence").cast(T.DoubleType()), F.lit(None).cast(T.DoubleType())),
    )


def write_outputs(final_df, delta_path: Path = FINAL_DELTA, csv_path: Path = FINAL_CSV) -> int:
    import csv

    final_df.write.format("delta").mode("overwrite").save(str(delta_path))
    columns = final_df.columns
    rows = [row.asDict() for row in final_df.orderBy("run_id").select(*columns).collect()]
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with open(csv_path, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)


def main() -> None:
    from src.spark_pipeline import build_spark

    spark = build_spark()
    spark.sparkContext.setLogLevel("ERROR")
    try:
        metrics_df = spark.read.format("delta").load(str(METRICS_DELTA))
        decisions_df = load_decisions(spark)
        validate_decisions(metrics_df, decisions_df)
        final_df = join_final(metrics_df, decisions_df)
        count = write_outputs(final_df)
        print(f"final delta table: {FINAL_DELTA}")
        print(f"csv export:        {FINAL_CSV}")
        print(f"final rows:        {count} (validated: one decision per run)")
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
