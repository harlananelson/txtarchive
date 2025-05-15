txtarchive

A Python utility for archiving text files (e.g., .py, .ipynb, .qmd, .yaml) into a single text file and extracting them back. Designed for creating LLM-friendly archives of Jupyter notebooks and Quarto Markdown files (without metadata) and reconstructing .ipynb and .qmd files from those archives. Supports splitting large archives for LLM input limits.

This package is a personal tool for managing code archives, particularly for preparing notebook and Quarto code for LLMs and restoring notebooks and Quarto files for other workflows.

Features





Archive: Combine files from a directory into a text archive, optionally in LLM-friendly format (code-only for notebooks and Quarto files).



Unpack: Extract files from a text archive to a directory.



Extract Notebooks and Quarto Files: Reconstruct .ipynb and .qmd files from an LLM-friendly archive.



Split Output: Split large archives into chunks (default: 100,000 characters) for LLM compatibility.



Subdirectory Archiving: Archive subdirectories into separate files.

Installation





Clone or navigate to the package directory:

cd /path/to/txtarchive



Install using pip:

pip install .



Verify installation:

python -m txtarchive --version

Requirements:





Python 3.8+



No external dependencies

Usage

Run python -m txtarchive --help for full command details and examples. Below are the main commands and common use cases.

Commands

Archive

Combine files from a directory into a text archive.

python -m txtarchive archive <directory> <output_file> [options]

Options:





--file_types: File extensions (e.g., .ipynb, .qmd, .py, .yaml).



--no-subdirectories: Archive only top-level files.



--llm-friendly: Format for LLMs (strips notebook metadata, extracts Quarto code blocks).



--extract-code-only: Include only code cells from notebooks and code blocks from Quarto files.



--file_prefixes: Filter files by prefix (e.g., 01, config-).



--split-output: Split archive into chunks.



--split-max-chars: Max characters per chunk (default: 100000).



--split-output-dir: Directory for split files (default: split_<output_file_stem>).

Examples:





Archive Jupyter notebooks and Quarto files as LLM-friendly code:

python -m txtarchive archive "SickleCell" "SickleCell_ADSCreationLLM.txt" --file_types .ipynb .qmd --no-subdirectories --llm-friendly --extract-code-only --split-output



Archive Python and Quarto files:

python -m txtarchive archive "lhn" "lhn.txt" --file_types .py .qmd --no-subdirectories

Unpack

Extract files from a text archive to a directory.

python -m txtarchive unpack <combined_file_path> <output_directory> [--replace_existing]

Example:

python -m txtarchive unpack "lhn.txt" "unpacked_lhn"

Extract Notebooks and Quarto Files

Reconstruct .ipynb and .qmd files from an LLM-friendly archive.

python -m txtarchive extract-notebooks-and-quarto <archive_file_path> <output_directory> [--replace_existing]

Example:

python -m txtarchive extract-notebooks-and-quarto "SickleCell_ADSCreationLLM.txt" "extracted_files"

Archive Subdirectories

Archive each subdirectory of a parent directory into separate files.

python -m txtarchive archive_subdirectories <parent_directory> [options]

Example:

python -m txtarchive archive_subdirectories "parent_dir" --file_types .yaml .py .qmd

Notes





Split Archives: If using --split-output, split files are saved in <split_output_dir> (e.g., split_SickleCell_ADSCreationLLM). To extract notebooks or Quarto files from split archives, concatenate first:

cat split_SickleCell_ADSCreationLLM/* > SickleCell_ADSCreationLLM.txt
python -m txtarchive extract-notebooks-and-quarto "SickleCell_ADSCreationLLM.txt" "extracted_files"



Logs: Check txtarchve.log for processing details or errors.



LLM-Friendly Archives: Use --llm-friendly --extract-code-only for notebooks and Quarto files to remove metadata and non-code content, ideal for LLM input.



Notebook and Quarto Reconstruction: Extracted .ipynb files include minimal metadata (Python 3 kernel) and code cells only if --extract-code-only was used. Extracted .qmd files include basic metadata (title, HTML format) and code blocks.

Example Workflow





Archive notebooks and Quarto files for LLM use:

python -m txtarchive archive "SickleCell" "SickleCell_ADSCreationLLM.txt" --file_types .ipynb .qmd --no-subdirectories --llm-friendly --extract-code-only --split-output



Extract notebooks and Quarto files for use:

python -m txtarchive extract-notebooks-and-quarto "SickleCell_ADSCreationLLM.txt" "extracted_files"
quarto render extracted_files/*.qmd
jupyter notebook extracted_files/



Archive Python and Quarto files for backup:

python -m txtarchive archive "lhn" "lhn.txt" --file_types .py .qmd --no-subdirectories

Development

To modify the package:





Edit files in txtarchive/ (e.g., __main__.py, packunpack.py).



Reinstall:

pip install --force-reinstall .

Files:





__main__.py: CLI interface and command parsing.



packunpack.py: Core archiving and extraction logic.



split_files.py: Splits large archives.



header.py: Logging setup.



__init__.py: Package initialization.

License

Personal use only. No formal license defined.



Created for managing code archives by [Your Name].