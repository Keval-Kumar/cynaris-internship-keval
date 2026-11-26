# Week 2 Day 4 — Data Cleaning Log

## Source
`data/week-2/raw/sunrise_resource_utilisation.csv`

## Before cleaning
- Rows: 400
- Columns: 14
- Missing cells: 0
- Exact duplicate rows: 0

## Actions
- Parsed `date` as datetime; unparseable dates remain missing and are reported.
- Filled missing numeric values with each column's median, only where missing values existed.
- Filled missing categorical values with the mode, only where a mode existed.
- Trimmed leading/trailing whitespace from text columns.
- Removed exact duplicate rows only.
- Did not automatically cap or delete outliers. Potential business-rule violations require source-owner confirmation.

## After cleaning
- Rows: 400
- Columns: 14
- Missing cells: 0
- Exact duplicate rows: 0

## Important data-quality observations
Review records where occupied beds exceed total beds, ICU occupied beds exceed ICU capacity, surgeries completed exceed scheduled surgeries, or percentages fall outside 0–100. These may be data-entry errors or valid differences in definitions; confirm with the data owner before correction.

## Output
`data/week-2/processed/cleaned_dataset.csv`
