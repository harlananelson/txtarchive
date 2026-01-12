# PROMPT TEMPLATE: Generate txtarchive LLM-Friendly Archive

## Instructions for LLM

When asked to create an archive from project specifications, you must follow the **txtarchive LLM-friendly format** exactly. This is a specific format used by the txtarchive Python tool.

---

## CRITICAL FORMAT REQUIREMENTS

### 1. HEADER BLOCK (Required)
```
# Archive created on: YYYY-MM-DD HH:MM:SS
# LLM-FRIENDLY CODE ARCHIVE
# Generated from: [project_name or directory]
# Date: YYYY-MM-DD HH:MM:SS
```

### 2. TABLE OF CONTENTS (Required)
Must list ALL files that will be in the archive, numbered sequentially:

```
# TABLE OF CONTENTS
1. file1.ipynb
2. file2.R
3. file3.py
4. analysis.qmd
```

**CRITICAL:** This must be a list of ACTUAL FILENAMES, not section descriptions.

### 3. FILE SEPARATORS (Required for each file)
Each file must start with this exact pattern:

```
################################################################################
# FILE 1: filename.ext
################################################################################

[file content here]


################################################################################
# FILE 2: nextfile.ext
################################################################################

[file content here]
```

**CRITICAL:** 
- Use exactly 80 "#" characters
- Format: `# FILE N: filename`
- Two blank lines between files

---

## COMPLETE TEMPLATE

```
# Archive created on: 2024-11-20 10:30:00
# LLM-FRIENDLY CODE ARCHIVE
# Generated from: ProjectName
# Date: 2024-11-20 10:30:00

# TABLE OF CONTENTS
1. setup.R
2. analysis.ipynb
3. figures.py

################################################################################
# FILE 1: setup.R
################################################################################

# R Setup Script
library(tidyverse)
library(survival)

# Load data
data <- read_csv("data.csv")


################################################################################
# FILE 2: analysis.ipynb
################################################################################

# Cell 1
import pandas as pd
import numpy as np

# Cell 2
data = pd.read_csv("data.csv")


################################################################################
# FILE 3: figures.py
################################################################################

import matplotlib.pyplot as plt
import seaborn as sns

# Create figure
plt.figure(figsize=(10, 6))
```

---

## COMMON MISTAKES TO AVOID

### ❌ WRONG: Section-based structure (like your example)
```
# TABLE OF CONTENTS
# 1. Setup and Data Loading
# 2. Table 1: Demographics
# 3. Tables 2-3: Mortality Rates

################################################################################
# SECTION 1: SETUP AND DATA LOADING
################################################################################
```
**Problem:** This treats it as ONE document with sections, not an archive of FILES.

### ❌ WRONG: Missing file list
```
# Archive created on: 2024-11-20

# Setup code here...
```
**Problem:** No TABLE OF CONTENTS listing files.

### ❌ WRONG: Incorrect file markers
```
# FILE 1: analysis.R
===================================

[content]
```
**Problem:** Wrong separator pattern (must be 80 # characters).

### ❌ WRONG: No file numbers
```
################################################################################
# FILE: analysis.ipynb
################################################################################
```
**Problem:** Missing file number (must be "FILE 1:", "FILE 2:", etc.).

---

## NOTEBOOK FORMAT (For .ipynb files)

When creating Jupyter notebook content in the archive, use this format:

```
################################################################################
# FILE 2: analysis.ipynb
################################################################################

# Cell 1
import pandas as pd
import numpy as np

# Cell 2
data = pd.read_csv("input.csv")

# Cell 3
# Analysis
result = data.groupby("category").mean()

# Markdown Cell 4
"""
## Results Summary

The analysis shows...
"""
```

**Format rules:**
- Each code cell: `# Cell N` followed by code
- Markdown cells: `# Markdown Cell N` followed by content in triple quotes `"""`
- Two blank lines between cells

---

## R SCRIPT FORMAT (For .R files)

```
################################################################################
# FILE 1: analysis.R
################################################################################

# Load libraries
library(tidyverse)
library(survival)

# Load data
data <- read_csv("data.csv")

# Analysis
model <- coxph(Surv(time, event) ~ group, data = data)
```

---

## VALIDATION CHECKLIST

Before generating the archive, verify:

- [ ] Header block present with all 4 lines
- [ ] TABLE OF CONTENTS lists actual filenames (not sections)
- [ ] Each file has proper separator (80 # characters)
- [ ] File numbering is sequential (FILE 1, FILE 2, FILE 3, ...)
- [ ] Filenames in TOC match filenames in separators exactly
- [ ] Two blank lines between files
- [ ] No "SECTION" markers (use FILE markers)

---

## EXAMPLE USAGE PROMPT

**Good prompt to LLM:**
"Create a txtarchive LLM-friendly archive with the following files:
1. setup.R - loads libraries and data
2. analysis.ipynb - performs survival analysis (3 cells)
3. figures.py - creates plots

Follow the txtarchive format exactly, including:
- Header with date
- TABLE OF CONTENTS listing these 3 files
- Proper FILE separators with 80 # characters
- Sequential file numbering"

---

## WHY THIS FORMAT MATTERS

1. **Extraction:** The `extract-notebooks` command looks for FILE markers to reconstruct files
2. **Parsing:** Tools parse by splitting on the FILE separator pattern
3. **Validation:** The TABLE OF CONTENTS is checked against actual files
4. **Reconstruction:** File numbers and names must match for proper extraction

---

## SPECIAL CASES

### Multiple notebooks in one archive
Each gets its own FILE marker:

```
# TABLE OF CONTENTS
1. notebook1.ipynb
2. notebook2.ipynb
3. notebook3.ipynb

################################################################################
# FILE 1: notebook1.ipynb
################################################################################

# Cell 1
...

################################################################################
# FILE 2: notebook2.ipynb
################################################################################

# Cell 1
...
```

### Mixed file types
All follow the same pattern:

```
# TABLE OF CONTENTS
1. script.R
2. analysis.ipynb
3. utils.py
4. report.qmd

[Each with proper FILE markers]
```

---

## COMPLETE WORKING EXAMPLE

```
# Archive created on: 2024-11-20 15:30:45
# LLM-FRIENDLY CODE ARCHIVE
# Generated from: SickleCell_Analysis
# Date: 2024-11-20 15:30:45

# TABLE OF CONTENTS
1. 01_setup.R
2. 02_demographics.ipynb
3. 03_survival_analysis.R

################################################################################
# FILE 1: 01_setup.R
################################################################################

# Setup script for SickleCell analysis
# Author: Generated from specifications
# Date: 2024-11-20

# Load required packages
pacman::p_load(
  tidyverse, survival, survminer, 
  data.table, lubridate
)

# Set paths
project_path <- here::here("Projects", "SickleCell")
data_path <- file.path(project_path, "data")

# Load data
scd_data <- read_csv(file.path(data_path, "sickle_cell_cohort.csv"))


################################################################################
# FILE 2: 02_demographics.ipynb
################################################################################

# Cell 1
import pandas as pd
import numpy as np
from tableone import TableOne

# Cell 2
# Load data
df = pd.read_csv("sickle_cell_cohort.csv")

# Cell 3
# Create Table 1
columns = ['age', 'gender', 'genotype', 'hydroxyurea']
categorical = ['gender', 'genotype', 'hydroxyurea']
groupby = 'scd_status'

table1 = TableOne(df, columns=columns, categorical=categorical, groupby=groupby)

# Markdown Cell 4
"""
## Demographics Table

This table shows the baseline characteristics of the SCD cohort
compared to the matched control group.
"""


################################################################################
# FILE 3: 03_survival_analysis.R
################################################################################

# Survival Analysis
# Compare SCD vs Control groups

library(survival)
library(survminer)

# Fit Kaplan-Meier curves
fit <- survfit(
  Surv(age_entry, age_exit, death) ~ scd_status,
  data = scd_data
)

# Create survival plot
ggsurvplot(
  fit,
  data = scd_data,
  conf.int = TRUE,
  risk.table = TRUE,
  xlab = "Age (years)",
  ylab = "Survival Probability"
)
```

---

## VERIFICATION COMMAND

After generating the archive, it should pass these tests:

```bash
# 1. Count files in TOC
grep -c "^[0-9]\+\." archive.txt

# 2. Count FILE markers
grep -c "^# FILE [0-9]\+:" archive.txt

# 3. These numbers should match!

# 4. Verify 80-character separators
grep "^#{80}$" archive.txt | wc -l
# Should be 2x the number of files (start and end markers)
```

---

## SUMMARY FOR LLM

When generating a txtarchive archive:

1. ✅ Start with proper header (4 lines)
2. ✅ List ALL files in TABLE OF CONTENTS (numbered)
3. ✅ Use FILE markers (not SECTION markers)
4. ✅ Use exactly 80 # characters in separators
5. ✅ Number files sequentially: FILE 1, FILE 2, FILE 3...
6. ✅ Match filenames exactly between TOC and FILE markers
7. ✅ Include actual code/content for each file
8. ✅ Two blank lines between files

**Remember:** You're creating an ARCHIVE of MULTIPLE FILES, not a single document with sections!