#!/bin/bash
# archive-by-filename.sh
# Archives specific files using txtarchive with explicit file list
# Usage: ./archive-by-filename.sh [file1.ipynb file2.py ...]

set -e

# === CONFIGURATION ===
SOURCE_DIR="${SOURCE_DIR:-.}"
ARCHIVE_DIR="${ARCHIVE_DIR:-./archive}"
ARCHIVE_BASE="${ARCHIVE_BASE:-archive}"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
OUTPUT_FILE="${ARCHIVE_DIR}/${ARCHIVE_BASE}_${TIMESTAMP}.txt"

# Use command-line arguments as files, or prompt if none given
if [ $# -gt 0 ]; then
    FILES_TO_ARCHIVE=("$@")
else
    echo "Usage: $0 file1.ipynb [file2.py ...]"
    echo "Or set FILES_TO_ARCHIVE as an array before calling."
    exit 1
fi

# === SETUP ===
mkdir -p "${ARCHIVE_DIR}"

# === ARCHIVE ===
echo "Creating archive: ${OUTPUT_FILE}"
echo "Files: ${FILES_TO_ARCHIVE[*]}"

python -m txtarchive archive \
    "${SOURCE_DIR}" \
    "${OUTPUT_FILE}" \
    --explicit-files "${FILES_TO_ARCHIVE[@]}" \
    --llm-friendly \
    --extract-code-only

echo "Archive complete: ${OUTPUT_FILE}"
