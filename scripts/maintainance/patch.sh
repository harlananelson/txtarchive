#!/bin/bash
# apply_markdown_fix.sh
# Run this from your txtarchive directory to fix markdown cell handling
# Usage: bash apply_markdown_fix.sh

PACKUNPACK="../txtarchive/txtarchive/packunpack.py"

if [ ! -f "$PACKUNPACK" ]; then
    echo "Error: $PACKUNPACK not found. Run from txtarchive root directory."
    exit 1
fi

# Backup original
cp "$PACKUNPACK" "${PACKUNPACK}.backup"
echo "Created backup: ${PACKUNPACK}.backup"

# Use Python to apply the fix (more reliable for multiline)
python3 << 'ENDPYTHON'
import re

with open("txtarchive/packunpack.py", "r") as f:
    content = f.read()

# The old block to find
old_block = '''        else:
            cells = []
            current_cell = []
            cell_number = None
            
            for line in content.splitlines():
                if line.startswith("# Cell "):
                    if current_cell:
                        cells.append({
                            "cell_type": "code",
                            "source": current_cell,
                            "metadata": {},
                            "execution_count": None,
                            "outputs": []
                        })
                        current_cell = []
                    try:
                        cell_number = int(line.split("# Cell ")[1])
                    except (IndexError, ValueError):
                        logger.warning(f"Invalid cell marker in {filename}: {line}")
                    continue
                current_cell.append(line + "\\n")
                
            if current_cell:
                cells.append({
                    "cell_type": "code",
                    "source": current_cell,
                    "metadata": {},
                    "execution_count": None,
                    "outputs": []
                })
                
            notebook["cells"] = cells
            logger.info(f"Reconstructed {len(cells)} code cells for {filename}")'''

# The new block to replace with
new_block = '''        else:
            cells = []
            current_cell = []
            cell_type = "code"  # Track cell type (code or markdown)
            cell_number = None
            code_cell_count = 0
            markdown_cell_count = 0
            
            for line in content.splitlines():
                if line.startswith("# Cell "):
                    # Save previous cell if exists
                    if current_cell:
                        cells.append({
                            "cell_type": cell_type,
                            "source": current_cell,
                            "metadata": {},
                            "execution_count": None,
                            "outputs": [] if cell_type == "code" else []
                        })
                        if cell_type == "code":
                            code_cell_count += 1
                        else:
                            markdown_cell_count += 1
                        current_cell = []
                    # Start new code cell
                    cell_type = "code"
                    try:
                        cell_number = int(line.split("# Cell ")[1])
                    except (IndexError, ValueError):
                        logger.warning(f"Invalid cell marker in {filename}: {line}")
                    continue
                elif line.startswith("# Markdown Cell "):
                    # Save previous cell if exists
                    if current_cell:
                        cells.append({
                            "cell_type": cell_type,
                            "source": current_cell,
                            "metadata": {},
                            "execution_count": None,
                            "outputs": [] if cell_type == "code" else []
                        })
                        if cell_type == "code":
                            code_cell_count += 1
                        else:
                            markdown_cell_count += 1
                        current_cell = []
                    # Start new markdown cell
                    cell_type = "markdown"
                    try:
                        cell_number = int(line.split("# Markdown Cell ")[1])
                    except (IndexError, ValueError):
                        logger.warning(f"Invalid markdown cell marker in {filename}: {line}")
                    continue
                current_cell.append(line + "\\n")
                
            # Don't forget the last cell
            if current_cell:
                cells.append({
                    "cell_type": cell_type,
                    "source": current_cell,
                    "metadata": {},
                    "execution_count": None,
                    "outputs": [] if cell_type == "code" else []
                })
                if cell_type == "code":
                    code_cell_count += 1
                else:
                    markdown_cell_count += 1
                
            notebook["cells"] = cells
            logger.info(f"Reconstructed {code_cell_count} code cells and {markdown_cell_count} markdown cells for {filename}")'''

if old_block in content:
    new_content = content.replace(old_block, new_block)
    with open("txtarchive/packunpack.py", "w") as f:
        f.write(new_content)
    print("✅ Fix applied successfully!")
    print("   extract-notebooks now handles # Markdown Cell N markers")
else:
    print("❌ Could not find the target block. Manual edit required.")
    print("   See packunpack_markdown_fix.patch for what to change.")
ENDPYTHON

echo ""
echo "To verify the fix, reinstall the package:"
echo "  pip install -e ."