
"""
Cynaris Internship - Week 2 Day 6
Great Expectations 1.25.0 Validation
Dataset: Sunrise Resource Utilisation

Run from project root:
python scripts/week-2/great_expectations_validation.py

The original CSV is never modified.
Fault injection uses a separate in-memory copy.
"""

from pathlib import Path
import json
import html
import sys

import pandas as pd
import great_expectations as gx


# --------------------------------------------------
# 1. Find project root
# --------------------------------------------------

def find_project_root():
    current = Path.cwd().resolve()

    for folder in (current, *current.parents):
        candidate = (
            folder
            / "data"
            / "week-2"
            / "raw"
            / "sunrise_resource_utilisation.csv"
        )

        if candidate.exists():
            return folder

    raise FileNotFoundError(
        "Cannot find data/week-2/raw/sunrise_resource_utilisation.csv. "
        "Run this script from inside your project."
    )


# --------------------------------------------------
# 2. Convert GX results
# --------------------------------------------------

def result_to_dict(result):
    if isinstance(result, dict):
        return result

    if hasattr(result, "to_json_dict"):
        return result.to_json_dict()

    if hasattr(result, "to_json"):
        raw = result.to_json()
        return json.loads(raw) if isinstance(raw, str) else raw

    raise TypeError(
        f"Cannot convert GX result to dictionary: {type(result)}"
    )


def result_success(result):
    if isinstance(result, dict):
        return bool(result.get("success", False))

    return bool(getattr(result, "success", False))


def get_expectation_results(validation_data):
    return validation_data.get("results", [])


# --------------------------------------------------
# 3. Run validation
# --------------------------------------------------

def run_validation(validation_definition, dataframe):
    return validation_definition.run(
        batch_parameters={"dataframe": dataframe}
    )


# --------------------------------------------------
# 4. Main program
# --------------------------------------------------

def main():

    root = find_project_root()

    raw_path = (
        root
        / "data"
        / "week-2"
        / "raw"
        / "sunrise_resource_utilisation.csv"
    )

    reports_dir = root / "reports" / "week-2"
    reports_dir.mkdir(parents=True, exist_ok=True)

    if not raw_path.exists():
        raise FileNotFoundError(f"Dataset not found: {raw_path}")

    df = pd.read_csv(raw_path)

    required_columns = [
        "record_id",
        "hospital",
        "department",
        "date",
        "total_beds",
        "occupied_beds",
        "doctor_attendance_pct",
        "nurse_attendance_pct",
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Dataset is missing required columns: {missing_columns}"
        )

    print("=" * 60)
    print("GREAT EXPECTATIONS DATA QUALITY VALIDATION")
    print("=" * 60)

    print("Great Expectations version:", gx.__version__)
    print("Dataset:", raw_path.relative_to(root))
    print("Rows:", len(df))
    print("Columns:", len(df.columns))

    # --------------------------------------------------
    # 5. Create ephemeral Data Context
    # --------------------------------------------------

    context = gx.get_context(mode="ephemeral")

    datasource = context.data_sources.add_pandas(
        name="sunrise_pandas"
    )

    data_asset = datasource.add_dataframe_asset(
        name="resource_utilisation"
    )

    batch_definition = (
        data_asset.add_batch_definition_whole_dataframe(
            "whole_resource_utilisation"
        )
    )

    # --------------------------------------------------
    # 6. Create eight expectations
    # --------------------------------------------------

    suite_name = "sunrise_resource_utilisation_suite"

    suite = gx.ExpectationSuite(name=suite_name)

    expectations = [

        # Completeness
        gx.expectations.ExpectColumnValuesToNotBeNull(
            column="record_id"
        ),

        # Uniqueness
        gx.expectations.ExpectColumnValuesToBeUnique(
            column="record_id"
        ),

        # Required text fields
        gx.expectations.ExpectColumnValuesToNotBeNull(
            column="hospital"
        ),

        gx.expectations.ExpectColumnValuesToNotBeNull(
            column="department"
        ),

        # Non-negative bed counts
        gx.expectations.ExpectColumnValuesToBeBetween(
            column="total_beds",
            min_value=0,
        ),

        gx.expectations.ExpectColumnValuesToBeBetween(
            column="occupied_beds",
            min_value=0,
        ),

        # Attendance percentage checks
        gx.expectations.ExpectColumnValuesToBeBetween(
            column="doctor_attendance_pct",
            min_value=0,
            max_value=100,
        ),

        gx.expectations.ExpectColumnValuesToBeBetween(
            column="nurse_attendance_pct",
            min_value=0,
            max_value=100,
        ),
    ]

    for expectation in expectations:
        suite.add_expectation(expectation)

    # IMPORTANT: Register suite BEFORE creating validation definition.
    context.suites.add(suite)

    # Retrieve the registered suite from the context.
    suite = context.suites.get(name=suite_name)

    print("\nExpectation suite registered successfully.")
    print("Number of expectations:", len(expectations))

    # --------------------------------------------------
    # 7. Create validation definition
    # --------------------------------------------------

    validation_definition = context.validation_definitions.add(
        gx.ValidationDefinition(
            name="sunrise_resource_utilisation_validation",
            data=batch_definition,
            suite=suite,
        )
    )

    print("Validation definition registered successfully.")

    # --------------------------------------------------
    # 8. Validate original dataset
    # --------------------------------------------------

    print("\nRunning original dataset validation...")

    original_result = run_validation(
        validation_definition,
        df,
    )

    original_dict = result_to_dict(original_result)

    # --------------------------------------------------
    # 9. Inject three intentional errors
    # --------------------------------------------------

    print("\nPreparing fault injection test...")

    faulty = df.copy(deep=True)

    if len(faulty) < 3:
        raise ValueError(
            "At least three rows are required for fault injection."
        )

    # Fault 1: Missing record ID
    faulty.loc[faulty.index[0], "record_id"] = None

    # Fault 2: Negative bed count
    faulty.loc[faulty.index[1], "total_beds"] = -1

    # Fault 3: Attendance above 100
    faulty.loc[
        faulty.index[2],
        "doctor_attendance_pct"
    ] = 150

    print("Three intentional errors inserted into a separate copy.")

    # --------------------------------------------------
    # 10. Validate faulty dataset
    # --------------------------------------------------

    print("\nRunning fault injection validation...")

    injected_result = run_validation(
        validation_definition,
        faulty,
    )

    injected_dict = result_to_dict(injected_result)

    # --------------------------------------------------
    # 11. Verify fault detection
    # --------------------------------------------------

    detected = {
        "Null record_id": False,
        "Negative total_beds": False,
        "doctor_attendance_pct above 100": False,
    }

    for item in get_expectation_results(injected_dict):

        config = item.get("expectation_config", {})
        kwargs = config.get("kwargs", {})

        column = kwargs.get("column")
        success = item.get("success", False)

        details = item.get("result", {})
        unexpected_count = details.get("unexpected_count", 0)

        if column == "record_id" and not success and unexpected_count:
            detected["Null record_id"] = True

        elif column == "total_beds" and not success and unexpected_count:
            detected["Negative total_beds"] = True

        elif (
            column == "doctor_attendance_pct"
            and not success
            and unexpected_count
        ):
            detected["doctor_attendance_pct above 100"] = True

    all_detected = all(detected.values())

    # --------------------------------------------------
    # 12. Save JSON evidence
    # --------------------------------------------------

    evidence = {
        "great_expectations_version": gx.__version__,
        "dataset": str(raw_path.relative_to(root)),
        "row_count": int(len(df)),
        "column_count": int(len(df.columns)),
        "expectation_count": len(expectations),

        "original_validation_success": result_success(
            original_result
        ),

        "original_validation": original_dict,

        "fault_injection_validation_success": result_success(
            injected_result
        ),

        "fault_injection_validation": injected_dict,

        "injected_faults_detected": detected,

        "all_three_faults_detected": all_detected,

        "note": (
            "The original CSV was not modified. "
            "Fault injection was performed on a separate copy. "
            "Cross-column bed and ICU rules require data-owner "
            "confirmation before enforcement."
        ),
    }

    json_path = (
        reports_dir / "great_expectations_validation.json"
    )

    json_path.write_text(
        json.dumps(evidence, indent=2, default=str),
        encoding="utf-8",
    )

    # --------------------------------------------------
    # 13. Generate HTML report
    # --------------------------------------------------

    def expectation_rows(validation_data):

        rows = []

        for item in get_expectation_results(validation_data):

            config = item.get("expectation_config", {})

            expectation_type = config.get(
                "type",
                "Expectation"
            )

            column = config.get("kwargs", {}).get("column", "")

            status = (
                "PASS"
                if item.get("success", False)
                else "FAIL"
            )

            details = item.get("result", {})
            unexpected = details.get("unexpected_count", 0)

            rows.append(
                "<tr>"
                f"<td>{html.escape(str(expectation_type))}</td>"
                f"<td>{html.escape(str(column))}</td>"
                f"<td>{status}</td>"
                f"<td>{html.escape(str(unexpected))}</td>"
                "</tr>"
            )

        return "\n".join(rows)

    fault_rows = "\n".join(
        (
            "<tr>"
            f"<td>{html.escape(name)}</td>"
            f"<td>{'DETECTED' if was_detected else 'NOT DETECTED'}</td>"
            "</tr>"
        )
        for name, was_detected in detected.items()
    )

    original_status = (
        "SUCCESS"
        if result_success(original_result)
        else "FAILURE"
    )

    injected_status = (
        "SUCCESS"
        if result_success(injected_result)
        else "FAILURE"
    )

    html_report = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Great Expectations Validation Report</title>
<style>
body {{
    font-family: Arial, sans-serif;
    max-width: 1050px;
    margin: 36px auto;
    padding: 0 20px;
    color: #222;
}}
table {{
    border-collapse: collapse;
    width: 100%;
    margin: 16px 0 28px;
}}
th, td {{
    border: 1px solid #ccc;
    padding: 9px;
    text-align: left;
}}
th {{ background: #eee; }}
.note {{
    background: #fff7df;
    padding: 12px;
    border-left: 4px solid #d99b22;
}}
</style>
</head>
<body>

<h1>Sunrise Resource Utilisation - Great Expectations Report</h1>

<p>Great Expectations version: {html.escape(gx.__version__)}</p>

<p>Rows checked: {len(df)} | Columns: {len(df.columns)}</p>

<h2>Original dataset validation: {original_status}</h2>

<table>
<tr>
<th>Expectation</th>
<th>Column</th>
<th>Result</th>
<th>Unexpected count</th>
</tr>

{expectation_rows(original_dict)}

</table>

<h2>Fault injection validation: {injected_status}</h2>

<table>
<tr>
<th>Injected fault</th>
<th>Detection result</th>
</tr>

{fault_rows}

</table>

<p>
<strong>All three injected faults detected:</strong>
{all_detected}
</p>

<p class="note">
The original CSV was not modified.
Fault injection used a separate in-memory copy.
The eight expectations above are Great Expectations checks.
Cross-column bed and ICU business rules require data-owner confirmation
before enforcement.
</p>

<p>Machine-readable evidence: great_expectations_validation.json</p>

</body>
</html>
"""

    html_path = (
        reports_dir / "great_expectations_report.html"
    )

    html_path.write_text(
        html_report,
        encoding="utf-8",
    )

    # --------------------------------------------------
    # 14. Print final results
    # --------------------------------------------------

    print("\n" + "=" * 60)
    print("ORIGINAL DATA VALIDATION")
    print("=" * 60)

    print(
        "Overall success:",
        result_success(original_result)
    )

    print("\n" + "=" * 60)
    print("FAULT INJECTION RESULTS")
    print("=" * 60)

    for name, was_detected in detected.items():

        status = (
            "DETECTED"
            if was_detected
            else "NOT DETECTED"
        )

        print(f"{name}: {status}")

    print("\nAll three faults detected:", all_detected)

    print("\n" + "=" * 60)
    print("REPORTS CREATED")
    print("=" * 60)

    print("-", html_path.relative_to(root))
    print("-", json_path.relative_to(root))

    if not all_detected:
        print(
            "\nWARNING: At least one injected fault "
            "was not detected. Inspect the JSON evidence."
        )
        sys.exit(2)

    print("\nValidation script completed.")


if __name__ == "__main__":
    main()
