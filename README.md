# TxtArchive: Code Archiving and File Transfer Toolkit

TxtArchive is a Python utility for archiving code files into text format for easy transfer between local machines and remote environments (like AWS cloud). It supports both standard archiving for file movement and LLM-friendly formats for AI analysis, with options for splitting large archives to fit transfer or token limits.

## Features

- **Archive & Unpack**: Combine files into text archives and extract them back to directories
- **File Transfer**: Move directories between local and remote systems via text files
- **LLM-Friendly Format**: Strip notebook outputs and metadata for AI analysis
- **Smart Splitting**: Split large archives into chunks for transfer or token limits
- **Flexible Filtering**: Select files by type, prefix, or specific directories
- **Dual Formats**: Standard format for exact file reconstruction, LLM format for code analysis

## Installation

1. Clone and install:
   ```bash
   git clone https://github.com/harlananelson/txtarchive.git
   cd txtarchive
   pip install .
   ```

2. Verify installation:
   ```bash
   python -m txtarchive --version
   ```

**Requirements**: Python 3.8+, `nbformat` (for Jupyter notebook support)

## Core Commands

- **Archive**: `python -m txtarchive archive <directory> <output_file> [options]`
- **Unpack**: `python -m txtarchive unpack <archive_file> <output_directory> [options]`
- **Extract Notebooks**: `python -m txtarchive extract-notebooks <archive_file> <output_directory> [options]`

## Key Options

- `--file_types .py .ipynb .yaml`: Include specific file types
- `--file_prefixes prefix1 prefix2`: Include only files starting with prefixes
- `--llm-friendly --extract-code-only`: Create LLM-optimized archives
- `--split-output`: Split archives into multiple files
- `--no-subdirectories`: Archive only top-level files
- `--root-files setup.py requirements.txt`: Include specific root files
- `--replace_existing`: Overwrite existing files when unpacking

## Complete Examples

### 1. SickleCell Project - LLM Analysis (Multi-file Split)

**Purpose**: Archive specific Jupyter notebooks for LLM analysis, splitting for token limits

**Archive** (creates split files for LLM processing):
```bash
python -m txtarchive archive "SickleCell" "SickleCell_analysis.txt" \
    --file_types .ipynb \
    --no-subdirectories \
    --llm-friendly \
    --extract-code-only \
    --split-output \
    --file_prefixes 015 016 017 050 060 065 067 
```

```bash
python -m txtarchive archive "SickleCell" "SickleCell_workflow_example.txt" \
    --file_types .ipynb \
    --no-subdirectories \
    --llm-friendly \
    --extract-code-only \
    --split-output \
    --file_prefixes 015 
```

```bash
python -m txtarchive archive "SickleCell" "SickleCell_all.txt" \
    --file_types .ipynb .yaml \
    --no-subdirectories \
    --llm-friendly \
    --extract-code-only \
    --split-output
```

**Result**: 
- `SickleCell_analysis.txt` (single archive)
- `split_SickleCell_analysis/` directory with `SickleCell_analysis_part1.txt`, `SickleCell_analysis_part2.txt`, etc.

**Extract Notebooks** (reconstruct .ipynb files):
```bash
# From split files
python -m txtarchive extract-notebooks "split_SickleCell_analysis" "extracted_notebooks" --replace_existing

# Or from single archive
python -m txtarchive extract-notebooks "SickleCell_analysis.txt" "extracted_notebooks" --replace_existing
```

**Archive** (creates split files for LLM processing):
```bash
python -m txtarchive archive "SickleCell" "SickleCell_R.txt" \
    --file_types .ipynb \
    --no-subdirectories \
    --llm-friendly \
    --extract-code-only \
    --split-output \
    --file_prefixes 1021 1020 1060 1030
```

```bash
python -m txtarchive archive "SickleCell_AI" "SickleCell_AI.txt" \
    --file_types .ipynb \
    --no-subdirectories \
    --llm-friendly \
    --extract-code-only \
    --split-output
```

**Result**: 
- `SickleCell_R.txt` (single archive)
- `split_SickleCell_R/` directory with `SickleCell_R_part1.txt`, `SickleCell_R_part2.txt`, etc.

**Extract Notebooks** (reconstruct .ipynb files):
```bash
# From split files
python -m txtarchive extract-notebooks "split_SickleCell_R" "extracted_notebooks" --replace_existing

# Or from single archive
python -m txtarchive extract-notebooks "SickleCell_R.txt" "extracted_notebooks" --replace_existing
```
---

### Rhino Shiny App

```bash

#!/bin/bash
# Archive code parts from Rhino R Shiny package using txtarchive, excluding renv directory
python -m txtarchive archive "schema" "schema/schema.txt" --file_types .R .js .scss .yaml .json--extract-code-only --split-output --exclude-dirs renv
```


### 2. LHN Package - File Transfer (Two Directory Levels)

**Purpose**: Move entire Python package between local and remote systems

**Archive** (for complete package transfer):
```bash
python -m txtarchive archive "lhn" "lhn/lhn.txt" \
    --file_types .py .yaml .md \
    --root-files setup.py requirements.txt environment_spark.yaml README.md pyproject.toml\
    --include-subdirs core utils tests lhn
```

**Transfer and Unpack** (on destination system):
```bash
# After transferring lhn_package.txt to remote system
python -m txtarchive unpack "lhn.txt" "lhn" --replace_existing
```

**Archive with Splitting** (for large packages):
```bash
python -m txtarchive archive "lhn" "lhn/lhn.txt" \
    --file_types .py .yaml .md \
    --root-files setup.py requirements.txt environment_spark.yaml \
    --split-output
```

**Unpack from Split Files**:
```bash
# Concatenate split files first
cat split_lhn/* > lhn.txt
python -m txtarchive unpack "lhn.txt" "lhn" --replace_existing
```

--- 

### .1 IU Diabetes

```bash
python -m txtarchive archive "IU-Diabetes-Diagnosis" "IU-Diabetes-Diagnosis.txt" \
    --file_types .py .md .sh .yaml .yml .json .txt .pth\
    --root-files gnnfork.py main.py README.md run.sh \
    --include-subdirs config data dataset runner \
    --split-output

```

---

### 3. Control Directory - Simple File Transfer (Single Directory)

**Purpose**: Archive single directory for moving between systems

**Archive** (all files in one directory):
```bash
python -m txtarchive archive "config" "config/config.txt" \
    --file_types .py .yaml .json  \
    --no-subdirectories
```

**Unpack** (on destination):
```bash
python -m txtarchive unpack "config.txt" "config" --replace_existing
```

**Archive with File Prefix Filter**:
```bash
python -m txtarchive archive "control" "control_config.txt" \
    --file_types .yaml .json \
    --no-subdirectories \
    --file_prefixes config- settings-
```

---

### 4. Multi-Directory Project - Selective Archiving

**Purpose**: Archive multiple specific directories from a larger project

**Archive Selected Directories**:
```bash
python -m txtarchive archive "MyProject" "project_core.txt" \
    --file_types .py .ipynb \
    --include-subdirs src tests notebooks \
    --root-files setup.py pyproject.toml
```

**Archive with LLM Format and Split**:
```bash
python -m txtarchive archive "MyProject" "project_llm.txt" \
    --file_types .py .ipynb \
    --include-subdirs src notebooks \
    --llm-friendly \
    --extract-code-only \
    --split-output
```

**Unpack**:
```bash
python -m txtarchive unpack "project_core.txt" "MyProject" --replace_existing
```

---

### 5. Configuration Files - Prefix-Based Selection

**Purpose**: Archive only configuration files with specific naming patterns

**Archive by Prefix**:
```bash
python -m txtarchive archive "configs" "system_configs.txt" \
    --file_types .yaml .json .toml \
    --no-subdirectories \
    --file_prefixes prod- dev- test-
```

**Archive Environment-Specific**:
```bash
python -m txtarchive archive "deployment" "prod_config.txt" \
    --file_types .yaml .env \
    --file_prefixes prod_ production_
```

**Unpack**:
```bash
python -m txtarchive unpack "system_configs.txt" "configs" --replace_existing
```

---

### 6. Notebook Development - LLM-Friendly Workflow

**Purpose**: Create clean code archives for LLM analysis and collaboration

**Archive for LLM** (strips outputs and metadata):
```bash
python -m txtarchive archive "analysis_notebooks" "clean_analysis.txt" \
    --file_types .ipynb \
    --llm-friendly \
    --extract-code-only \
    --file_prefixes 01_ 02_ 03_
```

**Archive with Split for Large Projects**:
```bash
python -m txtarchive archive "ml_pipeline" "pipeline_llm.txt" \
    --file_types .ipynb .py \
    --llm-friendly \
    --extract-code-only \
    --split-output \
    --split-max-chars 80000
```

**Extract Back to Notebooks**:
```bash
python -m txtarchive extract-notebooks "clean_analysis.txt" "restored_notebooks" --replace_existing
```

## File Transfer Workflow

### Local to Remote (AWS/Cloud):
1. **Archive locally**: `python -m txtarchive archive "myproject" "project.txt" --file_types .py .yaml`
2. **Transfer**: Copy `project.txt` to remote system (scp, rsync, cloud storage)
3. **Unpack remotely**: `python -m txtarchive unpack "project.txt" "myproject" --replace_existing`

### Large File Handling:
1. **Archive with split**: Add `--split-output` to create multiple smaller files
2. **Transfer split files**: Move the entire `split_*` directory
3. **Concatenate and unpack**: `cat split_*/* > archive.txt && python -m txtarchive unpack archive.txt output/`

## Tips for Different Use Cases

**For File Transfer:**
- Use standard format (no `--llm-friendly`) for exact file reconstruction
- Include `--root-files` for important project files like `setup.py`, `requirements.txt`
- Use `--split-output` for large projects that exceed transfer limits

**For LLM Analysis:**
- Use `--llm-friendly --extract-code-only` to minimize tokens
- Use `--file_prefixes` to analyze specific notebook sequences
- Split archives to fit model context windows

**For Backup/Archival:**
- Include all relevant file types with `--file_types`
- Use standard format to preserve exact file structure
- Consider excluding build directories with `--exclude-dirs build .git`

## Troubleshooting

- **Large files**: Use `--split-output` to create manageable chunks
- **Transfer errors**: Check `txtarchve.log` for detailed error messages
- **Missing files**: Verify file types and prefixes match your target files
- **Permission issues**: Ensure write access to output directories

## Security Notice

When using TxtArchive in environments handling sensitive data (e.g., HIPAA-regulated), users are solely responsible for ensuring compliance with all applicable privacy and security regulations. Always verify that archive outputs contain no sensitive information before transferring or sharing files.