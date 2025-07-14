#!/bin/bash

# run from the root of projects

echo "Archiving project..."

python -m txtarchive archive "SickleCell" "archive/SickleCell_workflow_example.txt" \
    --file_types .ipynb \
    --no-subdirectories \
    --llm-friendly \
    --extract-code-only \
    --split-output \
    --file_prefixes 015

python -m txtarchive archive "SickleCell_AI" "archive/SickleCell_AI_workflow_example.txt" \
    --file_types .ipynb \
    --no-subdirectories \
    --llm-friendly \
    --extract-code-only \
    --split-output \
    --file_prefixes 01

python -m txtarchive archive "SickleCell_AI" "archive/SickleCell_AI.txt" \
    --file_types .ipynb .yaml \
    --llm-friendly \
    --extract-code-only \
    --split-output \
    --exclude .ipynb_checkpoints

python -m txtarchive archive "SickleCell" "archive/SickleCell_workflow.txt" \
    --file_types .ipynb .yaml \
    --llm-friendly \
    --extract-code-only \
    --split-output \
    --exclude .ipynb_checkpoints \
    --file_prefixes 011 015 016 017 018 050 060 066 067 

echo "Archiving complete."