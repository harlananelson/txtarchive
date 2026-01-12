I need a shell script that uses the Python txtarchive module to create an LLM-friendly archive.

### Environment Context:
- Script will run from: /home/hnelson3/work/Users/hnelson3/Projects/SickleCell
- Source directory to archive: /home/hnelson3/work/Users/hnelson3/Projects/SickleCell
- Archive destination: /home/hnelson3/work/Users/hnelson3/archive
- Python txtarchive command: python -m txtarchive archive

### File Selection Mode:
**Option A - Explicit File List:**
Archive ONLY these specific files from the source directory:
- _targets.R
- 2010-Paper-figures.ipynb
- 106-Demographics.ipynb
- 1031-Mortality-3-age-table.ipynb
- 1030-Analysis-Survial-Plots-p-values.ipynb
- 100-Sickle-Cell-Survival-Curves.ipynb
- 108-insurance-grouped.ipynb

### Archive Configuration:
- Format: LLM-friendly (--llm-friendly flag)
- Extract code only: YES (--extract-code-only flag)
- Split output: YES (--split-output flag)
- Max tokens per split: 100000

### Naming Convention:
- Base name: SickleCell (extracted from source directory)
- Optional tag: paper
- Pattern: SickleCell_paper_{timestamp}.txt
- Timestamp format: YYYYMMDD_HHMMSS
- Split directory: SickleCell_paper_{timestamp}_split/

### Output Requirements:
- Create archive directory if it doesn't exist
- Clear console output showing progress
- Summary at end with file paths
- Error handling with set -e
