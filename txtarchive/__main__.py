# txtarchive/__main__.py
import argparse
import logging
from importlib.metadata import version
from txtarchive.packunpack import archive_files, run_unpack, archive_subdirectories, run_extract_notebooks, run_extract_notebooks_and_quarto
import os
import json as json_module
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
        logger.error(f"No response received for {file_path}")
        return False

    # Check for successful response: embedding present, or no error field
    if response_data.get("embedding") is not None:
        logger.info(f"Successfully ingested {file_path}")
        return True

    # Some endpoints return success without an embedding field
    error_message = response_data.get("response", "")
    if not error_message or (isinstance(error_message, str) and "error" not in error_message.lower()):
        logger.info(f"Successfully ingested {file_path}")
        return True

    # Check for known error patterns
    if "content too long" in str(error_message).lower():
        logger.error(f"Content too long for {file_path}. Consider splitting or reducing file size.")
    else:
        logger.error(f"Failed to ingest {file_path}. Reason: {error_message}")

    return False

def archive_and_ingest(
    directory,
    output_file_path,
    file_types=[".yaml", ".py", ".r", ".ipynb", ".qmd"],
    include_subdirectories=True,
    extract_code_only=False,
    file_prefixes=None,
    llm_friendly=True,
    split_output=False,
    max_tokens=75000,
    split_output_dir=None,
    exclude_dirs=None,
    root_files=None,
    include_subdirs=None,
    ingestion_method="auto",
    remove_archive=False,
    endpoint="train",           # Add this parameter
    test_endpoints=False,        # Add this parameter
    explicit_files=None,  # ← ADD THIS LINE
):
    """
    Archive files and then ingest them into Ask Sage.
    
    Args:
        ingestion_method (str): "directory", "archive", or "auto"
            - "directory": Ingest files directly from directory
            - "archive": Create archive first, then ingest
            - "auto": Automatically choose based on project size
        remove_archive (bool): Whether to remove the archive file after ingestion
        endpoint (str): Ask Sage endpoint to use ('train', 'chat', 'embed', 'upload')
        test_endpoints (bool): Whether to test all endpoints before ingestion
    """
    from pathlib import Path
    from .ask_sage import ingest_document, test_endpoints as test_all_endpoints
    
    directory = Path(directory)
    output_file_path = Path(output_file_path)
    
    # Ensure output directory exists
    output_file_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Test endpoints if requested
    if test_endpoints:
        logger.info("Testing all Ask Sage endpoints...")
        test_file = directory / "README.md"  # Use a common file for testing
        if not test_file.exists():
            # Find any suitable file for testing
            for file_type in file_types:
                test_files = list(directory.glob(f"*{file_type}"))
                if test_files:
                    test_file = test_files[0]
                    break
        
        if test_file.exists():
            try:
                results = test_all_endpoints(str(test_file))
                
                print("\n=== ENDPOINT TEST RESULTS ===")
                for endpoint_name, result in results.items():
                    status = "✅ SUCCESS" if result['success'] else "❌ FAILED"
                    print(f"{endpoint_name:10} | {status} | Status: {result.get('status_code', 'N/A')}")
                    if result.get('error'):
                        print(f"           | Error: {result['error'][:100]}...")
                
                # Recommend best endpoint
                successful_endpoints = [name for name, result in results.items() if result['success']]
                if successful_endpoints:
                    print(f"\n✅ Recommended endpoints: {', '.join(successful_endpoints)}")
                    if endpoint not in successful_endpoints:
                        print(f"⚠️  Warning: Your selected endpoint '{endpoint}' may not work optimally")
                        print(f"   Consider using: {successful_endpoints[0]}")
                else:
                    print("\n❌ No endpoints succeeded. Check your ACCESS_TOKEN and network connection.")
                    return
                    
            except Exception as e:
                logger.error(f"Endpoint testing failed: {e}")
                print(f"Endpoint testing failed: {e}")
                return
        else:
            logger.warning("No suitable test file found for endpoint testing")
    
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
        logger.info(f"Ingesting files directly from directory using '{endpoint}' endpoint")
        
        success_count = 0
        total_files = 0
        
        for path in directory.rglob("*") if include_subdirectories else directory.glob("*"):
            if path.is_file() and path.suffix in file_types:
                if not path.name.startswith((".", "#")):
                    total_files += 1
                    try:
                        logger.info(f"Ingesting {path} via {endpoint} endpoint")
                        # Here you'd need to modify ingest_document to accept endpoint parameter
                        response_data = ingest_document(str(path), endpoint=endpoint)
                        
                        if handle_ingestion_response(response_data, str(path)):
                            success_count += 1
                            
                    except Exception as e:
                        logger.error(f"Exception occurred while ingesting {path}: {e}")
        
        logger.info(f"Directory ingestion complete: {success_count}/{total_files} files successfully ingested")
        return
    
    elif ingestion_method == "archive":
        # Create archive first, then ingest
        logger.info(f"Creating archive for ingestion via '{endpoint}' endpoint")
        
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
            explicit_files=explicit_files,  
        )
        
        # Ingest the main archive ONLY if not splitting
        if not split_output:
            try:
                logger.info(f"Ingesting single archive via '{endpoint}' endpoint: {output_file_path}")
                response_data = ingest_document(str(output_file_path), endpoint=endpoint)
                
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
                logger.info(f"Ingesting split files via '{endpoint}' endpoint")
                split_files = sorted(split_dir.glob("*.txt"))
                success_count = 0
                
                for split_file in split_files:
                    try:
                        logger.info(f"Ingesting split file via '{endpoint}' endpoint: {split_file}")
                        response_data = ingest_document(str(split_file), endpoint=endpoint)
                        
                        if handle_ingestion_response(response_data, str(split_file)):
                            success_count += 1
                            
                    except Exception as e:
                        logger.error(f"Exception occurred while ingesting {split_file}: {e}")
                
                logger.info(f"Split file ingestion complete: {success_count}/{len(split_files)} files successfully ingested")
        
        # Clean up archive if requested
        if remove_archive:
            output_file_path.unlink()
            logger.info(f"Removed archive file: {output_file_path}")
        
        logger.info(f"Archive ingestion complete via '{endpoint}' endpoint")

 
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
    parser.add_argument(
        '--explicit-files',
        nargs='+',
        metavar='FILE',
        help='Explicit list of files to archive (relative to source directory or absolute paths). '
             'Bypasses directory scanning and archives only these specific files. '
             'Example: --explicit-files file1.ipynb file2.R "file with spaces.py"'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be archived without writing any files. '
             'Reports file count, estimated size, and lists included/excluded files.'
    )

def _describe_parser(parser, name=None):
    """Extract a machine-readable description of a parser's arguments."""
    result = {}
    if name:
        result["command"] = name
    result["description"] = parser.description or parser.format_usage()

    args_list = []
    for action in parser._actions:
        if isinstance(action, argparse._HelpAction):
            continue
        if isinstance(action, argparse._VersionAction):
            continue
        if isinstance(action, argparse._SubParsersAction):
            continue

        arg_info = {
            "name": action.dest,
            "flags": action.option_strings if action.option_strings else [action.dest],
            "required": action.required if hasattr(action, 'required') else not action.option_strings,
            "description": action.help or "",
        }

        if action.type is not None:
            arg_info["type"] = action.type.__name__
        elif isinstance(action, argparse._StoreTrueAction):
            arg_info["type"] = "bool"
        elif isinstance(action, argparse._StoreFalseAction):
            arg_info["type"] = "bool"
        else:
            arg_info["type"] = "string"

        if action.default is not argparse.SUPPRESS and action.default is not None:
            arg_info["default"] = action.default
        if action.choices:
            arg_info["choices"] = list(action.choices)
        if action.nargs:
            arg_info["nargs"] = str(action.nargs)

        args_list.append(arg_info)

    result["arguments"] = args_list
    return result


def main():
    # Configure logging for the application (the library only creates a NullHandler)
    app_logger = logging.getLogger('txtarchive')
    app_logger.setLevel(logging.INFO)
    if not app_logger.handlers or isinstance(app_logger.handlers[0], logging.NullHandler):
        # Remove NullHandler and add real handlers
        app_logger.handlers.clear()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        app_logger.addHandler(console_handler)
        file_handler = logging.FileHandler('txtarchive.log')
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        app_logger.addHandler(file_handler)

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

    ingest_parser.add_argument("--endpoint", choices=['train', 'chat', 'embed', 'upload'], default='train', help="Ask Sage endpoint to use")
    ingest_parser.add_argument("--test-endpoints", action='store_true', help="Test all endpoints to find the best one")

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
    
    archive_ingest_parser.add_argument('--endpoint', choices=['train', 'chat', 'embed', 'upload'], default='train', help='Ask Sage endpoint to use')
    archive_ingest_parser.add_argument('--test-endpoints', action='store_true', help='Test different endpoints to find the best token limits')
    
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
    unpack_parser.add_argument(
        '--kernel',
        type=str,
        default=None,
        help='Jupyter kernel name for notebooks (e.g. r_env, pyspark-lhn-dev). Overrides auto-detection.'
    )
    unpack_parser.add_argument(
        '--force',
        action='store_true',
        help='Force unpack even for LLM-friendly archives (best-effort, lossy extraction)'
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
    extract_nb_parser.add_argument(
        '--kernel',
        type=str,
        default=None,
        help='Jupyter kernel name for notebooks (e.g. r_env, pyspark-lhn-dev). Overrides auto-detection.'
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
    extract_nbq_parser.add_argument(
        '--kernel',
        type=str,
        default=None,
        help='Jupyter kernel name for notebooks (e.g. r_env, pyspark-lhn-dev). Overrides auto-detection.'
    )

    # Convert Word Command
    convert_word_parser = subparsers.add_parser(
        'convert-word',
        help='Convert Word documents (.docx) to markdown',
        description='Convert Word documents to clean markdown format.'
    )
    convert_word_parser.add_argument(
        'input_path',
        type=str,
        help='Path to a .docx file or directory containing .docx files'
    )
    convert_word_parser.add_argument(
        'output_path',
        type=str,
        nargs='?',
        default=None,
        help='Output path for markdown file (default: same name with .md extension)'
    )
    convert_word_parser.add_argument(
        '--method',
        choices=['auto', 'mammoth', 'pandoc', 'docx', 'basic'],
        default='auto',
        help='Conversion method (default: auto)'
    )
    convert_word_parser.add_argument(
        '--replace-existing',
        action='store_true',
        help='Overwrite existing markdown files'
    )

    # Convert HTML Command
    convert_html_parser = subparsers.add_parser(
        'convert-html',
        help='Convert HTML files to markdown',
        description='Convert Quarto-rendered or other HTML files to clean markdown, with optional base64 image extraction.'
    )
    convert_html_parser.add_argument(
        'input_path',
        type=str,
        help='Path to an .html file or directory containing .html files'
    )
    convert_html_parser.add_argument(
        'output_path',
        type=str,
        nargs='?',
        default=None,
        help='Output path for markdown file (default: same name with .md extension)'
    )
    convert_html_parser.add_argument(
        '--method',
        choices=['auto', 'pandoc', 'regex'],
        default='auto',
        help='Conversion method (default: auto)'
    )
    convert_html_parser.add_argument(
        '--no-extract-images',
        action='store_true',
        help='Do not extract base64 images to files; use placeholders instead'
    )
    convert_html_parser.add_argument(
        '--image-dir',
        type=str,
        default=None,
        help='Output directory for extracted images (default: <input_stem>_images/)'
    )
    convert_html_parser.add_argument(
        '--replace-existing',
        action='store_true',
        help='Overwrite existing markdown files'
    )

    # --- extract-report subcommand ---
    extract_report_parser = subparsers.add_parser(
        'extract-report',
        help='Extract structured data from report-spec HTML',
        description='Parse Quarto-rendered HTML reports following the 12-section report-spec format. '
                    'Extracts metadata, tables, model cards, and figures into YAML, JSON, or markdown.',
    )
    extract_report_parser.add_argument(
        'input_path',
        type=str,
        help='Path to the Quarto-rendered HTML file'
    )
    extract_report_parser.add_argument(
        '--format',
        choices=['yaml', 'json', 'markdown'],
        default='yaml',
        dest='output_format',
        help='Output format (default: yaml)'
    )
    extract_report_parser.add_argument(
        '--sections',
        type=str,
        default=None,
        help='Comma-separated section numbers to extract (e.g., 0,1,6). Default: all'
    )
    extract_report_parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='Output file path (default: stdout)'
    )
    extract_report_parser.add_argument(
        '--strict',
        action='store_true',
        help='Fail if expected sections are missing (default: best-effort)'
    )

    # Describe Command (machine-readable CLI schema)
    describe_parser = subparsers.add_parser(
        'describe',
        help='Output machine-readable JSON description of CLI commands and options',
        description='Dump the full CLI surface as JSON for agent/tool integration.'
    )
    describe_parser.add_argument(
        'describe_command',
        nargs='?',
        default=None,
        help='Specific command to describe (default: all commands)'
    )
    describe_parser.add_argument(
        '--format',
        choices=['json'],
        default='json',
        dest='describe_format',
        help='Output format (default: json)'
    )

    # Store subparsers for describe command access
    _subparser_map = {
        'archive': archive_parser,
        'unpack': unpack_parser,
        'archive-and-ingest': archive_ingest_parser,
        'ingest': ingest_parser,
        'generate': generate_parser,
        'archive_subdirectories': archive_subs_parser,
        'extract-notebooks': extract_nb_parser,
        'extract-notebooks-and-quarto': extract_nbq_parser,
        'convert-word': convert_word_parser,
        'convert-html': convert_html_parser,
        'extract-report': extract_report_parser,
        'describe': describe_parser,
    }

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # --- Command handler functions ---

    def handle_ingest(args):
        try:
            response_data = ingest_document(
                args.file,
                endpoint=getattr(args, 'endpoint', 'train'),
            )
            if handle_ingestion_response(response_data, args.file):
                print("Document ingested successfully!")
            else:
                print("Document ingestion failed. Check logs for details.")
        except Exception as e:
            print(f"Error: {e}")

    def handle_archive(args):
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
            explicit_files=getattr(args, 'explicit_files', None),
            dry_run=getattr(args, 'dry_run', False),
        )

    def handle_archive_and_ingest(args):
        archive_and_ingest(
            directory=args.directory,
            output_file_path=args.output_file,
            file_types=args.file_types,
            include_subdirectories=not args.no_subdirectories,
            extract_code_only=args.extract_code_only,
            llm_friendly=getattr(args, 'llm_friendly', True),
            file_prefixes=args.file_prefixes,
            split_output=args.split_output,
            max_tokens=args.max_tokens,
            split_output_dir=args.split_output_dir,
            exclude_dirs=args.exclude_dirs,
            root_files=args.root_files,
            include_subdirs=args.include_subdirs,
            ingestion_method=args.ingestion_method,
            remove_archive=args.rm_archive,
            endpoint=getattr(args, 'endpoint', 'train'),
            test_endpoints=getattr(args, 'test_endpoints', False),
            explicit_files=getattr(args, 'explicit_files', None),
        )

    def handle_unpack(args):
        logger.info(f"Unpacking files from {args.combined_file_path} to {args.output_directory} using replace_existing={args.replace_existing}")
        run_unpack(args.output_directory, args.combined_file_path, replace_existing=args.replace_existing, kernel=getattr(args, 'kernel', None), force=getattr(args, 'force', False))

    def handle_archive_subdirectories(args):
        archive_subdirectories(args.parent_directory, args.directories, args.combined_archive_dir, args.combined_archive_name, args.file_types)

    def handle_extract_notebooks(args):
        logger.info(f"Extracting notebooks from {args.archive_file_path} to {args.output_directory} using replace_existing={args.replace_existing}")
        run_extract_notebooks(args.archive_file_path, args.output_directory, replace_existing=args.replace_existing, kernel=getattr(args, 'kernel', None))

    def handle_extract_notebooks_and_quarto(args):
        logger.info(f"Extracting notebooks and Quarto files from {args.archive_file_path} to {args.output_directory} using replace_existing={args.replace_existing}")
        run_extract_notebooks_and_quarto(args.archive_file_path, args.output_directory, replace_existing=args.replace_existing, kernel=getattr(args, 'kernel', None))

    def handle_convert_word(args):
        from pathlib import Path
        from .word_converter import convert_word_to_markdown, convert_word_documents_in_directory
        input_path = Path(args.input_path)

        if input_path.is_file():
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
            output_dir = args.output_path or input_path
            converted_files = convert_word_documents_in_directory(
                input_path, output_dir, method=args.method,
                replace_existing=args.replace_existing
            )
            logger.info(f"Converted {len(converted_files)} Word documents in {input_path}")
        else:
            logger.error(f"Input path does not exist: {input_path}")

    def handle_convert_html(args):
        from pathlib import Path
        from .html_converter import convert_html_to_markdown, convert_html_documents_in_directory
        input_path = Path(args.input_path)
        extract_images = not args.no_extract_images
        image_dir = Path(args.image_dir) if args.image_dir else None

        if input_path.is_file():
            output_path = args.output_path
            if output_path is None:
                output_path = input_path.with_suffix('.md')
            else:
                output_path = Path(output_path)
            try:
                markdown_content = convert_html_to_markdown(
                    input_path, method=args.method,
                    extract_images=extract_images,
                    image_output_dir=image_dir
                )
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(markdown_content)
                logger.info(f"Successfully converted: {input_path} -> {output_path}")
            except Exception as e:
                logger.error(f"Failed to convert {input_path}: {e}")
        elif input_path.is_dir():
            output_dir = Path(args.output_path) if args.output_path else input_path
            converted_files = convert_html_documents_in_directory(
                input_path, output_dir, method=args.method,
                replace_existing=args.replace_existing,
                extract_images=extract_images
            )
            logger.info(f"Converted {len(converted_files)} HTML documents in {input_path}")
        else:
            logger.error(f"Input path does not exist: {input_path}")

    def handle_describe(args):
        target_cmd = args.describe_command
        if target_cmd:
            if target_cmd not in _subparser_map:
                print(f"Unknown command: {target_cmd}", file=__import__('sys').stderr)
                print(f"Available commands: {', '.join(sorted(_subparser_map.keys()))}", file=__import__('sys').stderr)
                raise SystemExit(1)
            schema = _describe_parser(_subparser_map[target_cmd], name=target_cmd)
        else:
            schema = {
                "tool": "txtarchive",
                "version": __version__,
                "description": parser.description,
                "commands": {
                    name: _describe_parser(sub_parser, name=name)
                    for name, sub_parser in _subparser_map.items()
                }
            }
        print(json_module.dumps(schema, indent=2))

    def handle_generate(args):
        logger.info(f"Generating archive from {args.study_plan_path} and {args.lhn_archive_path}")
        from txtarchive.packunpack import generate_archive
        generate_archive(args.study_plan_path, args.lhn_archive_path, args.output_archive_path, args.llm_model)

    def handle_extract_report(args):
        from pathlib import Path
        from .report_extractor import extract_report, format_yaml, format_json, format_markdown
        input_path = Path(args.input_path)

        if not input_path.is_file():
            logger.error(f"Input file does not exist: {input_path}")
            return

        section_filter = None
        if args.sections:
            try:
                section_filter = [int(s.strip()) for s in args.sections.split(",")]
            except ValueError:
                logger.error(f"Invalid --sections value: {args.sections}. Use comma-separated integers (e.g., 0,1,6)")
                return

        try:
            data = extract_report(input_path, sections=section_filter, strict=args.strict)
            if args.output_format == "json":
                output_text = format_json(data)
            elif args.output_format == "markdown":
                output_text = format_markdown(data)
            else:
                output_text = format_yaml(data)

            if args.output:
                output_path = Path(args.output)
                output_path.write_text(output_text, encoding="utf-8")
                logger.info(f"Extracted report data written to: {output_path}")
            else:
                print(output_text)
        except Exception as e:
            logger.error(f"Failed to extract report: {e}")
            if args.strict:
                raise

    # --- Command dispatch ---
    command_handlers = {
        'ingest': handle_ingest,
        'archive': handle_archive,
        'archive-and-ingest': handle_archive_and_ingest,
        'unpack': handle_unpack,
        'archive_subdirectories': handle_archive_subdirectories,
        'extract-notebooks': handle_extract_notebooks,
        'extract-notebooks-and-quarto': handle_extract_notebooks_and_quarto,
        'convert-word': handle_convert_word,
        'convert-html': handle_convert_html,
        'describe': handle_describe,
        'generate': handle_generate,
        'extract-report': handle_extract_report,
    }

    handler = command_handlers.get(args.command)
    if handler:
        handler(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()