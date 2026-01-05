#!/bin/bash
# Generate timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DIRNAME="updatebionic"

python -m txtarchive archive "../updatebionic" "../.archive/${DIRNAME}_${TIMESTAMP}.txt" \
    --root-files README.md requirements-R.txt requirements-python.txt requirements.txt environment-ml.yml updatebionic-ml.sh \
    --include-subdirs nix \
    --file_types .py .yaml .json .sh .md .txt .yml .nix .toml \
    --llm-friendly \
    --split-output \
    --max-tokens 3000 \
    --split-output-dir "../.archive/${DIRNAME}_${TIMESTAMP}_split"