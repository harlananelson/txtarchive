def archive_subdirectories(parent_directory, archive_dir=None, archive_name='all_archives.txt', directories=None):
    """
    Combine the contents of all archives in the specified subdirectories into a single file.

    This function reads the contents of all archives in the specified subdirectories and combines them into a single
    file. The combined file is saved in the parent directory with the specified name.

    Parameters:
    parent_directory (str): The parent directory containing the subdirectories.
    archive_dir (str): The directory where the archives are stored. If None, the parent directory is used.
    archive_name (str): The name of the combined archive file.
    directories (list of str): The subdirectories to include. If None, all subdirectories are included.

    Returns:
    None
    """
    print("function: archive_subdirectories")
    all_archives_content = ""

    # If no specific directories are provided, use all subdirectories
    if directories is None:
        print(f"using All directories of {parent_directory}")
        directories = os.listdir(parent_directory)
    else:
        print(f"only using the directories: {directories}") 

    # Iterate over all items in parent directory
    for item in directories:
        # Define the name of the archive file for each subdirectory
        archive_file_name = f"{item}_{archive_name}.txt"
        archive_file = os.path.join(archive_dir or parent_directory, archive_file_name)
        
        # Check if the archive file exists and read its content
        if os.path.isfile(archive_file):
            with open(archive_file, 'r') as file:
                print(f"Extract Archived {archive_file} \n")
                content = file.read()
                print(f"---\nDirectory: {item}\n")
                all_archives_content += f"---\nDirectory: {item}\n---\n{content}\n\n"
                print("End of Directory\n")
        else:
            print(f"No archive file found for directory {item}")

    # Write all archives content to a single file in the parent directory
    if not archive_name.endswith('.txt'):
        archive_name += '.txt'
    
    archive_path = os.path.join(archive_dir or parent_directory, archive_name)
    with open(archive_path, 'w') as file:
        file.write(all_archives_content)

    print(f"All archives combined into {archive_path}")

# Create an archive of yaml configuration files.

# Create the 'configuration' directory if it doesn't exist
os.makedirs('configuration', exist_ok=True)

# Get a list of all Python files in 'lhn' directory and its subdirectories
python_files = glob.glob('configuration/*.yaml', recursive=True)

# Open the output file
with open('configuration.txt', 'w') as f:
    # For each Python file
    for file in python_files:
        print(f"{file}")
        # Write the file name to the output file
        f.write(f'FILE: {file}\n')
        
        # Write the contents of the file to the output file
        with open(file, 'r') as file_contents:
            f.write(file_contents.read())
            f.write('\n')