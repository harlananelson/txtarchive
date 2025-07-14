# TxtArchive: Code Archiving and File Transfer Toolkit

TxtArchive is a Python utility for packaging code files into plain text archives. This makes it easy to transfer projects between environments (e.g., local to cloud) or share selective code with LLMs for analysis/generation. It supports standard formats for exact reconstruction and LLM-optimized formats (e.g., stripped notebooks) to fit token limits.

## Key Use Cases

- Seamless File Transfer via Copy Buffer: In restricted environments (e.g., no direct file upload), archive a directory to a text file, copy-paste it, and unpack on the other side.
- Collaborating with LLMs: Select specific files/types/prefixes to create a clean archive for LLM input—great for targeted code reviews or modifications.
- LLM-Generated Projects: Describe an analysis to an LLM, have it output an archive with generated code/notebooks, then unpack for a ready-to-run project.

## Features

- Archive & Unpack: Combine files into text archives and extract them back to directories.
- File Transfer: Move directories between local and remote systems via text files.
- LLM-Friendly Format: Strip notebook outputs and metadata for efficient AI analysis.
- Smart Splitting: Split large archives into chunks for transfer limits or LLM context windows.
Flexible Filtering: Select files by type, prefix, or directories.
- Dual Formats: Standard for exact reconstruction; LLM-optimized for code analysis.

## Installation

TxtArchive requires Python 3.8+ and works best with `nbformat` for handling Jupyter notebooks (essential for LLM-friendly archiving and extraction).

1. Clone the repository:
   ```bash
   git clone https://github.com/harlananelson/txtarchive.git
   cd txtarchive
   ```

2. Install the package:
   ```bash
   pip install .
   ```
   (For editable mode during development: `pip install -e .`)

3. Verify the installation:
   ```bash
   python -m txtarchive --version
   ```


**Requirements**: Python 3.8+, `nbformat` (for Jupyter notebook support)

## Core Commands

Run commands via `python -m txtarchive <command> [args] [options]`. Use `--help` for details on any command.

- **Archive**: Create a text archive from a directory (ideal for transfer or LLM input).
  ```bash
  python -m txtarchive archive <directory> <output_file> [options]
  ```

- **Unpack**: Extract files from an archive back to a directory (for reconstructing after transfer).
  ```bash
  python -m txtarchive unpack <archive_file> <output_directory> [options]
  ```

- **Extract Notebooks**: Reconstruct Jupyter notebooks (.ipynb) from an archive (supports LLM-friendly or standard formats).
  ```bash
  python -m txtarchive extract-notebooks <archive_file_or_split_dir> <output_directory> [options]
  ```

- **Extract Notebooks and Quarto**: Reconstruct Jupyter notebooks (.ipynb) and Quarto files (.qmd) from an archive (extends extraction for mixed workflows).
  ```bash
  python -m txtarchive extract-notebooks-and-quarto <archive_file_or_split_dir> <output_directory> [options]
  ```

- **Archive Subdirectories**: Archive each subdirectory separately and combine them (useful for modular projects).
  ```bash
  python -m txtarchive archive_subdirectories <parent_directory> [options]
  ```

- **Generate**: Use an LLM to create an archive based on a study plan and module (ties into LLM-generated analysis use case; currently supports mock mode).
  ```bash
  python -m txtarchive generate <study_plan_path> <lhn_archive_path> <output_archive_path> [options]
  ```

## Key Options

Options vary by command—here's a breakdown. Defaults are noted where applicable.

### For `archive`
| Option | Description | Example/Default |
|--------|-------------|-----------------|
| `--file_types` | File extensions to include (nargs='+'). | `.py .ipynb .yaml` (default: `.yaml .py .r .ipynb .qmd`) |
| `--no-subdirectories` | Archive only top-level files (action='store_true'). | N/A |
| `--extract-code-only` | Extract just code/Markdown from notebooks (for LLM efficiency; action='store_true'). | N/A |
| `--llm-friendly` | Optimize format for LLM input (no metadata; action='store_true'). | N/A |
| `--file_prefixes` | Include only files starting with these (nargs='+'). | `prefix1 prefix2` |
| `--split-output` | Split archive into chunks (action='store_true'). | N/A |
| `--split-max-chars` | Max characters per split file. | `100000` (default) |
| `--split-output-dir` | Directory for split files. | Defaults to `split_<output_file_stem>` |
| `--exclude-dirs` | Subdirs to skip (nargs='+'). | `build .git` |
| `--root-files` | Specific root files to include (nargs='+'). | `setup.py requirements.txt` |
| `--include-subdirs` | Specific subdirs to include (nargs='+'). | `src tests` |

### For `unpack`, `extract-notebooks`, `extract-notebooks-and-quarto`
| Option | Description | Example/Default |
|--------|-------------|-----------------|
| `--replace_existing` | Overwrite existing files (action='store_true'). | N/A |

### For `archive_subdirectories`
| Option | Description | Example/Default |
|--------|-------------|-----------------|
| `--directories` | Specific subdirs to archive (nargs='+'). | Defaults to all |
| `--combined_archive_dir` | Dir for combined archives. | Defaults to parent dir |
| `--combined_archive_name` | Name of combined file. | `all_combined_archives.txt` (default) |
| `--file_types` | File extensions to include (nargs='+'). | `.yaml .py .r` (default: `.yaml .py .r .ipynb .qmd`) |

### For `generate`
| Option | Description | Example/Default |
|--------|-------------|-----------------|
| `--llm-model` | LLM model to use. | `mock` (default) |


## Examples

These are ready-to-copy bash commands demonstrating common workflows. Replace placeholders (e.g., `<directory>`) with your paths. See Core Commands for full details.

### 1. Copy-Buffer File Transfer (Local to Remote/Cloud)
**Purpose**: Archive a project to text, copy-paste (e.g., via buffer), and unpack remotely—perfect for restricted environments.

- Archive a Python package (standard format for exact reconstruction):
  ```bash
  python -m txtarchive archive "<directory>" "<output_file>.txt" \
      --file_types .py .yaml .md \
      --root-files setup.py requirements.txt \
      --include-subdirs src utils tests \
      --split-output
  ```
  **Result**: Creates `<output_file>.txt` (and split dir if large). Copy the file(s), then on remote:
  ```bash
  # If split: cat split_*/* > <output_file>.txt
  python -m txtarchive unpack "<output_file>.txt" "<output_dir>" --replace_existing
  ```

- Archive subdirectories separately (for modular projects):
  ```bash
  python -m txtarchive archive_subdirectories "<parent_dir>" \
      --directories subdir1 subdir2 \
      --file_types .py .yaml
  ```
  **Result**: Individual and combined archives. Unpack as above.

### 2. Selective File Sharing with LLMs
**Purpose**: Create optimized archives for LLM input (e.g., code review), filtering to reduce tokens.

- Archive notebooks for analysis (LLM-friendly, split for context limits):
  ```bash
  python -m txtarchive archive "<notebooks_dir>" "<output_file>.txt" \
      --file_types .ipynb \
      --no-subdirectories \
      --llm-friendly \
      --extract-code-only \
      --file_prefixes 01_ 02_ \
      --split-output \
      --split-max-chars 80000
  ```
  **Result**: LLM-ready `<output_file>.txt` and split dir. Paste into LLM prompt.

- Extract reconstructed notebooks from LLM output/modifications:
  ```bash
  python -m txtarchive extract-notebooks "<archive_or_split_dir>" "<output_dir>" --replace_existing
  ```
  (Use `extract-notebooks-and-quarto` for mixed .ipynb/.qmd.)

### 3. LLM-Generated Archives for Analysis
**Purpose**: Describe a task to an LLM, get an archive back, and unpack for ready code.

- Generate notebooks from a study plan (using mock LLM for testing):
  ```bash
  python -m txtarchive generate "<study_plan.txt>" "<module_archive.txt>" "<output_archive>.txt" \
      --llm-model mock
  ```
  **Result**: Archive with generated .ipynb files. Then extract:
  ```bash
  python -m txtarchive extract-notebooks "<output_archive>.txt" "<project_dir>" --replace_existing
  ```

## File Transfer Workflow

Use this for moving projects via text (e.g., copy buffer in restricted envs like cloud consoles). Works with standard or split archives.

### Local to Remote (e.g., AWS/Cloud)
1. **Archive locally** (standard format for fidelity):
   ```bash
   python -m txtarchive archive "<project_dir>" "<archive>.txt" --file_types .py .yaml --root-files requirements.txt
   ```
   Add `--split-output` for large projects.

2. **Transfer**: Copy `<archive>.txt` (or split dir) via buffer, scp, or cloud storage.

3. **Unpack remotely**:
   ```bash
   # If split: cat split_*/* > <archive>.txt
   python -m txtarchive unpack "<archive>.txt" "<output_dir>" --replace_existing
   ```

For LLM-optimized transfers (use case #b), add `--llm-friendly --extract-code-only` during archiving.

## Tips for Different Use Cases

- **For File Transfer (Use Case #a)**:
  - Stick to standard format (no `--llm-friendly`) for exact reconstruction.
  - Always include `--root-files` for key setup files (e.g., `setup.py`, `requirements.txt`).
  - Use `--split-output` and `--exclude-dirs build .git` for large/unclean projects.
  - In remote envs, verify TxtArchive is installed first (see Installation).

- **For Selective LLM Sharing (Use Case #b)**:
  - Add `--llm-friendly --extract-code-only` to strip extras and save tokens.
  - Filter with `--file_prefixes` for focused sequences (e.g., notebook steps).
  - Split via `--split-output` to match LLM context windows (e.g., 80k chars).
  - After LLM feedback, extract with `extract-notebooks` or `extract-notebooks-and-quarto`.

- **For LLM-Generated Archives (Use Case #c)**:
  - Describe your idea to an LLM (e.g., "Generate a Python package for data analysis using these modules...") and prompt it to output in TxtArchive format.
  - The LLM creates an archive (e.g., via `generate` command or manual prompt), which you unpack to ready files like Jupyter notebooks (.ipynb), Quarto Markdown (.qmd), RStudio projects (.Rmd/.R), or Python packages (.py files + setup).
  - **Example LLM Prompt** (copy-paste this as a starting point):
    ```
    Output a TxtArchive-compatible archive for my idea: [describe analysis, e.g., 'a SickleCell data pipeline']. Include Jupyter notebooks for steps like data cleaning and viz. Use this format:

    # LLM-FRIENDLY CODE ARCHIVE
    # TABLE OF CONTENTS
    1. cleaning.ipynb
    2. analysis.ipynb

    ################################################################################ 
    # FILE 1: cleaning.ipynb
    ################################################################################ 
    # Cell 1
    import pandas as pd
    ...
    ```
  - Then unpack:
    ```bash
    python -m txtarchive extract-notebooks "<llm_archive>.txt" "<project_dir>" --replace_existing
    ```
    (Adapt for Quarto/R: use `extract-notebooks-and-quarto`; for RStudio/Python packages, unpack standard and add manual setup like .Rproj files.)
  - Tip: Use `--llm-model` in `generate` for real integrations (mock for testing); ensure the LLM includes file extensions for correct extraction.



## Troubleshooting

If something goes wrong, start by checking `txtarchve.log` (generated in your working dir) for details. Run with `--help` or verbose logging if needed.

- **Large Files or Token Limits** (common in LLM sharing): Use `--split-output --split-max-chars 80000` to chunk archives; verify splits concatenate correctly with `cat`.
- **Missing/Incomplete Files** (e.g., during transfer or extraction): Double-check `--file_types`, `--file_prefixes`, and `--include-subdirs` match your project; for notebooks, ensure `nbformat` is installed.
- **Permission/Output Errors** (e.g., unpacking remotely): Confirm write access to output dirs; use `--replace_existing` to overwrite safely.
- **LLM-Related Issues** (e.g., generated archives won't extract): Validate the archive format (should have # TABLE OF CONTENTS and sections); test with mock mode in `generate` first.
- **Other Errors**: If code execution fails (e.g., JSON decode in notebooks), retry with clean inputs or report issues on GitHub with log excerpts.

### Proposed Security Notice Section
The original is strong and cautious—perfect for public repos handling potential sensitive data. I kept it almost verbatim but added a brief tie-in to LLM use cases (e.g., generated code might inadvertently include sensitive patterns) for relevance, without scaring folks off.

## Security Notice

TxtArchive does not encrypt or obfuscate content—archives are plain text. When handling sensitive data (e.g., in HIPAA-regulated environments or LLM-generated code that might include proprietary logic), you are solely responsible for compliance with all privacy and security regulations. Always inspect archives for sensitive information before transferring, sharing, or prompting LLMs. For high-security needs, consider additional tools like encryption.