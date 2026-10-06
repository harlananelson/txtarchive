import json
import re
from pathlib import Path
from .header import logger
from datetime import datetime
from .source_paths import (
    ArchiveEntry,
    archive_alias,
    format_knowledge_manifest,
    git_context,
    iter_llm_sections,
    iter_standard_sections,
    knowledge_file_text,
    number_entries,
    parse_knowledge_text,
    render_archive,
    repo_relative_posix,
    safe_child,
)

def read_notebook(notebook_path):
    """
    Read a Jupyter notebook file and handle encoding issues. Return the content.

    Args:
        notebook_path (Path): Path to the Jupyter notebook file.

    Returns:
        dict: The notebook content as a dictionary, or None if an error occurs.
    """
    try:
        with notebook_path.open("r", encoding="utf-8", errors="replace") as file:
            notebook = json.load(file)
        return notebook
    except json.JSONDecodeError as e:
        logger.error(f"Error reading {notebook_path}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error reading {notebook_path}: {e}")
        return None

def remove_outputs_from_code_cells(notebook):
    """
    Remove the output from code cells in a Jupyter notebook.

    Args:
        notebook (dict): The notebook content as a dictionary.

    Returns:
        dict: The notebook content with outputs stripped.
    """
    for cell in notebook.get("cells", []):
        if cell["cell_type"] == "code":
            cell["outputs"] = []
    return notebook

def strip_outputs_from_ipynb(file_path):
    """
    Remove the output from a Jupyter notebook and preserve only the code.

    Args:
        file_path (Path): Path to the Jupyter notebook file.

    Returns:
        str: The notebook content with outputs stripped as a JSON string.
    """
    try:
        with file_path.open("r", encoding="utf-8", errors="replace") as file:
            notebook = json.load(file)
        for cell in notebook.get("cells", []):
            if cell["cell_type"] == "code":
                cell["outputs"] = []
        return json.dumps(notebook, indent=4)
    except Exception as e:
        logger.error(f"Error processing {file_path}: {e}")
        return None

def concatenate_files(directory, combined_file_path, file_types=[".yaml", ".py", ".r"]):
    """
    Concatenate files of specified types in a directory into a single text file.
    """
    logger.info("Concatenating files in directory: %s", directory)
    directory = Path(directory)
    git = git_context(directory)
    entries = []

    for path in directory.rglob("*"):
        if (
            path.is_file()
            and not path.name.startswith((".", "#"))
            and directory in path.parents
        ):
            content = None
            rel_path = path.relative_to(directory)
            
            is_init_file = path.name == "__init__.py"
            if is_init_file:
                logger.info(f"Found __init__.py file at {path}, attempting to read...")

            if path.suffix == ".ipynb":
                logger.info("Archiving %s", path.name)
                content = read_notebook(path)
                if content is not None:
                    content = remove_outputs_from_code_cells(content)
                    content = json.dumps(content, indent=4)
            elif path.suffix in file_types:
                logger.info("Processing %s", path.name)
                try:
                    with path.open("r", encoding="utf-8") as file:
                        content = file.read()
                        if is_init_file:
                            logger.info(f"Successfully read __init__.py, content length: {len(content)}")
                            logger.info(f"First 50 characters: {repr(content[:50])}")
                except FileNotFoundError:
                    logger.error("File not found: %s", path)
                    continue
                except Exception as e:
                    logger.error(f"Error reading file {path}: {str(e)}")
                    continue

            if content is not None:
                if is_init_file:
                    logger.info(f"Adding __init__.py content to archive, path: {rel_path}")
                entries.append(ArchiveEntry(
                    alias=archive_alias(rel_path),
                    source=repo_relative_posix(path, directory, git),
                    content=content,
                ))
            elif is_init_file:
                logger.warning(f"No content was obtained from __init__.py at {path}")

    entries.sort(key=lambda entry: entry.alias)
    entries = number_entries(entries)
    created = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    all_contents = render_archive(
        entries,
        llm_friendly=False,
        git=git,
        created=created,
        include_patch_instructions=False,
        line_numbers=False,
    )
    logger.info(f"Total content size to write: {len(all_contents)} bytes")
    
    with combined_file_path.open("w", encoding="utf-8") as file:
        file.write(all_contents)
    logger.info("Files concatenated into: %s", combined_file_path)

def unpack_files(output_directory, combined_file_path, replace_existing=False):
    """
    Unpack files from a combined text file into a specified directory.

    Args:
        output_directory (Path): Directory to output the unpacked files.
        combined_file_path (Path): Path to the combined text file.
        replace_existing (bool): Whether to replace existing files (default: False).
    """
    if isinstance(combined_file_path, str):
        combined_file_path = Path(combined_file_path)
    if isinstance(output_directory, str):
        output_directory = Path(output_directory)

    with combined_file_path.open("r", encoding="utf-8") as file:
        combined_content = file.read()

    if not output_directory.exists():
        try:
            output_directory.mkdir(parents=True, exist_ok=True)
            logger.info("Created directory: %s", output_directory)
        except Exception as e:
            logger.error(f"Error creating directory {output_directory}: {e}")
            return
    else:
        logger.info("Directory already exists: %s", output_directory)

    for filename, content, _meta in iter_standard_sections(combined_content):
        try:
            output_path = safe_child(output_directory, filename)
            if output_path is None:
                logger.error(f"Path traversal blocked: {filename}")
                continue

            output_path.parent.mkdir(parents=True, exist_ok=True)

            if output_path.exists() and not replace_existing:
                output_path = output_path.with_suffix(output_path.suffix + "_copy")

            with output_path.open("w", encoding="utf-8") as file:
                file.write(content)
                logger.info("Unpacked file: %s", output_path)
        except Exception as e:
            logger.error(f"Error processing section for {filename}: {e}")
            continue
    logger.info("Files unpacked into: %s", output_directory)

def run_concat(
    current_directory,
    combined_files="combined_files.txt",
    file_types=[".yaml", ".py", ".r"],
):
    """
    Wrapper for the `concatenate_files` function.

    Args:
        current_directory (Path): Directory to search for files.
        combined_files (Path): Path to the output file.
        file_types (list): List of file extensions to include.
    """
    if isinstance(current_directory, str):
        current_directory = Path(current_directory)
    if isinstance(combined_files, str):
        combined_files = Path(combined_files)

    concatenate_files(current_directory, combined_files, file_types=file_types)

# Modify run_unpack to use auto-detection
def run_unpack(output_directory, combined_file_path, replace_existing=False, kernel=None, force=False):
    """Run unpack with auto-detection."""
    logger.info(
        f"Unpacking files from {combined_file_path} to {output_directory} using replace_existing={replace_existing}"
    )
    if kernel:
        logger.info(f"Using explicit kernel: {kernel}")
    unpack_files_auto(output_directory, combined_file_path, replace_existing, kernel=kernel, force=force)
    logger.info(f"Files have been unpacked into: {output_directory}")


def archive_subdirectories(
    parent_directory,
    directories=None,
    combined_archive_dir=None,
    combined_archive_name="all_combined_archives.txt",
    file_types=[".yaml", ".py", ".r"],
):
    """
    Archive specified subdirectories into combined archive files.

    Args:
        parent_directory (Path): Parent directory containing subdirectories to archive.
        directories (list): Specific subdirectories to archive (default is all subdirectories).
        combined_archive_dir (Path): Directory to store the combined archive files.
        combined_archive_name (str): Base name for the combined archive files.
        file_types (list): List of file extensions to include.
    """
    parent_directory = Path(parent_directory)
    if directories is None:
        directories = [d for d in parent_directory.iterdir() if d.is_dir()]
    else:
        directories = [parent_directory / d for d in directories]

    if combined_archive_dir is not None:
        combined_archive_dir = Path(combined_archive_dir)
        combined_archive_dir.mkdir(parents=True, exist_ok=True)

    for item_path in directories:
        if item_path.is_dir():
            archive_file_name = f"{item_path.name}_{combined_archive_name}.txt"
            archive_file = (
                (combined_archive_dir / archive_file_name)
                if combined_archive_dir
                else (parent_directory / archive_file_name)
            )
            run_concat(item_path, combined_files=archive_file, file_types=file_types)
            logger.info("Archived %s into %s", item_path, archive_file)

    combine_all_archives(
        parent_directory, combined_archive_dir, combined_archive_name, directories
    )

def _is_databricks_content(file_content):
    """
    Detect if file content appears to be from a Databricks notebook.

    Checks for Databricks-specific patterns like # MAGIC commands.

    Args:
        file_content (str): The file content to check

    Returns:
        bool: True if content appears to be Databricks format
    """
    # Check for explicit Databricks header
    if '# Databricks notebook source' in file_content:
        return True
    # Check for MAGIC commands (markdown, sql, python, etc.)
    if '# MAGIC %' in file_content or '# MAGIC #' in file_content:
        return True
    return False


def _reconstruct_databricks_notebook(file_content, filename):
    """
    Reconstruct a Databricks notebook from LLM-friendly cell markers.

    Args:
        file_content (str): The text content with # Cell N markers
        filename (str): The filename (for logging)

    Returns:
        str: Databricks notebook source format
    """
    lines = []
    lines.append("# Databricks notebook source")

    content_lines = file_content.splitlines()
    i = 0
    cell_count = 0

    while i < len(content_lines):
        line = content_lines[i]

        # Check for markdown cell
        if line.startswith("# Markdown Cell "):
            if cell_count > 0:
                lines.append("")
                lines.append("# COMMAND ----------")
                lines.append("")
            cell_count += 1

            # Look for triple quotes on next line
            i += 1
            if i < len(content_lines) and content_lines[i].strip() == '"""':
                # Start collecting markdown content
                i += 1
                lines.append("# MAGIC %md")
                while i < len(content_lines):
                    if content_lines[i].strip() == '"""':
                        # End of markdown
                        break
                    # Add MAGIC prefix to markdown lines
                    md_line = content_lines[i]
                    lines.append(f"# MAGIC {md_line}")
                    i += 1
            i += 1

        # Check for code cell
        elif line.startswith("# Cell "):
            if cell_count > 0:
                lines.append("")
                lines.append("# COMMAND ----------")
                lines.append("")
            cell_count += 1

            # Collect code until next cell marker or end
            i += 1
            cell_lines = []
            while i < len(content_lines):
                next_line = content_lines[i]
                # Check if we've hit the next cell marker
                if next_line.startswith("# Cell ") or next_line.startswith("# Markdown Cell ") or next_line.startswith("# Raw Cell "):
                    break
                cell_lines.append(content_lines[i])
                i += 1

            # Remove trailing empty lines
            while cell_lines and not cell_lines[-1].strip():
                cell_lines.pop()

            # Add cell content
            for cell_line in cell_lines:
                lines.append(cell_line)
        else:
            i += 1

    logger.info(f"Reconstructed {cell_count} cells for Databricks notebook: {filename}")
    return '\n'.join(lines)


def _make_kernel_metadata(kernel_name):
    """Build kernel metadata from an explicit kernel name.

    Recognizes common R kernel names (containing 'r' or 'ir') and treats
    everything else as a Python kernel.  The *display_name* is set to the
    kernel name itself so Jupyter shows a recognizable label.

    Args:
        kernel_name (str): Jupyter kernel name, e.g. ``r_env``,
            ``pyspark-lhn-dev``, ``ir``, ``python3``.

    Returns:
        dict: Notebook-level ``metadata`` dict with ``kernelspec`` and
        ``language_info`` keys.
    """
    is_r = kernel_name in ("ir", "r_env") or kernel_name.startswith("r_")
    if is_r:
        return {
            "kernelspec": {
                "display_name": kernel_name,
                "language": "R",
                "name": kernel_name,
            },
            "language_info": {"name": "R"},
        }
    return {
        "kernelspec": {
            "display_name": kernel_name,
            "language": "python",
            "name": kernel_name,
        },
        "language_info": {"name": "python", "version": "3.10.0"},
    }


def _jupyter_kernel_from_raw_yaml(content):
    """Parse ``jupyter: <kernel>`` from a Raw Cell YAML front matter block."""
    in_raw = False
    in_yaml = False
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("# Raw Cell "):
            in_raw = True
            in_yaml = False
            continue
        if not in_raw:
            continue
        if stripped == '"""':
            if in_yaml:
                break
            in_yaml = True
            continue
        if in_yaml and stripped == "---":
            continue
        if in_yaml and stripped.startswith("jupyter:"):
            return stripped.split(":", 1)[1].strip()
    return None


def _detect_notebook_kernel(content, kernel=None):
    """Detect notebook language from content and return appropriate kernel metadata.

    If *kernel* is given it takes precedence over auto-detection.
    """
    if kernel:
        return _make_kernel_metadata(kernel)

    yaml_kernel = _jupyter_kernel_from_raw_yaml(content)
    if yaml_kernel:
        return _make_kernel_metadata(yaml_kernel)

    is_r = bool(
        re.search(r'\blibrary\(', content) or
        re.search(r'\bpacman::p_load\(', content) or
        re.search(r'\btidyverse\b', content) or
        re.search(r'\btidymodels\b', content) or
        re.search(r'\btar_load\(', content)
    )
    if is_r:
        return {
            "kernelspec": {
                "display_name": "R",
                "language": "R",
                "name": "ir"
            },
            "language_info": {
                "name": "R"
            }
        }
    return {
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3"
        },
        "language_info": {
            "name": "python",
            "version": "3.10.0"
        }
    }


def _reconstruct_notebook_from_cells(file_content, filename, kernel=None):
    """
    Reconstruct a Jupyter notebook from LLM-friendly cell markers.

    Args:
        file_content (str): The text content with # Cell N markers
        filename (str): The filename (for logging)
        kernel (str, optional): Explicit Jupyter kernel name to use instead
            of auto-detection (e.g. ``r_env``, ``pyspark-lhn-dev``).

    Returns:
        dict: A notebook dictionary ready for JSON serialization
    """
    notebook = {
        "cells": [],
        "metadata": _detect_notebook_kernel(file_content, kernel=kernel),
        "nbformat": 4,
        "nbformat_minor": 5
    }

    # If content is already JSON, just parse it
    if file_content.strip().startswith("{"):
        try:
            notebook = json.loads(file_content)
            logger.info(f"Restored JSON notebook: {filename}")
            return notebook
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {filename}: {e}")
            return None

    # Parse the text format with both code and markdown cells
    cells = []
    content_lines = file_content.splitlines()
    i = 0

    while i < len(content_lines):
        line = content_lines[i]

        # Check for markdown cell
        if line.startswith("# Markdown Cell "):
            # Look for triple quotes on next line
            i += 1
            if i < len(content_lines) and content_lines[i].strip() == '"""':
                # Start collecting markdown content
                i += 1
                markdown_content = []
                while i < len(content_lines):
                    if content_lines[i].strip() == '"""':
                        # End of markdown
                        break
                    markdown_content.append(content_lines[i] + '\n')
                    i += 1

                # Create markdown cell
                cells.append({
                    "cell_type": "markdown",
                    "metadata": {},
                    "source": markdown_content if markdown_content else []
                })
            i += 1

        # Check for raw cell (e.g., Quarto YAML headers)
        elif line.startswith("# Raw Cell "):
            # Look for triple quotes on next line
            i += 1
            if i < len(content_lines) and content_lines[i].strip() == '"""':
                # Start collecting raw content
                i += 1
                raw_content = []
                while i < len(content_lines):
                    if content_lines[i].strip() == '"""':
                        # End of raw cell
                        break
                    raw_content.append(content_lines[i] + '\n')
                    i += 1

                # Create raw cell
                cells.append({
                    "cell_type": "raw",
                    "metadata": {},
                    "source": raw_content if raw_content else []
                })
            i += 1

        # Check for code cell
        elif line.startswith("# Cell "):
            # Collect code until next cell marker or end
            i += 1
            code_content = []
            while i < len(content_lines):
                if i >= len(content_lines):
                    break
                next_line = content_lines[i]
                # Check if we've hit the next cell marker
                if next_line.startswith("# Cell ") or next_line.startswith("# Markdown Cell ") or next_line.startswith("# Raw Cell "):
                    break
                code_content.append(content_lines[i] + '\n')
                i += 1

            # Remove trailing empty lines but keep internal blank lines
            while code_content and not code_content[-1].strip():
                code_content.pop()

            # Only add cell if it has content
            if any(line.strip() for line in code_content):
                cells.append({
                    "cell_type": "code",
                    "execution_count": None,
                    "metadata": {},
                    "outputs": [],
                    "source": code_content
                })
        else:
            i += 1

    notebook["cells"] = cells

    # Count cell types for logging
    code_cells = len([c for c in cells if c['cell_type'] == 'code'])
    markdown_cells = len([c for c in cells if c['cell_type'] == 'markdown'])
    raw_cells = len([c for c in cells if c['cell_type'] == 'raw'])
    logger.info(f"Reconstructed {code_cells} code cells, {markdown_cells} markdown cells, and {raw_cells} raw cells for {filename}")

    return notebook


def unpack_llm_archive(output_directory, combined_file_path, replace_existing=False, kernel=None):
    """
    Unpack files from an LLM-friendly format archive.

    Automatically detects .ipynb files and reconstructs them as proper JSON notebooks
    from the # Cell N markers. All other files are extracted as plain text.

    Args:
        output_directory (Path): Directory to output the unpacked files.
        combined_file_path (Path): Path to the LLM-friendly archive file.
        replace_existing (bool): Whether to replace existing files.
        kernel (str, optional): Explicit Jupyter kernel name for notebooks
            (e.g. ``r_env``, ``pyspark-lhn-dev``).  Overrides auto-detection.
    """
    if isinstance(combined_file_path, str):
        combined_file_path = Path(combined_file_path)
    if isinstance(output_directory, str):
        output_directory = Path(output_directory)

    with combined_file_path.open("r", encoding="utf-8") as file:
        content = file.read()

    sections = list(iter_llm_sections(content))

    if not sections:
        logger.warning("No files found in LLM-friendly archive format")
        return

    # Create output directory if needed
    if not output_directory.exists():
        try:
            output_directory.mkdir(parents=True)
            logger.info(f"Created directory: {output_directory}")
        except Exception as e:
            logger.error(f"Error creating directory: {e}")
            return

    # Process each file section. The name on the FILE line is the archive-relative
    # path (the alias). path: metadata is the git checkout path and is not used
    # as the unpack destination, so a subdirectory archive still restores flat.
    for filename, file_content, _meta in sections:
        file_path = safe_child(output_directory, filename)
        if file_path is None:
            logger.error(f"Path traversal blocked: {filename}")
            continue

        # Check if file exists and handle accordingly
        if file_path.exists() and not replace_existing:
            logger.info(f"Skipped existing file: {file_path}")
            continue

        # Create parent directories if needed
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Handle .ipynb files specially - reconstruct as JSON notebook
        if filename.endswith('.ipynb'):
            notebook = _reconstruct_notebook_from_cells(file_content, filename, kernel=kernel)
            if notebook is None:
                continue
            try:
                with file_path.open("w", encoding="utf-8") as f:
                    json.dump(notebook, f, indent=2)
                logger.info(f"Unpacked notebook: {file_path}")
            except Exception as e:
                logger.error(f"Error writing notebook {file_path}: {e}")
        # Handle Databricks notebooks (.py files with MAGIC commands or cell markers)
        elif filename.endswith('.py') and _is_databricks_content(file_content):
            databricks_content = _reconstruct_databricks_notebook(file_content, filename)
            try:
                with file_path.open("w", encoding="utf-8") as f:
                    f.write(databricks_content)
                logger.info(f"Unpacked Databricks notebook: {file_path}")
            except Exception as e:
                logger.error(f"Error writing Databricks notebook {file_path}: {e}")
        else:
            # Write other files as plain text
            try:
                with file_path.open("w", encoding="utf-8") as f:
                    f.write(file_content)
                logger.info(f"Unpacked file: {file_path}")
            except Exception as e:
                logger.error(f"Error writing file {file_path}: {e}")

    logger.info(f"Files unpacked into: {output_directory}")


def auto_detect_archive_format(archive_path):
    """
    Detect whether archive is standard or LLM-friendly format.
    
    Returns:
        str: 'standard' or 'llm-friendly'
    """
    with open(archive_path, 'r', encoding='utf-8') as f:
        # The source manifest can push the first file delimiter past a short
        # prefix. The format banner is always near the top; also scan a wider
        # window so a delimiter-only (pre-banner) archive is still recognized.
        content = f.read(65536)

    if (
        "# LLM-FRIENDLY CODE ARCHIVE" in content
        or "################################################################################\n# FILE " in content
    ):
        return 'llm-friendly'
    elif '# Standard Archive Format' in content or '---\nFilename: ' in content:
        return 'standard'
    else:
        # Default to standard for backward compatibility
        return 'standard'


def _is_knowledge_file(path):
    """True when the file begins with a flattened-knowledge source header."""
    try:
        with Path(path).open("r", encoding="utf-8", errors="replace") as handle:
            first = handle.readline(4096)
    except OSError:
        return False
    return first.startswith("# source:")


def _is_knowledge_directory(path):
    path = Path(path)
    if not path.is_dir():
        return False
    for child in path.iterdir():
        if child.is_file() and child.name != "MANIFEST.txt" and _is_knowledge_file(child):
            return True
    return False


def unpack_knowledge_pack(output_directory, knowledge_path, replace_existing=False):
    """Restore numbered knowledge files using each file's ``# source:`` path.

    ``knowledge_path`` may be one knowledge file or a directory of them.
    ``MANIFEST.txt`` and files without a source header are skipped. The source
    path is the checkout path recorded at pack time (git-root-relative when the
    archive came from a work tree).
    """
    knowledge_path = Path(knowledge_path)
    output_directory = Path(output_directory)
    output_directory.mkdir(parents=True, exist_ok=True)

    if knowledge_path.is_file():
        files = [knowledge_path]
    else:
        files = sorted(p for p in knowledge_path.iterdir() if p.is_file())

    for file_path in files:
        if file_path.name == "MANIFEST.txt":
            continue
        try:
            text = file_path.read_text(encoding="utf-8")
        except OSError as exc:
            logger.error(f"Error reading knowledge file {file_path}: {exc}")
            continue
        parsed = parse_knowledge_text(text)
        if parsed is None:
            continue
        dest = safe_child(output_directory, parsed["path"])
        if dest is None:
            logger.error(f"Path traversal blocked: {parsed['path']}")
            continue
        if dest.exists() and not replace_existing:
            logger.info(f"Skipped existing file: {dest}")
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(parsed["content"], encoding="utf-8")
        logger.info(f"Unpacked knowledge file: {dest}")
    logger.info(f"Knowledge files unpacked into: {output_directory}")


def unpack_files_auto(output_directory, combined_file_path, replace_existing=False, kernel=None, force=False):
    """
    Auto-detect format and unpack accordingly.

    By default, raises an error if the archive is in LLM-friendly format,
    because LLM-friendly archives are lossy (no metadata, cell outputs stripped)
    and cannot reconstruct the original files faithfully.

    Use ``force=True`` or ``--force`` on the CLI to override and attempt
    extraction anyway via ``unpack_llm_archive``.
    """
    archive_path = Path(combined_file_path)
    if archive_path.is_dir() and _is_knowledge_directory(archive_path):
        logger.info("Detected numbered knowledge pack")
        return unpack_knowledge_pack(output_directory, archive_path, replace_existing)
    if archive_path.is_file() and _is_knowledge_file(archive_path):
        logger.info("Detected numbered knowledge file")
        return unpack_knowledge_pack(output_directory, archive_path, replace_existing)
    if archive_path.is_dir():
        # Split parts each carry the manifest. Join them, then unpack the text.
        joined = _read_archive_content(archive_path)
        if not joined:
            raise SystemExit(f"Error: no archive content in '{archive_path}'")
        import tempfile
        tmp = tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8")
        try:
            tmp.write(joined)
            tmp.close()
            return unpack_files_auto(
                output_directory, tmp.name, replace_existing, kernel=kernel, force=force,
            )
        finally:
            Path(tmp.name).unlink(missing_ok=True)

    format_type = auto_detect_archive_format(combined_file_path)

    logger.info(f"Detected archive format: {format_type}")

    if format_type == 'llm-friendly':
        if not force:
            msg = (
                f"Error: '{combined_file_path}' is in LLM-friendly format, "
                "which is designed for AI consumption and cannot faithfully reconstruct original files.\n"
                "\n"
                "Options:\n"
                "  1. Re-archive in standard format (without --llm-friendly) for faithful reconstruction:\n"
                "       python -m txtarchive archive <dir> <output>\n"
                "       python -m txtarchive unpack <output> <restored_dir>\n"
                "\n"
                "  2. Extract notebooks from the LLM-friendly archive:\n"
                "       python -m txtarchive extract-notebooks <archive> <output_dir>\n"
                "\n"
                "  3. Force unpack anyway (best-effort, lossy):\n"
                "       python -m txtarchive unpack <archive> <output_dir> --force\n"
            )
            logger.error(msg)
            raise SystemExit(msg)
        logger.warning("Force-unpacking LLM-friendly archive (results may be lossy)")
        return unpack_llm_archive(output_directory, combined_file_path, replace_existing, kernel=kernel)
    else:
        return unpack_files(output_directory, combined_file_path, replace_existing)





def combine_all_archives(
    parent_directory,
    combined_archive_dir=None,
    combined_archive_name="all_combined_archives.txt",
    directories=None,
):
    """
    Combine all individual archive files into a single archive file.

    Args:
        parent_directory (Path): Parent directory containing the archive files.
        combined_archive_dir (Path): Directory containing the combined archive files.
        combined_archive_name (str): Name of the final combined archive file.
        directories (list): List of directories to include in the combined archive.
    """
    all_archives_content = ""
    logger.info("Combining all archives into a single file...")

    parent_directory = Path(parent_directory)
    if directories is None:
        directories = [d for d in parent_directory.iterdir() if d.is_dir()]
    else:
        directories = [Path(parent_directory) / d for d in directories]

    for item in directories:
        archive_file_name = f"{item.name}_{combined_archive_name}.txt"
        archive_file = (
            (combined_archive_dir / archive_file_name)
            if combined_archive_dir
            else (parent_directory / archive_file_name)
        )
        logger.info("Combining archive file: %s", archive_file)

        if archive_file.is_file():
            with archive_file.open("r") as file:
                content = file.read()
                all_archives_content += (
                    f"---\nDirectory: {item.name}\n---\n{content}\n\n"
                )

    combined_archive_path = (
        (combined_archive_dir / combined_archive_name)
        if combined_archive_dir
        else (parent_directory / combined_archive_name)
    )
    with combined_archive_path.open("w") as file:
        file.write(all_archives_content)
    logger.info("All archives combined into: %s", combined_archive_path)

def unpack_all_archives(
    parent_directory, combined_archive_name="all_combined_archives.txt", overwrite=True
):
    """
    Unpack all archives from a combined archive file.

    Args:
        parent_directory (Path): Parent directory containing the combined archive file.
        combined_archive_name (str): Name of the combined archive file.
        overwrite (bool): Whether to overwrite existing files.
    """
    parent_directory = Path(parent_directory)
    combined_archive_path = parent_directory / combined_archive_name

    with combined_archive_path.open("r") as file:
        combined_content = file.read()

    directory_sections = combined_content.split("---\nDirectory: ")[1:]

    for section in directory_sections:
        directory_name, content = section.split("\n---\n", 1)
        directory_path = parent_directory / directory_name.strip()
        directory_path.mkdir(parents=True, exist_ok=True)

        archive_file_path = directory_path / "combined_files.txt"
        if archive_file_path.exists() and not overwrite:
            archive_file_path = directory_path / "combined_files_copy.txt"

        with archive_file_path.open("w") as file:
            file.write(content)

        unpack_files(archive_file_path, directory_path)
        logger.info("Unpacked archive in: %s", directory_path)

def _read_file_content(file_path, extract_code_only=False):
    """Read a file and return its content string, handling notebooks and HTML specially.

    Args:
        file_path (Path): Path to the file to read.
        extract_code_only (bool): For notebooks, extract cell markers instead of raw JSON.

    Returns:
        str or None: The file content, or None on error.
    """
    if file_path.suffix == ".ipynb":
        try:
            notebook_content = read_notebook(file_path)
            if not notebook_content:
                return None
            if extract_code_only:
                content = ""
                for cell_idx, cell in enumerate(notebook_content.get("cells", []), 1):
                    cell_source = "".join(cell.get("source", []))
                    if not cell_source.strip():
                        continue
                    if cell["cell_type"] == "code":
                        content += f"# Cell {cell_idx}\n{cell_source}\n\n"
                    elif cell["cell_type"] == "markdown":
                        content += f"# Markdown Cell {cell_idx}\n"
                        content += '"""\n'
                        content += cell_source
                        if not cell_source.endswith('\n'):
                            content += '\n'
                        content += '"""\n\n'
                    elif cell["cell_type"] == "raw":
                        content += f"# Raw Cell {cell_idx}\n"
                        content += '"""\n'
                        content += cell_source
                        if not cell_source.endswith('\n'):
                            content += '\n'
                        content += '"""\n\n'
                return content
            else:
                return json.dumps(remove_outputs_from_code_cells(notebook_content), indent=4)
        except Exception as e:
            logger.error(f"Error processing notebook {file_path}: {e}")
            return f"# Error processing notebook: {e}\n\n"
    elif file_path.suffix == ".html":
        try:
            from .html_converter import convert_html_to_markdown_text
            with file_path.open("r", encoding="utf-8", errors="replace") as f:
                html_content = f.read()
            return convert_html_to_markdown_text(html_content)
        except Exception as e:
            logger.error(f"Error converting HTML {file_path}: {e}")
            return f"# Error converting HTML: {e}\n\n"
    elif file_path.suffix.lower() in (".qmd", ".rmd"):
        try:
            with file_path.open("r", encoding="utf-8", errors="replace") as f:
                text = f.read()
        except Exception as e:
            logger.error(f"Error reading {file_path}: {e}")
            return f"# Error reading file: {e}\n\n"
        # In LLM-friendly (code-only) mode, normalize the qmd into the canonical
        # cell-marker form so it can be extracted to .ipynb OR .qmd. In standard
        # mode keep the qmd verbatim (exact reconstruction).
        if extract_code_only:
            try:
                from .quarto_cells import qmd_to_llm_cells
                return qmd_to_llm_cells(text)
            except Exception as e:
                logger.error(f"Error converting qmd to cells {file_path}: {e}")
                return text
        return text
    else:
        try:
            with file_path.open("r", encoding="utf-8", errors="replace") as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            return f"# Error reading file: {e}\n\n"


def _path_matches_include_subdirs(file_path, base_directory, include_subdirs):
    """
    Check if a file path should be included based on include_subdirs filter.

    Args:
        file_path (Path): The file path to check.
        base_directory (Path): The base directory of the archive.
        include_subdirs (set): Set of subdirectory names to include.

    Returns:
        bool: True if the file should be included.
    """
    if not include_subdirs:
        return True

    try:
        rel_path = file_path.relative_to(base_directory)
    except ValueError:
        return False

    rel_path_str = str(rel_path).replace('\\', '/')

    for subdir in include_subdirs:
        subdir_normalized = subdir.replace('\\', '/')
        if rel_path_str.startswith(subdir_normalized + '/') or \
           str(rel_path.parent).replace('\\', '/') == subdir_normalized:
            logger.debug(f"File {rel_path} matches include_subdir: {subdir}")
            return True

    return False


def archive_files(
    directory,
    output_file_path,
    file_types=[".yaml", ".py", ".r", ".ipynb", ".qmd"],
    include_subdirectories=True,
    extract_code_only=False,
    file_prefixes=None,
    llm_friendly=False,
    split_output=False,
    max_tokens=100000,
    split_output_dir=None,
    exclude_dirs=None,
    root_files=None,
    include_subdirs=None,
    explicit_files=None,
    dry_run=False,
    update_only=False,
    patch_instructions=None,
    line_numbers=False,
    knowledge=False,
    knowledge_dir=None,
):
    directory = Path(directory) if isinstance(directory, str) else directory
    output_file_path = Path(output_file_path) if isinstance(output_file_path, str) else output_file_path
    default_exclude_dirs = {"build", ".pytest_cache", "__pycache__", ".venv", ".git", ".ipynb_checkpoints"}
    exclude_dirs = set(exclude_dirs or []) | default_exclude_dirs
    root_files = set(root_files or [])
    include_subdirs = set(include_subdirs or [])
    processed_files = set()
    file_list = []

    logger.info(f"Archiving files from: {directory}")
    logger.info(f"Excluding directories: {exclude_dirs}")
    creation_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    git = git_context(directory)
    if git.in_git:
        logger.info(
            "Git checkout: repo %s @ %s (%s)",
            git.repo_name,
            git.commit or "none",
            git.branch or "none",
        )
    use_line_numbers = bool(line_numbers) and bool(llm_friendly)
    if line_numbers and not llm_friendly:
        logger.warning("line numbers apply to LLM-friendly archives only; ignoring")
    if patch_instructions is None:
        use_patch_instructions = bool(llm_friendly)
    else:
        use_patch_instructions = bool(patch_instructions) and bool(llm_friendly)

    def _push(rel_path, content, file_path):
        alias = archive_alias(rel_path)
        file_list.append(ArchiveEntry(
            alias=alias,
            source=repo_relative_posix(file_path, directory, git),
            content=content,
        ))
        processed_files.add(alias)

    if not directory.is_dir():
        logger.error(f"Input directory does not exist: {directory}")
        raise FileNotFoundError(f"Input directory does not exist: {directory}")

    output_file_path.parent.mkdir(parents=True, exist_ok=True)
    logger.info(f"Ensured output directory exists: {output_file_path.parent}")

    # Handle explicit file list mode
    if explicit_files is not None:
        logger.info(f"Using explicit file list mode with {len(explicit_files)} files")
        
        for file_name in explicit_files:
            file_path = Path(file_name)
            if not file_path.is_absolute():
                file_path = directory / file_name
            
            if not file_path.exists():
                logger.error(f"Explicit file not found: {file_path}")
                continue
            
            if not file_path.is_file():
                logger.warning(f"Skipping non-file path: {file_path}")
                continue
            
            try:
                rel_path = file_path.relative_to(directory)
            except ValueError:
                rel_path = Path(file_path.name)
                logger.warning(f"File {file_path} is outside source directory, using filename only: {rel_path}")
            
            logger.info(f"Processing explicit file: {file_path}")
            content = _read_file_content(file_path, extract_code_only=extract_code_only)

            if content is not None:
                _push(rel_path, content, file_path)

        logger.info(f"Processed {len(file_list)} explicit files")

    else:
        # Standard directory scanning mode (when explicit_files is None)
        # Process root files first
        for file_name in root_files:
            path = directory / file_name
            if not path.is_file():
                logger.warning(f"Root file not found: {path}")
                continue
            if path.name.startswith((".", "#")) and path.name != ".gitignore":
                logger.info(f"Skipping hidden root file: {path}")
                continue
            logger.info(f"Processing root file: {path}")
            rel_path = path.relative_to(directory)
            try:
                with path.open("r", encoding="utf-8", errors="replace") as file:
                    content = file.read()
                _push(rel_path, content, path)
            except Exception as e:
                logger.error(f"Error reading root file {path}: {e}")
                content = f"# Error reading file: {e}\n\n"
                _push(rel_path, content, path)

        # Get file iterator
        file_iterator = directory.rglob("*") if include_subdirectories else directory.glob("*")

        for path in file_iterator:
            if include_subdirectories:
                path_parts = path.relative_to(directory).parts
                if any(part in exclude_dirs for part in path_parts):
                    continue
        
            rel_path = path.relative_to(directory)
        
            if include_subdirs and not _path_matches_include_subdirs(path, directory, include_subdirs):
                if path.parent != directory:
                    continue
        
            is_root_file = rel_path.parent == Path(".")
        
            if path.is_file():
                is_gitignore = path.name == ".gitignore"
                if not (is_gitignore or (not path.name.startswith((".", "#")) and path.suffix in file_types)):
                    continue
                if is_root_file and path.name in root_files:
                    logger.info(f"Skipping already processed root file: {path}")
                    continue
                if archive_alias(rel_path) in processed_files:
                    logger.info(f"Skipping already processed file: {path}")
                    continue
                if file_prefixes and not is_gitignore and not any(path.name.startswith(prefix) for prefix in file_prefixes):
                    continue
                
                logger.info(f"Processing file: {path}")
                content = _read_file_content(path, extract_code_only=extract_code_only)

                if content is not None:
                    _push(rel_path, content, path)

    # Rest of the function continues here (sorting, TOC, output)...
    file_list.sort(key=lambda entry: entry.alias)
    file_list = number_entries(file_list)

    if dry_run:
        total_chars = sum(len(entry.content) for entry in file_list)
        estimated_tokens = total_chars // 4  # rough estimate: ~4 chars per token
        format_name = "LLM-friendly" if llm_friendly else "Standard"
        issues = []

        # Check for missing root files
        for rf in (root_files or set()):
            rf_path = directory / rf
            if not rf_path.is_file():
                issues.append(f"Root file not found: {rf}")

        if not file_list:
            issues.append("No files matched the given filters")

        print(f"\n{'='*60}")
        print(f"DRY RUN — Archive Preview")
        print(f"{'='*60}")
        print(f"Source directory:  {directory}")
        print(f"Output file:      {output_file_path}")
        print(f"Format:           {format_name}")
        print(f"Repo:             {git.repo_name} @ {git.commit or 'none'} ({git.branch or 'none'})")
        print(f"Files to archive: {len(file_list)}")
        print(f"Estimated chars:  {total_chars:,}")
        print(f"Estimated tokens: {estimated_tokens:,}")
        if split_output:
            print(f"Split output:     yes (max {max_tokens:,} tokens/file)")
        print(f"\nFiles that would be included:")
        for idx, entry in enumerate(file_list, 1):
            size_kb = len(entry.content) / 1024
            print(f"  {idx:3d}. {entry.alias} -> {entry.source} ({size_kb:.1f} KB)")

        if issues:
            print(f"\nIssues:")
            for issue in issues:
                print(f"  - {issue}")

        print(f"{'='*60}")
        print("No files were written.")
        return None

    all_contents = render_archive(
        file_list,
        llm_friendly=llm_friendly,
        git=git,
        created=creation_date,
        include_patch_instructions=use_patch_instructions,
        line_numbers=use_line_numbers,
    )

    if update_only:
        from .split_files import _write_if_changed
        if _write_if_changed(output_file_path, all_contents):
            logger.info(f"Archive updated at: {output_file_path}")
        else:
            logger.info(f"Archive unchanged: {output_file_path} — kept existing file")
    else:
        with output_file_path.open("w", encoding="utf-8") as file:
            file.write(all_contents)
        logger.info(f"Archive created at: {output_file_path}")

    if split_output:
        from .split_files import split_file
        split_dir = Path(split_output_dir) if split_output_dir else output_file_path.parent / f"split_{output_file_path.stem}"
        split_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Ensured split output directory exists: {split_dir}")
        split_file(output_file_path, max_tokens=max_tokens, output_dir=split_dir,
                   update_only=update_only)
        logger.info(f"Split files created in: {split_dir}")

    if knowledge or knowledge_dir:
        dest = Path(knowledge_dir) if knowledge_dir else (
            output_file_path.parent / f"{output_file_path.stem}_knowledge"
        )
        _write_knowledge_pack(file_list, dest, git, update_only=update_only)
        logger.info(f"Knowledge files written in: {dest}")

    return output_file_path


def _write_knowledge_pack(entries, dest, git, update_only=False):
    """Write flattened numbered knowledge files plus MANIFEST.txt.

    Each file starts with ``# source: <repo-relative path> (repo <name> @ <sha>)``.
    Stale numbered files from a previous pack of this directory are removed so a
    re-run cannot leave a Copilot upload pointing at a deleted source.
    """
    from .split_files import _write_if_changed

    dest = Path(dest)
    dest.mkdir(parents=True, exist_ok=True)
    expected = {"MANIFEST.txt"}
    manifest = format_knowledge_manifest(entries, git)

    def _emit(path, text):
        if update_only:
            _write_if_changed(path, text)
        else:
            path.write_text(text, encoding="utf-8")

    _emit(dest / "MANIFEST.txt", manifest)
    for entry in entries:
        _emit(dest / entry.numbered, knowledge_file_text(entry, git))
        expected.add(entry.numbered)

    for child in dest.iterdir():
        if not child.is_file() or child.name in expected:
            continue
        if child.name == "MANIFEST.txt" or re.match(r"^\d+-.*\.txt$", child.name):
            child.unlink()
            logger.info(f"Removed stale knowledge file: {child}")


def _split_part_sort_key(path):
    """Sort ``name_part2`` before ``name_part10`` (numeric, not lexicographic)."""
    match = re.search(r"_part(\d+)$", Path(path).stem)
    if match:
        return (0, int(match.group(1)), Path(path).name)
    return (1, 0, Path(path).name)


def _split_part_for_join(split_content, keep_header):
    """Clean one split chunk for reassembly into a single archive string.

    ``# Part N`` lines are dropped (they are navigation, not file content).
    Chunks after the first repeat the source manifest; only their file sections
    are kept so the repeated header does not become part of the previous file.
    """
    cleaned_lines = [
        line for line in split_content.splitlines()
        if line.strip() not in ["<DOCUMENT>", "</DOCUMENT>"]
        and not line.startswith("# Part ")
    ]
    text = "\n".join(cleaned_lines)
    if text and not text.endswith("\n"):
        text += "\n"
    if keep_header:
        return text
    llm_at = text.find("################################################################################\n# FILE ")
    std_at = text.find("---\nFilename: ")
    starts = [pos for pos in (llm_at, std_at) if pos != -1]
    if not starts:
        return ""
    return text[min(starts):]


def _read_archive_content(archive_file_path):
    """
    Read archive content from a single file or directory of split files.

    Handles split-file cleanup (removing <DOCUMENT> wrappers and # Part lines).

    Args:
        archive_file_path (Path): Path to archive file or directory of split files.

    Returns:
        str or None: The archive content, or None on error.
    """
    archive_file_path = Path(archive_file_path)
    content = ""

    if archive_file_path.is_dir():
        logger.info(f"Processing split files in directory: {archive_file_path}")
        split_files = sorted(archive_file_path.glob("*.txt"), key=_split_part_sort_key)
        if not split_files:
            logger.error(f"No split files found in {archive_file_path}")
            return None
        for index, split_file in enumerate(split_files):
            logger.info(f"Reading split file: {split_file}")
            try:
                with split_file.open("r", encoding="utf-8") as file:
                    split_content = file.read()
                # Later parts repeat the manifest so each upload stands alone.
                # When rejoining, keep that preamble only from the first part so
                # it is not swallowed into the previous file's body.
                content += _split_part_for_join(split_content, keep_header=(index == 0))
            except Exception as e:
                logger.error(f"Error reading split file {split_file}: {e}")
                continue
    else:
        logger.info(f"Processing single archive: {archive_file_path}")
        try:
            with archive_file_path.open("r", encoding="utf-8") as file:
                content = file.read()
        except Exception as e:
            logger.error(f"Error reading archive {archive_file_path}: {e}")
            return None

    if "TABLE OF CONTENTS" not in content:
        logger.error("Archive missing TABLE OF CONTENTS; may be incomplete")
        return None

    return content


def _parse_archive_sections(content):
    """
    Parse archive content and yield (filename, file_content, is_llm_friendly) tuples.

    Auto-detects LLM-friendly vs standard format.

    Args:
        content (str): The full archive content.

    Yields:
        tuple: (filename, file_content, is_llm_friendly) for each file section.
    """
    # Try LLM-friendly format first. Path metadata lines stay out of the body,
    # and line-number prefixes are stripped when the section declares them.
    llm_sections = list(iter_llm_sections(content))
    if llm_sections:
        for filename, file_content, _meta in llm_sections:
            yield filename, file_content, True
    else:
        for filename, file_content, _meta in iter_standard_sections(content):
            yield filename, file_content, False


def extract_notebooks_to_ipynb(archive_file_path, output_directory, replace_existing=False, kernel=None):
    """
    Extract Jupyter notebooks from an LLM-friendly text archive into .ipynb files.
    Now handles both code cells and markdown cells.

    Args:
        archive_file_path (Path): Path to the LLM-friendly archive file or directory of split files.
        output_directory (Path): Directory to save the reconstructed .ipynb files.
        replace_existing (bool): Whether to overwrite existing files (default: False).
        kernel (str, optional): Explicit Jupyter kernel name. Overrides auto-detection.
    """
    output_directory = Path(output_directory)
    logger.info(f"Extracting notebooks to {output_directory}")

    content = _read_archive_content(archive_file_path)
    if content is None:
        return

    output_directory.mkdir(parents=True, exist_ok=True)

    from .quarto_cells import has_cell_markers

    for filename, file_content, is_llm_friendly in _parse_archive_sections(content):
        # Accept .ipynb directly, and also coerce a cell-form .qmd/.Rmd to .ipynb
        # ("extract to anything" from the canonical cell form).
        is_nb = filename.endswith(".ipynb")
        is_quarto_cells = (
            filename.lower().endswith((".qmd", ".rmd"))
            and has_cell_markers(file_content)
        )
        if not (is_nb or is_quarto_cells):
            logger.debug(f"Skipping non-notebook file: {filename}")
            continue

        out_name = filename if is_nb else str(Path(filename).with_suffix(".ipynb"))
        output_path = output_directory / out_name
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if output_path.exists() and not replace_existing:
            output_path = output_path.with_stem(f"{output_path.stem}_copy")
            logger.info(f"File exists, using {output_path.name}")

        notebook = _reconstruct_notebook_from_cells(file_content, out_name, kernel=kernel)
        if notebook is None:
            continue

        try:
            with output_path.open("w", encoding="utf-8") as file:
                json.dump(notebook, file, indent=2)
            logger.info(f"Created notebook: {output_path}")
        except Exception as e:
            logger.error(f"Error writing {output_path}: {e}")

def run_extract_notebooks(archive_file_path, output_directory, replace_existing=False, kernel=None):
    """
    Wrapper for extract_notebooks_to_ipynb.
    """
    extract_notebooks_to_ipynb(archive_file_path, output_directory, replace_existing, kernel=kernel)
    logger.info(f"Notebooks extracted to: {output_directory}")

def extract_notebooks_and_quarto(archive_file_path, output_directory, replace_existing=False, kernel=None):
    """
    Extract Jupyter notebooks and Quarto files from an LLM-friendly or standard text archive.

    Args:
        archive_file_path (Path): Path to the archive file or directory of split files.
        output_directory (Path): Directory to save the reconstructed .ipynb and .qmd files.
        replace_existing (bool): Whether to overwrite existing files (default: False).
        kernel (str, optional): Explicit Jupyter kernel name. Overrides auto-detection.
    """
    output_directory = Path(output_directory)
    logger.info(f"Extracting notebooks and Quarto files to {output_directory}")

    content = _read_archive_content(archive_file_path)
    if content is None:
        return

    output_directory.mkdir(parents=True, exist_ok=True)

    for filename, file_content, is_llm_friendly in _parse_archive_sections(content):
        if not (filename.endswith(".ipynb") or filename.endswith(".qmd")):
            logger.debug(f"Skipping unsupported file: {filename}")
            continue

        output_path = output_directory / filename
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if output_path.exists() and not replace_existing:
            output_path = output_path.with_stem(f"{output_path.stem}_copy")
            logger.info(f"File exists, using {output_path.name}")

        if filename.endswith(".ipynb"):
            if is_llm_friendly:
                notebook = _reconstruct_notebook_from_cells(file_content, filename, kernel=kernel)
                if notebook is None:
                    continue
            else:
                try:
                    notebook = json.loads(file_content)
                    logger.info(f"Restored JSON notebook: {filename}")
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON in {filename}: {e}")
                    continue

            try:
                with output_path.open("w", encoding="utf-8") as file:
                    json.dump(notebook, file, indent=2)
                logger.info(f"Created notebook: {output_path}")
            except Exception as e:
                logger.error(f"Error writing {output_path}: {e}")
        else:  # .qmd / .Rmd
            from .quarto_cells import llm_cells_to_qmd, has_cell_markers
            if is_llm_friendly and has_cell_markers(file_content):
                # Canonical cell form -> reconstruct a .qmd (target chosen here).
                kmeta = _detect_notebook_kernel(file_content, kernel=kernel)
                ks = kmeta.get("kernelspec", {})
                lang = "r" if (ks.get("language", "").lower() == "r"
                               or ks.get("name", "").lower() in ("ir", "r_env")) else "python"
                out_text = llm_cells_to_qmd(file_content, default_lang=lang)
            else:
                out_text = file_content  # back-compat: verbatim qmd blob
            try:
                with output_path.open("w", encoding="utf-8") as file:
                    file.write(out_text)
                logger.info(f"Created Quarto file: {output_path}")
            except Exception as e:
                logger.error(f"Error writing {output_path}: {e}")

def run_extract_notebooks_and_quarto(archive_file_path, output_directory, replace_existing=False, kernel=None):
    """
    Wrapper for extract_notebooks_and_quarto.
    """
    extract_notebooks_and_quarto(archive_file_path, output_directory, replace_existing, kernel=kernel)
    logger.info(f"Notebooks and Quarto files extracted to: {output_directory}")

def validate_archive(archive_file_path):
    with Path(archive_file_path).open("r", encoding="utf-8") as file:
        content = file.read()
    if "TABLE OF CONTENTS" not in content:
        logger.error("Archive missing TABLE OF CONTENTS")
        return False
    if not content.split("################################################################################\n# FILE ")[1:]:
        logger.error("No notebook sections found")
        return False
    return True

def generate_archive(study_plan_path, lhn_archive_path, output_archive_path, llm_model="mock"):
    """
    Generate a txtarchive archive using an LLM.
    """
    with Path(study_plan_path).open("r", encoding="utf-8") as f:
        study_plan = f.read()
    
    lhn_content = ""
    lhn_path = Path(lhn_archive_path)
    if lhn_path.is_dir():
        for index, split_file in enumerate(sorted(lhn_path.glob("*.txt"), key=_split_part_sort_key)):
            with split_file.open("r", encoding="utf-8") as f:
                lhn_content += _split_part_for_join(f.read(), keep_header=(index == 0))
    else:
        with lhn_path.open("r", encoding="utf-8") as f:
            lhn_content = f.read()
    
    prompt = (
        "You are a code generation assistant. The lhn module is a Python library for "
        "healthcare analytics, with functions for data loading, analysis, and visualization.\n\n"
        f"**Study Plan**: {study_plan}\n\n"
        f"**lhn Module Archive**:\n{lhn_content}\n\n"
        "Generate a txtarchive-compatible archive with Jupyter notebooks implementing the "
        "study plan using lhn functions. Use this format:\n\n"
        "# LLM-FRIENDLY CODE ARCHIVE\n"
        "# Generated from: study\n"
        f"# Date: {datetime.now().strftime('%Y-%m-%d')}\n"
        "# TABLE OF CONTENTS\n"
        "1. data_cleaning.ipynb\n"
        "2. analysis.ipynb\n"
        "\n"
        "################################################################################\n"
        "# FILE 1: data_cleaning.ipynb\n"
        "################################################################################\n"
        "# Cell 1\n"
        "<code>\n"
        "# Cell 2\n"
        "<code>\n"
        "\n"
        "################################################################################\n"
        "# FILE 2: analysis.ipynb\n"
        "################################################################################\n"
        "# Cell 1\n"
        "<code>\n"
        "\n"
        "Output only the archive text."
    )
    
    archive_content = mock_llm_call(prompt) if llm_model == "mock" else call_llm(prompt, llm_model)
    
    with Path(output_archive_path).open("w", encoding="utf-8") as f:
        f.write(archive_content)
    logger.info(f"Generated archive: {output_archive_path}")

def mock_llm_call(prompt):
    """
    Mock LLM response for testing.
    """
    return (
        "# LLM-FRIENDLY CODE ARCHIVE\n"
        "# Generated from: study\n"
        "# Date: 2025-04-15\n"
        "# TABLE OF CONTENTS\n"
        "1. data_cleaning.ipynb\n"
        "2. analysis.ipynb\n"
        "\n"
        "################################################################################\n"
        "# FILE 1: data_cleaning.ipynb\n"
        "################################################################################\n"
        "# Cell 1\n"
        "import lhn.preprocessing\n"
        'data = lhn.preprocessing.load_data("data.csv")\n'
        "# Cell 2\n"
        "clean_data = lhn.preprocessing.clean_data(data)\n"
        "\n"
        "################################################################################\n"
        "# FILE 2: analysis.ipynb\n"
        "################################################################################\n"
        "# Cell 1\n"
        "import lhn.analytics\n"
        "model = lhn.analytics.run_regression(clean_data)\n"
    )

def call_llm(prompt, llm_model):
    """
    Placeholder for real LLM API call.
    """
    raise NotImplementedError("Real LLM integration not implemented.")