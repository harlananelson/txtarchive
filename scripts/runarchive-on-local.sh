#!/bin/bash

# run from the root of projects

echo "Archiving project..."

python -m txtarchive archive "lhn" "archive/lhn.txt" \
    --file_types .py .yaml .md \
    --root-files setup.py requirements.txt environment_spark.yaml \
    --split-output 

python -m txtarchive archive "../txtarchive" "../archive/txtarchive.txt" \
    --file_types .py .yaml .md \
    --root-files setup.py requirements.txt environment_spark.yaml \
    --exclude-dirs .venv __pycache__ .git \
    --llm-friendly \
    --split-output \
    --max-tokens 3000

python -m txtarchive archive srajesh_OMOP/omop_etl "archive/srajesh_OMOP_models.txt" \
    --file_types .py .yaml .md .json .sql \
    --root-files __init__.py README.md plan.md \
    --split-output


python -m txtarchive archive "healtheintent/config" "archive/config.txt" \
    --file_types .py .yaml .json  \
    --no-subdirectories

python -m txtarchive archive "updatebionic" "archive/updatebionic.txt" \
    --file_types .py .yaml .json  \
    --no-subdirectories

python -m txtarchive archive "lhnmetadata" "archive/lhnmetadata.txt" \
    --file_types .py .yaml .md .ipynb \
    --llm-friendly \
    --extract-code-only \
    --split-output 