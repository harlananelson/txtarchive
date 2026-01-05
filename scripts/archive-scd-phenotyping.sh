python -m txtarchive archive "../SCDCernerProject/python/scd_phenotyping" "../.archive/scd_phenotyping.txt" \
    --file_types .py .yaml .md .toml\
    --root-files setup.py requirements.txt environment_spark.yaml pyproject.toml\
    --split-output 
