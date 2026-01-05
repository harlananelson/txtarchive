# SCD Phenotyping

**Architectural Component: Clinical Logic Layer**

## Overview

`scd_phenotyping` is a specialized Python library designed to identify and classify Sickle Cell Disease (SCD) patients within Electronic Health Record (EHR) data. It implements deterministic algorithms based on two primary data axes:

1.  **ICD-based Phenotyping:** Utilizes regex pattern matching against diagnostic codes (ICD-9/10) combined with encounter frequency and type (Inpatient vs. Outpatient) logic.
2.  **Lab-based Phenotyping:** Classifies genotypes (e.g., HbSS, HbSC) based on hemoglobin fractionation ratios (HbS%, HbA%, etc.).

This package leverages **DuckDB** for high-performance SQL-on-Pandas execution, ensuring scalability for large encounter datasets.

## Installation

This package is managed via `pyproject.toml`.

```bash
pip install .
````

## Dependencies

  * `pandas`
  * `duckdb`
  * `numpy`

## Usage Patterns

### 1\. ICD Phenotyping

The algorithm filters encounters based on ICD regex patterns defined in `config.py` and aggregates them to determine a patient's probability of having SCD.

**Input Requirements:**

  * `enc_df`: DataFrame of clinical encounters (must contain Patient ID, Encounter Type, Start/End Dates).
  * `icd_df`: DataFrame of diagnosis codes (must contain Patient ID, Diagnosis Code, Date).

<!-- end list -->

```python
import pandas as pd
from scd_phenotyping import run_icd_phenotyping

# 1. Load Data
enc_df = pd.read_parquet("encounters.parquet")
icd_df = pd.read_parquet("diagnoses.parquet")

# 2. Define Column Mapping (Maps logic to your schema)
col_map = {
    'id': 'person_id',
    'encType': 'enc_type_code',
    'encStart': 'admit_date',
    'encEnd': 'discharge_date',
    'icdCode': 'diagnosis_code',
    'icdTime': 'diagnosis_date'
}

# 3. Execute
# Returns a DataFrame with 'person_id' and 'IcdPheno' (e.g., 'SCD_Case', 'Possible/Control')
results = run_icd_phenotyping(enc_df, icd_df, col_map)
```

### 2\. Lab Phenotyping

Classifies patient genotype based on a single row of hemoglobin lab results.

```python
from scd_phenotyping import classify_lab_row

# Example Row (Wide format expected)
lab_result = {
    'HgbS': 85.0,
    'HgbA': 2.0,
    'HgbF': 13.0,
    'HgbC': 0.0,
    'total_hgb': 100.0,
    'S_percent': 85.0,
    'A_percent': 2.0
}

phenotype = classify_lab_row(lab_result)
print(phenotype) 
# Output: 'SCD_SS'
```

## Configuration

Clinical definitions are centralized in `scd_phenotyping/config.py`.

  * **ICD\_REGEX:** Dictionary mapping conditions (SCD, Thalassemia, Trait) to regex patterns.
  * **ENC\_TYPES\_MAP:** Normalizes source system encounter types to standard logic categories (IP, OP, ER, OB).

**Architectural Note:** Do not modify `config.py` without clinical review.

## Authors

  * Gerard Dreason Hills MD
  * Harlan A Nelson

-----

## Filename: .gitignore

# Python

**pycache**/
\*.py[cod]
\*$py.class

# Distribution / Packaging

dist/
build/
\*.egg-info/

# Data (CRITICAL: Do not commit PHI)

\*.csv
\*.parquet
\*.feather
\*.pkl
data/
raw\_data/

# Environments

.env
.venv
env/
venv/

# IDEs

.vscode/
.idea/

# Jupyter

.ipynb\_checkpoints

-----

## Filename: LICENSE

Copyright (c) 2025 SCD Data Pipeline Team

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

-----

## Filename: tests/**init**.py

# Test Suite for SCD Phenotyping

-----

## Filename: tests/test\_phenotyping.py

import unittest
import pandas as pd
from scd\_phenotyping import classify\_lab\_row, aggregate\_lab\_phenotypes

class TestLabLogic(unittest.TestCase):

```
def test_classify_ss_genotype(self):
    """Test classic HbSS presentation: High S, Low A."""
    row = {'S_percent': 80.0, 'A_percent': 5.0}
    result = classify_lab_row(row)
    self.assertEqual(result, 'SCD_SS')

def test_classify_trait(self):
    """Test Trait presentation: A > S."""
    row = {'S_percent': 35.0, 'A_percent': 60.0}
    result = classify_lab_row(row)
    self.assertEqual(result, 'S_Trait')

def test_aggregation(self):
    """Test that the most frequent phenotype is selected for a patient."""
    data = {
        'personid': [1, 1, 1],
        'LabPhenotype': ['SCD_SS', 'SCD_SS', 'Inconclusive']
    }
    df = pd.DataFrame(data)
    result = aggregate_lab_phenotypes(df)
    
    # Should return one row for person 1 with the mode (SCD_SS)
    self.assertEqual(len(result), 1)
    self.assertEqual(result.iloc[0]['LabPhenotype'], 'SCD_SS')
```

if **name** == '**main**':
unittest.main()

```