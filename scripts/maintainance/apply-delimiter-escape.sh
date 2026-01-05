#!/bin/bash
# apply_delimiter_escape.sh
# Run from txtarchive root directory
# Usage: bash apply_delimiter_escape.sh

set -e

PACKUNPACK="txtarchive/packunpack.py"

if [ ! -f "$PACKUNPACK" ]; then
    echo "Error: $PACKUNPACK not found. Run from txtarchive root directory."
    exit 1
fi

# Backup
cp "$PACKUNPACK" "${PACKUNPACK}.backup.$(date +%Y%m%d_%H%M%S)"
echo "Created backup"

python3 << 'ENDPYTHON'
import re

with open("txtarchive/packunpack.py", "r") as f:
    content = f.read()

changes_made = 0

# =============================================================================
# CHANGE 1a: Escape delimiter in archive_files() when writing LLM-friendly format
# =============================================================================
old_llm_archive = '''    if llm_friendly:
        for idx, (rel_path, content) in enumerate(file_list, 1):
            all_contents += f"{'#' * 80}\\n# FILE {idx}: {rel_path}\\n{'#' * 80}\\n\\n"
            all_contents += content
            all_contents += "\\n\\n"'''

new_llm_archive = '''    if llm_friendly:
        for idx, (rel_path, content) in enumerate(file_list, 1):
            all_contents += f"{'#' * 80}\\n# FILE {idx}: {rel_path}\\n{'#' * 80}\\n\\n"
            # Escape delimiter pattern in content to prevent quoting problem
            escaped_content = content.replace("---\\nFilename: ", "---\\\\nFilename: ")
            all_contents += escaped_content
            all_contents += "\\n\\n"'''

if old_llm_archive in content:
    content = content.replace(old_llm_archive, new_llm_archive)
    print("✅ CHANGE 1a: Added escape in archive_files() LLM-friendly section")
    changes_made += 1
else:
    print("⚠️  CHANGE 1a: LLM-friendly pattern not found (may already be applied)")

# =============================================================================
# CHANGE 1b: Escape delimiter in archive_files() when writing standard format
# =============================================================================
old_archive = '''    else:
        for rel_path, content in file_list:
            all_contents += f"---\\nFilename: {rel_path}\\n---\\n{content}\\n\\n"'''

new_archive = '''    else:
        for rel_path, content in file_list:
            # Escape delimiter pattern in content to prevent quoting problem
            escaped_content = content.replace("---\\nFilename: ", "---\\\\nFilename: ")
            all_contents += f"---\\nFilename: {rel_path}\\n---\\n{escaped_content}\\n\\n"'''

if old_archive in content:
    content = content.replace(old_archive, new_archive)
    print("✅ CHANGE 1b: Added escape in archive_files() standard format section")
    changes_made += 1
else:
    print("⚠️  CHANGE 1b: Pattern not found (may already be applied)")

# =============================================================================
# CHANGE 2: Unescape delimiter in unpack_files() when writing content
# =============================================================================
old_unpack = '''            with output_path.open("w", encoding="utf-8") as file:
                file.write(content)
                logger.info("Unpacked file: %s", output_path)'''

new_unpack = '''            with output_path.open("w", encoding="utf-8") as file:
                # Unescape delimiter pattern that was escaped during archiving
                unescaped_content = content.replace("---\\\\nFilename: ", "---\\nFilename: ")
                file.write(unescaped_content)
                logger.info("Unpacked file: %s", output_path)'''

if old_unpack in content:
    content = content.replace(old_unpack, new_unpack)
    print("✅ CHANGE 2: Added unescape in unpack_files()")
    changes_made += 1
else:
    print("⚠️  CHANGE 2: Pattern not found (may already be applied)")

# =============================================================================
# CHANGE 3: Unescape delimiter in unpack_llm_archive()
# =============================================================================
old_llm_unpack = '''        # Write the file
        try:
            with file_path.open("w", encoding="utf-8") as f:
                f.write(content)
            logger.info(f"Unpacked file: {file_path}")'''

new_llm_unpack = '''        # Write the file
        try:
            with file_path.open("w", encoding="utf-8") as f:
                # Unescape delimiter pattern that was escaped during archiving
                unescaped_content = content.replace("---\\\\nFilename: ", "---\\nFilename: ")
                f.write(unescaped_content)
            logger.info(f"Unpacked file: {file_path}")'''

if old_llm_unpack in content:
    content = content.replace(old_llm_unpack, new_llm_unpack)
    print("✅ CHANGE 3: Added unescape in unpack_llm_archive()")
    changes_made += 1
else:
    print("⚠️  CHANGE 3: Pattern not found (may already be applied or function differs)")

# Write updated file
with open("txtarchive/packunpack.py", "w") as f:
    f.write(content)

print(f"\n{'='*60}")
print(f"Applied {changes_made}/4 changes")
if changes_made > 0:
    print("Run: pip install -e . to reinstall")
    print("\nThe delimiter pattern '---\\nFilename: ' in file content")
    print("will now be escaped to '---\\\\nFilename: ' during archiving")
    print("and unescaped back during unpacking.")
ENDPYTHON