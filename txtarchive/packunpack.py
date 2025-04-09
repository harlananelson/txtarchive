import json
from pathlib import Path
from .header import logger
from datetime import datetime, timedelta, date, time #example


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
    except json.JSONDecoderError as e:
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
        # Ensure UTF-8 encoding with error handling
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
    all_contents = ""

    for path in directory.rglob("*"):
        if (
            path.is_file()
            and not path.name.startswith((".", "#"))
            and directory in path.parents
        ):
            content = None
            # Get relative path from the base directory for unique identification
            rel_path = path.relative_to(directory)
            
            # Special handling for __init__.py files
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
                    with path.open("r", encoding="utf-8") as file:  # Explicitly use utf-8 encoding
                        content = file.read()
                        if is_init_file:
                            logger.info(f"Successfully read __init__.py, content length: {len(content)}")
                            logger.info(f"First 50 characters: {repr(content[:50])}")  # Debug: see what's in the content
                except FileNotFoundError:
                    logger.error("File not found: %s", path)
                    continue
                except Exception as e:
                    logger.error(f"Error reading file {path}: {str(e)}")
                    continue

            if content is not None:
                if is_init_file:
                    logger.info(f"Adding __init__.py content to archive, path: {rel_path}")
                
                # Use relative path in the filename identifier to make it unique
                all_contents += f"---\nFilename: {rel_path}\n---\n{content}\n\n"
            elif is_init_file:
                logger.warning(f"No content was obtained from __init__.py at {path}")

    # Add debug: Log the total size of all_contents before writing
    logger.info(f"Total content size to write: {len(all_contents)} bytes")
    
    with combined_file_path.open("w", encoding="utf-8") as file:  # Explicitly use utf-8 encoding
        file.write(all_contents)
    logger.info("Files concatenated into: %s", combined_file_path)

# ... (other imports and functions unchanged) ...

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

    sections = combined_content.split("---\nFilename: ")[1:]

    if not output_directory.exists():
        try:
            output_directory.mkdir(parents=True, exist_ok=True)
            logger.info("Created directory: %s", output_directory)
        except Exception as e:
            logger.error(f"Error creating directory {output_directory}: {e}")
            return
    else:
        logger.info("Directory already exists: %s", output_directory)

    for section in sections:
        filename, content = section.split("\n---\n", 1)
        
        # Handle relative paths in the filename
        output_path = output_directory / filename.strip()
        
        # Create parent directories if they don't exist
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        if output_path.exists() and not replace_existing:
            output_path = output_path.with_suffix(output_path.suffix + "_copy")
            
        with output_path.open("w", encoding="utf-8") as file:
            file.write(content)
            logger.info("Unpacked file: %s", output_path)
    logger.info("Files unpacked into: %s", output_directory)





def run_concat_no_subdirs(
    current_directory,
    combined_files="combined_files.txt",
    file_types=[".yaml", ".py", ".r"],
    file_prefixes=None,  # New parameter for filtering by prefix
):
    """
    Concatenate files of specified types in just the top-level directory (no subdirectories).

    Args:
        current_directory (Path): Directory to search for files.
        combined_files (Path): Path to the output file.
        file_types (list): List of file extensions to include.
        file_prefixes (list): List of prefixes to filter filenames (default is None, which includes all files).
    """
    if isinstance(current_directory, str):
        current_directory = Path(current_directory)
    if isinstance(combined_files, str):
        combined_files = Path(combined_files)

    logger.info(
        "Concatenating files in top-level directory only: %s", current_directory
    )
    all_contents = ""

    # Use glob instead of rglob to only search the top level
    for path in current_directory.glob("*"):
        # Check if the file matches the prefix filter (if any)
        if file_prefixes and not any(path.name.startswith(prefix) for prefix in file_prefixes):
            continue
            
        if path.is_file() and not path.name.startswith((".", "#")):
            content = None

            if path.suffix == ".ipynb" and ".ipynb" in file_types:
                logger.info("Archiving %s", path.name)
                content = read_notebook(path)
                if content is not None:
                    content = remove_outputs_from_code_cells(content)
                    content = json.dumps(content, indent=4)
            elif path.suffix in file_types:
                logger.info("Processing %s", path.name)
                try:
                    with path.open("r") as file:
                        content = file.read()
                except FileNotFoundError:
                    logger.error("File not found: %s", path)
                    continue

            if content is not None:
                all_contents += f"---\nFilename: {path.name}\n---\n{content}\n\n"

    with combined_files.open("w") as file:
        file.write(all_contents)
    logger.info("Files concatenated into: %s", combined_files)


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


def run_unpack(output_directory, combined_file_path, replace_existing=False):
    """
    Wrapper for the `unpack_files` function.

    Args:
        output_directory (Path): Directory to output the unpacked files.
        combined_file_path (Path): Path to the combined text file.
        replace_existing (bool): Whether to replace existing files (default: False).
    """
    if isinstance(combined_file_path, str):
        combined_file_path = Path(combined_file_path)
    if isinstance(output_directory, str):
        output_directory = Path(output_directory)

    unpack_files(output_directory, combined_file_path, replace_existing=replace_existing)
    logger.info("Files have been unpacked into: %s", output_directory)



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
        directories = [Path(parent_directory) / d for d in directories]

    if combined_archive_dir is not None:
        combined_archive_dir = Path(combined_archive_dir)
        combined_archive_dir.mkdir(parents=True, exist_ok=True)

    for item in directories:
        item_path = parent_directory / item
        if item_path.is_dir():
            archive_file_name = f"{item.name}_{combined_archive_name}.txt"
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


def create_llm_archive(directory, output_file_path, file_types=[".py", ".yaml", ".r", ".ipynb", ".sh"], file_prefixes=None, include_subdirectories=True):
    """
    Create a single text file containing all code from the specified directory,
    formatted in a way that's ideal for input to an LLM.
    
    Args:
        directory (Path): Directory to search for files.
        output_file_path (Path): Path to the output file.
        file_types (list): List of file extensions to include.
        file_prefixes (list): List of filename prefixes to include (default is None, which includes all files).
        include_subdirectories (bool): Whether to traverse subdirectories (default is True).
    """
    if isinstance(directory, str):
        directory = Path(directory)
    if isinstance(output_file_path, str):
        output_file_path = Path(output_file_path)
    
    logger.info(f"Creating LLM-friendly archive from directory: {directory}")
    all_contents = ""
    
    # Add a header with information about the archive
    all_contents += f"# LLM-FRIENDLY CODE ARCHIVE\n"
    all_contents += f"# Generated from: {directory}\n"
    all_contents += f"# Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

    # Track processed files for the table of contents
    file_list = []
    
    # First pass: collect all files to process
    if include_subdirectories:
        file_iterator = directory.rglob("*")
    else:
        file_iterator = directory.glob("*")

    for path in file_iterator:
        if (path.is_file() and 
            not path.name.startswith((".", "#")) and 
            path.suffix in file_types):
            
            # Check if the file matches the prefix filter (if any)
            if file_prefixes and not any(path.name.startswith(prefix) for prefix in file_prefixes):
                continue
                
            rel_path = path.relative_to(directory)
            file_list.append((rel_path, path))
    
    # Sort files by relative path for better organization
    file_list.sort(key=lambda x: str(x[0]))
    
    # Generate table of contents
    all_contents += "# TABLE OF CONTENTS\n"
    for idx, (rel_path, _) in enumerate(file_list, 1):
        all_contents += f"{idx}. {rel_path}\n"
    all_contents += "\n\n"
    
    # Second pass: process and add file contents
    for idx, (rel_path, path) in enumerate(file_list, 1):
        logger.info(f"Processing {path.name}")
        
        # Add a clear section header for each file
        all_contents += f"{'#' * 80}\n"
        all_contents += f"# FILE {idx}: {rel_path}\n"
        all_contents += f"{'#' * 80}\n\n"
        
        content = None
        
        if path.suffix == ".ipynb":
            # For Jupyter notebooks, extract only the code cells without outputs
            try:
                with path.open("r", encoding="utf-8", errors="replace") as file:
                    notebook = json.load(file)
                
                # Extract code from each cell
                for cell_idx, cell in enumerate(notebook.get("cells", []), 1):
                    if cell["cell_type"] == "code":
                        cell_content = "".join(cell.get("source", []))
                        if cell_content.strip():  # Only include non-empty cells
                            all_contents += f"# Cell {cell_idx}\n"
                            all_contents += cell_content
                            all_contents += "\n\n"
            except Exception as e:
                logger.error(f"Error processing notebook {path}: {e}")
                all_contents += f"# Error processing notebook: {e}\n\n"
        else:
            # For regular code files, include the entire content
            try:
                with path.open("r", encoding="utf-8", errors="replace") as file:
                    content = file.read()
                    all_contents += content
                    all_contents += "\n\n"
            except Exception as e:
                logger.error(f"Error reading {path}: {e}")
                all_contents += f"# Error reading file: {e}\n\n"
    
    # Write the combined content to the output file
    with output_file_path.open("w", encoding="utf-8") as file:
        file.write(all_contents)
    
    logger.info(f"LLM-friendly archive created at: {output_file_path}")
    return output_file_path


import json
from pathlib import Path
from .header import logger
from datetime import datetime
import os

def archive_files(
    directory,
    output_file_path,
    file_types=[".yaml", ".py", ".r"],
    include_subdirectories=True,
    extract_code_only=False,
    file_prefixes=None,
    llm_friendly=False,
):
    """
    Archives files from a directory with various options.

    Args:
        directory (Path): Directory to search for files.
        output_file_path (Path): Path to the output file.
        file_types (list): List of file extensions to include.
        include_subdirectories (bool): Whether to traverse subdirectories.
        extract_code_only (bool): Extract only code cells from Jupyter notebooks.
        file_prefixes (list): List of filename prefixes to include.
        llm_friendly (bool): Format output for LLM consumption.
    """

    directory = Path(directory) if isinstance(directory, str) else directory
    output_file_path = Path(output_file_path) if isinstance(output_file_path, str) else output_file_path

    logger.info(f"Archiving files from: {directory}")
    all_contents = ""

    # Add creation date at the top
    creation_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    all_contents += f"# Archive created on: {creation_date}\n\n"

    if llm_friendly:
        all_contents += "# LLM-FRIENDLY CODE ARCHIVE\n"
        all_contents += f"# Generated from: {directory}\n"
        all_contents += f"# Date: {creation_date}\n\n"  # Replace the existing date line
        file_list = []  # For table of contents
    else:
        all_contents += "# Standard Archive Format\n\n"  # Optional: distinguish from LLM-friendly

    # Determine file iteration method
    file_iterator = directory.rglob("*") if include_subdirectories else directory.glob("*")

    for path in file_iterator:
        if path.is_file() and not path.name.startswith((".", "#")) and path.suffix in file_types:
            if file_prefixes and not any(path.name.startswith(prefix) for prefix in file_prefixes):
                continue

            rel_path = path.relative_to(directory)

            content = None
            if path.suffix == ".ipynb":
                try:
                    notebook_content = read_notebook(path)
                    if notebook_content:
                        if extract_code_only:
                            content = ""
                            for cell_idx, cell in enumerate(notebook_content.get("cells", []), 1):
                                if cell["cell_type"] == "code" and cell.get("source"):
                                    cell_content = "".join(cell.get("source", []))
                                    if cell_content.strip():
                                        content += f"# Cell {cell_idx}\n{cell_content}\n\n"
                        else:
                            content = json.dumps(remove_outputs_from_code_cells(notebook_content), indent=4)
                except Exception as e:
                    logger.error(f"Error processing notebook {path}: {e}")
                    content = f"# Error processing notebook: {e}\n\n"
            else:
                try:
                    with path.open("r", encoding="utf-8", errors="replace") as file:
                        content = file.read()
                except Exception as e:
                    logger.error(f"Error reading file {path}: {e}")
                    content = f"# Error reading file: {e}\n\n"

            if content is not None:
                if llm_friendly:
                    file_list.append((rel_path, path))
                else:
                    all_contents += f"---\nFilename: {rel_path}\n---\n{content}\n\n"

    if llm_friendly:
        file_list.sort(key=lambda x: str(x[0]))
        all_contents += "# TABLE OF CONTENTS\n"
        all_contents += "\n".join(f"{idx}. {rel_path}" for idx, (rel_path, _) in enumerate(file_list, 1))
        all_contents += "\n\n"

        for idx, (rel_path, path) in enumerate(file_list, 1):
            all_contents += f"{'#' * 80}\n# FILE {idx}: {rel_path}\n{'#' * 80}\n\n"
            try:
                with path.open("r", encoding="utf-8", errors="replace") as file:
                    all_contents += file.read()
            except Exception as e:
                logger.error(f"Error reading file {path}: {e}")
                all_contents += f"# Error reading file: {e}\n\n"
            all_contents += "\n\n"

    with output_file_path.open("w", encoding="utf-8", errors="replace") as file:
        file.write(all_contents)

    logger.info(f"Archive created at: {output_file_path}")
    return output_file_path