python -m txtarchive archive "txtarchive" "archive/txtarchive.txt" \
    --file_types .py .yaml .md \
    --root-files setup.py requirements.txt environment_spark.yaml \
    --exclude-dirs .venv __pycache__ .git \
    --split-output

