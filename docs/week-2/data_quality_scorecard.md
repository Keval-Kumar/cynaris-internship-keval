# Week 2 Day 6 — Data Quality Scorecard

Dataset: `sunrise_resource_utilisation.csv`  
Records: 400 | Columns: 14

| DAMA dimension | Assessment evidence | Initial status | Recommendation |
|---|---|---|---|
| Completeness | 0 missing cells across the dataset | No missing cells detected | Monitor required fields on every load |
| Accuracy | Bed-capacity and attendance-range checks included | Review | Confirm flagged values against source systems |
| Consistency | Cross-field rules such as occupied beds <= total beds | Review | Enforce agreed business rules |
| Timeliness | Static CSV does not establish arrival latency | Not measurable from this file | Define and monitor an agreed freshness SLA |
| Uniqueness | Duplicate record IDs: 0 | No duplicate IDs detected | Enforce unique record IDs |
| Validity | Date parsing, non-negative counts and percentage ranges checked | Review | Validate types, domains and allowed values at ingestion |

## Recommendations
1. Resolve all failed validation checks with the data owner.
2. Add automated checks to the data ingestion pipeline.
3. Record data lineage, ownership and refresh timestamps.
4. Keep patient-level identifiers out of this operational dataset; assess linked datasets separately.
5. Recalculate this scorecard after remediation.

Scores are qualitative because the supplied dataset does not define target thresholds for every DAMA dimension. Do not interpret them as an audited compliance rating.
