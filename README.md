# txtarchive

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![GitHub Issues](https://img.shields.io/github/issues/yourusername/txtarchive)](https://github.com/yourusername/txtarchive/issues)

`txtarchive` is a Python utility for archiving text files (e.g., `.py`, `.ipynb`, `.yaml`) into a single text file and extracting them back. It’s designed to create LLM-friendly archives of Jupyter notebooks (stripping metadata) and reconstruct `.ipynb` files for Jupyter workflows. The package supports splitting large archives to fit LLM input limits, making it ideal for code sharing and automation in data science and healthcare analytics.

## Features

- **Archive**: Combine files from a directory into a single text archive, with optional LLM-friendly formatting (code-only for notebooks).
- **Unpack**: Extract files from a text archive to a directory, preserving structure.
- **Extract Notebooks**: Reconstruct `.ipynb` files from LLM-friendly archives.
- **Split Output**: Split large archives into chunks (default: 100,000 characters) for LLM compatibility.
- **Subdirectory Archiving**: Archive subdirectories into separate files for modular workflows.

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/txtarchive.git
   cd txtarchive
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

Run `python -m txtarchive --help` for full command details. Below are the main commands and examples tailored to common use cases.

### Commands

#### Archive
Combine files into a text archive.

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
- Archive Jupyter notebooks for LLM use:
  ```bash
  python -m txtarchive archive "SickleCell" "SickleCell_ADSCreationLLM.txt" --file_types .ipynb --no-subdirectories --llm-friendly --extract-code-only --split-output
  ```
- Archive Python files for backup:
  ```bash
  python -m txtarchive archive "lhn" "lhn.txt" --file_types .py --no-subdirectories
  ```

#### Unpack
Extract files from a text archive.

```bash
python -m txtarchive unpack <archive_file> <output_directory> [--replace_existing]
```

**Example**:
```bash
python -m txtarchive unpack "lhn.txt" "unpacked_lhn"
```

#### Extract Notebooks
Reconstruct `.ipynb` files from an LLM-friendly archive.

```bash
python -m txtarchive extract-notebooks <archive_file> <output_directory> [--replace_existing]
```

**Example**:
```bash
python -m txtarchive extract-notebooks "SickleCell_ADSCreationLLM.txt" "extracted_notebooks"
```

#### Archive Subdirectories
Archive each subdirectory into separate files.

```bash
python -m txtarchive archive_subdirectories <parent_directory> [options]
```

**Example**:
```bash
python -m txtarchive archive_subdirectories "parent_dir" --file_types .yaml .py
```

### Notes

- **Split Archives**: Split files are saved in `<split_output_dir>` (e.g., `split_SickleCell_ADSCreationLLM`). To extract notebooks from split archives, concatenate first:
  ```bash
  cat split_SickleCell_ADSCreationLLM/*.txt > SickleCell_ADSCreationLLM.txt
  python -m txtarchive extract-notebooks "SickleCell_ADSCreationLLM.txt" "extracted_notebooks"
  ```
- **Logs**: Check `txtarchve.log` for processing details or errors.
- **LLM-Friendly Archives**: Use `--llm-friendly --extract-code-only` to strip notebook metadata and non-code cells.
- **Notebook Reconstruction**: Extracted `.ipynb` files include minimal metadata (Python 3 kernel) and code cells only if `--extract-code-only` was used.

## Example Workflow

1. Archive notebooks for LLM use:
   ```bash
   python -m txtarchive archive "SickleCell" "SickleCell_ADSCreationLLM.txt" --file_types .ipynb --no-subdirectories --llm-friendly --extract-code-only --split-output
   ```

2. Extract notebooks for Jupyter:
   ```bash
   python -m txtarchive extract-notebooks "SickleCell_ADSCreationLLM.txt" "extracted_notebooks"
   jupyter notebook extracted_notebooks/
   ```

3. Archive a Python package:
   ```bash
   python -m txtarchive archive "lhn" "lhn.txt" --file_types .py .yaml --root-files setup.py requirements.txt
   ```

## Development

To contribute or modify the package:
1. Fork and clone the repository.
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install in editable mode:
   ```bash
   pip install -e .
   ```
4. Edit files in `txtarchive/` (e.g., `__main__.py`, `packunpack.py`).
5. Test changes:
   ```bash
   pytest tests/
   ```
6. Submit a pull request.

**Key Files**:
- `__main__.py`: CLI interface.
- `packunpack.py`: Core archiving/extraction logic.
- `split_files.py`: Archive splitting.
- `tests/`: Unit tests.

## Contributing

Contributions are welcome! Please:
1. Open an issue to discuss changes.
2. Follow the code style (PEP 8).
3. Add tests for new features.
4. Update `README.md` if needed.

See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## License

MIT License. See [LICENSE](LICENSE) for details.

---

Developed by Harlan A Nelson for managing code archives in data science workflows.