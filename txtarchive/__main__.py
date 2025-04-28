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

# Sickle Cell
prompt: I want to create an archive of the ADS creation python scripts (specific files) in my SickleCell project for use with an LLM model.
response: python -m txtarchive archive "SickleCell" "SickleCell_ADSCreationLLM.txt" --file_types .ipynb --no-subdirectories --llm-friendly --extract-code-only --split-output --file_prefixes 011 015 016 017 050 060 065 066 067 070
  python -m txtarchive archive "SickleCell" "SickleCell_ADSCreationLLM.txt" --file_types .ipynb .yaml --no-subdirectories --file_prefixes 011 015 016 017 050 060 065 066 067 070 --llm-friendly --extract-code-only
  python -m txtarchive archive "SickleCell" "SickleCell_ADSCreationLLM.txt" --file_types .ipynb --no-subdirectories --file_prefixes 015 --llm-friendly --extract-code-only

prompt: I want to create an archive of the R code scripts( specific files) in my SickleCell project for use with an LLM
    python -m txtarchive archive "SickleCell" "SickleCell_AnalysisLLM.txt" --file_types .ipynb --no-subdirectories --llm-friendly --extract-code-only --split-output --file_prefixes 1030

# Martini_Gilbert_EBP_Well_being
prompt: I want to create an archive of my Martini_Gilbert_EBP_Well-being project for use with an LLM
response: 
    python -m txtarchive archive "Martini_Gilbert_EBP_Well-being" "Martini_Gilbert_EBP_Well-being.txt" --file_types qmd R r  --no-subdirectories --llm-friendly --extract-code-only --split-output

python -m txtarchive archive "lhn" "lhn/lhn-llm-friendly.txt" \
  --file_types .py .md .yaml \
  --llm-friendly \
  --split-output \
  --split-output-dir "lhn/split_lhn" \
  --exclude-dirs build .git old \
  --root-files setup.py environment_archive_env.yaml environment_spark.yaml \
  --include-subdirs lhn \
  --file_prefixes extract resource shared introspection header cohort data_display data_transformation file_operations function_parameters pandas_utilities spark_utils list_operations query features resource metadata item

  from foresight.discern import push_discern
from lhn.shared_methods import SharedMethodsMixin
from lhn.introspection_utils import coalesce, set_default_params
from lhn.header import re, F, StringType, spark, time, pprint, pd, copy
from lhn.cohort import identify_target_records, write_index_table
from lhn.data_display import print_pd, showIU
from lhn.data_summary import attrition
from lhn.data_transformation import write_sorted_index_table
from lhn.file_operations import put_to_hdfs
from lhn.function_parameters import setFunctionParameters
from lhn.pandas_utils import dict2Pandas
from lhn.spark_query import add_parsed_column
from lhn.spark_utils import  writeTable
from lhn.list_operations import noColColide, unique_non_none
from lhn.query import extract_fields_flat_top, query_flat_rwd
import unicodedata
from pprint import pformat
from lhn.features import select_only_baseline, analyze_clinical_measurements
from lhn.header import get_logger 

# Config

python -m txtarchive archive "config" "config/configYAML-llm-friendly.txt" \
  --file_types .yaml \
  --llm-friendly \
  --split-output \
  --split-output-dir "config/split_lhn" 


# To unpack the archive later:
# python -m txtarchive unpack "txtarchive/txtarchive-llm-friendly.txt" "extracted_txtarchive"
```

prompt: I want to create an archive of my lhn package for use with and LLM, in only one file
response:
    python -m txtarchive archive "lhn" "lhn-llm-friendly.txt" --file_types .py --no-subdirectories --llm-friendly --split-output

prompt:I want to create an archive of my lhn package, for use with an LLM, but split into multiple files
response:
    python -m txtarchive archive "lhn" "lhn-llm-friendly.txt" --file_types .py --no-subdirectories --llm-friendly --split-output --split-output-dir "split_lhn"

# txtarchive
prompt: I want to create an archive of my lhn package that I can later unpack 
response
    python -m txtarchive archive "txtarchive" "txtarchive.txt" --file_types .py --no-subdirectories
prompt: I want to unpack an archive of my lhn package I made previously
response:
    python -m txtarchive unpack "txtarchive.txt" txtarchive 

prompt: I want to extract notebooks form a text archive that was created for use with LLMs
response:
    python -m txtarchive extract-notebooks "split_SickleCell_ADSCreationLLM" "extracted_notebooks"

prompt: I want to create an archive of a directory and also include the subdirectories
response:
    python -m txtarchive archive "lhn" "lhn/lhn.txt" --file_types .py .md .yaml

prompt: I had an LLM generate a set of archived notebooks that I now want to extract
    python -m txtarchive extract-notebooks "split_SickleCell_ADSCreationLLM" "extracted_notebooks"

```bash
#!/bin/bash
# Command to archive the txtarchive Python package into an LLM-friendly text archive
# inside the txtarchive directory. Includes top-level files (e.g., .gitignore, README.md,
# usage.py, setup.py) and the txtarchive/txtarchive subdirectory (e.g., __init__.py, header.py).

prompt: I want to create an archive of the txtarchive package.
reponse: # Create the standard archive
python -m txtarchive archive "txtarchive" "txtarchive/txtarchive.txt" \
  --file_types .py .md .yaml

prompt: I want to create an archive of the config directory
reponse: python -m txtarchive archive "config" "config/config-LLM-archive.txt" --file_types .yaml

python -m txtarchive archive "txtarchive" "txtarchive/txtarchive-llm-friendly.txt" \
  --file_types .py .md .yaml \
  --llm-friendly \
  --split-output \
  --split-output-dir "txtarchive/split_txtarchive"

# a not LLM friendly version
python -m txtarchive archive "txtarchive" "txtarchive/txtarchive.txt" \
  --file_types .py .md .yaml \
  --file_prefixes .gitignore 

# To unpack the archive later:
python -m txtarchive unpack "txtarchive.txt" "txtarchive" --replace_existing

# python -m txtarchive unpack "txtarchive/txtarchive-llm-friendly.txt" "extracted_txtarchive"
```

prompt: I want to us LLM create create a project (directory) of code that will create an analsysis
reponse:
(reponse needs work to improve and make functional)
  Command to streamline LLM interaction
  This could call an LLM API (e.g., via openai or huggingface), pass the study plan and lhn archive, and save the generated archive.
    python -m txtarchive generate <study_plan> <lhn_archive> <output_archive>

    python -m txtarchive archive "lhn" "lhn-llm-friendly.txt" --file_types .py --no-subdirectories --llm-friendly --split-output --summarize
    echo "Analyze diabetes data" > study.txt
    python -m txtarchive generate "study.txt" "lhn-llm-friendly.txt" "study_archive.txt" --llm-model mock
    python -m txtarchive extract-notebooks "study_archive.txt" "study_notebooks"
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

# the end




    