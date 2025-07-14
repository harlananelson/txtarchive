from pathlib import Path
from .utilities import archive_selected_file_types, archive_configuration_files
from .packunpack import concatenate_files, archive_subdirectories, combine_all_archives, run_concat, unpack_files
from .header import logger

def test_archive_selected_file_types():
    # Your debug statement
    archive_path = Path(Path.cwd() / "archivefiles" / "archive.csv")
    logger.debug(F"Writing combined archive to: {archive_path}")
    
    print("Testing archive_selected_file_types... ")
    dirtxt = 'configuration'
    example_directory = Path.cwd() / dirtxt
    print(f"Example directory: {example_directory}")
    
    combined_archive_name = Path.cwd() / 'archivefiles' / f'{dirtxt}_combined.txt'
    
    archive_selected_file_types(
        parent_directory = example_directory,
        directories=None,
        combined_archive_dir=Path("archivefiles"),
        combined_archive_name=combined_archive_name,
        file_types=['.yaml']
    )
    
def test_archive_configuration_files():
    print("Testing archive_configuration_files... ")
    archive_configuration_files()
    print("Completed archive_configuration_files.")
 

def _test_package_functionality():
    # Your debug statement
    
    logger.debug(f"Writing combined archive to: {archive_path}")
    
    print("Testing package functionality...")
    dirtxt = 'configuration'
    example_directory = Path.cwd() / dirtxt
    print(f"Example directory: {example_directory}")
    
    combined_archive_name = Path.cwd() / 'archivefiles' / f'{dirtxt}_combined.txt'
    
    concatenate_files(directory = example_directory, 
                      combined_file_path = combined_archive_name, 
                      file_types=['.yaml'])
    
    
    print(f"Completed archive_selected_file_types for directory: {example_directory}")

   
if __name__ == "__main__":
    logger.basicConfig(level=logger.info, format="%(asctime)s - %(levelname)s - %(message)s")
    test_archive_selected_file_types()