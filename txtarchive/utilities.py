# These function actuall are not needed because the functionality is already implemented in packunpack.py and demonstrated 
# in test_packunpack.py. The functions are not used in the main program and are not tested in the test_package.py.

from pathlib import Path
import logging


from pathlib import Path
import logging

def archive_selected_file_types(parent_directory, directories=None, 
                                combined_archive_dir=None,
                                combined_archive_name='all_combined_archives.txt',
                                file_types=['.yaml', '.py', '.r']):
    """
    Given a parent directory, archive all files of a specific type in the directory and its subdirectories.
    
    Args:
        parent_directory (Path): The parent directory to search for files.
        directories (list): A list of specific directories to archive. If None, all subdirectories will be used.
        combined_archive_dir (Path): The directory where the combined archive will be saved. If None, the parent directory will be used.
        combined_archive_name (Path): The name of the combined archive file.
        file_types (list): A list of file extensions to include in the archive.
    """
    all_archives_content = ""

    parent_directory = Path(parent_directory)
    if combined_archive_dir:
        combined_archive_dir = Path(combined_archive_dir)
    combined_archive_name = Path(combined_archive_name)

    # If no specific directories are provided, use all subdirectories
    if directories is None:
        directories = [d for d in parent_directory.iterdir() if d.is_dir()]
    else:
        directories = [Path(parent_directory) / d for d in directories]

    logging.debug(f"Directories to process: {directories}")

    # Iterate over all items in parent directory
    for item in directories:
        logging.debug(f"Processing directory: {item}")
        
        # Define the name of the archive file for each subdirectory
        archive_file_name = f"{item.name}_{combined_archive_name.stem}.txt"
        archive_file = (combined_archive_dir / archive_file_name) if combined_archive_dir else (parent_directory / archive_file_name)
        
        logging.debug(f"Looking for archive file: {archive_file}")
        
        # Check if the archive file exists and read its content
        if archive_file.is_file():
            logging.debug(f"Found archive file: {archive_file}")
            with archive_file.open('r') as file:
                content = file.read()
                all_archives_content += f"---\nDirectory: {item.name}\n---\n{content}\n\n"
        else:
            logging.info(f"No archive file found for directory {item.name}")

    # Ensure the combined archive name has a .txt extension
    if combined_archive_name.suffix != '.txt':
        combined_archive_name = combined_archive_name.with_suffix('.txt')
    
    archive_path = (combined_archive_dir / combined_archive_name) if combined_archive_dir else (parent_directory / combined_archive_name)
    
    logging.debug(f"Writing combined archive to: {archive_path}")
    
    with archive_path.open('w') as file:
        file.write(all_archives_content)

    logging.info(f"All archives combined into {archive_path}")

def archive_configuration_files():
    # Create the 'configuration' directory if it doesn't exist
    configuration_dir = Path('configuration')
    configuration_dir.mkdir(exist_ok=True)

    # Get a list of all YAML files in 'configuration' directory
    yaml_files = list(configuration_dir.glob('*.yaml'))

    # Open the output file
    with Path('configuration.txt').open('w') as f:
        # For each YAML file
        for file in yaml_files:
            logging.info(f"{file}")
            # Write the file name to the output file
            f.write(f'FILE: {file}\n')

            # Write the contents of the file to the output file
            with file.open('r') as file_contents:
                f.write(file_contents.read())
                f.write('\n')

# Example usage
# parent_directory = '/path/to/Projects'
# archive_selected_file_types(parent_directory)
# archive_configuration_files()
