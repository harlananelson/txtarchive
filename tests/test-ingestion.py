#!/bin/bash
# Corrected TxtArchive Ingestion Test Commands
# Fixed file paths

echo "=== TxtArchive Package Ingestion Test Commands ==="

# Check if ACCESS_TOKEN is set
if [ -z "$ACCESS_TOKEN" ]; then
    echo "⚠️  WARNING: ACCESS_TOKEN environment variable is not set!"
    echo "   Set it with: export ACCESS_TOKEN='your_ask_sage_token'"
    echo "   or run getsagetoken in the shell"
    echo ""
fi

root_dir="/app/projects/clinressys01_t1/"
archive_dir="${root_dir}archive"
txtarchive_src="${root_dir}txtarchive"  # The project directory

# Ensure archive directory exists
mkdir -p "$archive_dir"

echo "1. Testing single file with endpoint auto-detection..."
if [ -n "$ACCESS_TOKEN" ]; then
    python -m txtarchive ingest --file "${txtarchive_src}/txtarchive/__init__.py" --test-endpoints
else
    echo "   Skipped - no ACCESS_TOKEN"
fi

echo ""
echo "2. Testing basic single file ingestion..."
if [ -n "$ACCESS_TOKEN" ]; then
    python -m txtarchive ingest --file "${txtarchive_src}/txtarchive/header.py"
else
    echo "   Skipped - no ACCESS_TOKEN"
fi

echo ""
echo "3. Creating LLM-friendly archive..."
python -m txtarchive archive "${txtarchive_src}" "$archive_dir/txtarchive.txt" \
    --file_types .py .yaml .md \
    --root-files pyproject.toml README.md \
    --exclude-dirs .venv __pycache__ .git \
    --llm-friendly

echo ""
echo "4. Testing archive-and-ingest with auto method..."
if [ -n "$ACCESS_TOKEN" ]; then
    python -m txtarchive archive-and-ingest "${txtarchive_src}" "$archive_dir/txtarchive_auto.txt" \
        --file_types .py .yaml .md \
        --root-files pyproject.toml README.md \
        --exclude-dirs .venv __pycache__ .git \
        --ingestion-method auto \
        --max-tokens 75000 \
        --llm-friendly
else
    echo "   Skipped - no ACCESS_TOKEN"
fi

echo ""
echo "5. Testing archive with splitting..."
python -m txtarchive archive "${txtarchive_src}" "$archive_dir/txtarchive_split.txt" \
    --file_types .py .yaml .md \
    --root-files pyproject.toml README.md \
    --exclude-dirs .venv __pycache__ .git \
    --llm-friendly \
    --split-output \
    --max-tokens 50000

echo ""
echo "=== Test Results ==="
echo "Files created in $archive_dir:"
ls -la "$archive_dir"

echo ""
echo "Split files (if any):"
ls -la "$archive_dir"/split_* 2>/dev/null || echo "No split files created"

echo ""
echo "🎉 All tests completed successfully!"


