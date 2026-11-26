

**# Week 2 – Baseline Metrics Report**



**## Dataset Overview**

**- Total records: 400**

**- Total hospitals: 4**

**- Total departments: 9**

**- Missing values: 0**



**## Overall Baseline Metrics**



**| Metric | Value |**

**|---|---:|**

**| Total bed capacity | 25,833 |**

**| Occupied beds | 23,254 |**

**| Bed occupancy | 90.02% |**

**| ICU bed capacity | 6,790 |**

**| Occupied ICU beds | 5,925 |**

**| ICU occupancy | 87.26% |**

**| Surgeries scheduled | 2,978 |**

**| Surgeries completed | 2,757 |**

**| Surgery completion | 92.58% |**

**| Average doctor attendance | 84.95% |**

**| Average nurse attendance | 87.42% |**

**| Average patient waiting time | 78.66 minutes |**

**| Total readmissions | 1,592 |**



**## Data Quality Observations**



**The pipeline identified the following cross-column consistency warnings:**



**- Occupied beds exceed total beds in 175 records.**

**- ICU occupied beds exceed ICU capacity in 175 records.**

**- Completed surgeries exceed scheduled surgeries in 182 records.**



**These observations require business-rule confirmation and further investigation. No automatic corrections were applied.**



**## Output**

**The detailed baseline values are available in:**

**`reports/week-2/baseline\_metrics.csv`**



**Hospital-wise and department-wise results are available in their respective CSV reports.**



