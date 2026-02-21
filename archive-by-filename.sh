#!/bin/bash
# archive_Demographics.sh
# Archives specific files using txtarchive with explicit file list
# Called from: ~/work/Users/hnelson3/Projects/

set -e

# === CONFIGURATION ===
# Run from Projects
SOURCE_DIR="."
ARCHIVE_DIR="./archive"
ARCHIVE_BASE="disease-severity"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
OUTPUT_FILE="${ARCHIVE_DIR}/${ARCHIVE_BASE}_${TIMESTAMP}.txt"

# Parameterized file list (Bash array)
FILES_TO_ARCHIVE=(
    "270-Model-Mortality-using-LOINC-3-levels-jan30-2025.ipynb"
)

# === SETUP ===
mkdir -p "${ARCHIVE_DIR}"

# === ARCHIVE ===
echo "Creating archive: ${OUTPUT_FILE}"
echo "Files: ${FILES_TO_ARCHIVE[*]}"

python -m txtarchive archive \
    "${SOURCE_DIR}" \
    "${OUTPUT_FILE}" \
    --explicit-files "${FILES_TO_ARCHIVE[@]}" \
    --file_types .ipynb \
    --llm-friendly \
    --extract-code-only

echo "Archive complete: ${OUTPUT_FILE}"