import os
from pathlib import Path

# Configuration
MAX_CHARS = 100000  # Target chunk size (adjustable)
INPUT_DIR = "lhn_files"  # Directory with your files
OUTPUT_DIR = "split_lhn_files"  # Where split files go

# txtarchive/split_files.py
import os
from pathlib import Path
from .header import logger  # Import logger for consistency

# Configuration
MAX_CHARS = 100000  # Target chunk size (adjustable)
INPUT_DIR = "lhn_files"  # Directory with your files
OUTPUT_DIR = "split_lhn_files"  # Where split files go

def split_file(file_path, max_chars=MAX_CHARS, output_dir=OUTPUT_DIR):
    """Split a file into chunks under max_chars, preserving document structure."""
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    logger.info(f"Ensured output directory exists: {output_dir}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    file_name = Path(file_path).stem  # e.g., 'lhn-llm-friendly'
    file_ext = Path(file_path).suffix  # e.g., '.txt'
    total_chars = len(content)
    
    if total_chars <= max_chars:
        # No split needed, copy as-is
        output_path = os.path.join(output_dir, f"{file_name}{file_ext}")
        with open(output_path, 'w', encoding='utf-8') as out_f:
            out_f.write(f"<DOCUMENT>\n{content}\n</DOCUMENT>")
        logger.info(f"Copied {file_name}{file_ext} ({total_chars} chars)")
        return
    
    # Split into chunks
    lines = content.splitlines()
    current_chunk = []
    current_chars = 0
    part_num = 1
    
    for line in lines:
        line_chars = len(line) + 1  # +1 for newline
        if current_chars + line_chars > max_chars and current_chunk:
            # Write current chunk
            output_path = os.path.join(output_dir, f"{file_name}_part{part_num}{file_ext}")
            with open(output_path, 'w', encoding='utf-8') as out_f:
                chunk_content = "\n".join(current_chunk)
                out_f.write(f"<DOCUMENT>\n# Part {part_num} of {file_name}{file_ext}\n{chunk_content}\n</DOCUMENT>")
            logger.info(f"Wrote {output_path} ({current_chars} chars)")
            current_chunk = []
            current_chars = 0
            part_num += 1
        
        current_chunk.append(line)
        current_chars += line_chars
    
    # Write final chunk
    if current_chunk:
        output_path = os.path.join(output_dir, f"{file_name}_part{part_num}{file_ext}")
        with open(output_path, 'w', encoding='utf-8') as out_f:
            chunk_content = "\n".join(current_chunk)
            out_f.write(f"<DOCUMENT>\n# Part {part_num} of {file_name}{file_ext}\n{chunk_content}\n</DOCUMENT>")
        logger.info(f"Wrote {output_path} ({current_chars} chars)")

def process_directory(input_dir=INPUT_DIR, output_dir=OUTPUT_DIR, max_chars=MAX_CHARS):
    """Process all files in input_dir, splitting large ones."""
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Iterate over files
    for file_name in os.listdir(input_dir):
        file_path = os.path.join(input_dir, file_name)
        if os.path.isfile(file_path):
            split_file(file_path, max_chars, output_dir)

if __name__ == "__main__":
    process_directory()
