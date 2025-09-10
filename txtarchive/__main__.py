# txtarchive/__main__.py
import argparse
import logging
from importlib.metadata import version
from txtarchive.packunpack import archive_files, run_unpack, archive_subdirectories, run_extract_notebooks, run_extract_notebooks_and_quarto
import os
from txtarchive.ask_sage import ingest_document
from .header import logger

__version__ = version("txtarchive")

def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    epilog = """
Examples:
# Archive Jupyter notebooks and Quarto files (LLM-friendly)
python -m txtarchive archive "lhnmetadata" "lhnmetadata/lhnmetadata.txt" \
    --file_types .ipynb .qmd --no-subdirectories --llm-friendly --extract-code-only

# Archive Jupyter notebooks (standard mode with TOC)
python -m txtarchive archive "lhnmetadata" "lhnmetadata/lhnmetadata.txt" \
    --file_types .ipynb --no-subdirectories

# Extract notebooks and Quarto files (LLM-friendly or standard archive)
python -m txtarchive extract-notebooks-and-quarto "lhnmetadata/lhnmetadata.txt" "lhynmetadata" --replace_existing
"""

    # [Rest of the file unchanged: parser setup, commands for archive, unpack, generate, archive_subdirectories, extract-notebooks, extract-notebooks-and-quarto]

    parser = argparse.ArgumentParser(
        description="txtarchive: A utility for archiving and extracting text files, Jupyter notebooks, and Quarto files.",
        epilog=epilog,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('--version', action='version', version=f'%(prog)s {__version__}', help='Show the version and exit')

    subparsers = parser.add_subparsers(dest='command', help='Available commands', required=False)

    # Add a subcommand for document ingestion
    ingest_parser = subparsers.add_parser("ingest", help="Ingest a document into Ask Sage")
    ingest_parser.add_argument(
        "--file", required=True, help="Path to the document to be ingested"
    )

    # Archive Command
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
        help='File extensions to include (e.g., .ipynb .qmd)'
    )
    archive_parser.add_argument(
        '--no-subdirectories',
        action='store_true',
        help='Exclude subdirectories, archive only top-level files'
    )
    archive_parser.add_argument(
        '--extract-code-only',
        action='store_true',
        help='Extract code and Markdown cells from Jupyter notebooks'
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

    # Unpack Command
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

    # Generate Command
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

    # Archive Subdirectories Command
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

    # Extract Notebooks Command
    extract_nb_parser = subparsers.add_parser(
        'extract-notebooks',
        help='Extract Jupyter notebooks from an LLM-friendly or standard archive',
        description='Reconstruct .ipynb files from an LLM-friendly or standard text archive or a directory of split archive files.'
    )
    extract_nb_parser.add_argument(
        'archive_file_path',
        type=str,
        help='Path to the archive file or directory of split files (input)'
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

    # Extract Notebooks and Quarto Command
    extract_nbq_parser = subparsers.add_parser(
        'extract-notebooks-and-quarto',
        help='Extract Jupyter notebooks and Quarto files from an LLM-friendly archive',
        description='Reconstruct .ipynb and .qmd files from an LLM-friendly text archive or a directory of split archive files, based on file extensions.'
    )
    extract_nbq_parser.add_argument(
        'archive_file_path',
        type=str,
        help='Path to the archive file or directory of split files (input)'
    )
    extract_nbq_parser.add_argument(
        'output_directory',
        type=str,
        help='Directory to save the reconstructed .ipynb and .qmd files (output)'
    )
    extract_nbq_parser.add_argument(
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

    
    # ask_sage ingestion handling
    if args.command == "ingest":
        # Handle the "ingest" command
        try:
            response = ingest_document(args.file)
            print("Document ingested successfully!")
            print("Response:", response)
        except Exception as e:
            print(f"Error: {e}")
    else:
        parser.print_help()


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
    elif args.command == 'extract-notebooks-and-quarto':
        logger.info(f"Extracting notebooks and Quarto files from {args.archive_file_path} to {args.output_directory} using replace_existing={args.replace_existing}")
        run_extract_notebooks_and_quarto(args.archive_file_path, args.output_directory, replace_existing=args.replace_existing)
    elif args.command == 'generate':
        logger.info(f"Generating archive from {args.study_plan_path} and {args.lhn_archive_path}")
        generate_archive(args.study_plan_path, args.lhn_archive_path, args.output_archive_path, args.llm_model)

if __name__ == "__main__":
    main()