import json
from pathlib import Path
from .header import logger

def read_notebook(notebook_path):
    """
    Read a Jupyter notebook file and handle encoding issues. Return the content.

    Args:
        notebook_path (Path): Path to the Jupyter notebook file.

    Returns:
        dict: The notebook content as a dictionary, or None if an error occurs.
    """
    try:
        with notebook_path.open('r', encoding='utf-8', errors='replace') as file:
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
    for cell in notebook.get('cells', []):
        if cell['cell_type'] == 'code':
            cell['outputs'] = []
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
        with file_path.open('r', encoding = 'utf-8', errors='replace') as file:
            notebook = json.load(file)
        for cell in notebook.get('cells', []):
            if cell['cell_type'] == 'code':
                cell['outputs'] = []
        return json.dumps(notebook, indent=4)
    except Exception as e:
        logger.error(f"Error processing {file_path}: {e}")
        return None

def concatenate_files(directory, combined_file_path, file_types=['.yaml', '.py', '.r']):
    """
    Concatenate files of specified types in a directory into a single text file.

    Args:
        directory (Path): Directory to search for files.
        combined_file_path (Path): Path to the output file.
        file_types (list): List of file extensions to include.
    """
    logger.info("Concatenating files in directory: %s", directory)
    all_contents = ""

    for path in directory.rglob('*'):
        if path.is_file() and not path.name.startswith(('.', '#')) and directory in path.parents:
            content = None

            if path.suffix == '.ipynb':
                logger.info("Archiving %s", path.name)
                content = read_notebook(path)
                if content is not None:
                    content = remove_outputs_from_code_cells(content)
                    content = json.dumps(content, indent=4)
            elif path.suffix in file_types:
                logger.info("Processing %s", path.name)
                try:
                    with path.open('r') as file:
                        content = file.read()
                except FileNotFoundError:
                    logger.error("File not found: %s", path)
                    continue

            if content is not None:
                all_contents += f"---\nFilename: {path.name}\n---\n{content}\n\n"

    with combined_file_path.open('w') as file:
        file.write(all_contents)
    logger.info("Files concatenated into: %s", combined_file_path)

def unpack_files(combined_file_path, output_directory, replace_existing=False):
    """
    Unpack files from a combined text file into a specified directory.

    Args:
        combined_file_path (Path): Path to the combined text file.
        output_directory (Path): Directory to output the unpacked files.
    """
    with combined_file_path.open('r') as file:
        combined_content = file.read()

    sections = combined_content.split('---\nFilename: ')[1:]

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
        filename, content = section.split('\n---\n', 1)
        output_path = output_directory / filename.strip()
        if output_path.exists() and not replace_existing:
            output_path = output_directory / f"{filename.strip()}_copy"
        with output_path.open('w') as file:
            file.write(content)
            logger.info("Unpacked file: %s", output_path)
    logger.info("Files unpacked into: %s", output_directory)

def run_concat(current_directory, combined_files='combined_files.txt', file_types=['.yaml', '.py', '.r']):
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

def run_unpack(combined_file_path, output_directory, replace_existing=False):
    """
    Wrapper for the `unpack_files` function.

    Args:
        combined_file_path (Path): Path to the combined text file.
        output_directory (Path): Directory to output the unpacked files.
    """
    if isinstance(combined_file_path, str):
        combined_file_path = Path(combined_file_path)
    if isinstance(output_directory, str):
        output_directory = Path(output_directory)

    unpack_files(combined_file_path, output_directory, replace_existing=replace_existing)
    logger.info("Files have been unpacked into: %s", output_directory)

def archive_subdirectories(parent_directory, directories=None, combined_archive_dir=None, combined_archive_name='all_combined_archives.txt', file_types=['.yaml', '.py', '.r']):
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
            archive_file = (combined_archive_dir / archive_file_name) if combined_archive_dir else (parent_directory / archive_file_name)
            run_concat(item_path, combined_files=archive_file, file_types=file_types)
            logger.info("Archived %s into %s", item_path, archive_file)

    combine_all_archives(parent_directory, combined_archive_dir, combined_archive_name, directories)

def combine_all_archives(parent_directory, combined_archive_dir=None, combined_archive_name='all_combined_archives.txt', directories=None):
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
        archive_file = (combined_archive_dir / archive_file_name) if combined_archive_dir else (parent_directory / archive_file_name)
        logger.info("Combining archive file: %s", archive_file)

        if archive_file.is_file():
            with archive_file.open('r') as file:
                content = file.read()
                all_archives_content += f"---\nDirectory: {item.name}\n---\n{content}\n\n"

    combined_archive_path = (combined_archive_dir / combined_archive_name) if combined_archive_dir else (parent_directory / combined_archive_name)
    with combined_archive_path.open('w') as file:
        file.write(all_archives_content)
    logger.info("All archives combined into: %s", combined_archive_path)

def unpack_all_archives(parent_directory, combined_archive_name='all_combined_archives.txt', overwrite=True):
    """
    Unpack all archives from a combined archive file.

    Args:
        parent_directory (Path): Parent directory containing the combined archive file.
        combined_archive_name (str): Name of the combined archive file.
        overwrite (bool): Whether to overwrite existing files.
    """
    parent_directory = Path(parent_directory)
    combined_archive_path = parent_directory / combined_archive_name

    with combined_archive_path.open('r') as file:
        combined_content = file.read()

    directory_sections = combined_content.split('---\nDirectory: ')[1:]

    for section in directory_sections:
        directory_name, content = section.split('\n---\n', 1)
        directory_path = parent_directory / directory_name.strip()
        directory_path.mkdir(parents=True, exist_ok=True)

        archive_file_path = directory_path / 'combined_files.txt'
        if archive_file_path.exists() and not overwrite:
            archive_file_path = directory_path / 'combined_files_copy.txt'

        with archive_file_path.open('w') as file:
            file.write(content)

        unpack_files(archive_file_path, directory_path)
        logger.info("Unpacked archive in: %s", directory_path)

# Example usage
# parent_directory = '/path/to/Projects'
# unpack_all_archives(parent_directory)