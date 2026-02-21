# txtarchive/__init__.py
PACKAGE_CONSTANT = 'constant value'

def _initialize_package():
    pass

_initialize_package()

from .packunpack import (
    concatenate_files,
    archive_subdirectories,
    combine_all_archives,
    run_concat,
    unpack_files,
    run_concat_no_subdirs,
    archive_files,
    run_unpack,
    extract_notebooks_to_ipynb,
    run_extract_notebooks,
    generate_archive,
)

from .html_converter import (
    convert_html_to_markdown,
    convert_html_to_markdown_text,
    convert_html_documents_in_directory,
)

__all__ = [
    'concatenate_files',
    'archive_subdirectories',
    'combine_all_archives',
    'run_concat',
    'unpack_files',
    'run_concat_no_subdirs',
    'archive_files',
    'run_unpack',
    'extract_notebooks_to_ipynb',
    'run_extract_notebooks',
    'generate_archive',
    'convert_html_to_markdown',
    'convert_html_to_markdown_text',
    'convert_html_documents_in_directory',
]