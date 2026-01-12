# Explicit Files Feature Implementation for txtarchive

## Summary
This document describes the changes needed to add explicit file list functionality to txtarchive.

## Feature Overview
Allows users to specify an exact list of files to archive, bypassing directory scanning logic.

### Usage Example:
```bash
python -m txtarchive archive /path/to/source /path/to/output.txt \
    --explicit-files file1.ipynb file2.R file3.ipynb \
    --llm-friendly --extract-code-only --split-output
```

---

## File 1: packunpack.py - ALREADY UPDATED ✓

The updated `packunpack.py` is saved at `/home/claude/packunpack.py`

### Changes Made:
1. Added `explicit_files=None` parameter to `archive_files()` function signature
2. Added explicit files handling logic after line 624
3. Wrapped existing directory scanning in `else:` block

### Key Implementation Details:
- Validates that each explicit file exists
- Supports both absolute and relative paths
- Processes notebooks with extract_code_only support
- Handles files outside source directory gracefully
- Maintains all existing functionality (llm_friendly, split_output, etc.)

---

## File 2: __main__.py - NEEDS UPDATE

### Location in Your Code:
Find the `add_common_archive_args()` function in `__main__.py`

### Change Required:
Add this argument to the function (after existing arguments):

```python
def add_common_archive_args(parser):
    """Add common archive arguments to a parser to reduce duplication."""
    # ... existing arguments ...
    
    parser.add_argument(
        '--explicit-files',
        nargs='+',
        metavar='FILE',
        help='Explicit list of files to archive (bypasses directory scanning)'
    )
```

### Update Archive Command Handler:
In the `elif args.command == 'archive':` section, pass the new parameter:

```python
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
        explicit_files=args.explicit_files,  # ← ADD THIS LINE
    )
```

### Update Archive-and-Ingest Command Handler:
Similarly, in the `elif args.command == 'archive-and-ingest':` section:

```python
elif args.command == 'archive-and-ingest':
    archive_and_ingest(
        directory=args.directory,
        output_file_path=args.output_file,
        # ... other existing parameters ...
        explicit_files=args.explicit_files,  # ← ADD THIS LINE
    )
```

---

## File 3: __init__.py - NO CHANGES NEEDED ✓

The `archive_files` function is already exported, so no changes needed.

---

## Testing the Feature

### Test 1: Basic Explicit Files
```bash
python -m txtarchive archive /path/to/project /path/to/output.txt \
    --explicit-files file1.py file2.py \
    --llm-friendly
```

### Test 2: Notebooks with Code Extraction
```bash
python -m txtarchive archive /path/to/project /path/to/output.txt \
    --explicit-files notebook1.ipynb notebook2.ipynb \
    --llm-friendly --extract-code-only --split-output
```

### Test 3: Mixed File Types
```bash
python -m txtarchive archive /path/to/project /path/to/output.txt \
    --explicit-files _targets.R analysis.ipynb report.md \
    --llm-friendly --split-output --max-tokens 100000
```

### Test 4: Files with Spaces
```bash
python -m txtarchive archive /path/to/project /path/to/output.txt \
    --explicit-files "100 Sickle-Cell-Survival-Curves.ipynb" "108 insurance-grouped.ipynb" \
    --llm-friendly
```

---

## Error Handling

The feature handles these cases:
1. **File not found**: Logs error, continues with other files
2. **Non-file paths**: Logs warning, skips
3. **Files outside source directory**: Uses filename only, logs warning
4. **Notebook processing errors**: Includes error message in archive

---

## Implementation Notes

### Why This Approach?
- Explicit files bypass all directory scanning logic (cleaner, faster)
- Maintains full compatibility with existing features
- No breaking changes to API

### Performance
- Explicit file mode is significantly faster for small file lists
- No directory traversal overhead
- Useful for large projects where you only need specific files

### Backward Compatibility
- All existing commands work unchanged
- New parameter is optional (defaults to None)
- Directory scanning is default behavior when --explicit-files not provided

---

## Shell Script Generation

With this feature, the shell script for your SickleCell project becomes simpler:

```bash
#!/bin/bash
set -e

SOURCE_DIR="/home/hnelson3/work/Users/hnelson3/Projects/SickleCell"
ARCHIVE_DIR="/home/hnelson3/work/Users/hnelson3/archive"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
OUTPUT_FILE="${ARCHIVE_DIR}/SickleCell_paper_${TIMESTAMP}.txt"
SPLIT_DIR="${ARCHIVE_DIR}/SickleCell_paper_${TIMESTAMP}_split"

mkdir -p "$ARCHIVE_DIR"

python -m txtarchive archive \
    "$SOURCE_DIR" \
    "$OUTPUT_FILE" \
    --explicit-files \
        "_targets.R" \
        "2010-Paper-figures.ipynb" \
        "106-Demographics.ipynb" \
        "1031-Mortality-3-age-table.ipynb" \
        "1030-Analysis-Survial-Plots-p-values.ipynb" \
        "100-Sickle-Cell-Survival-Curves.ipynb" \
        "108-insurance-grouped.ipynb" \
    --llm-friendly \
    --extract-code-only \
    --split-output \
    --max-tokens 100000 \
    --split-output-dir "$SPLIT_DIR"

echo "Archive created: $OUTPUT_FILE"
if [ -d "$SPLIT_DIR" ]; then
    echo "Split files: $SPLIT_DIR"
fi
```

---

## Next Steps

1. Replace your `packunpack.py` with the updated version from `/home/claude/packunpack.py`
2. Update your `__main__.py` following the instructions above
3. Test with a simple case
4. Use for your SickleCell paper project

---

## Questions or Issues?

If you encounter any issues:
1. Check that file paths are correct (relative to source directory)
2. Verify files exist before running
3. Check logs for specific error messages
4. Test with a single file first