# txtarchive/__main__.py
import argparse
import logging
from importlib.metadata import version
from txtarchive.packunpack import archive_files, run_unpack, archive_subdirectories, run_extract_notebooks, run_extract_notebooks_and_quarto
import os
from txtarchive.ask_sage import ingest_document
from .header import logger

__version__ = version("txtarchive")

def handle_ingestion_response(response_data, file_path):
    """
    Handle the response from ingest_document with robust error checking.
    
    Args:
        response_data: The response from ingest_document
        file_path: Path of the file being ingested (for logging)
    
    Returns:
        bool: True if ingestion was successful, False otherwise
    """
    if not response_data:
        logger.error(f"⚠️ No response received for {file_path}")
        return False
    
    # Check for successful embedding creation
    if response_data.get("embedding") is not None:
        logger.info(f"✅ Successfully ingested {file_path}")
        return True
    
    # Check for error messages in response
    error_message = response_data.get("response", "Unknown API error")
    if "content too long" in str(error_message).lower():
        logger.error(f"⚠️ Content too long for {file_path}. Consider splitting or reducing file size.")
    else:
        logger.error(f"⚠️ Failed to ingest {file_path}. Reason: {error_message}")
    
    return False

def archive_and_ingest(
    directory,
    output_file_path,
    file_types=[".yaml", ".py", ".r", ".ipynb", ".qmd"],
    include_subdirectories=True,
    extract_code_only=False,
    file_prefixes=None,
    llm_friendly=True,  # Default to LLM-friendly for ingestion
    split_output=False,
    max_tokens=75000,
    split_output_dir=None,
    exclude_dirs=None,
    root_files=None,
    include_subdirs=None,
    ingestion_method="auto",
    remove_archive=False
):
    """
    Archive files and then ingest them into Ask Sage.
    
    Args:
        ingestion_method (str): "directory", "archive", or "auto"
            - "directory": Ingest files directly from directory
            - "archive": Create archive first, then ingest
            - "auto": Automatically choose based on project size
        remove_archive (bool): Whether to remove the archive file after ingestion
    """
    from pathlib import Path
    
    directory = Path(directory)
    output_file_path = Path(output_file_path)
    
    # Ensure output directory exists
    output_file_path.parent.mkdir(parents=True, exist_ok=True)
    
    if ingestion_method == "auto":
        # Count files to decide method
        file_count = 0
        total_size = 0
        
        for path in directory.rglob("*") if include_subdirectories else directory.glob("*"):
            if path.is_file() and path.suffix in file_types:
                file_count += 1
                try:
                    total_size += path.stat().st_size
                except:
                    pass
        
        # Use directory method for small projects, archive for large ones
        if file_count <= 10 and total_size < 1024 * 1024:  # < 1MB
            ingestion_method = "directory"
            logger.info(f"Auto-selected directory method ({file_count} files, {total_size/1024:.1f}KB)")
        else:
            ingestion_method = "archive"
            logger.info(f"Auto-selected archive method ({file_count} files, {total_size/1024:.1f}KB)")
    
    if ingestion_method == "directory":
        # Ingest files directly
        logger.info("Ingesting files directly from directory")
        
        success_count = 0
        total_files = 0
        
        for path in directory.rglob("*") if include_subdirectories else directory.glob("*"):
            if path.is_file() and path.suffix in file_types:
                if not path.name.startswith((".", "#")):
                    total_files += 1
                    try:
                        logger.info(f"Ingesting {path}")
                        response_data = ingest_document(str(path))
                        
                        if handle_ingestion_response(response_data, str(path)):
                            success_count += 1
                            
                    except Exception as e:
                        logger.error(f"Exception occurred while ingesting {path}: {e}")
        
        logger.info(f"Directory ingestion complete: {success_count}/{total_files} files successfully ingested")
        return
    
    elif ingestion_method == "archive":
        # Create archive first, then ingest
        logger.info("Creating archive for ingestion")
        
        archive_files(
            directory=directory,
            output_file_path=output_file_path,
            file_types=file_types,
            include_subdirectories=include_subdirectories,
            extract_code_only=extract_code_only,
            llm_friendly=llm_friendly,
            file_prefixes=file_prefixes,
            split_output=split_output,
            max_tokens=max_tokens,
            split_output_dir=split_output_dir,
            exclude_dirs=exclude_dirs,
            root_files=root_files,
            include_subdirs=include_subdirs,
        )
        
        # Ingest the main archive ONLY if not splitting
        if not split_output:
            try:
                logger.info(f"Ingesting single archive: {output_file_path}")
                response_data = ingest_document(str(output_file_path))
                
                if not handle_ingestion_response(response_data, str(output_file_path)):
                    logger.error("Failed to ingest main archive")
                    return
                    
            except Exception as e:
                logger.error(f"Failed to ingest archive: {e}")
                raise
        
        # Handle split files if they exist
        if split_output:
            split_dir = Path(split_output_dir) if split_output_dir else output_file_path.parent / f"split_{output_file_path.stem}"
            if split_dir.exists():
                logger.info("Ingesting split files")
                split_files = sorted(split_dir.glob("*.txt"))
                success_count = 0
                
                for split_file in split_files:
                    try:
                        logger.info(f"Ingesting split file: {split_file}")
                        response_data = ingest_document(str(split_file))
                        
                        if handle_ingestion_response(response_data, str(split_file)):
                            success_count += 1
                            
                    except Exception as e:
                        logger.error(f"Exception occurred while ingesting {split_file}: {e}")
                
                logger.info(f"Split file ingestion complete: {success_count}/{len(split_files)} files successfully ingested")
        
        # Clean up archive if requested
        if remove_archive:
            output_file_path.unlink()
            logger.info(f"Removed archive file: {output_file_path}")
        
        logger.info("Archive ingestion complete")

def add_common_archive_args(parser):
    """Add common archive arguments to a parser to reduce duplication."""
    parser.add_argument(
        'directory',
        type=str,
        help='Directory containing files to archive (input)'
    )
    parser.add_argument(
        'output_file',
        type=str,
        help='Path to the output archive file (output)'
    )
    parser.add_argument(
        '--file_types',
        nargs='+',
        default=['.yaml', '.py', '.r', '.ipynb', '.qmd'],
        help='File extensions to include (e.g., .ipynb .qmd)'
    )
    parser.add_argument(
        '--no-subdirectories',
        action='store_true',
        help='Exclude subdirectories, archive only top-level files'
    )
    parser.add_argument(
        '--extract-code-only',
        action='store_true',
        help='Extract code and Markdown cells from Jupyter notebooks'
    )
    parser.add_argument(
        '--llm-friendly',
        action='store_true',
        help='Format archive for LLM input (e.g., no notebook metadata)'
    )
    parser.add_argument(
        '--file_prefixes',
        nargs='+',
        help='Include only files starting with these prefixes (e.g., config- 01)'
    )
    parser.add_argument(
        '--split-output',
        action='store_true',
        help='Split the output archive into chunks'
    )
    parser.add_argument(
        '--max-tokens',
        type=int,
        default=100000,
        help='Maximum tokens per split file (default: 100000)'
    )
    parser.add_argument(
        '--split-output-dir',
        type=str,
        help='Directory for split files (default: split_<output_file_stem>)'
    )
    parser.add_argument(
        '--exclude-dirs',
        nargs='+',
        help='Subdirectories to exclude (e.g., build .git old .venv __pycache__)'
    )
    parser.add_argument(
        '--root-files',
        nargs='+',
        help='Specific root files to include regardless of file_types (e.g., requirements.txt setup.py)'
    )
    parser.add_argument(
        '--include-subdirs',
        nargs='+',
        help='Specific subdirectories to include (e.g., lhn)'
    )

def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    epilog = """
Examples:
# Archive Jupyter notebooks and Quarto files (LLM-friendly)
python -m txtarchive archive "lhnmetadata" "lhnmetadata/lhnmetadata.txt" \
    --file_types .ipynb .qmd --no-subdirectories --llm-friendly --extract-code-only

# Archive with exclusions and splitting
python -m txtarchive archive "txtarchive" "archive/txtarchive.txt" \
    --file_types .py .yaml .md \
    --root-files pyproject.toml README.md \
    --exclude-dirs .venv __pycache__ .git \
    --split-output --max-tokens 75000

# Archive and ingest into Ask Sage
python -m txtarchive archive-and-ingest "txtarchive" "archive/txtarchive.txt" \
    --file_types .py .yaml .md \
    --root-files pyproject.toml README.md \
    --exclude-dirs .venv __pycache__ .git \
    --llm-friendly --extract-code-only \
    --max-tokens 75000 --ingestion-method auto

# Just ingest an existing document
python -m txtarchive ingest --file "archive/txtarchive.txt"
"""

    parser = argparse.ArgumentParser(
        description="txtarchive: A utility for archiving and extracting text files, Jupyter notebooks, and Quarto files.",
        epilog=epilog,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('--version', action='version', version=f'%(prog)s {__version__}', help='Show the version and exit')

    subparsers = parser.add_subparsers(dest='command', help='Available commands', required=False)

    # Ingest Command
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
    add_common_archive_args(archive_parser)

    # Archive and Ingest Command
    archive_ingest_parser = subparsers.add_parser(
        'archive-and-ingest',
        help='Archive files and ingest into Ask Sage',
        description='Create an archive and immediately ingest it into Ask Sage.'
    )
    add_common_archive_args(archive_ingest_parser)
    
    # Add unique arguments for archive-and-ingest
    archive_ingest_parser.add_argument(
        '--ingestion-method',
        choices=['directory', 'archive', 'auto'],
        default='auto',
        help='How to ingest: directory (file by file), archive (create archive first), or auto (decide based on size)'
    )
    archive_ingest_parser.add_argument(
        '--rm-archive',
        action='store_true',
        help='Remove the archive file after ingestion'
    )
    
    # Set default for llm-friendly in archive-and-ingest
    archive_ingest_parser.set_defaults(llm_friendly=True)

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

    # Handle commands
    if args.command == "ingest":
        try:
            response_data = ingest_document(args.file)
            
            if handle_ingestion_response(response_data, args.file):
                print("Document ingested successfully!")
                if response_data:
                    print("Response:", response_data)
            else:
                print("Document ingestion failed. Check logs for details.")
                
        except Exception as e:
            print(f"Error: {e}")
            
    elif args.command == 'archive':
        archive_files(
            directory=args.directory,
            output_file_path=args.output_file,
            file_types=args.file_types,
            include_subdirectories=not args.no_subdirectories,
            extract_code_only=args.extract_code_only,
            llm_friendly=args.llm_friendly,
            file_prefixes=args.file_prefixes,
            split_output=args.split_output,
            max_tokens=args.max_tokens,
            split_output_dir=args.split_output_dir,
            exclude_dirs=args.exclude_dirs,
            root_files=args.root_files,
            include_subdirs=args.include_subdirs,
        )
        
    elif args.command == 'archive-and-ingest':
        archive_and_ingest(
            directory=args.directory,
            output_file_path=args.output_file,
            file_types=args.file_types,
            include_subdirectories=not args.no_subdirectories,
            extract_code_only=args.extract_code_only,
            llm_friendly=getattr(args, 'llm_friendly', True),  # Default to True for ingestion
            file_prefixes=args.file_prefixes,
            split_output=args.split_output,
            max_tokens=args.max_tokens,
            split_output_dir=args.split_output_dir,
            exclude_dirs=args.exclude_dirs,
            root_files=args.root_files,
            include_subdirs=args.include_subdirs,
            ingestion_method=args.ingestion_method,
            remove_archive=args.rm_archive,
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
        
    elif args.command == 'convert-word':
        from pathlib import Path
        input_path = Path(args.input_path)
        
        if input_path.is_file():
            # Convert single file
            output_path = args.output_path
            if output_path is None:
                output_path = input_path.with_suffix('.md')
            
            try:
                markdown_content = convert_word_to_markdown(input_path, method=args.method)
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(markdown_content)
                logger.info(f"Successfully converted: {input_path} -> {output_path}")
            except Exception as e:
                logger.error(f"Failed to convert {input_path}: {e}")
                
        elif input_path.is_dir():
            # Convert directory of files
            output_dir = args.output_path or input_path
            converted_files = convert_word_documents_in_directory(
                input_path, 
                output_dir, 
                method=args.method,
                replace_existing=args.replace_existing
            )
            logger.info(f"Converted {len(converted_files)} Word documents in {input_path}")
        else:
            logger.error(f"Input path does not exist: {input_path}")
        
    elif args.command == 'generate':
        logger.info(f"Generating archive from {args.study_plan_path} and {args.lhn_archive_path}")
        from txtarchive.packunpack import generate_archive
        generate_archive(args.study_plan_path, args.lhn_archive_path, args.output_archive_path, args.llm_model)
        
    else:
        parser.print_help()

if __name__ == "__main__":
    main()