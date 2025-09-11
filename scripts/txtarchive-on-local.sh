python -m txtarchive archive "txtarchive" "archive/txtarchive.txt" \
    --file_types .py .yaml .md \
    --root-files setup.py requirements.txt environment_spark.yaml \
    --exclude-dirs .venv __pycache__ .git \
    --split-output \
    --split-max-tokens 7500  


    # For small projects - ingest files directly
python -m txtarchive archive-and-ingest "small-project" "archive/small.txt" \
    --ingestion-method directory --file_types .py .md

# For large projects - create archive and split as needed  
python -m txtarchive archive-and-ingest "large-project" "archive/large.txt" \
    --ingestion-method archive --max-tokens 75000

# Let the tool decide automatically
python -m txtarchive archive-and-ingest "my-project" "archive/project.txt" \
    --ingestion-method auto

