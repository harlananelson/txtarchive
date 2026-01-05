python -m txtarchive archive "../lhn" "../.archive/lhn.txt" \
    --file_types .py .yaml .md \
    --root-files setup.py requirements.txt environment_spark.yaml \
    --exclude-dirs .venv __pycache__ .git \
    --llm-friendly \
    --split-output \
    --max-tokens 3000