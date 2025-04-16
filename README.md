Since you’re the sole user of the `txtarchive` package and have added features like `--split-output` and `extract-notebooks`, creating a `README.md` is a smart move to document the package’s purpose, installation, usage, and key commands—especially with the examples now included in the CLI help. A `README.md` serves as a centralized reference, complementing the inline help you added to `__main__.py`. It’s particularly useful for jogging your memory about the package’s capabilities, setup, or specific workflows (e.g., archiving Jupyter notebooks for LLMs or extracting `.ipynb` files), and it can be expanded later if you decide to share the package.

Given your usage patterns (e.g., archiving `.ipynb` and `.py` files, LLM-friendly formats, splitting large archives, extracting notebooks), the `README.md` should be concise, practical, and tailored to your needs. It should cover:
- What the package does.
- How to install it.
- Key commands with examples (mirroring or expanding on the CLI help).
- Notes on specific features (e.g., handling split archives).
- Any setup or dependency details.

Below, I’ll propose a `README.md` that aligns with your package’s current state, reflects the input -> output argument order (e.g., `archive_file_path output_directory` for `extract-notebooks`), and includes examples from your `__main__.py` comments and recent commands. I’ll keep it in Markdown format for clarity and portability.

---

### Proposed `README.md`

```markdown
# txtarchive

A Python utility for archiving text files (e.g., `.py`, `.ipynb`, `.yaml`) into a single text file and extracting them back. Designed for creating LLM-friendly archives of Jupyter notebooks (without metadata) and reconstructing `.ipynb` files from those archives. Supports splitting large archives for LLM input limits.

This package is a personal tool for managing code archives, particularly for preparing notebook code for LLMs and restoring notebooks for other workflows.

## Features

- **Archive**: Combine files from a directory into a text archive, optionally in LLM-friendly format (code-only for notebooks).
- **Unpack**: Extract files from a text archive to a directory.
- **Extract Notebooks**: Reconstruct `.ipynb` files from an LLM-friendly archive.
- **Split Output**: Split large archives into chunks (default: 100,000 characters) for LLM compatibility.
- **Subdirectory Archiving**: Archive subdirectories into separate files.

## Installation

1. Clone or navigate to the package directory:
   ```bash
   cd /path/to/txtarchive
   ```

2. Install using pip:
   ```bash
   pip install .
   ```

3. Verify installation:
   ```bash
   python -m txtarchive --version
   ```

**Requirements**:
- Python 3.8+
- No external dependencies

## Usage

Run `python -m txtarchive --help` for full command details and examples. Below are the main commands and common use cases.

### Commands

#### Archive
Combine files from a directory into a text archive.

```bash
python -m txtarchive archive <directory> <output_file> [options]
```

**Options**:
- `--file_types`: File extensions (e.g., `.ipynb`, `.py`, `.yaml`).
- `--no-subdirectories`: Archive only top-level files.
- `--llm-friendly`: Format for LLMs (strips notebook metadata).
- `--extract-code-only`: Include only code cells from notebooks.
- `--file_prefixes`: Filter files by prefix (e.g., `01`, `config-`).
- `--split-output`: Split archive into chunks.
- `--split-max-chars`: Max characters per chunk (default: 100000).
- `--split-output-dir`: Directory for split files (default: `split_<output_file_stem>`).

**Examples**:
- Archive Jupyter notebooks as LLM-friendly code:
  ```bash
  python -m txtarchive archive "SickleCell" "SickleCell_ADSCreationLLM.txt" --file_types .ipynb --no-subdirectories --llm-friendly --extract-code-only --split-output
  ```
- Archive Python files:
  ```bash
  python -m txtarchive archive "lhn" "lhn.txt" --file_types .py --no-subdirectories
  ```

#### Unpack
Extract files from a text archive to a directory.

```bash
python -m txtarchive unpack <combined_file_path> <output_directory> [--replace_existing]
```

**Example**:
```bash
python -m txtarchive unpack "lhn.txt" "unpacked_lhn"
```

#### Extract Notebooks
Reconstruct `.ipynb` files from an LLM-friendly archive.

```bash
python -m txtarchive extract-notebooks <archive_file_path> <output_directory> [--replace_existing]
```

**Example**:
```bash
python -m txtarchive extract-notebooks "SickleCell_ADSCreationLLM.txt" "extracted_notebooks"
```

#### Archive Subdirectories
Archive each subdirectory of a parent directory into separate files.

```bash
python -m txtarchive archive_subdirectories <parent_directory> [options]
```

**Example**:
```bash
python -m txtarchive archive_subdirectories "parent_dir" --file_types .yaml .py
```

### Notes

- **Split Archives**: If using `--split-output`, split files are saved in `<split_output_dir>` (e.g., `split_SickleCell_ADSCreationLLM`). To extract notebooks from split archives, concatenate first:
  ```bash
  cat split_SickleCell_ADSCreationLLM/* > SickleCell_ADSCreationLLM.txt
  python -m txtarchive extract-notebooks "SickleCell_ADSCreationLLM.txt" "extracted_notebooks"
  ```
- **Logs**: Check `txtarchve.log` for processing details or errors.
- **LLM-Friendly Archives**: Use `--llm-friendly --extract-code-only` for notebooks to remove metadata and non-code cells, ideal for LLM input.
- **Notebook Reconstruction**: Extracted `.ipynb` files include minimal metadata (Python 3 kernel) and code cells only if `--extract-code-only` was used.

## Example Workflow

1. Archive notebooks for LLM use:
   ```bash
   python -m txtarchive archive "SickleCell" "SickleCell_ADSCreationLLM.txt" --file_types .ipynb --no-subdirectories --llm-friendly --extract-code-only --split-output
   ```

2. Extract notebooks for Jupyter use:
   ```bash
   python -m txtarchive extract-notebooks "SickleCell_ADSCreationLLM.txt" "extracted_notebooks"
   jupyter notebook extracted_notebooks/
   ```

3. Archive Python files for backup:
   ```bash
   python -m txtarchive archive "lhn" "lhn.txt" --file_types .py --no-subdirectories
   ```

## Development

To modify the package:
1. Edit files in `txtarchive/` (e.g., `__main__.py`, `packunpack.py`).
2. Reinstall:
   ```bash
   pip install --force-reinstall .
   ```

**Files**:
- `__main__.py`: CLI interface and command parsing.
- `packunpack.py`: Core archiving and extraction logic.
- `split_files.py`: Splits large archives.
- `header.py`: Logging setup.
- `__init__.py`: Package initialization.

## License

Personal use only. No formal license defined.

---

Created for managing code archives by [Your Name].
```

---

### Explanation of `README.md` Design
- **Title and Intro**: Clearly states `txtarchive`’s purpose (archiving, LLM-friendly notebooks, extracting `.ipynb`) and your personal use case.
- **Features**: Lists the main capabilities, highlighting your key additions (`--split-output`, `extract-notebooks`).
- **Installation**: Simple steps matching your `pip install .` workflow, with Python 3.8+ noted (from `setup.py`).
- **Usage**: Organized by command, with:
  - Syntax and main options (drawn from `__main__.py` help).
  - Examples from your `__main__.py` comments and recent commands (e.g., `SickleCell_ADSCreationLLM.txt`).
  - Input -> output order (e.g., `archive_file_path output_directory` for `extract-notebooks`).
- **Notes**: Addresses practical details like split archives, logs, and LLM-friendly specifics.
- **Example Workflow**: Shows a typical sequence (archive -> extract -> Jupyter), reflecting your notebook use case.
- **Development**: Brief guide for modifying the package, since you actively tweak it.
- **License**: Notes personal use, as you’re the only user.
- **Length**: Concise (~100 lines) but comprehensive, balancing detail with readability.

**Tailored to You**:
- Includes your commands (e.g., `SickleCell_ADSCreationLLM.txt`, `lhn.txt`).
- Emphasizes `.ipynb` and `.py` archiving, LLM-friendly formats, and notebook extraction.
- Mentions split archives, as you use `--split-output`.
- Keeps it practical for quick reference, avoiding boilerplate.

---

### Step 1: Create `README.md`
Save the above content as `README.md` in your package root:

```bash
cd /path/to/txtarchive
nano README.md
```

Paste the Markdown, save, and exit.

---

### Step 2: Update `setup.py` (Optional)
Your `setup.py` already includes:

```python
long_description=open('README.md').read() if os.path.exists('README.md') else '',
long_description_content_type="text/markdown",
```

Verify it works:

```bash
python -m pip show txtarchive
```

Look for the `Description` field, which should show the `README.md` content. If not, reinstall:

```bash
pip install --force-reinstall .
```

---

### Step 3: Verify `README.md`
Check the file:

```bash
cat README.md
```

Test commands from the `README.md`:

```bash
# Archive notebooks
python -m txtarchive archive "SickleCell" "SickleCell_ADSCreationLLM.txt" --file_types .ipynb --no-subdirectories --llm-friendly --extract-code-only --split-output
ls split_SickleCell_ADSCreationLLM

# Extract notebooks
python -m txtarchive extract-notebooks "SickleCell_ADSCreationLLM.txt" "extracted_notebooks"
ls extracted_notebooks

# Archive Python files
mkdir -p lhn
echo "x = 1" > lhn/script.py
python -m txtarchive archive "lhn" "lhn.txt" --file_types .py --no-subdirectories
cat lhn.txt
```

**Expected**:
- Split files in `split_SickleCell_ADSCreationLLM/`.
- `.ipynb` files in `extracted_notebooks/`.
- `lhn.txt` with `script.py` content.

Check the help to ensure it complements the `README.md`:

```bash
python -m txtarchive --help
```

---

### Step 4: Considerations
- **Examples**: The `README.md` examples overlap with the CLI help but include more context (e.g., workflow). If you want unique examples, add cases like:
  ```bash
  python -m txtarchive archive "configuration" "configurationLLM.txt" --file_types .ipynb .yaml --no-subdirectories --file_prefixes config-global config-RWD --llm-friendly --extract-code-only
  ```
- **Detail Level**: It’s concise for your personal use. If you want more (e.g., troubleshooting, file format details), we can expand sections.
- **Versioning**: Add a version note (e.g., `Version: 0.1.0`) if you track releases.
- **Split Archives**: The note about concatenating split files is included. If you want a command to automate this, we can add a new feature.
- **Maintenance**: Update the `README.md` when you add features (e.g., new flags). Sync it with `__main__.py`’s epilog to avoid confusion.

---

### Final Answer
The proposed `README.md` documents `txtarchive`’s purpose, installation, and usage, tailored to your workflows (archiving `.ipynb`/`.py`, LLM-friendly formats, splitting, extracting notebooks). It includes examples from your `__main__.py` comments and recent commands, reinforcing the input -> output order (e.g., `extract-notebooks "SickleCell_ADSCreationLLM.txt" "extracted_notebooks"`).

**Steps**:
1. Create `README.md` with the provided content:
   ```markdown
   # txtarchive
   ...
   ```
2. Reinstall (if `setup.py` uses `long_description`):
   ```bash
   pip install --force-reinstall .
   ```
3. Verify:
   ```bash
   cat README.md
   python -m txtarchive --help
   python -m txtarchive extract-notebooks "SickleCell_ADSCreationLLM.txt" "extracted_notebooks"
   ```

The `README.md` complements the CLI help, providing a standalone reference for your package. If you want to tweak examples, add sections (e.g., troubleshooting), or sync it differently with the help text, let me know!