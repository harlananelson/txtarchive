# txtarchive/__main__.py
import argparse
import logging
from importlib.metadata import version
from txtarchive.packunpack import archive_files, run_unpack, archive_subdirectories, run_extract_notebooks
from .header import logger

__version__ = version("txtarchive")

def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    epilog = """
Examples:

# Standard Archiving (for later unpacking)

# Archive the txtarchive package (Python, Markdown, YAML files)
# Incorporates the Python package structure of having an outer txtarchive directory and an inner txtarchive directory
python -m txtarchive archive "txtarchive" "txtarchive/txtarchive.txt" \
    --file_types .py .md .yaml \
    --root-files .gitignore setup.py

# Unpack the txtarchive archive
python -m txtarchive unpack "txtarchive/txtarchive.txt" "extracted_txtarchive" --replace_existing

# Archive the update files
python -m txtarchive archive "shell" "shell/shell.txt" \
    --file_types .py .md .yaml \
    --no-subdirectories \
    --file_types .sh .txt \
    --file_prefixes claude-update-lhn requirement

# Unpack shell files
python -m txtarchive unpack "shell.txt" "shell" --replace_existing

# Archive lhn package with subdirectories
# Note: Ensure archive uses forward slashes (e.g., lhn/cohort.py) to create correct subdirectories
python -m txtarchive archive "lhn" "lhn/lhn.txt" \
    --file_types .py .md .yaml \
    --root-files requirements.txt setup.py environment_spark.yaml environment_archive_env.yaml

# Unpack the lhn archive
python -m txtarchive unpack "lhn.txt" "lhn" --replace_existing

# LLM-Friendly Archiving (single file)
# Archive lhn package for LLM use (Python files, no subdirectories)
python -m txtarchive archive "lhn" "lhn-llm-friendly.txt" \
    --file_types .py \
    --no-subdirectories \
    --llm-friendly \
    --extract-code-only

# LLM-Friendly Archiving (split output)
# Archive SickleCell notebooks for LLM use with split output
python -m txtarchive archive "SickleCell" "SickleCell_ADSCreationLLM.txt" \
    --file_types .ipynb .yaml \
    --no-subdirectories \
    --llm-friendly \
    --extract-code-only \
    --split-output \
    --split-output-dir "split_SickleCell"

# LLM-Friendly Archiving with File Prefixes
# Archive specific SickleCell notebooks for LLM use (selected by prefix)
python -m txtarchive archive "SickleCell" "SickleCell_ADSCreationLLM.txt" \
    --file_types .ipynb \
    --no-subdirectories \
    --llm-friendly \
    --extract-code-only \
    --split-output \
    --file_prefixes 011 015

# Archive specific lhn modules for LLM use (selected by prefix)
python -m txtarchive archive "lhn" "lhn-llm-friendly.txt" \
    --file_types .py \
    --no-subdirectories \
    --llm-friendly \
    --extract-code-only \
    --split-output \
    --split-output-dir "split_lhn" \
    --file_prefixes extract resource

# Extract Notebooks from LLM-Friendly Archive
# Extract notebooks from a split archive
python -m txtarchive extract-notebooks "split_SickleCell_ADSCreationLLM" "extracted_notebooks" --replace_existing

# Archive Config Directory (YAML files)
python -m txtarchive archive "config" "config/config-LLM-archive.txt" \
    --file_types .yaml \
    --llm-friendly \
    --split-output \
    --split-output-dir "config/split_config"
"""

    parser = argparse.ArgumentParser(
        description="txtarchive: A utility for archiving and extracting text files and Jupyter notebooks.",
        epilog=epilog,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('--version', action='version', version=f'%(prog)s {__version__}', help='Show the version and exit')

    subparsers = parser.add_subparsers(dest='command', help='Available commands', required=False)

    # --- archive Command ---
    archive_parser = subparsers.add_parser(
        'archive',
        help='Archive files into a single text file',
        description='Combine files from a directory into a text archive, optionally in LLM-friendly format.'
    )
    archive_parser.add_argument(
        'directory',
        type=str,
        help='Directory containing files to archive (input)'
    )
    archive_parser.add_argument(
        'output_file',
        type=str,
        help='Path to the output archive file (output)'
    )
    archive_parser.add_argument(
        '--file_types',
        nargs='+',
        default=['.yaml', '.py', '.r'],
        help='File extensions to include (e.g., .ipynb .py)'
    )
    archive_parser.add_argument(
        '--no-subdirectories',
        action='store_true',
        help='Exclude subdirectories, archive only top-level files'
    )
    archive_parser.add_argument(
        '--extract-code-only',
        action='store_true',
        help='Extract only code cells from Jupyter notebooks'
    )
    archive_parser.add_argument(
        '--llm-friendly',
        action='store_true',
        help='Format archive for LLM input (e.g., no notebook metadata)'
    )
    archive_parser.add_argument(
        '--file_prefixes',
        nargs='+',
        help='Include only files starting with these prefixes (e.g., config- 01)'
    )
    archive_parser.add_argument(
        '--split-output',
        action='store_true',
        help='Split the output archive into chunks of --split-max-chars'
    )
    archive_parser.add_argument(
        '--split-max-chars',
        type=int,
        default=100000,
        help='Maximum characters per split file (default: 100000)'
    )
    archive_parser.add_argument(
        '--split-output-dir',
        type=str,
        help='Directory for split files (default: split_<output_file_stem>)'
    )
    archive_parser.add_argument(
        '--exclude-dirs',
        nargs='+',
        help='Subdirectories to exclude (e.g., build .git old)'
    )
    archive_parser.add_argument(
        '--root-files',
        nargs='+',
        help='Specific root files to include regardless of file_types (e.g., requirements.txt setup.py)'
    )
    archive_parser.add_argument(
        '--include-subdirs',
        nargs='+',
        help='Specific subdirectories to include (e.g., lhn)'
    )

    # --- unpack Command ---
    unpack_parser = subparsers.add_parser(
        'unpack',
        help='Unpack a text archive into individual files',
        description='Extract files from a text archive into a directory.'
    )
    unpack_parser.add_argument(
        'combined_file_path',
        type=str,
        help='Path to the text archive file (input)'
    )
    unpack_parser.add_argument(
        'output_directory',
        type=str,
        help='Directory to save the unpacked files (output)'
    )
    unpack_parser.add_argument(
        '--replace_existing',
        action='store_true',
        help='Replace existing files in the output directory'
    )

    generate_parser = subparsers.add_parser(
        'generate',
        help='Generate a txtarchive archive using an LLM',
        description='Create an archive of Jupyter notebooks based on a study plan and lhn module.'
    )
    generate_parser.add_argument(
        'study_plan_path',
        type=str,
        help='Path to the study plan file (input)'
    )
    generate_parser.add_argument(
        'lhn_archive_path',
        type=str,
        help='Path to the lhn module archive file or split directory (input)'
    )
    generate_parser.add_argument(
        'output_archive_path',
        type=str,
        help='Path to the generated archive file (output)'
    )
    generate_parser.add_argument(
        '--llm-model',
        type=str,
        default='mock',
        help='LLM model to use (default: mock)'
    )

    # --- archive_subdirectories Command ---
    archive_subs_parser = subparsers.add_parser(
        'archive_subdirectories',
        help='Archive subdirectories into separate text files',
        description='Create archives for each subdirectory of a parent directory.'
    )
    archive_subs_parser.add_argument(
        'parent_directory',
        type=str,
        help='Parent directory containing subdirectories to archive (input)'
    )
    archive_subs_parser.add_argument(
        '--directories',
        nargs='+',
        help='Specific subdirectories to archive (default: all)'
    )
    archive_subs_parser.add_argument(
        '--combined_archive_dir',
        type=str,
        help='Directory for combined archive files (default: parent directory)'
    )
    archive_subs_parser.add_argument(
        '--combined_archive_name',
        type=str,
        default='all_combined_archives.txt',
        help='Name of the combined archive file (default: all_combined_archives.txt)'
    )
    archive_subs_parser.add_argument(
        '--file_types',
        nargs='+',
        default=['.yaml', '.py', '.r'],
        help='File extensions to include (e.g., .yaml .py)'
    )

    # --- extract-notebooks Command ---
    extract_nb_parser = subparsers.add_parser(
        'extract-notebooks',
        help='Extract Jupyter notebooks from an LLM-friendly archive',
        description='Reconstruct .ipynb files from an LLM-friendly text archive or a directory of split archive files.'
    )
    extract_nb_parser.add_argument(
        'archive_file_path',
        type=str,
        help='Path to the LLM-friendly archive file or directory of split files (input)'
    )
    extract_nb_parser.add_argument(
        'output_directory',
        type=str,
        help='Directory to save the reconstructed .ipynb files (output)'
    )
    extract_nb_parser.add_argument(
        '--replace_existing',
        action='store_true',
        help='Replace existing .ipynb files in the output directory'
    )

    args = parser.parse_args()

    if not args.command:
        if hasattr(args, 'version'):
            parser.parse_args(['--version'])
        else:
            parser.print_help()
        return

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
            exclude_dirs=args.exclude_dirs,
            root_files=args.root_files,
            include_subdirs=args.include_subdirs,
        )
    elif args.command == 'unpack':
        logger.info(f"Unpacking files from {args.combined_file_path} to {args.output_directory} using replace_existing={args.replace_existing}")
        run_unpack(args.output_directory, args.combined_file_path, replace_existing=args.replace_existing)
    elif args.command == 'archive_subdirectories':
        archive_subdirectories(args.parent_directory, args.directories, args.combined_archive_dir, args.combined_archive_name, args.file_types)
    elif args.command == 'extract-notebooks':
        logger.info(f"Extracting notebooks from {args.archive_file_path} to {args.output_directory} using replace_existing={args.replace_existing}")
        run_extract_notebooks(args.archive_file_path, args.output_directory, replace_existing=args.replace_existing)
    elif args.command == 'generate':
        logger.info(f"Generating archive from {args.study_plan_path} and {args.lhn_archive_path}")
        generate_archive(args.study_plan_path, args.lhn_archive_path, args.output_archive_path, args.llm_model)

if __name__ == "__main__":
    main()