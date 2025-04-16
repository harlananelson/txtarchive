# txtarchive/__main__.py
import argparse
import logging
import pkg_resources  # For Python < 3.8
from txtarchive.packunpack import archive_files, run_unpack, archive_subdirectories  # Absolute import
from .header import logger

try:
    from importlib.metadata import version as get_version  # Python 3.8+
    __version__ = get_version("txtarchive")
except ImportError:
    __version__ = pkg_resources.get_distribution("txtarchive").version



    # home/hnelson3/work/Users/hnelson3/txtarchive
    # (/tmp/r_env) hnelson3@ip-10-42-66-149:~/work/

    # python -m txtarchive archive "SickleCell" "SickleCell.txt" --file_types .ipynb --no-subdirectories --file_prefixes 011 015 016 017 050 060 065 066 067 070
    # Extract the data creation notebooks for LLM
    # python -m txtarchive archive "SickleCell" "SickleCellADSLLM.txt" --file_types .ipynb --llm-friendly --extract-code-only --no-subdirectories --file_prefixes 011 015 016 017 050 060 065 066 067 070
    # python -m txtarchive archive "SickleCell" "SickleCellRLLM.txt" --file_types .ipynb --llm-friendly --extract-code-only --no-subdirectories --file_prefixes 103 105 106 220 230 240 250 
    
    # python -m txtarchive archive "Projects/SickleCell" "Projects/SickleCell.txt" --file_types .ipynb --no-subdirectories --file_prefixes 011 015 016 017 050 060 065 066 067 070
    # python -m txtarchive archive "/home/hnelson3/work/Users/hnelson3/Projects/SickleCell" "/home/hnelson3/work/Users/hnelson3/Projects/SickleCell_ADSCreationLLM.txt" --file_types .ipynb .yaml --no-subdirectories --file_prefixes 000 011 015 016 017 050 060 065 066 067 070 --llm-friendly --extract-code-only
    # python -m txtarchive archive "lhn" "lhnLLM.txt" --file_types .py --no-subdirectories  --llm-friendly --extract-code-only
    
    # python -m txtarchive archive "lhn" "lhnLLM.txt" --file_types .ipynb --no-subdirectories --llm-friendly --extract-code-only --split-output --split-output-dir split_lhnLLM
    
    # python -m txtarchive archive "configuration" "configurationLLM.txt" --file_types .ipynb .yaml --no-subdirectories --file_prefixes config-global config-RWD  --llm-friendly --extract-code-only
    # python -m txtarchive archive "lhn" "lhn.txt"  --no-subdirectories
    # python -m txtarchive unpack "lhn" "lhn.txt"  # Correct usage

    # python -m txtarchive archive "txtarchive" "txtarchive.txt"  --no-subdirectories
    # python -m txtarchive unpack "txtarchive" "txtarchive.txt"  # Correct usage


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    parser = argparse.ArgumentParser(description="textarchive command line utility.")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # --- archive Command ---
    archive_parser = subparsers.add_parser('archive', help='Archive files with various options')
    archive_parser.add_argument('directory', type=str, help='Directory containing files to archive')
    archive_parser.add_argument('output_file', type=str, help='Path to the output file')
    archive_parser.add_argument('--file_types', nargs='+', default=['.yaml', '.py', '.r'], help='List of file extensions to include')
    archive_parser.add_argument('--no-subdirectories', action='store_true', help='Do not include subdirectories')
    archive_parser.add_argument('--extract-code-only', action='store_true', help='Extract only code from Jupyter notebooks')
    archive_parser.add_argument('--llm-friendly', action='store_true', help='Format output for LLM consumption')
    archive_parser.add_argument('--file_prefixes', nargs='+', help='List of filename prefixes to include')

    # --- unpack Command ---
    unpack_parser = subparsers.add_parser('unpack', help='Unpack files from a combined file')
    unpack_parser.add_argument('output_directory', type=str, help='Directory to output the unpacked files')
    unpack_parser.add_argument('combined_file_path', type=str, help='Path to the combined text file')
    unpack_parser.add_argument('--replace_existing', action='store_true', help='Replace existing files in the output directory')

    # --- archive_subdirectories Command ---
    archive_subs_parser = subparsers.add_parser('archive_subdirectories', help='Archive subdirectories of a parent directory')
    archive_subs_parser.add_argument('parent_directory', type=str, help='Parent directory containing subdirectories to archive')
    archive_subs_parser.add_argument('--directories', nargs='+', help='List of subdirectories to archive (default: all subdirectories)', default=None)
    archive_subs_parser.add_argument('--combined_archive_dir', type=str, help='Directory to store the combined archive file (default: parent directory)', default=None)
    archive_subs_parser.add_argument('--combined_archive_name', type=str, help='Name of the combined archive file (default: all_combined_archives.txt)', default='all_combined_archives.txt')
    archive_subs_parser.add_argument('--file_types', nargs='+', default=['.yaml', '.py', '.r'], help='List of file extensions to include in the archive')

    archive_parser.add_argument('--split-output', action='store_true', help='Split the output file into chunks for LLM input')
    archive_parser.add_argument('--split-max-chars', type=int, default=100000, help='Maximum characters per split file')
    archive_parser.add_argument('--split-output-dir', type=str, help='Directory for split files (default: split_<output_file_stem>)')

    args = parser.parse_args()

    if args.command == 'archive':
        archive_files(
            directory=args.directory,
            output_file_path=args.output_file,
            file_types=args.file_types,
            include_subdirectories=not args.no_subdirectories,
            extract_code_only=args.extract_code_only,
            llm_friendly=args.llm_friendly,
            file_prefixes=args.file_prefixes,
            split_output=args.split_output,
            max_chars=args.split_max_chars,
            split_output_dir=args.split_output_dir,
        )
    elif args.command == 'unpack':
        logger.info(f"Unpacking files from {args.combined_file_path} to {args.output_directory} using replace_existing={args.replace_existing}")
        run_unpack(args.output_directory, args.combined_file_path, replace_existing=args.replace_existing)  # Corrected order
    elif args.command == 'archive_subdirectories':
        archive_subdirectories(args.parent_directory, args.directories, args.combined_archive_dir, args.combined_archive_name, args.file_types)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()