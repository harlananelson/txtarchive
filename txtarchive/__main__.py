# txtarchive/__main__.py
import argparse
import logging
from importlib.metadata import version
from txtarchive.packunpack import archive_files, run_unpack, archive_subdirectories, run_extract_notebooks_and_quarto
from .header import logger

__version__ = version("txtarchive")

def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    epilog = """
Examples:

# unpack
python -m txtarchive unpack "sparktables.txt" "SickleCell-AI" --replace_existing

# Standard Archiving (for later unpacking)
# python -m txtarchive archive "lhnmetadata" "lhnmetadata.txt" --file_types .ipynb --no-subdirectories

# Archive the txtarchive package (Python, Markdown, YAML, Quarto files)
# Incorporates the Python package structure of having an outer txtarchive directory and an inner txtarchive directory
python -m txtarchive archive "txtarchive" "txtarchive/txtarchive.txt" \
    --file_types .py .md .yaml .qmd \
    --root-files .gitignore setup.py

# Unpack the txtarchive archive
python -m txtarchive unpack "txtarchive/txtarchive.txt" "extracted_txtarchive" --replace_existing

# Archive the update files
python -m txtarchive archive "shell" "shell/shell.txt" \
    --file_types .py .md .yaml .qmd \
    --no-subdirectories \
    --file_types .sh .txt \
    --file_prefixes claude-update-lhn requirement

# Unpack shell files
python -m txtarchive unpack "shell.txt" "shell" --replace_existing

# Archive lhn package with subdirectories
# Note: Ensure archive uses forward slashes (e.g., lhn/cohort.py) to create correct subdirectories
python -m txtarchive archive "lhn" "lhn/lhn.txt" \
    --file_types .py .md .yaml .qmd \
    --root-files requirements.txt setup.py environment_spark.yaml environment_archive_env.yaml

# Unpack the lhn archive
python -m txtarchive unpack "lhn.txt" "lhn" --replace_existing

# LLM-Friendly Archiving (single file)
# Archive lhn package for LLM use (Python and Quarto files, no subdirectories)
python -m txtarchive archive "lhn" "lhn-llm-friendly.txt" \
    --file_types .py .qmd \
    --no-subdirectories \
    --llm-friendly \
    --split-output \
    --extract-code-only \
    --split-output-dir "split_lhn"

# LLM-Friendly Archiving (split output)
# Archive SickleCell notebooks and Quarto files for LLM use with split output
python -m txtarchive archive "SickleCell" "SickleCell_ADSCreationLLM.txt" \
    --file_types .ipynb .qmd .yaml \
    --llm-friendly \
    --extract-code-only \
    --split-output \
    --split-output-dir "split_SickleCell"

# LLM-Friendly Archiving with File Prefixes
# Archive specific SickleCell notebooks and Quarto files for LLM use (selected by prefix)
python -m txtarchive archive "SickleCell" "SickleCell_ADSCreationLLM.txt" \
    --file_types .ipynb .qmd \
    --no-subdirectories \
    --llm-friendly \
    --extract-code-only \
    --split-output \
    --file_prefixes 011-Demographics 015-Compile-EHR 016-Labs-to-show 017-Find-heart 060-Create-ADS 065-Create-feature 066-Create-feature 067-Create-Features 018-VIP 110-Sickle-Study-dataset-86424

# Archive specific lhn modules and Quarto files for LLM use (selected by prefix)
python -m txtarchive archive "lhn" "lhn-llm-friendly.txt" \
    --file_types .py .qmd \
    --no-subdirectories \
    --llm-friendly \
    --extract-code-only \
    --split-output \
    --split-output-dir "split_lhn" \
    --file_prefixes extract resource

# Extract Notebooks and Quarto Files from LLM-Friendly Archive
# Extract notebooks and Quarto files from a split archive
python -m txtarchive extract-notebooks-and-quarto "split_SickleCell_ADSCreationLLM" "extracted_files" --replace_existing

# Archive Config Directory (YAML and Quarto files)
python -m txtarchive archive "config" "config/config-LLM-archive.txt" \
    --file_types .yaml .qmd \
    --llm-friendly \
    --split-output \
    --split-output-dir "config/split_config"
"""

    parser = argparse.ArgumentParser(
        description="txtarchive: A utility for archiving and extracting text files, Jupyter notebooks, and Quarto Markdown files.",
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
        default=['.yaml', '.py', '.r', '.ipynb', '.qmd'],
        help='File extensions to include (e.g., .ipynb .qmd .py)'
    )
    archive_parser.add_argument(
        '--no-subdirectories',
        action='store_true',
        help='Exclude subdirectories, archive only top-level files'
    )
    archive_parser.add_argument(
        '--extract-code-only',
        action='store_true',
        help='Extract only code cells from Jupyter notebooks and code blocks from Quarto files'
    )
    archive_parser.add_argument(
        '--llm-friendly',
        action='store_true',
        help='Format archive for LLM input (e.g., no notebook metadata, only code blocks for Quarto)'
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
        default=['.yaml', '.py', '.r', '.ipynb', '.qmd'],
        help='File extensions to include (e.g., .yaml .py .qmd)'
    )

    # --- extract-notebooks-and-quarto Command ---
    extract_nb_parser = subparsers.add_parser(
        'extract-notebooks-and-quarto',
        help='Extract Jupyter notebooks and Quarto Markdown files from an LLM-friendly archive',
        description='Reconstruct .ipynb and .qmd files from an LLM-friendly text archive or a directory of split archive files.'
    )
    extract_nb_parser.add_argument(
        'archive_file_path',
        type=str,
        help='Path to the LLM-friendly archive file or directory of split files (input)'
    )
    extract_nb_parser.add_argument(
        'output_directory',
        type=str,
        help='Directory to save the reconstructed .ipynb and .qmd files (output)'
    )
    extract_nb_parser.add_argument(
        '--replace_existing',
        action='store_true',
        help='Replace existing .ipynb and .qmd files in the output directory'
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
    elif args.command == 'extract-notebooks-and-quarto':
        logger.info(f"Extracting notebooks and Quarto files from {args.archive_file_path} to {args.output_directory} using replace_existing={args.replace_existing}")
        run_extract_notebooks_and_quarto(args.archive_file_path, args.output_directory, replace_existing=args.replace_existing)
    elif args.command == 'generate':
        logger.info(f"Generating archive from {args.study_plan_path} and {args.lhn_archive_path}")
        generate_archive(args.study_plan_path, args.lhn_archive_path, args.output_archive_path, args.llm_model)

if __name__ == "__main__":
    main()