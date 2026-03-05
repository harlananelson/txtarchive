import os
from pathlib import Path
from .header import logger  # Import logger for consistency

DEFAULT_MAX_TOKENS = 10000  # Target chunk size (adjustable)
DEFAULT_OUTPUT_DIR = "split_txtarchive"  # Where split files go

# Patterns for archive file boundaries
_LLM_FRIENDLY_SEPARATOR = "################################################################################\n# FILE "
_STANDARD_SEPARATOR = "---\nFilename: "


def split_file(file_path, max_tokens=DEFAULT_MAX_TOKENS, output_dir=DEFAULT_OUTPUT_DIR):
    """Split a file into chunks under max_tokens, preserving archive file boundaries.

    For txtarchive files, splits at file section boundaries (# FILE or ---Filename:)
    to avoid corrupting entries. Falls back to line-based splitting for non-archive files.

    Args:
        file_path (str or Path): Path to the input file.
        max_tokens (int): Maximum approximate tokens per chunk (default: 10000).
        output_dir (str or Path): Directory to save split files (default: split_txtarchive).
    """
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    logger.info(f"Ensured output directory exists: {output_dir}")

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    file_name = Path(file_path).stem  # e.g., 'txtarchive'
    file_ext = Path(file_path).suffix  # e.g., '.txt'
    total_tokens = len(content.split())  # Approximate token count

    if total_tokens <= max_tokens:
        # No split needed, copy as-is
        output_path = os.path.join(output_dir, f"{file_name}{file_ext}")
        with open(output_path, 'w', encoding='utf-8') as out_f:
            out_f.write(content)
        logger.info(f"Copied {file_name}{file_ext} ({total_tokens} tokens)")
        return

    # Detect archive format and split on boundaries
    if _LLM_FRIENDLY_SEPARATOR in content:
        _split_on_boundaries(content, _LLM_FRIENDLY_SEPARATOR, file_name, file_ext, max_tokens, output_dir)
    elif _STANDARD_SEPARATOR in content:
        _split_on_boundaries(content, _STANDARD_SEPARATOR, file_name, file_ext, max_tokens, output_dir)
    else:
        _split_by_lines(content, file_name, file_ext, max_tokens, output_dir)


def _split_on_boundaries(content, separator, file_name, file_ext, max_tokens, output_dir):
    """Split archive content at file section boundaries."""
    parts = content.split(separator)
    header = parts[0]  # Archive header (before first file section)
    sections = parts[1:]  # Individual file sections

    current_chunk = header
    part_num = 1

    for section in sections:
        section_with_sep = separator + section
        section_tokens = len(section_with_sep.split())
        current_tokens = len(current_chunk.split())

        if current_tokens + section_tokens > max_tokens and current_chunk.strip():
            # Write current chunk
            output_path = os.path.join(output_dir, f"{file_name}_part{part_num}{file_ext}")
            with open(output_path, 'w', encoding='utf-8') as out_f:
                out_f.write(current_chunk)
            logger.info(f"Wrote {output_path} ({current_tokens} tokens)")
            current_chunk = ""  # Start new chunk without duplicating header
            part_num += 1

        current_chunk += section_with_sep

    # Write final chunk
    if current_chunk.strip():
        current_tokens = len(current_chunk.split())
        output_path = os.path.join(output_dir, f"{file_name}_part{part_num}{file_ext}")
        with open(output_path, 'w', encoding='utf-8') as out_f:
            out_f.write(current_chunk)
        logger.info(f"Wrote {output_path} ({current_tokens} tokens)")


def _split_by_lines(content, file_name, file_ext, max_tokens, output_dir):
    """Fallback: split non-archive files by lines."""
    lines = content.splitlines()
    current_chunk = []
    current_tokens = 0
    part_num = 1

    for line in lines:
        line_tokens = len(line.split())
        if current_tokens + line_tokens > max_tokens and current_chunk:
            output_path = os.path.join(output_dir, f"{file_name}_part{part_num}{file_ext}")
            with open(output_path, 'w', encoding='utf-8') as out_f:
                out_f.write("\n".join(current_chunk))
            logger.info(f"Wrote {output_path} ({current_tokens} tokens)")
            current_chunk = []
            current_tokens = 0
            part_num += 1

        current_chunk.append(line)
        current_tokens += line_tokens

    if current_chunk:
        output_path = os.path.join(output_dir, f"{file_name}_part{part_num}{file_ext}")
        with open(output_path, 'w', encoding='utf-8') as out_f:
            out_f.write("\n".join(current_chunk))
        logger.info(f"Wrote {output_path} ({current_tokens} tokens)")


def process_directory(input_dir, output_dir=DEFAULT_OUTPUT_DIR, max_tokens=DEFAULT_MAX_TOKENS):
    """Process all files in input_dir, splitting large ones."""
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    # Iterate over files
    for file_name in os.listdir(input_dir):
        file_path = os.path.join(input_dir, file_name)
        if os.path.isfile(file_path):
            split_file(file_path, max_tokens, output_dir)

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        split_file(sys.argv[1])
    else:
        print("Usage: python -m txtarchive.split_files <file_path>")
