import os
from pathlib import Path
from .header import logger  # Import logger for consistency

DEFAULT_MAX_TOKENS = 10000  # Target chunk size (adjustable)
DEFAULT_OUTPUT_DIR = "split_txtarchive"  # Where split files go

# Patterns for archive file boundaries
_LLM_FRIENDLY_SEPARATOR = "################################################################################\n# FILE "
_STANDARD_SEPARATOR = "---\nFilename: "


def _content_key(text):
    """Comparison key for update mode: the content minus volatile header lines.

    Archives carry a '# Archive created on: <date>' line that changes every
    run even when nothing else does; ignoring it lets update mode detect
    'no real change' and leave the existing file (and its mtime) untouched.
    """
    return "\n".join(
        line for line in text.splitlines()
        if not line.startswith("# Archive created on:")
        and not line.startswith("# Date:")
    )


def _write_if_changed(path, content):
    """Write content to path only if it differs (ignoring the date line).

    Returns True if the file was written, False if it was already current.
    Used by update mode so unchanged outputs keep their mtime — a daily
    sync/upload step can then skip them.
    """
    p = Path(path)
    if p.exists():
        try:
            old = p.read_text(encoding="utf-8")
        except OSError:
            old = None
        if old is not None and _content_key(old) == _content_key(content):
            return False
    p.write_text(content, encoding="utf-8")
    return True


def _emit(output_path, content, update_only):
    """Write one output chunk, honoring update mode. Returns the Path written/kept."""
    p = Path(output_path)
    if update_only:
        if _write_if_changed(p, content):
            logger.info(f"Updated {p} ({len(content.split())} tokens)")
        else:
            logger.info(f"Unchanged {p} — kept existing file")
    else:
        with p.open("w", encoding="utf-8") as out_f:
            out_f.write(content)
        logger.info(f"Wrote {p} ({len(content.split())} tokens)")
    return p


def split_file(file_path, max_tokens=DEFAULT_MAX_TOKENS, output_dir=DEFAULT_OUTPUT_DIR,
               update_only=False):
    """Split a file into chunks under max_tokens, preserving archive file boundaries.

    For txtarchive files, splits at file section boundaries (# FILE or ---Filename:)
    to avoid corrupting entries. Falls back to line-based splitting for non-archive files.

    Args:
        file_path (str or Path): Path to the input file.
        max_tokens (int): Maximum approximate tokens per chunk (default: 10000).
        output_dir (str or Path): Directory to save split files (default: split_txtarchive).
        update_only (bool): If True, rewrite a chunk only when its content changed
            (comparison ignores the archive date line) and delete stale part files
            from previous runs. Unchanged chunks keep their mtime.

    Returns:
        list[Path]: the chunk files written or kept current in output_dir.
    """
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    logger.info(f"Ensured output directory exists: {output_dir}")

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    file_name = Path(file_path).stem  # e.g., 'txtarchive'
    file_ext = Path(file_path).suffix  # e.g., '.txt'
    total_tokens = len(content.split())  # Approximate token count

    outputs = []
    if total_tokens <= max_tokens:
        # No split needed, copy as-is
        outputs.append(_emit(os.path.join(output_dir, f"{file_name}{file_ext}"),
                             content, update_only))
    elif _LLM_FRIENDLY_SEPARATOR in content:
        outputs = _split_on_boundaries(content, _LLM_FRIENDLY_SEPARATOR, file_name,
                                       file_ext, max_tokens, output_dir, update_only)
    elif _STANDARD_SEPARATOR in content:
        outputs = _split_on_boundaries(content, _STANDARD_SEPARATOR, file_name,
                                       file_ext, max_tokens, output_dir, update_only)
    else:
        outputs = _split_by_lines(content, file_name, file_ext, max_tokens,
                                  output_dir, update_only)

    if update_only:
        _remove_stale_parts(output_dir, file_name, file_ext, outputs)
    return outputs


def _remove_stale_parts(output_dir, file_name, file_ext, outputs):
    """Delete previous-run chunk files that this run did not produce.

    A shrinking archive leaves orphan *_partN files behind; in update mode
    those would keep stale content visible to whatever consumes the directory
    (e.g. a Copilot upload), so they are removed.
    """
    keep = {Path(p).name for p in outputs}
    candidates = list(Path(output_dir).glob(f"{file_name}_part*{file_ext}"))
    candidates += list(Path(output_dir).glob(f"{file_name}{file_ext}"))
    for f in candidates:
        if f.name not in keep:
            f.unlink()
            logger.info(f"Removed stale chunk: {f}")


def _split_on_boundaries(content, separator, file_name, file_ext, max_tokens,
                         output_dir, update_only=False):
    """Split archive content at file section boundaries. Returns chunk paths."""
    parts = content.split(separator)
    header = parts[0]  # Archive header (before first file section)
    sections = parts[1:]  # Individual file sections

    current_chunk = header
    part_num = 1
    outputs = []

    for section in sections:
        section_with_sep = separator + section
        section_tokens = len(section_with_sep.split())
        current_tokens = len(current_chunk.split())

        if current_tokens + section_tokens > max_tokens and current_chunk.strip():
            outputs.append(_emit(
                os.path.join(output_dir, f"{file_name}_part{part_num}{file_ext}"),
                current_chunk, update_only))
            current_chunk = ""  # Start new chunk without duplicating header
            part_num += 1

        current_chunk += section_with_sep

    # Write final chunk
    if current_chunk.strip():
        outputs.append(_emit(
            os.path.join(output_dir, f"{file_name}_part{part_num}{file_ext}"),
            current_chunk, update_only))
    return outputs


def _split_by_lines(content, file_name, file_ext, max_tokens, output_dir,
                    update_only=False):
    """Fallback: split non-archive files by lines. Returns chunk paths."""
    lines = content.splitlines()
    current_chunk = []
    current_tokens = 0
    part_num = 1
    outputs = []

    for line in lines:
        line_tokens = len(line.split())
        if current_tokens + line_tokens > max_tokens and current_chunk:
            outputs.append(_emit(
                os.path.join(output_dir, f"{file_name}_part{part_num}{file_ext}"),
                "\n".join(current_chunk), update_only))
            current_chunk = []
            current_tokens = 0
            part_num += 1

        current_chunk.append(line)
        current_tokens += line_tokens

    if current_chunk:
        outputs.append(_emit(
            os.path.join(output_dir, f"{file_name}_part{part_num}{file_ext}"),
            "\n".join(current_chunk), update_only))
    return outputs


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
