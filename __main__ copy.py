import argparse
import logging
from .packunpack import run_concat, run_unpack, archive_subdirectories, run_concat_no_subdirs
from .packunpack import create_llm_archive
from .header import logger

# to run
# Add the current directory to the python path
# export PYTHONPATH=$PYTHONPATH:.

# Create an archive for LLM
# python -m txtarchive create_llm_archive "txtarchive" "txtarchive_llm.txt" --file_types ".py" --no-subdirectories
# python -m txtarchive create_llm_archive "txtarchive" "txtarchive_llm.txt" --file_types .py .yaml
# python -m txtarchive create_llm_archive "SCDCernerProject/Projects/SickleCell" "SCDCernerProject/Projects/SickleCell_LLM.txt" --file_types .ipynb --file_prefixes 011 015 016 017 050 060 065 066 067 070

# Archive selected files by prefix
# python -m txtarchive run_concat_no_subdirs "Projects/SickleCell" "Projects/SickleCell.txt" --file_types .ipynb --file_prefixes 011 015 016 017 050 060 065 066 067 070 
# python -m txtarchive run_concat_no_subdirs "Projects/SickleCell" "Projects/SickleCell.txt" --file_types .ipynb

# python -m txtarchive run_concat "adhocquery" "adhocquery-archive.txt" --file_types .ipynb .yaml .py
# python -m txtarchive run_concat "IU-Diabetes-Diagnosis" "IU-Diabetes-Diagnosis/IU-Diabetes-Diagnosis-archive.txt" --file_types .ipynb .yaml .py

# archive_subdirectories("Projects/IU-Diabetes-Diagnosis", "Projects/IU-Diabetes-Diagnosis.txt", [".ipynb", ".yaml"])

# python -m txtarchive run_concat "Projects/Demographics" "Projects/demographics.txt" --file_types .ipynb .yaml

# archive the updateln directory from the lhn
# python -m txtarchive run_concat "Projects/updatelhn" "Projects/updatelhn/updatelhn.txt" --file_types .py .sh .ipynb

# make sure your are in the root directory of the package, that is the directory containing the txtarchive directory
# archive the txtarchive package
# python -m txtarchive run_concat "txtarchive" "txtarchive.txt" --file_types .py
# python -m txtarchive run_unpack "txtarchive.txt" "txtarchive" --replace_existing
# python -m txtarchive run_unpack "txtarchive.txt" "txtarchive"

# Archive the configuration directory
# python -m txtarchive run_concat "configuration" "configuration.txt" --file_types .yaml
# python -m txtarchive run_unpack "configuration.txt" "configuration"

###### LHN ############# Archive the lhn module
# python -m txtarchive create_llm_archive "lhn" "lhn_llm.txt" --file_types ".py" --no-subdirectories
# python -m txtarchive run_concat "lhn" "lhn/lhn.txt" --file_types .py
# python -m txtarchive run_unpack "lhn.txt" "lhn" --replace_existing
# python -m txtarchive create_llm_archive "lhn" "lhn/lhn-llm.txt" --file_types .py

# Archive the demographics directory
# python -m txtarchive run_concat "Projects/Demographics" "Projects/demographics.txt" --file_types .ipynb .yaml
# python -m txtarchive run_unpack "Projects/demographics.txt" "Projects/Demographics"
# python -m txtarchive run_unpack "lhn.txt" "lhn" --replace_existing

# pack the r directory
# python -m txtarchive run_concat "r" "r.txt" --file_types .r
# python -m txtarchive run_unpack "r.txt" "r"
# pack folder guide
# python -m txtarchive run_concat "guide" "guide.txt" --file_types .ipynb
# python -m txtarchive run_unpack "guide.txt" "guide"

# pack the SickleCell directory in the
# python -m txtarchive run_concat "Projects/SickleCell" "Projects/SickleCell.txt" --file_types .ipynb
# python -m txtarchive run_unpack "Projects/SickleCell.txt" "Projects/SickleCell"
# pack the SickleCell directory in Projects/sicklecell/SickleCell
# python -m txtarchive run_concat "../sicklecell/SickleCell" "Projects/SickleCell.txt" --file_types .ipynb
# pack the shell directory
# python -m txtarchive run_concat "shell" "shell.txt" --file_types .sh
# python -m txtarchive run_unpack "shell.txt" "shell"

# tunneling through http://127.0.0.1:33496/user/hnelson3/
# to use the jupyter notebook goto http://

# Can I use pandoc to convert 015-sickle-cell-cohort-extraction-by-ICD-RWD.html to ipynb?
# pandoc 015-sickle-cell-cohort-extraction-by-ICD-RWD.html -o 015-sickle-cell-cohort-extraction-by-ICD-RWD.ipynb

# pandoc 050-Create-ADS.html
# pandoc 050-Create-ADS.html -o 050-Create-ADS.ipynb
# pandoc 100-Sickle-Cell-Survival-Curves.html -o 100-Sickle-Cell-Survival-Curves.ipynb
# pandoc 210-Review-Death.html -o 210-Review-Death.ipynb

def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    parser = argparse.ArgumentParser(description="textarchive command line utility.")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')


    # This is the part of __main__.py to modify

    
    # Add to your subparsers in main()
    concat_no_subdirs_parser = subparsers.add_parser('run_concat_no_subdirs', help='Concatenate files in a directory (no subdirectories)')
    concat_no_subdirs_parser.add_argument('current_directory', type=str, help='Directory containing files to concatenate')
    concat_no_subdirs_parser.add_argument('combined_files', type=str, help='Path to the output file')
    concat_no_subdirs_parser.add_argument('--file_types', nargs='+', default=['.yaml', '.py', '.r'], help='List of file extensions to include')
    concat_no_subdirs_parser.add_argument('--file_prefixes', nargs='+', help='List of filename prefixes to include')  # New argument

    llm_archive_parser = subparsers.add_parser('create_llm_archive', help='Create a single LLM-friendly archive of all code')
    llm_archive_parser.add_argument('directory', type=str, help='Directory containing code to archive')
    llm_archive_parser.add_argument('output_file', type=str, help='Path to the output file')
    llm_archive_parser.add_argument('--file_types', nargs='+', default=['.py', '.yaml', '.r', '.ipynb', '.sh'], 
                                help='List of file extensions to include')
    llm_archive_parser.add_argument('--file_prefixes', nargs='+', help='List of filename prefixes to include')
    llm_archive_parser.add_argument('--no-subdirectories', action='store_true', help='Do not include subdirectories')




# ... (rest of the code) ...
    

    # Sub parser for archive_subdirectories command
    archive_parser = subparsers.add_parser('archive_subdirectories', help='Archive subdirectories of a parent directory')
    archive_parser.add_argument('parent_directory', type=str, help='Parent directory containing subdirectories to archive')
    archive_parser.add_argument('--directories', nargs='+', help='List of subdirectories to archive (default: all subdirectories)', default=None)
    archive_parser.add_argument('--combined_archive_dir', type=str, help='Directory to store the combined archive file (default: parent directory)', default=None)
    archive_parser.add_argument('--combined_archive_name', type=str, help='Name of the combined archive file (default: all_combined_archives.txt)', default='all_combined_archives.txt')
    archive_parser.add_argument('--file_types', nargs='+', default=['.yaml', '.py', '.r'], help='List of file extensions to include in the archive')

    # Sub parser for the run_concat command
    concat_parser = subparsers.add_parser('run_concat', help='Concatenate files in a directory')
    concat_parser.add_argument('current_directory', type=str, help='Directory containing files to concatenate')
    concat_parser.add_argument('combined_files', type=str, help='Path to the output file')
    concat_parser.add_argument('--file_types', nargs='+', default=['.yaml', '.py', '.r'], help='List of file extensions to include')

    # Sub parser for the run_unpack command
    unpack_parser = subparsers.add_parser('run_unpack', help='Unpack files from a combined file')
    unpack_parser.add_argument('combined_file_path', type=str, help='Path to the combined text file')
    unpack_parser.add_argument('output_directory', type=str, help='Directory to output the unpacked files')
    unpack_parser.add_argument('--replace_existing', action='store_true', help='Replace existing files in the output directory')

    args = parser.parse_args()

    if args.command == 'archive_subdirectories':
        archive_subdirectories(args.parent_directory, args.directories, args.combined_archive_dir, args.combined_archive_name, args.file_types)
    elif args.command == 'run_concat':
        run_concat(args.current_directory, args.combined_files, file_types=args.file_types)
    elif args.command == 'run_unpack':
        logger.info(f"Unpacking files from {args.combined_file_path} to {args.output_directory} using replace_existing={args.replace_existing}")
        run_unpack(args.combined_file_path, args.output_directory, replace_existing=args.replace_existing)
    elif args.command == 'run_concat_no_subdirs':
        run_concat_no_subdirs(args.current_directory, args.combined_files, file_types=args.file_types, file_prefixes=args.file_prefixes)
    elif args.command == 'create_llm_archive':
        create_llm_archive(args.directory, args.output_file, file_types=args.file_types, file_prefixes=args.file_prefixes, include_subdirectories=not args.no_subdirectories)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()