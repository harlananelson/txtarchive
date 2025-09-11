# TxtArchive: Code Archiving and File Transfer Toolkit

TxtArchive is a Python utility for packaging code files into plain text archives with direct integration to Ask Sage for AI-powered analysis. This makes it easy to transfer projects between environments (e.g., local to cloud), share selective code with LLMs for analysis/generation, and ingest codebases into AI knowledge systems.

## Key Use Cases

1. **Seamless File Transfer via Copy Buffer**: In restricted environments (e.g., no direct file upload), archive a directory to a text file, copy-paste it, and unpack on the other side.

2. **AI-Powered Code Analysis**: Archive and ingest code directly into Ask Sage for intelligent analysis, documentation generation, or code review.

3. **Collaborating with LLMs**: Select specific files/types/prefixes to create a clean archive for LLM input—great for targeted code reviews or modifications.

4. **LLM-Generated Projects**: Describe an analysis to an LLM, have it output an archive with generated code/notebooks, then unpack for a ready-to-run project.

## Features

- **Archive & Unpack**: Combine files into text archives and extract them back to directories
- **AI Integration**: Direct ingestion into Ask Sage for code analysis and documentation
- **File Transfer**: Move directories between local and remote systems via text files
- **LLM-Friendly Format**: Strip notebook outputs and metadata for efficient AI analysis
- **Smart Splitting**: Split large archives into chunks for transfer limits or LLM context windows
- **Flexible Filtering**: Select files by type, prefix, or directories
- **Dual Formats**: Standard for exact reconstruction; LLM-optimized for code analysis
- **Jupyter Support**: Handle notebooks with code extraction and reconstruction

## Installation

TxtArchive requires Python 3.8+ and works best with `nbformat` for handling Jupyter notebooks.

1. Clone the repository:
   ```bash
   git clone https://github.com/harlananelson/txtarchive.git
   cd txtarchive
   ```

2. Install the package:
   ```bash
   pip install -e .
   ```

3. Set up Ask Sage integration (optional):
   ```bash
   export ACCESS_TOKEN="your_ask_sage_token"
   ```

4. Verify the installation:
   ```bash
   python -m txtarchive --version
   ```

## Core Commands

Run commands via `python -m txtarchive <command> [args] [options]`. Use `--help` for details on any command.

### Archive Commands
- **archive**: Create a text archive from a directory
- **archive-and-ingest**: Create archive and immediately ingest into Ask Sage
- **archive_subdirectories**: Archive each subdirectory separately

### Extraction Commands
- **unpack**: Extract files from an archive back to a directory
- **extract-notebooks**: Reconstruct Jupyter notebooks (.ipynb) from an archive
- **extract-notebooks-and-quarto**: Reconstruct both .ipynb and .qmd files

### AI Integration Commands
- **ingest**: Ingest a single document into Ask Sage
- **archive-and-ingest**: Combined archiving and ingestion workflow

### Generation Commands
- **generate**: Use an LLM to create an archive based on a study plan

## Quick Start Examples

### 1. Archive and Ingest Your Python Package
```bash
# Archive and ingest your package for AI analysis
python -m txtarchive archive-and-ingest "my_package" "archive/my_package.txt" \
    --file_types .py .md \
    --root-files setup.py requirements.txt \
    --exclude-dirs .venv __pycache__ .git \
    --llm-friendly \
    --ingestion-method auto
```

### 2. Create LLM-Friendly Archive for Code Review
```bash
# Create optimized archive for LLM analysis
python -m txtarchive archive "src/" "code_review.txt" \
    --file_types .py .ipynb \
    --llm-friendly \
    --extract-code-only \
    --split-output \
    --split-max-tokens 75000
```

### 3. Transfer Project via Copy Buffer
```bash
# Local: Create archive
python -m txtarchive archive "project/" "project.txt" \
    --file_types .py .yaml .md \
    --split-output

# Remote: Unpack archive
python -m txtarchive unpack "project.txt" "restored_project/" --replace_existing
```

## Complete Command Reference

### Archive Command
```bash
python -m txtarchive archive <directory> <output_file> [options]
```

**Key Options:**
- `--file_types .py .ipynb .yaml`: File extensions to include
- `--llm-friendly`: Optimize format for AI analysis
- `--extract-code-only`: Extract only code from notebooks
- `--split-output`: Split into smaller chunks
- `--split-max-tokens 75000`: Max tokens per chunk
- `--exclude-dirs .git __pycache__`: Directories to skip
- `--root-files setup.py requirements.txt`: Specific root files to include
- `--include-subdirs src tests`: Only include these subdirectories
- `--file_prefixes 01_ config_`: Only files starting with these prefixes
- `--no-subdirectories`: Archive only top-level files

### Archive-and-Ingest Command
```bash
python -m txtarchive archive-and-ingest <directory> <output_file> [options]
```

**Additional Options:**
- `--ingestion-method auto|directory|archive`: How to ingest files
  - `auto`: Automatically choose based on project size
  - `directory`: Ingest files one by one
  - `archive`: Create archive first, then ingest
- `--max-tokens 75000`: Maximum tokens per ingestion chunk
- `--keep-archive`: Keep archive file after ingestion

### Ingestion Command
```bash
python -m txtarchive ingest --file <file_path>
```

### Unpack Command
```bash
python -m txtarchive unpack <archive_file> <output_directory> [options]
```

**Options:**
- `--replace_existing`: Overwrite existing files

### Extract Commands
```bash
# Extract notebooks only
python -m txtarchive extract-notebooks <archive_file> <output_directory> [options]

# Extract notebooks and Quarto files
python -m txtarchive extract-notebooks-and-quarto <archive_file> <output_directory> [options]
```

## Comprehensive Examples

### Example 1: Python Package Analysis
Analyze a complete Python package with Ask Sage:

```bash
# Archive and ingest a Python package for AI analysis
python -m txtarchive archive-and-ingest "txtarchive" "archive/txtarchive.txt" \
    --file_types .py .yaml .md \
    --root-files pyproject.toml README.md \
    --exclude-dirs .venv __pycache__ .git \
    --llm-friendly \
    --split-output \
    --split-max-tokens 7500 \
    --ingestion-method archive
```

### Example 2: Jupyter Notebook Workflow
Work with Jupyter notebooks for data science projects:

```bash
# Archive notebooks for LLM analysis
python -m txtarchive archive "notebooks/" "analysis.txt" \
    --file_types .ipynb \
    --llm-friendly \
    --extract-code-only \
    --file_prefixes 01_ 02_ 03_ \
    --split-output \
    --split-max-tokens 50000

# Extract modified notebooks back
python -m txtarchive extract-notebooks "analysis.txt" "modified_notebooks/" \
    --replace_existing
```

### Example 3: Selective Code Sharing
Share specific parts of a large codebase:

```bash
# Archive only specific modules and configuration
python -m txtarchive archive "large_project/" "selected_code.txt" \
    --file_types .py .yaml \
    --include-subdirs core utils config \
    --root-files requirements.txt docker-compose.yml \
    --llm-friendly \
    --split-output
```

### Example 4: Multi-Language Project
Archive a project with multiple languages:

```bash
# Archive full-stack project
python -m txtarchive archive "webapp/" "fullstack.txt" \
    --file_types .py .js .jsx .ts .tsx .css .yaml .md \
    --root-files package.json requirements.txt README.md \
    --exclude-dirs node_modules .venv dist build \
    --split-output \
    --split-max-tokens 100000
```

### Example 5: Research Project with Mixed Content
Archive a research project with code, notebooks, and documentation:

```bash
# Archive research project
python -m txtarchive archive-and-ingest "research_project/" "research.txt" \
    --file_types .py .ipynb .qmd .md .yaml \
    --root-files environment.yml README.md \
    --include-subdirs src notebooks docs \
    --llm-friendly \
    --extract-code-only \
    --ingestion-method auto \
    --max-tokens 75000
```

### Example 6: Configuration Management
Archive and transfer configuration files:

```bash
# Archive configuration files
python -m txtarchive archive "config/" "configs.txt" \
    --file_types .yaml .json .toml .ini .env \
    --root-files .gitignore .dockerignore \
    --no-subdirectories

# Transfer and unpack on remote system
python -m txtarchive unpack "configs.txt" "deployed_config/" --replace_existing
```

### Example 8: Documentation with Word Documents
Archive mixed documentation including Word documents:

```bash
# Convert Word docs and archive documentation
python -m txtarchive archive-and-ingest "documentation/" "archive/docs.txt" \
    --file_types .md .docx .txt \
    --convert-word \
    --word-method mammoth \
    --llm-friendly \
    --ingestion-method auto \
    --max-tokens 50000
```

### Example 9: Research Project with Mixed Content
Archive a research project with code, notebooks, and Word documents:

```bash
# Complete research project archival
python -m txtarchive archive "research_project/" "archive/research.txt" \
    --file_types .py .ipynb .docx .md .yaml \
    --root-files README.md requirements.txt \
    --convert-word \
    --word-method auto \
    --llm-friendly \
    --extract-code-only \
    --split-output \
    --max-tokens 75000
```

## Ingestion Methods Explained

### Auto Method (Recommended)
Automatically chooses the best ingestion strategy based on project size:
- Small projects (≤10 files, <1MB): Uses directory method
- Larger projects: Uses archive method with splitting

### Directory Method
Ingests files one by one directly from the filesystem:
- Best for: Small projects, selective file sharing
- Pros: No intermediate archive, fine-grained control
- Cons: Many API calls for large projects

### Archive Method
Creates an archive first, then ingests it:
- Best for: Large projects, complete codebases
- Pros: Single or few API calls, preserves structure
- Cons: Creates intermediate files

## File Transfer Workflows

### Local to Cloud/Remote
1. **Archive locally**:
   ```bash
   python -m txtarchive archive "project/" "project.txt" \
       --file_types .py .yaml --root-files requirements.txt \
       --split-output
   ```

2. **Transfer**: Copy via clipboard, scp, or cloud storage

3. **Unpack remotely**:
   ```bash
   python -m txtarchive unpack "project.txt" "restored_project/" --replace_existing
   ```

### Cloud to Local with AI Analysis
1. **Archive and analyze in cloud**:
   ```bash
   python -m txtarchive archive-and-ingest "cloud_project/" "analysis.txt" \
       --llm-friendly --ingestion-method auto
   ```

2. **Download insights**: Get AI analysis from Ask Sage

3. **Apply changes locally**: Use insights to improve code

## AI Integration Features

### Ask Sage Integration
- **Automatic Ingestion**: Direct integration with Ask Sage API
- **Smart Chunking**: Automatically splits large codebases for optimal ingestion
- **Token Management**: Respects API limits with intelligent splitting
- **Error Handling**: Robust error handling and retry logic

### LLM-Friendly Formatting
- **Clean Code**: Strips unnecessary metadata and outputs
- **Structured Layout**: Clear file boundaries and table of contents
- **Token Optimization**: Efficient format to maximize content within token limits
- **Code Focus**: Emphasizes code and documentation over noise

## Configuration and Environment

### Environment Variables
```bash
# Required for Ask Sage integration
export ACCESS_TOKEN="your_ask_sage_api_token"

# Optional: Default archive directory
export TXTARCHIVE_DIR="./archives"

# Optional: Default max tokens
export TXTARCHIVE_MAX_TOKENS="75000"
```

### Configuration Files
Create a `.txtarchive.yaml` in your project root for default settings:

```yaml
default_file_types:
  - .py
  - .md
  - .yaml
  - .ipynb

exclude_dirs:
  - .venv
  - __pycache__
  - .git
  - node_modules
  - dist
  - build

root_files:
  - requirements.txt
  - setup.py
  - pyproject.toml
  - package.json
  - README.md

max_tokens: 75000
llm_friendly: true
```

## Advanced Usage

### Custom File Processing
For specialized file types, extend the package:

```python
from txtarchive.packunpack import archive_files

# Custom archive with specific processing
archive_files(
    directory="my_project",
    output_file_path="custom.txt",
    file_types=[".py", ".sql", ".js"],
    custom_processors={
        ".sql": lambda content: clean_sql_comments(content),
        ".js": lambda content: minify_js(content)
    }
)
```

### Batch Processing
Process multiple projects:

```bash
# Archive multiple subdirectories
python -m txtarchive archive_subdirectories "projects/" \
    --directories proj1 proj2 proj3 \
    --file_types .py .md \
    --combined_archive_name "all_projects.txt"
```

### Integration with CI/CD
Use in automated pipelines:

```bash
# In your CI pipeline
python -m txtarchive archive-and-ingest "$CI_PROJECT_DIR" "ci_analysis.txt" \
    --file_types .py .yaml \
    --exclude-dirs .venv __pycache__ .pytest_cache \
    --ingestion-method archive \
    --max-tokens 50000
```

## Troubleshooting

### Common Issues

**Large Files or Token Limits** (common in AI ingestion):
- Use `--split-output --max-tokens 5000` to chunk archives
- Verify splits concatenate correctly with `cat`
- Check logs for "content too long" messages
- Reduce file scope with `--file_types` or `--file_prefixes`

**Missing/Incomplete Files** (during transfer or extraction):
- Double-check `--file_types`, `--file_prefixes`, and `--include-subdirs` match your project
- For notebooks, ensure `nbformat` is installed
- Verify file permissions and paths

**Ask Sage Ingestion Errors**:
- Ensure `ACCESS_TOKEN` environment variable is set correctly
- Check API connectivity and token validity
- Review error messages for "content too long" or other API errors
- Try smaller `--max-tokens` values (5000, 2000, 1000)
- Use `--ingestion-method auto` for intelligent method selection

**Permission/Output Errors** (unpacking remotely):
- Confirm write access to output directories
- Use `--replace_existing` to overwrite safely
- Check available disk space

**LLM-Related Issues** (generated archives won't extract):
- Validate archive format (should have "# TABLE OF CONTENTS" and file sections)
- Test with mock mode in `generate` first
- Ensure proper file extensions in generated content

**Performance Issues**:
- Use `--exclude-dirs` to skip unnecessary directories (.git, __pycache__, node_modules)
- Enable `--split-output` for large projects
- Choose appropriate `--ingestion-method` (auto recommended)

### Error Handling Features

TxtArchive includes robust error handling for API integrations:

- **Response Validation**: Automatically checks API responses for success indicators
- **Retry Logic**: Graceful handling of temporary failures
- **Progress Tracking**: Clear logging of ingestion success/failure rates
- **Content Size Management**: Intelligent chunking and splitting for API limits
- **Detailed Logging**: Comprehensive logs in `txtarchve.log`

### Log Analysis

Check `txtarchve.log` for detailed information:

```bash
# View recent errors
grep "ERROR" txtarchve.log | tail -10

# Check ingestion results
grep "Successfully ingested\|Failed to ingest" txtarchve.log

# Monitor token usage
grep "tokens" txtarchve.log
```

### Performance Tips

1. **For Large Codebases**: Use archive method with splitting
2. **For Small Projects**: Use directory method for simplicity  
3. **For Mixed Content**: Use auto method for optimal strategy
4. **For Notebooks**: Always use `--extract-code-only` and `--llm-friendly`
5. **For API Limits**: Start with small `--max-tokens` and increase gradually

## Security Notice

TxtArchive does not encrypt or obfuscate content—archives are plain text. When handling sensitive data (e.g., in HIPAA-regulated environments or LLM-generated code that might include proprietary logic), you are solely responsible for compliance with all privacy and security regulations. Always inspect archives for sensitive information before transferring, sharing, or ingesting into AI systems. For high-security needs, consider additional tools like encryption.

## Contributing

We welcome contributions! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality  
4. Ensure all tests pass
5. Submit a pull request

For bug reports and feature requests, please use GitHub Issues.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Changelog

### v0.1.0
- Initial release with basic archive/unpack functionality
- LLM-friendly format support
- Jupyter notebook handling
- Ask Sage integration
- Robust error handling and response validation
- Auto-detection of optimal ingestion methods