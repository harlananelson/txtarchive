
# On your Mac (local)
cd /path/to/txtarchive
python -m txtarchive archive "." "../.archive/txtarchive.txt" \
    --file_types .py .yaml .md .toml \
    --root-files setup.py pyproject.toml \
    --exclude-dirs .venv __pycache__ .git build txtarchive.egg-info
