import json
from pathlib import Path
from .header import logger
from datetime import datetime

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
    all_contents = ""

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
                all_contents += f"---\nFilename: {rel_path}\n---\n{content}\n\n"
            elif is_init_file:
                logger.warning(f"No content was obtained from __init__.py at {path}")

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
        try:
            filename, content = section.split("\n---\n", 1)
            normalized_filename = filename.strip().replace('\\\\', '/').replace('\\', '/')
            logger.debug(f"Normalized filename: {normalized_filename}")
            
            output_path = output_directory / normalized_filename
            
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

def run_concat_no_subdirs(
    current_directory,
    combined_files="combined_files.txt",
    file_types=[".yaml", ".py", ".r"],
    file_prefixes=None,
):
    """
    Concatenate files of specified types in just the top-level directory (no subdirectories).

    Args:
        current_directory (Path): Directory to search for files.
        combined_files (Path): Path to the output file.
        file_types (list): List of file extensions to include.
        file_prefixes (list): List of prefixes to filter filenames (default is None).
    """
    if isinstance(current_directory, str):
        current_directory = Path(current_directory)
    if isinstance(combined_files, str):
        combined_files = Path(combined_files)

    logger.info(
        "Concatenating files in top-level directory only: %s", current_directory
    )
    all_contents = ""

    for path in current_directory.glob("*"):
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

# Modify run_unpack to use auto-detection
def run_unpack(output_directory, combined_file_path, replace_existing=False):
    """Run unpack with auto-detection."""
    logger.info(
        f"Unpacking files from {combined_file_path} to {output_directory} using replace_existing={replace_existing}"
    )
    unpack_files_auto(output_directory, combined_file_path, replace_existing)
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

def unpack_llm_archive(output_directory, combined_file_path, replace_existing=False):
    """
    Unpack files from an LLM-friendly format archive.
    
    Args:
        output_directory (Path): Directory to output the unpacked files.
        combined_file_path (Path): Path to the LLM-friendly archive file.
        replace_existing (bool): Whether to replace existing files.
    """
    if isinstance(combined_file_path, str):
        combined_file_path = Path(combined_file_path)
    if isinstance(output_directory, str):
        output_directory = Path(output_directory)
    
    with combined_file_path.open("r", encoding="utf-8") as file:
        content = file.read()
    
    # Parse LLM-friendly format: split on file separators
    sections = content.split("################################################################################\n# FILE ")
    
    if len(sections) <= 1:
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
    
    # Process each file section
    for section in sections[1:]:  # Skip the header before first file
        # Parse: "N: filename\n###...###\n\ncontent"
        lines = section.split('\n', 2)
        if len(lines) < 3:
            continue
            
        # Extract filename from "N: filename"
        first_line = lines[0]
        if ': ' in first_line:
            filename = first_line.split(': ', 1)[1].strip()
        else:
            continue
        
        # Skip the separator line (line 1 is "###...###")
        # Content starts at line 2
        content = lines[2] if len(lines) > 2 else ""
        
        # Create file path
        file_path = output_directory / filename
        
        # Check if file exists and handle accordingly
        if file_path.exists() and not replace_existing:
            logger.info(f"Skipped existing file: {file_path}")
            continue
        
        # Create parent directories if needed
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write the file
        try:
            with file_path.open("w", encoding="utf-8") as f:
                f.write(content)
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
        content = f.read(2000)  # Read first 2000 chars
        
    if '################################################################################\n# FILE ' in content:
        return 'llm-friendly'
    elif '---\nFilename: ' in content:
        return 'standard'
    else:
        # Default to standard for backward compatibility
        return 'standard'


def unpack_files_auto(output_directory, combined_file_path, replace_existing=False):
    """
    Auto-detect format and unpack accordingly.
    """
    format_type = auto_detect_archive_format(combined_file_path)
    
    logger.info(f"Detected archive format: {format_type}")
    
    if format_type == 'llm-friendly':
        return unpack_llm_archive(output_directory, combined_file_path, replace_existing)
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

def create_llm_archive(directory, output_file_path, file_types=[".py", ".yaml", ".r", ".ipynb", ".qmd"], file_prefixes=None, include_subdirectories=True):
    """
    Create a single text file containing all code from the specified directory,
    formatted in a way that's ideal for input to an LLM.
    
    Args:
        directory (Path): Directory to search for files.
        output_file_path (Path): Path to the output file.
        file_types (list): List of file extensions to include.
        file_prefixes (list): List of filename prefixes to include (default is None).
        include_subdirectories (bool): Whether to traverse subdirectories (default is True).
    """
    if isinstance(directory, str):
        directory = Path(directory)
    if isinstance(output_file_path, str):
        output_file_path = Path(output_file_path)
    
    logger.info(f"Creating LLM-friendly archive from directory: {directory}")
    all_contents = ""
    
    all_contents += f"# LLM-FRIENDLY CODE ARCHIVE\n"
    all_contents += f"# Generated from: {directory}\n"
    all_contents += f"# Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

    file_list = []
    
    if include_subdirectories:
        file_iterator = directory.rglob("*")
    else:
        file_iterator = directory.glob("*")

    for path in file_iterator:
        if (path.is_file() and 
            not path.name.startswith((".", "#")) and 
            path.suffix in file_types):
            
            if file_prefixes and not any(path.name.startswith(prefix) for prefix in file_prefixes):
                continue
                
            rel_path = path.relative_to(directory)
            file_list.append((rel_path, path))
    
    file_list.sort(key=lambda x: str(x[0]))
    
    all_contents += "# TABLE OF CONTENTS\n"
    for idx, (rel_path, _) in enumerate(file_list, 1):
        all_contents += f"{idx}. {rel_path}\n"
    all_contents += "\n\n"
    
    for idx, (rel_path, path) in enumerate(file_list, 1):
        logger.info(f"Processing {path.name}")
        
        all_contents += f"{'#' * 80}\n"
        all_contents += f"# FILE {idx}: {rel_path}\n"
        all_contents += f"{'#' * 80}\n\n"
        
        content = None
        
        if path.suffix == ".ipynb":
            try:
                with path.open("r", encoding="utf-8", errors="replace") as file:
                    notebook = json.load(file)
                
                for cell_idx, cell in enumerate(notebook.get("cells", []), 1):
                    if cell["cell_type"] == "code":
                        cell_content = "".join(cell.get("source", []))
                        if cell_content.strip():
                            all_contents += f"# Cell {cell_idx}\n"
                            all_contents += cell_content
                            all_contents += "\n\n"
                    elif cell["cell_type"] == "markdown":
                        cell_content = "".join(cell.get("source", []))
                        if cell_content.strip():
                            all_contents += f"# Markdown Cell {cell_idx}\n"
                            all_contents += '"""\n'
                            all_contents += cell_content
                            if not cell_content.endswith('\n'):
                                all_contents += '\n'
                            all_contents += '"""\n\n'
            except Exception as e:
                logger.error(f"Error processing notebook {path}: {e}")
                all_contents += f"# Error processing notebook: {e}\n\n"
        else:
            try:
                with path.open("r", encoding="utf-8", errors="replace") as file:
                    content = file.read()
                    all_contents += content
                    all_contents += "\n\n"
            except Exception as e:
                logger.error(f"Error reading {path}: {e}")
                all_contents += f"# Error reading file: {e}\n\n"
    
    with output_file_path.open("w", encoding="utf-8") as file:
        file.write(all_contents)
    
    logger.info(f"LLM-friendly archive created at: {output_file_path}")
    return output_file_path

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
):
    directory = Path(directory) if isinstance(directory, str) else directory
    output_file_path = Path(output_file_path) if isinstance(output_file_path, str) else output_file_path
    default_exclude_dirs = {"build", ".pytest_cache"}
    exclude_dirs = set(exclude_dirs or []) | default_exclude_dirs
    root_files = set(root_files or [])
    include_subdirs = set(include_subdirs or [])
    processed_files = set()
    file_list = []

    logger.info(f"Archiving files from: {directory}")
    logger.info(f"Excluding directories: {exclude_dirs}")
    all_contents = ""
    creation_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    all_contents += f"# Archive created on: {creation_date}\n\n"

    if llm_friendly:
        all_contents += "# LLM-FRIENDLY CODE ARCHIVE\n"
        all_contents += f"# Generated from: {directory}\n"
        all_contents += f"# Date: {creation_date}\n\n"
    else:
        all_contents += "# Standard Archive Format\n\n"

    if not directory.is_dir():
        logger.error(f"Input directory does not exist: {directory}")
        raise FileNotFoundError(f"Input directory does not exist: {directory}")

    output_file_path.parent.mkdir(parents=True, exist_ok=True)
    logger.info(f"Ensured output directory exists: {output_file_path.parent}")

    # Handle explicit file list mode
    if explicit_files is not None:
        logger.info(f"Using explicit file list mode with {len(explicit_files)} files")
        
        for file_name in explicit_files:
            # Support both absolute paths and relative to directory
            file_path = Path(file_name)
            if not file_path.is_absolute():
                file_path = directory / file_name
            
            # Validate file exists
            if not file_path.exists():
                logger.error(f"Explicit file not found: {file_path}")
                continue
            
            if not file_path.is_file():
                logger.warning(f"Skipping non-file path: {file_path}")
                continue
            
            # Calculate relative path for archive
            try:
                rel_path = file_path.relative_to(directory)
            except ValueError:
                # File is outside directory, use just the filename
                rel_path = Path(file_path.name)
                logger.warning(f"File {file_path} is outside source directory, using filename only: {rel_path}")
            
            logger.info(f"Processing explicit file: {file_path}")
            
            # Process the file content
            content = None
            
            if file_path.suffix == ".ipynb":
                try:
                    notebook_content = read_notebook(file_path)
                    if notebook_content:
                        if extract_code_only:
                            content = ""
                            for cell_idx, cell in enumerate(notebook_content.get("cells", []), 1):
                                if cell["cell_type"] == "code" and cell.get("source"):
                                    cell_content = "".join(cell.get("source", []))
                                    if cell_content.strip():
                                        content += f"# Cell {cell_idx}\n{cell_content}\n\n"
                                elif cell["cell_type"] == "markdown" and cell.get("source"):
                                    cell_content = "".join(cell.get("source", []))
                                    if cell_content.strip():
                                        content += f"# Markdown Cell {cell_idx}\n"
                                        content += '"""\n'
                                        content += cell_content
                                        if not cell_content.endswith('\n'):
                                            content += '\n'
                                        content += '"""\n\n'
                        else:
                            content = json.dumps(remove_outputs_from_code_cells(notebook_content), indent=4)
                except Exception as e:
                    logger.error(f"Error processing notebook {file_path}: {e}")
                    content = f"# Error processing notebook: {e}\n\n"
            else:
                try:
                    with file_path.open("r", encoding="utf-8", errors="replace") as file:
                        content = file.read()
                except Exception as e:
                    logger.error(f"Error reading file {file_path}: {e}")
                    content = f"# Error reading file: {e}\n\n"
            
            if content is not None:
                file_list.append((rel_path, content))
                processed_files.add(str(rel_path))
        
        # Skip to the output generation section
        logger.info(f"Processed {len(file_list)} explicit files")
    
    # Helper function to check if a path matches include_subdirs criteria
    def path_matches_include_subdirs(file_path, base_directory):
        """
        Check if a file path should be included based on include_subdirs.
        
        Improved logic:
        1. If include_subdirs is empty, include all files (old behavior)
        2. If include_subdirs is specified, check if ANY part of the relative path
           starts with any of the include_subdirs values
        
        Examples:
        - include_subdirs = ['R', 'inst/raw', 'HOWTO']
        - R/script.R -> matches 'R'
        - inst/raw/data.csv -> matches 'inst/raw'
        - inst/other/file.txt -> does NOT match
        - HOWTO/guide.md -> matches 'HOWTO'
        """
        if not include_subdirs:
            return True
        
        try:
            rel_path = file_path.relative_to(base_directory)
        except ValueError:
            return False
        
        # Convert to string with forward slashes for consistent comparison
        rel_path_str = str(rel_path).replace('\\', '/')
        
        # Check if the relative path starts with any of the include_subdirs
        for subdir in include_subdirs:
            subdir_normalized = subdir.replace('\\', '/')
            # Check if the file is in this subdirectory or deeper
            if rel_path_str.startswith(subdir_normalized + '/') or \
               str(rel_path.parent).replace('\\', '/') == subdir_normalized:
                logger.debug(f"File {rel_path} matches include_subdir: {subdir}")
                return True
        
        return False

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
                file_list.append((rel_path, content))
                processed_files.add(str(rel_path))
            except Exception as e:
                logger.error(f"Error reading root file {path}: {e}")
                content = f"# Error reading file: {e}\n\n"
                file_list.append((rel_path, content))
                processed_files.add(str(rel_path))

        # Get file iterator
        file_iterator = directory.rglob("*") if include_subdirectories else directory.glob("*")

        for path in file_iterator:
            # Check exclusion - check if any parent directory is in exclude_dirs
            if include_subdirectories:
                path_parts = path.relative_to(directory).parts
                if any(part in exclude_dirs for part in path_parts):
                    continue
        
            rel_path = path.relative_to(directory)
        
            # NEW: Check if path matches include_subdirs criteria
            if include_subdirs and not path_matches_include_subdirs(path, directory):
                # File is not in an included subdirectory, skip unless it's a root file
                if path.parent != directory:  # Not a root-level file
                    continue
        
            # Rest of the logic remains the same
            is_root_file = rel_path.parent == Path(".")
        
            if path.is_file():
                is_gitignore = path.name == ".gitignore"
                if not (is_gitignore or (not path.name.startswith((".", "#")) and path.suffix in file_types)):
                    continue
                if is_root_file and path.name in root_files:
                    logger.info(f"Skipping already processed root file: {path}")
                    continue
                if str(rel_path) in processed_files:
                    logger.info(f"Skipping already processed file: {path}")
                    continue
                if file_prefixes and not is_gitignore and not any(path.name.startswith(prefix) for prefix in file_prefixes):
                    continue
                
                logger.info(f"Processing file: {path}")
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
                                    elif cell["cell_type"] == "markdown" and cell.get("source"):
                                        cell_content = "".join(cell.get("source", []))
                                        if cell_content.strip():
                                            content += f"# Markdown Cell {cell_idx}\n{cell_content}\n\n"
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
                    file_list.append((rel_path, content))
                    processed_files.add(str(rel_path))

        # Rest of the function continues as before...
    file_list.sort(key=lambda x: str(x[0]))
    all_contents += "# TABLE OF CONTENTS\n"
    all_contents += "\n".join(f"{idx}. {rel_path}" for idx, (rel_path, _) in enumerate(file_list, 1))
    all_contents += "\n\n"

    if llm_friendly:
        for idx, (rel_path, content) in enumerate(file_list, 1):
            all_contents += f"{'#' * 80}\n# FILE {idx}: {rel_path}\n{'#' * 80}\n\n"
            all_contents += content
            all_contents += "\n\n"
    else:
        for rel_path, content in file_list:
            all_contents += f"---\nFilename: {rel_path}\n---\n{content}\n\n"

    with output_file_path.open("w", encoding="utf-8") as file:
        file.write(all_contents)

    logger.info(f"Archive created at: {output_file_path}")

    if split_output:
        from .split_files import split_file
        split_dir = Path(split_output_dir) if split_output_dir else output_file_path.parent / f"split_{output_file_path.stem}"
        split_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Ensured split output directory exists: {split_dir}")
        split_file(output_file_path, max_tokens=max_tokens, output_dir=split_dir)
        logger.info(f"Split files created in: {split_dir}")

    return output_file_path

def extract_notebooks_to_ipynb(archive_file_path, output_directory, replace_existing=False):
    """
    Extract Jupyter notebooks from an LLM-friendly text archive into .ipynb files.
    Now handles both code cells and markdown cells.

    Args:
        archive_file_path (Path): Path to the LLM-friendly archive file or directory of split files.
        output_directory (Path): Directory to save the reconstructed .ipynb files.
        replace_existing (bool): Whether to overwrite existing files (default: False).
    """
    archive_file_path = Path(archive_file_path)
    output_directory = Path(output_directory)
    
    logger.info(f"Extracting notebooks to {output_directory}")
    
    content = ""
    if archive_file_path.is_dir():
        logger.info(f"Processing split files in directory: {archive_file_path}")
        split_files = sorted(archive_file_path.glob("*.txt"), key=lambda x: x.name)
        if not split_files:
            logger.error(f"No split files found in {archive_file_path}")
            return
        for split_file in split_files:
            logger.info(f"Reading split file: {split_file}")
            try:
                with split_file.open("r", encoding="utf-8") as file:
                    split_content = file.read()
                    lines = split_content.splitlines()
                    cleaned_lines = [
                        line for line in lines
                        if line.strip() not in ["<DOCUMENT>", "</DOCUMENT>"]
                        and not line.startswith("# Part ")
                    ]
                    content += "\n".join(cleaned_lines) + "\n"
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
            return
    
    if "TABLE OF CONTENTS" not in content:
        logger.error("Archive missing TABLE OF CONTENTS; may be incomplete")
        return
    
    output_directory.mkdir(parents=True, exist_ok=True)
    
    sections = content.split("################################################################################\n# FILE ")
    if len(sections) < 2:
        logger.warning(f"No notebook sections found in archive")
        return
    
    for section in sections[1:]:
        lines = section.split("\n", 2)
        if len(lines) < 3:
            logger.warning(f"Invalid section format: {section[:50]}...")
            continue
            
        file_info = lines[0].strip()
        try:
            file_num, filename = file_info.split(": ", 1)
            filename = filename.strip()
            if not filename.endswith(".ipynb"):
                logger.debug(f"Skipping non-notebook file: {filename}")
                continue
        except ValueError:
            logger.warning(f"Invalid file info format: {file_info}")
            continue
            
        file_content = lines[2]
        
        output_path = output_directory / filename
        
        # Ensure parent directories exist
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        if output_path.exists() and not replace_existing:
            output_path = output_path.with_stem(f"{output_path.stem}_copy")
            logger.info(f"File exists, using {output_path.name}")
            
        notebook = {
            "cells": [],
            "metadata": {
                "kernelspec": {
                    "display_name": "Python 3",
                    "language": "python",
                    "name": "python3"
                },
                "language_info": {
                    "name": "python",
                    "version": "3.10.0"
                }
            },
            "nbformat": 4,
            "nbformat_minor": 5
        }
        
        if file_content.strip().startswith("{"):
            try:
                notebook = json.loads(file_content)
                logger.info(f"Restored JSON notebook: {filename}")
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON in {filename}: {e}")
                continue
        else:
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
                        if next_line.startswith("# Cell ") or next_line.startswith("# Markdown Cell "):
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
            logger.info(f"Reconstructed {code_cells} code cells and {markdown_cells} markdown cells for {filename}")
        
        try:
            with output_path.open("w", encoding="utf-8") as file:
                json.dump(notebook, file, indent=2)
            logger.info(f"Created notebook: {output_path}")
        except Exception as e:
            logger.error(f"Error writing {output_path}: {e}")

def run_extract_notebooks(archive_file_path, output_directory, replace_existing=False):
    """
    Wrapper for extract_notebooks_to_ipynb.
    """
    extract_notebooks_to_ipynb(archive_file_path, output_directory, replace_existing)
    logger.info(f"Notebooks extracted to: {output_directory}")

def extract_notebooks_and_quarto(archive_file_path, output_directory, replace_existing=False):
    """
    Extract Jupyter notebooks and Quarto files from an LLM-friendly or standard text archive.

    Args:
        archive_file_path (Path): Path to the archive file or directory of split files.
        output_directory (Path): Directory to save the reconstructed .ipynb and .qmd files.
        replace_existing (bool): Whether to overwrite existing files (default: False).
    """
    archive_file_path = Path(archive_file_path)
    output_directory = Path(output_directory)
    
    logger.info(f"Extracting notebooks and Quarto files to {output_directory}")
    
    content = ""
    if archive_file_path.is_dir():
        logger.info(f"Processing split files in directory: {archive_file_path}")
        split_files = sorted(archive_file_path.glob("*.txt"), key=lambda x: x.name)
        if not split_files:
            logger.error(f"No split files found in {archive_file_path}")
            return
        for split_file in split_files:
            logger.info(f"Reading split file: {split_file}")
            try:
                with split_file.open("r", encoding="utf-8") as file:
                    split_content = file.read()
                    lines = split_content.splitlines()
                    cleaned_lines = [
                        line for line in lines
                        if line.strip() not in ["<DOCUMENT>", "</DOCUMENT>"]
                        and not line.startswith("# Part ")
                    ]
                    content += "\n".join(cleaned_lines) + "\n"
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
            return
    
    if "TABLE OF CONTENTS" not in content:
        logger.error("Archive missing TABLE OF CONTENTS; may be incomplete")
        return
    
    output_directory.mkdir(parents=True, exist_ok=True)
    
    # Try LLM-friendly format first
    sections = content.split("################################################################################\n# FILE ")
    is_llm_friendly = len(sections) > 1
    
    if not is_llm_friendly:
        # Try standard format
        sections = content.split("---\nFilename: ")[1:]
        if len(sections) < 1:
            logger.warning(f"No file sections found in archive")
            return
    
    for section in sections:
        if is_llm_friendly:
            lines = section.split("\n", 2)
            if len(lines) < 3:
                logger.warning(f"Invalid LLM-friendly section format: {section[:50]}...")
                continue
            file_info = lines[0].strip()
            try:
                file_num, filename = file_info.split(": ", 1)
                filename = filename.strip()
                if not (filename.endswith(".ipynb") or filename.endswith(".qmd")):
                    logger.warning(f"Skipping unsupported file: {filename}")
                    continue
            except ValueError:
                logger.warning(f"Invalid file info format: {file_info}")
                continue
            content = lines[2]
        else:
            try:
                filename, content = section.split("\n---\n", 1)
                filename = filename.strip()
                if not (filename.endswith(".ipynb") or filename.endswith(".qmd")):
                    logger.warning(f"Skipping unsupported file: {filename}")
                    continue
            except ValueError:
                logger.warning(f"Invalid standard section format: {section[:50]}...")
                continue
        
        output_path = output_directory / filename
        if output_path.exists() and not replace_existing:
            output_path = output_path.with_stem(f"{output_path.stem}_copy")
            logger.info(f"File exists, using {output_path.name}")
            
        if filename.endswith(".ipynb"):
            notebook = {
                "cells": [],
                "metadata": {
                    "kernelspec": {
                        "display_name": "Python 3",
                        "language": "python",
                        "name": "python3"
                    },
                    "language_info": {
                        "name": "python"
                    }
                },
                "nbformat": 4,
                "nbformat_minor": 5
            }
            
            if is_llm_friendly:
                cells = []
                current_cell = []
                cell_type = None
                cell_number = None
                
                for line in content.splitlines():
                    if line.startswith("# Cell "):
                        if current_cell:
                            cells.append({
                                "cell_type": cell_type,
                                "source": current_cell,
                                "metadata": {},
                                "execution_count": None,
                                "outputs": []
                            })
                            current_cell = []
                        cell_type = "code"
                        try:
                            cell_number = int(line.split("# Cell ")[1])
                        except (IndexError, ValueError):
                            logger.warning(f"Invalid cell marker in {filename}: {line}")
                        continue
                    elif line.startswith("# Markdown Cell "):
                        if current_cell:
                            cells.append({
                                "cell_type": cell_type,
                                "source": current_cell,
                                "metadata": {},
                                "execution_count": None,
                                "outputs": []
                            })
                            current_cell = []
                        cell_type = "markdown"
                        try:
                            cell_number = int(line.split("# Markdown Cell ")[1])
                        except (IndexError, ValueError):
                            logger.warning(f"Invalid cell marker in {filename}: {line}")
                        continue
                    current_cell.append(line + "\n")
                    
                if current_cell:
                    cells.append({
                        "cell_type": cell_type,
                        "source": current_cell,
                        "metadata": {},
                        "execution_count": None,
                        "outputs": []
                    })
                
                notebook["cells"] = cells
                logger.info(f"Reconstructed {len(cells)} cells for {filename}")
            else:
                try:
                    notebook = json.loads(content)
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
        else:  # .qmd
            try:
                with output_path.open("w", encoding="utf-8") as file:
                    file.write(content)
                logger.info(f"Created Quarto file: {output_path}")
            except Exception as e:
                logger.error(f"Error writing {output_path}: {e}")

def run_extract_notebooks_and_quarto(archive_file_path, output_directory, replace_existing=False):
    """
    Wrapper for extract_notebooks_and_quarto.
    """
    extract_notebooks_and_quarto(archive_file_path, output_directory, replace_existing)
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
        for split_file in sorted(lhn_path.glob("*.txt")):
            with split_file.open("r", encoding="utf-8") as f:
                split_content = f.read()
                lines = [
                    line for line in split_content.splitlines()
                    if line.strip() not in ["<DOCUMENT>", "</DOCUMENT>"]
                    and not line.startswith("# Part ")
                ]
                lhn_content += "\n".join(lines) + "\n"
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