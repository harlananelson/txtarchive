# Improved LLM Prompt Template for Creating Archive Scripts

## Universal Basic Template

```
I need a shell script that uses the Python txtarchive module to create an LLM-friendly archive.

### Environment Context:
- Script will run from: [EXECUTION_DIRECTORY]
- Source directory to archive: [SOURCE_DIRECTORY_PATH]
- Archive destination: [ARCHIVE_OUTPUT_PATH]
- Python txtarchive command: python -m txtarchive archive

### File Selection Mode:
[Choose ONE and fill in details]

**Option A - Explicit File List:**
Archive ONLY these specific files:
- [FILE1_PATH]
- [FILE2_PATH]
- [FILE3_PATH]

**Option B - Pattern-Based Selection:**
- File extensions to include: [SPACE_SEPARATED_LIST] (e.g., .py .ipynb .md)
- Root files to always include: [LIST] (e.g., README.md setup.py)
- Exclude directories: [LIST] (e.g., .venv __pycache__ .git)
- Subdirectories to limit to: [OPTIONAL_LIST or "ALL"]

**Option C - Mixed Mode:**
- Specific files: [LIST]
- Plus all files matching: [EXTENSIONS]
- Exclude directories: [LIST]

### Archive Configuration:
- Format: LLM-friendly (--llm-friendly flag)
- Extract code only: [YES/NO] (--extract-code-only flag)
- Split output: YES (--split-output flag)
- Max tokens per split: [NUMBER] (e.g., 100000)

### Naming Convention:
- Base name: [DIRNAME] (extracted from source directory)
- Optional tag: [TAG] (e.g., "paper", "analysis", "v2") or NONE
- Pattern: {dirname}_{tag}_{timestamp}.txt if tag provided
           {dirname}_{timestamp}.txt if no tag
- Timestamp format: YYYYMMDD_HHMMSS
- Split directory: {same_base}_split/

### Output Requirements:
- Create archive directory if it doesn't exist
- Clear console output showing progress
- Summary at end with file paths
- Error handling with set -e
```

---

## Filled Example 1: Explicit File List

```
I need a shell script that uses the Python txtarchive module to create an LLM-friendly archive.

### Environment Context:
- Script will run from: /home/hnelson3/work/Users/hnelson3/Projects/SickleCell
- Source directory to archive: /home/hnelson3/work/Users/hnelson3/Projects/SickleCell
- Archive destination: /home/hnelson3/work/Users/hnelson3/archive
- Python txtarchive command: python -m txtarchive archive

### File Selection Mode:
**Option A - Explicit File List:**
Archive ONLY these specific files:
- _targets.ipynb
- 2010-Paper-figures.ipynb

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
```

---

## Filled Example 2: Pattern-Based (Full Project)

```
I need a shell script that uses the Python txtarchive module to create an LLM-friendly archive.

### Environment Context:
- Script will run from: /app/projects/clinressys01_t1/txtarchive
- Source directory to archive: /app/projects/clinressys01_t1/txtarchive
- Archive destination: /app/projects/clinressys01_t1/.archive
- Python txtarchive command: python -m txtarchive archive

### File Selection Mode:
**Option B - Pattern-Based Selection:**
- File extensions to include: .py .md .toml .yaml .txt
- Root files to always include: pyproject.toml README.md
- Exclude directories: .venv __pycache__ .git build dist .pytest_cache
- Subdirectories to limit to: ALL

### Archive Configuration:
- Format: LLM-friendly (--llm-friendly flag)
- Extract code only: NO
- Split output: YES (--split-output flag)
- Max tokens per split: 150000

### Naming Convention:
- Base name: txtarchive (extracted from source directory)
- Optional tag: NONE
- Pattern: txtarchive_{timestamp}.txt
- Timestamp format: YYYYMMDD_HHMMSS
- Split directory: txtarchive_{timestamp}_split/

### Output Requirements:
- Create archive directory if it doesn't exist
- Clear console output showing progress
- Summary at end with file paths
- Error handling with set -e
```

---

## Filled Example 3: Mixed Mode (Data Science Paper)

```
I need a shell script that uses the Python txtarchive module to create an LLM-friendly archive.

### Environment Context:
- Script will run from: /home/user/projects/ml-analysis
- Source directory to archive: /home/user/projects/ml-analysis
- Archive destination: /home/user/archives
- Python txtarchive command: python -m txtarchive archive

### File Selection Mode:
**Option C - Mixed Mode:**
- Specific files: manuscript.md references.bib
- Plus all files matching: .ipynb .py
- Exclude directories: .venv data/raw .ipynb_checkpoints

### Archive Configuration:
- Format: LLM-friendly (--llm-friendly flag)
- Extract code only: YES (--extract-code-only flag for notebooks)
- Split output: YES (--split-output flag)
- Max tokens per split: 100000

### Naming Convention:
- Base name: ml-analysis (extracted from source directory)
- Optional tag: submission
- Pattern: ml-analysis_submission_{timestamp}.txt
- Timestamp format: YYYYMMDD_HHMMSS
- Split directory: ml-analysis_submission_{timestamp}_split/

### Output Requirements:
- Create archive directory if it doesn't exist
- Clear console output showing progress
- Summary at end with file paths
- Error handling with set -e
```
