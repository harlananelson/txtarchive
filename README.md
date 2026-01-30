# TxtArchive: Code Archiving and File Transfer Toolkit

> **For LLMs Reading This**: This tool creates text-based archives of codebases in two formats: **Standard** (for exact reconstruction) and **LLM-Friendly** (optimized for AI analysis). The key thing to understand is which commands work with which formats - see the compatibility matrix below.

## Quick Reference for LLMs

### Archive Formats Explained

TxtArchive supports **two distinct archive formats**:

| Format | Separator Pattern | Purpose | Unpacking |
|--------|------------------|---------|-----------|
| **Standard** | `---\nFilename: path/to/file.py\n---` | Exact file reconstruction | ✅ `unpack` command |
| **LLM-Friendly** | `# FILE 1: path/to/file.py\n###...###` | AI analysis, stripped metadata | ✅ `unpack` (auto-detects) or `extract-notebooks` for .ipynb |

### Format Selection Decision Tree

```
Are you creating an archive?
├─ For transfer/reconstruction → Use standard format (default, no --llm-friendly flag)
├─ For LLM analysis → Use --llm-friendly flag
└─ For Ask Sage ingestion → Use --llm-friendly flag
```

### Command + Format Compatibility Matrix

| Command | Standard Format | LLM-Friendly Format | Notes |
|---------|----------------|---------------------|-------|
| `archive` | ✅ Creates | ✅ Creates with `--llm-friendly` | Choose format at creation |
| `unpack` | ✅ Unpacks | ✅ Unpacks (auto-detects format) | Works with both formats |
| `extract-notebooks` | ❌ | ✅ Extracts .ipynb | Reconstructs notebooks from cell markers |
| `extract-notebooks-and-quarto` | ❌ | ✅ Extracts .ipynb + .qmd | LLM format only |
| `archive-and-ingest` | N/A | ✅ Recommended for AI | Uses LLM format |

### Format Auto-Detection

The `unpack` command automatically detects the archive format and uses the appropriate parser:

```bash
# Both formats work with unpack (auto-detected)
python -m txtarchive archive myproject/ archive.txt
python -m txtarchive unpack archive.txt restored_project/

python -m txtarchive archive myproject/ archive.txt --llm-friendly
python -m txtarchive unpack archive.txt restored_project/  # Also works!
```

**Note:** For Jupyter notebooks in LLM-friendly format, use `extract-notebooks` to reconstruct `.ipynb` files with proper cell structure from the `# Cell N` markers.

## Architecture Overview (for LLM Understanding)

### How txtarchive Represents Files

**Standard Format Example:**
```
# Archive created on: 2025-10-08 14:49:03
# Standard Archive Format
# TABLE OF CONTENTS
1. test.txt
---
Filename: test.txt
---
content here
---
Filename: another.py
---
more content
```

**LLM-Friendly Format Example:**
```
# Archive created on: 2025-10-08 14:50:32
# LLM-FRIENDLY CODE ARCHIVE
# Generated from: /path/to/project
# Date: 2025-10-08 14:50:32
# TABLE OF CONTENTS
1. test.txt
2. another.py

################################################################################
# FILE 1: test.txt
################################################################################

content here

################################################################################
# FILE 2: another.py
################################################################################

more content
```

### Why Two Formats?

1. **Standard Format**: Preserves exact file structure for reconstruction
   - Every file section starts with `---\nFilename: `
   - Parser: `sections = content.split("---\nFilename: ")[1:]`

2. **LLM-Friendly Format**: Optimized for token efficiency
   - Strips notebook outputs, removes metadata
   - Clear visual boundaries with `#` separators
   - Parser: `sections = content.split("################################################################################\n# FILE ")`

## Installation

```bash
git clone https://github.com/harlananelson/txtarchive.git
cd txtarchive
pip install -e .

# Optional: For Ask Sage integration
export ACCESS_TOKEN="your_ask_sage_token"

# Verify
python -m txtarchive --version
```

## ❄️ Nix Development Environment (Recommended)

This project supports **Nix**, a powerful package manager that ensures every developer uses the *exact* same version of Python, Pandoc, and system libraries. This eliminates "it works on my machine" errors.

### Why use Nix?
* **Hermetic Dependencies:** Installs the correct version of `pandoc` automatically (no need for `brew install` or `apt-get`).
* **Reproducible Builds:** The `flake.lock` file guarantees identical environments across all machines.
* **Dual-Support:** You can still use standard `pip` / `python -m` if you prefer (see standard installation above).

### 1. Install Nix (macOS / Linux)
If you don't have Nix, install it using the Determinate Systems installer (recommended):
```bash
curl --proto '=https' --tlsv1.2 -sSf -L [https://install.determinate.systems/nix](https://install.determinate.systems/nix) | sh -s -- install

```

### 2. Enter the Dev Shell

To start developing with all dependencies (Python 3.x, Pandoc, etc.) pre-configured:

```bash
# This downloads and sets up the environment in a temporary shell
nix develop

```

*Once inside this shell, you can run `python -m txtarchive ...` immediately.*

### 3. Build the Production Binary

To create a standalone, optimized executable of `txtarchive`:

```bash
nix build

```

This creates a `./result` symlink. You can run the binary directly:

```bash
./result/bin/txtarchive --help

```

### 4. Troubleshooting

* **Pandoc Errors:** If you are *not* using Nix and see a "Pandoc not found" error, you must install it manually (`brew install pandoc`). The Nix environment handles this for you automatically.

## Core Commands with Format Guidance

### `archive` - Create an Archive

**Syntax:**
```bash
python -m txtarchive archive <directory> <output_file> [options]
```

**Format Selection:**
- **Default**: Standard format (no flag needed)
- **LLM-friendly**: Add `--llm-friendly` flag

**Key Options:**
- `--file_types .py .md .yaml` - File extensions to include (default: .yaml, .py, .r, .ipynb, .qmd)
- `--llm-friendly` - **Changes output format** to LLM-optimized
- `--extract-code-only` - Strip notebook outputs (only with `--llm-friendly`)
- `--split-output` - Split into chunks (useful for token limits)
- `--max-tokens 75000` - Maximum tokens per chunk
- `--exclude-dirs .venv __pycache__ .git` - Directories to skip
- `--root-files setup.py README.md` - Specific root files to always include
- `--include-subdirs src tests` - Only include these subdirectories

**Examples:**

```bash
# Standard format for reconstruction
python -m txtarchive archive myproject/ myproject.txt \
    --file_types .py .yaml

# LLM-friendly format for AI analysis
python -m txtarchive archive myproject/ myproject_llm.txt \
    --file_types .py .md \
    --llm-friendly \
    --extract-code-only
```

### `unpack` - Extract Files from Archive

**Syntax:**
```bash
python -m txtarchive unpack <archive_file> <output_directory> [--replace_existing]
```

The `unpack` command automatically detects the archive format (standard or LLM-friendly) and extracts files accordingly.

**Smart notebook reconstruction** (LLM-friendly archives):
- `.ipynb` files → Reconstructed as JSON notebooks from `# Cell N` markers
- `.py` files with `# MAGIC` patterns → Reconstructed as Databricks notebooks with `# COMMAND ----------` separators
- All other files → Extracted as plain text

**Options:**
- `--replace_existing` - Overwrite existing files

**Example:**
```bash
# Standard format
python -m txtarchive archive myproject/ archive.txt
python -m txtarchive unpack archive.txt restored/ --replace_existing

# LLM-friendly format (also works - auto-detected)
python -m txtarchive archive myproject/ archive.txt --llm-friendly
python -m txtarchive unpack archive.txt restored/ --replace_existing
```

### `extract-notebooks` - Extract Jupyter Notebooks

**Syntax:**
```bash
python -m txtarchive extract-notebooks <archive_file> <output_directory> [--replace_existing]
```

**⚠️ FORMAT REQUIREMENT: LLM-FRIENDLY FORMAT ONLY**

This command parses the LLM-friendly format and reconstructs `.ipynb` files.

**Example:**
```bash
# Create LLM-friendly archive with notebooks
python -m txtarchive archive notebooks/ notebooks.txt \
    --file_types .ipynb \
    --llm-friendly \
    --extract-code-only

# Extract them back
python -m txtarchive extract-notebooks notebooks.txt restored_notebooks/ \
    --replace_existing
```

### `archive-and-ingest` - Create and Send to Ask Sage

**Syntax:**
```bash
python -m txtarchive archive-and-ingest <directory> <output_file> [options]
```

**Format:** Always uses LLM-friendly format (automatic)

**Additional Options:**
- `--ingestion-method auto|directory|archive` - How to ingest (default: auto)
- `--rm-archive` - Delete archive after successful ingestion

**Example:**
```bash
python -m txtarchive archive-and-ingest myproject/ analysis.txt \
    --file_types .py .md \
    --exclude-dirs .venv __pycache__ \
    --ingestion-method auto
```

## Common Workflows

### Workflow 1: Project Transfer (Local → Remote)

**Use Standard Format:**
```bash
# Local machine: Create standard archive
python -m txtarchive archive myproject/ transfer.txt \
    --file_types .py .yaml .md \
    --exclude-dirs .venv __pycache__

# Copy transfer.txt to remote (scp, clipboard, etc.)

# Remote machine: Unpack
python -m txtarchive unpack transfer.txt myproject/ --replace_existing
```

### Workflow 2: AI Code Review

**Use LLM-Friendly Format:**
```bash
# Create optimized archive for LLM
python -m txtarchive archive src/ review.txt \
    --file_types .py \
    --llm-friendly \
    --split-output \
    --max-tokens 75000

# Send to LLM for analysis (copy/paste or API)
# LLM provides feedback

# If LLM generates modified code, use extract-notebooks if applicable
```

### Workflow 3: Ask Sage Integration

**Use archive-and-ingest (Automatic LLM Format):**
```bash
python -m txtarchive archive-and-ingest myproject/ analysis.txt \
    --file_types .py .md .yaml \
    --root-files requirements.txt setup.py \
    --exclude-dirs .venv __pycache__ .git \
    --ingestion-method auto \
    --max-tokens 75000
```

## Troubleshooting Guide for LLMs

### Issue: "Unpack creates empty directory"

**Diagnosis:** The archive format may not be recognized, or the archive is malformed.

**Solution:**
```bash
# Check format
head -n 10 your_archive.txt

# Standard format should have: "---\nFilename: "
# LLM-friendly format should have: "# LLM-FRIENDLY CODE ARCHIVE" and "# FILE 1:"

# Both formats are supported by unpack (auto-detected)
python -m txtarchive unpack your_archive.txt output_dir/ --replace_existing
```

### Issue: "extract-notebooks doesn't find files"

**Diagnosis:** You're using standard format archive with extract-notebooks.

**Solution:**
```bash
# extract-notebooks requires LLM-friendly format
python -m txtarchive archive notebooks/ notebooks.txt --llm-friendly
python -m txtarchive extract-notebooks notebooks.txt output/
```

### Issue: "Too many tokens for LLM"

**Solution:**
```bash
# Use split-output with smaller chunks
python -m txtarchive archive large_project/ archive.txt \
    --llm-friendly \
    --split-output \
    --max-tokens 50000 \
    --split-output-dir chunks/
```

### Issue: "Files missing after unpack"

**Check:**
1. File types included: `--file_types .py .md` (defaults exclude .txt, .json, etc.)
2. Root files specified: `--root-files README.md setup.py`
3. Subdirectories: `--include-subdirs src tests` or remove `--no-subdirectories`

**Solution:**
```bash
# Be explicit about what to include
python -m txtarchive archive myproject/ archive.txt \
    --file_types .py .md .yaml .txt .json .toml \
    --root-files README.md setup.py pyproject.toml \
    --exclude-dirs .venv __pycache__ node_modules
```

## API Reference for Programmatic Use

```python
from txtarchive.packunpack import archive_files, unpack_files_auto

# Create standard archive
archive_files(
    directory="myproject",
    output_file_path="archive.txt",
    file_types=[".py", ".md"],
    llm_friendly=False  # Standard format
)

# Create LLM-friendly archive
archive_files(
    directory="myproject",
    output_file_path="archive_llm.txt",
    file_types=[".py", ".md"],
    llm_friendly=True  # LLM format
)

# Unpack any format (auto-detects)
unpack_files_auto(
    output_directory="restored",
    combined_file_path="archive.txt",
    replace_existing=True
)
```

## Environment Variables

```bash
# Required for Ask Sage integration
export ACCESS_TOKEN="your_ask_sage_api_token"
```

## Feature Roadmap

### Current Capabilities

- **Auto-detection of archive format** - `unpack` command detects and handles both formats
- **General unpack for LLM-friendly format** - `unpack_llm_archive()` implemented
- **Jupyter notebook reconstruction** - Automatically rebuilds `.ipynb` files from `# Cell N` markers
- **Databricks notebook reconstruction** - Automatically rebuilds `.py` Databricks notebooks with `# COMMAND ----------` separators and `# MAGIC` prefixes

### Planned Improvements

1. Add `convert` command to switch between formats
2. Improve error messages for malformed archives

## Contributing

See issues for feature requests and bugs. Pull requests welcome!

## License

MIT License

## Changelog

### v0.2.0
- Auto-detection of archive format in `unpack` command
- `unpack_llm_archive()` for general LLM format unpacking
- Improved notebook cell parsing with markdown support
- Databricks notebook support - auto-reconstructs `.py` files with `# MAGIC` patterns

### v0.1.0
- Initial release with archive/unpack
- LLM-friendly format support
- Jupyter notebook handling
- Ask Sage integration
- Word document conversion