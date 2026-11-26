
from pathlib import Path
import json
import logging
import pandas as pd

# --------------------------------------------------
# 1. Project paths
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "week-2"
    / "raw"
    / "sunrise_resource_utilisation.csv"
)

PROCESSED_DIR = PROJECT_ROOT / "data" / "week-2" / "processed"
REPORT_DIR = PROJECT_ROOT / "reports" / "week-2"

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
REPORT_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE = REPORT_DIR / "pipeline_execution.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, mode="w", encoding="utf-8"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# --------------------------------------------------
# 2. Required columns
# --------------------------------------------------

REQUIRED_COLUMNS = [
    "record_id",
    "hospital",
    "department",
    "date",
    "total_beds",
    "occupied_beds",
    "icu_beds_total",
    "icu_beds_occupied",
    "surgeries_scheduled",
    "surgeries_completed",
    "doctor_attendance_pct",
    "nurse_attendance_pct",
    "avg_patient_wait_mins",
    "readmission_count"
]


def safe_percentage(numerator, denominator):
    if denominator == 0:
        return 0.0
    return round((numerator / denominator) * 100, 2)


# --------------------------------------------------
# 3. Load and inspect data
# --------------------------------------------------

def load_data():
    logger.info("Starting data pipeline")

    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"Dataset not found: {INPUT_FILE}")

    df = pd.read_csv(INPUT_FILE)

    missing_columns = [
        col for col in REQUIRED_COLUMNS
        if col not in df.columns
    ]

    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")

    logger.info("Dataset loaded successfully")
    logger.info("Rows: %s, Columns: %s", df.shape[0], df.shape[1])

    return df


# --------------------------------------------------
# 4. Data quality checks
# --------------------------------------------------

def validate_data(df):
    checks = {
        "no_missing_values": bool(not df[REQUIRED_COLUMNS].isnull().any().any()),
        "unique_record_ids": bool(df["record_id"].is_unique),
        "non_negative_bed_values": bool(
            (df[["total_beds", "occupied_beds",
                 "icu_beds_total", "icu_beds_occupied"]] >= 0).all().all()
        ),
        "attendance_percentages_valid": bool(
            df[["doctor_attendance_pct", "nurse_attendance_pct"]]
            .apply(lambda col: col.between(0, 100).all()).all()
        ),
        "non_negative_surgery_values": bool(
            (df[["surgeries_scheduled", "surgeries_completed"]] >= 0).all().all()
        )
    }

    # These are warnings, not automatic corrections.
    warnings = {
        "occupied_beds_exceed_total_beds": int(
            (df["occupied_beds"] > df["total_beds"]).sum()
        ),
        "icu_occupied_exceed_icu_capacity": int(
            (df["icu_beds_occupied"] > df["icu_beds_total"]).sum()
        ),
        "completed_surgeries_exceed_scheduled": int(
            (df["surgeries_completed"] > df["surgeries_scheduled"]).sum()
        )
    }

    for name, result in checks.items():
        logger.info("%s: %s", name, "PASS" if result else "FAIL")

    for name, count in warnings.items():
        logger.warning("%s: %s records", name, count)

    return checks, warnings


# --------------------------------------------------
# 5. Calculate baseline metrics
# --------------------------------------------------

def calculate_baseline(df):
    total_beds = int(df["total_beds"].sum())
    occupied_beds = int(df["occupied_beds"].sum())

    icu_capacity = int(df["icu_beds_total"].sum())
    icu_occupied = int(df["icu_beds_occupied"].sum())

    scheduled = int(df["surgeries_scheduled"].sum())
    completed = int(df["surgeries_completed"].sum())

    metrics = [
        ("total_records", len(df), "records"),
        ("total_hospitals", df["hospital"].nunique(), "hospitals"),
        ("total_departments", df["department"].nunique(), "departments"),
        ("total_bed_capacity", total_beds, "beds"),
        ("total_occupied_beds", occupied_beds, "beds"),
        (
            "overall_bed_occupancy_pct",
            safe_percentage(occupied_beds, total_beds),
            "percent"
        ),
        ("total_icu_bed_capacity", icu_capacity, "beds"),
        ("total_icu_beds_occupied", icu_occupied, "beds"),
        (
            "icu_occupancy_pct",
            safe_percentage(icu_occupied, icu_capacity),
            "percent"
        ),
        ("total_surgeries_scheduled", scheduled, "surgeries"),
        ("total_surgeries_completed", completed, "surgeries"),
        (
            "surgery_completion_pct",
            safe_percentage(completed, scheduled),
            "percent"
        ),
        (
            "average_doctor_attendance_pct",
            round(float(df["doctor_attendance_pct"].mean()), 2),
            "percent"
        ),
        (
            "average_nurse_attendance_pct",
            round(float(df["nurse_attendance_pct"].mean()), 2),
            "percent"
        ),
        (
            "average_patient_wait_mins",
            round(float(df["avg_patient_wait_mins"].mean()), 2),
            "minutes"
        ),
        (
            "total_readmissions",
            int(df["readmission_count"].sum()),
            "readmissions"
        )
    ]

    baseline_df = pd.DataFrame(
        metrics,
        columns=["metric", "value", "unit"]
    )

    return baseline_df


# --------------------------------------------------
# 6. Hospital and department analysis
# --------------------------------------------------

def calculate_group_metrics(df, group_column):
    result = df.groupby(group_column).agg(
        records=("record_id", "count"),
        total_beds=("total_beds", "sum"),
        occupied_beds=("occupied_beds", "sum"),
        icu_beds_total=("icu_beds_total", "sum"),
        icu_beds_occupied=("icu_beds_occupied", "sum"),
        surgeries_scheduled=("surgeries_scheduled", "sum"),
        surgeries_completed=("surgeries_completed", "sum"),
        avg_doctor_attendance=("doctor_attendance_pct", "mean"),
        avg_nurse_attendance=("nurse_attendance_pct", "mean"),
        avg_patient_wait_mins=("avg_patient_wait_mins", "mean"),
        total_readmissions=("readmission_count", "sum")
    ).reset_index()

    result["bed_occupancy_pct"] = (
        result["occupied_beds"] /
        result["total_beds"].replace(0, pd.NA) * 100
    ).fillna(0).round(2)

    result["icu_occupancy_pct"] = (
        result["icu_beds_occupied"] /
        result["icu_beds_total"].replace(0, pd.NA) * 100
    ).fillna(0).round(2)

    result["surgery_completion_pct"] = (
        result["surgeries_completed"] /
        result["surgeries_scheduled"].replace(0, pd.NA) * 100
    ).fillna(0).round(2)

    return result.round(2)


# --------------------------------------------------
# 7. Save pipeline outputs
# --------------------------------------------------

def save_outputs(df, baseline_df, checks, warnings):
    # Add analytical columns without changing the raw source.
    processed = df.copy()

    processed["bed_occupancy_pct"] = (
        processed["occupied_beds"] /
        processed["total_beds"].replace(0, pd.NA) * 100
    ).fillna(0).round(2)

    processed["icu_occupancy_pct"] = (
        processed["icu_beds_occupied"] /
        processed["icu_beds_total"].replace(0, pd.NA) * 100
    ).fillna(0).round(2)

    processed["surgery_completion_pct"] = (
        processed["surgeries_completed"] /
        processed["surgeries_scheduled"].replace(0, pd.NA) * 100
    ).fillna(0).round(2)

    processed.to_csv(
        PROCESSED_DIR / "sunrise_resource_utilisation_processed.csv",
        index=False
    )

    baseline_df.to_csv(
        REPORT_DIR / "baseline_metrics.csv",
        index=False
    )

    calculate_group_metrics(df, "hospital").to_csv(
        REPORT_DIR / "hospital_metrics.csv",
        index=False
    )

    calculate_group_metrics(df, "department").to_csv(
        REPORT_DIR / "department_metrics.csv",
        index=False
    )

    summary = {
        "pipeline": "Week 2 Sunrise Resource Utilisation Pipeline",
        "source_file": str(INPUT_FILE.relative_to(PROJECT_ROOT)),
        "records_processed": len(df),
        "columns_processed": len(df.columns),
        "hospital_count": int(df["hospital"].nunique()),
        "department_count": int(df["department"].nunique()),
        "validation_checks": checks,
        "all_validation_checks_passed": all(checks.values()),
        "data_quality_warnings": warnings,
        "outputs": [
            "data/week-2/processed/sunrise_resource_utilisation_processed.csv",
            "reports/week-2/baseline_metrics.csv",
            "reports/week-2/hospital_metrics.csv",
            "reports/week-2/department_metrics.csv"
        ]
    }

    with open(
        REPORT_DIR / "pipeline_run_summary.json",
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(summary, file, indent=4)

    logger.info("All pipeline outputs saved successfully")


# --------------------------------------------------
# 8. Main execution
# --------------------------------------------------

def main():
    df = load_data()

    checks, warnings = validate_data(df)

    baseline_df = calculate_baseline(df)

    save_outputs(df, baseline_df, checks, warnings)

    logger.info("Baseline metrics:")
    logger.info("\n%s", baseline_df.to_string(index=False))

    logger.info("Pipeline execution completed")


if __name__ == "__main__":
    main()
