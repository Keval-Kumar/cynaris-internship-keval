

**# Week 2 – Repeatable Data Pipeline**



**## 1. Objective**

**To develop a repeatable Python-based data pipeline for processing and analysing the Sunrise Resource Utilisation dataset.**



**## 2. Tools Used**

**- Python 3**

**- Pandas**

**- JSON**

**- Logging**

**- Git and GitHub**



**## 3. Source Dataset**

**File: `data/week-2/raw/sunrise\_resource\_utilisation.csv`**



**- Records: 400**

**- Columns: 14**

**- Hospitals: 4**

**- Departments: 9**



**## 4. Pipeline Execution**



**Run the following command from the project root:**



**```powershell**

**python scripts/week-2/run\_pipeline.py**

**```**



**## 5. Pipeline Operations**

**1. Load the source CSV dataset.**

**2. Check required columns.**

**3. Inspect missing values and record ID uniqueness.**

**4. Perform basic data-quality checks.**

**5. Identify cross-column consistency warnings.**

**6. Calculate overall baseline metrics.**

**7. Calculate hospital-wise and department-wise metrics.**

**8. Export processed data and reports.**

**9. Record execution details in a log file.**



**## 6. Generated Outputs**

**- `data/week-2/processed/sunrise\_resource\_utilisation\_processed.csv`**

**- `reports/week-2/baseline\_metrics.csv`**

**- `reports/week-2/hospital\_metrics.csv`**

**- `reports/week-2/department\_metrics.csv`**

**- `reports/week-2/pipeline\_run\_summary.json`**

**- `reports/week-2/pipeline\_execution.log`**



**## 7. Execution Result**

**The pipeline executed successfully on 26 November 2026.**



**- Records processed: 400**

**- Columns processed: 14**

**- Basic validation checks: 5 passed**

**- Cross-column consistency warnings: 3 categories identified**



**## 8. Data Preservation**

**The original raw CSV is not overwritten. Processed data and analytical reports are saved separately.**



