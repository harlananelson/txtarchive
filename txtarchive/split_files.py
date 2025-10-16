import os
from pathlib import Path
from .header import logger  # Import logger for consistency

# Configuration
MAX_TOKENS = 10000  # Target chunk size (adjustable)
OUTPUT_DIR = "split_txtarchive"  # Where split files go

def split_file(file_path, max_tokens=MAX_TOKENS, output_dir=OUTPUT_DIR):
    """Split a file into chunks under max_tokens, preserving document structure."""
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    logger.info(f"Ensured output directory exists: {output_dir}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    file_name = Path(file_path).stem  # e.g., 'txtarchive'
    file_ext = Path(file_path).suffix  # e.g., '.txt'
    total_tokens = len(content.split())  # Approximate token count
    
    if total_tokens <= max_tokens:
        # No split needed, copy as-is
        output_path = os.path.join(output_dir, f"{file_name}{file_ext}")
        with open(output_path, 'w', encoding='utf-8') as out_f:
            out_f.write(content)
        logger.info(f"Copied {file_name}{file_ext} ({total_tokens} tokens)")
        return
    
    # Split into chunks
    lines = content.splitlines()
    current_chunk = []
    current_tokens = 0
    part_num = 1
    
    for line in lines:
        line_tokens = len(line.split())  # Approximate token count for the line
        if current_tokens + line_tokens > max_tokens and current_chunk:
            # Write current chunk
            output_path = os.path.join(output_dir, f"{file_name}_part{part_num}{file_ext}")
            with open(output_path, 'w', encoding='utf-8') as out_f:
                chunk_content = "\n".join(current_chunk)
                out_f.write(chunk_content)
            logger.info(f"Wrote {output_path} ({current_tokens} tokens)")
            current_chunk = []
            current_tokens = 0
            part_num += 1
        
        current_chunk.append(line)
        current_tokens += line_tokens
    
    # Write final chunk
    if current_chunk:
        output_path = os.path.join(output_dir, f"{file_name}_part{part_num}{file_ext}")
        with open(output_path, 'w', encoding='utf-8') as out_f:
            chunk_content = "\n".join(current_chunk)
            out_f.write(chunk_content)
        logger.info(f"Wrote {output_path} ({current_tokens} tokens)")

def process_directory(input_dir, output_dir=OUTPUT_DIR, max_tokens=MAX_TOKENS):
    """Process all files in input_dir, splitting large ones."""
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Iterate over files
    for file_name in os.listdir(input_dir):
        file_path = os.path.join(input_dir, file_name)
        if os.path.isfile(file_path):
            split_file(file_path, max_tokens, output_dir)

if __name__ == "__main__":
    # Example usage
    input_file = "/app/projects/clinressys01_t1/archive/split_txtarchive/txtarchive.txt"
    split_file(input_file)