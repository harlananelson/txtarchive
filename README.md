---
title: "TxtArchive: Code Archiving and File Transfer Toolkit"
author: "Harlan A. Nelson"
format: html
bibliography: references.bib
---

# TxtArchive: Code Archiving and File Transfer Toolkit

TxtArchive is a Python utility for packaging code files into plain text archives with direct integration to Ask Sage for AI-powered analysis [@cite354]. This makes it easy to transfer projects between environments (e.g., local to cloud), share selective code with LLMs for analysis/generation, and ingest codebases into AI knowledge systems [@cite355].

## Key Use Cases

1. **Seamless File Transfer via Copy Buffer**: In restricted environments (e.g., no direct file upload), archive a directory to a text file, copy-paste it, and unpack on the other side [@cite356].
2. **AI-Powered Code Analysis**: Archive and ingest code directly into Ask Sage for intelligent analysis, documentation generation, or code review [@cite357].
3. **Collaborating with LLMs**: Select specific files/types/prefixes to create a clean archive for LLM input—great for targeted code reviews or modifications [@cite358].
4. **LLM-Generated Projects**: Describe an analysis to an LLM, have it output an archive with generated code/notebooks, then unpack for a ready-to-run project [@cite359].

## Features

- **Archive & Unpack**: Combine files into text archives and extract them back to directories [@cite360].
- **AI Integration**: Direct ingestion into Ask Sage for code analysis and documentation [@cite360; @cite397].
- **File Transfer**: Move directories between local and remote systems via text files [@cite360].
- **LLM-Friendly Format**: Strip notebook outputs and metadata for efficient AI analysis [@cite360; @cite505-@cite507].
- **Smart Splitting**: Split large archives into chunks for transfer limits or LLM context windows [@cite360; @cite186-@cite193].
- **Flexible Filtering**: Select files by type, prefix, or directories [@cite360; @cite317-@cite322].
- **Dual Formats**: Standard for exact reconstruction; LLM-optimized for code analysis [@cite360-@cite361].
- **Jupyter Support**: Handle notebooks with code extraction and reconstruction [@cite361; @cite627-@cite649].
- **Word Conversion**: Convert `.docx` files to Markdown for inclusion in archives [@cite232-@cite268].

## Installation

TxtArchive requires Python 3.7.6+ [@cite398].

1. Clone the repository:
   ```bash
   git clone https://github.com/harlananelson/txtarchive.git
   cd txtarchive
   ```
   [@cite362]

2. Install the package:
   ```bash
   pip install -e .
   ```
   [@cite363]

3. Set up Ask Sage integration (optional):
   ```bash
   export ACCESS_TOKEN="your_ask_sage_token"
   ```
   [@cite364; @cite403]

4. Verify the installation:
   ```bash
   python -m txtarchive --version
   ```
   [@cite365; @cite323]

## Core Commands

Run commands via `python -m txtarchive <command> [args] [options]`.
Use `--help` for details on any command [@cite366; @cite323].

### Archive Commands

- **`archive`**: Create a text archive from a directory [@cite324].
- **`archive-and-ingest`**: Create archive and immediately ingest into Ask Sage [@cite325].
- **`archive_subdirectories`**: Archive each subdirectory separately [@cite334].

### Extraction Commands

- **`unpack`**: Extract files from an archive back to a directory [@cite327].
- **`extract-notebooks`**: Reconstruct Jupyter notebooks (.ipynb) from an archive [@cite337].
- **`extract-notebooks-and-quarto`**: Reconstruct both .ipynb and .qmd files [@cite338].

### AI Integration Commands

- **`ingest`**: Ingest a single document into Ask Sage [@cite323].
- **`archive-and-ingest`**: Combined archiving and ingestion workflow [@cite325].

### Generation Commands

- **`generate`**: Use an LLM to create an archive based on a study plan [@cite329].

### Utility Commands

- **`convert-word`**: Convert `.docx` files to Markdown format [@cite364; @cite367-@cite368].

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
[@cite369-@cite370]

### 2. Create LLM-Friendly Archive for Code Review

```bash
# Create optimized archive for LLM analysis, split into 75k token chunks
python -m txtarchive archive "src/" "code_review.txt" \
    --file_types .py .ipynb \
    --llm-friendly \
    --extract-code-only \
    --split-output \
    --max-tokens 75000
```
[@cite370-@cite371]

### 3. Transfer Project via Copy Buffer

```bash
# Local: Create archive
python -m txtarchive archive "project/" "project.txt" \
    --file_types .py .yaml .md \
    --split-output
# Remote: Unpack archive
python -m txtarchive unpack "project.txt" "restored_project/" --replace_existing
```
[@cite371-@cite372]

## Complete Command Reference

### Archive Command

```bash
python -m txtarchive archive <directory> <output_file> [options]
```
[@cite324]

**Key Options:**

- `--file_types .py .ipynb .yaml`: File extensions to include (default: .yaml, .py, .r, .ipynb, .qmd) [@cite318].
- `--llm-friendly`: Optimize format for AI analysis [@cite319].
- `--extract-code-only`: Extract only code/markdown from notebooks.
- `--split-output`: Split the output archive into chunks [@cite320].
- `--max-tokens <int>`: Maximum tokens per split file (default: 100000) [@cite320].
- `--split-output-dir <path>`: Directory for split files [@cite320].
- `--exclude-dirs .git __pycache__`: Directories to skip [@cite321].
- `--root-files setup.py requirements.txt`: Specific root files to include [@cite321].
- `--include-subdirs src tests`: Only include these subdirectories [@cite322].
- `--file_prefixes 01_ config_`: Only files starting with these prefixes [@cite319].
- `--no-subdirectories`: Archive only top-level files [@cite318].

### Archive-and-Ingest Command

```bash
python -m txtarchive archive-and-ingest <directory> <output_file> [options]
```
[@cite325]

Accepts all arguments from the `archive` command.

**Additional Options:**

- `--ingestion-method auto|directory|archive`: How to ingest files (default: auto) [@cite326].
- `--rm-archive`: Remove the archive file after successful ingestion [@cite326].

### Ingestion Command

```bash
python -m txtarchive ingest --file <file_path>
```
[@cite323]

### Unpack Command

```bash
python -m txtarchive unpack <archive_file> <output_directory> [options]
```
[@cite327]

**Options:**

- `--replace_existing`: Overwrite existing files [@cite328].

### Extract Commands

```bash
# Extract notebooks only
python -m txtarchive extract-notebooks <archive_file> <output_directory> [options]
# Extract notebooks and Quarto files
python -m txtarchive extract-notebooks-and-quarto <archive_file> <output_directory> [options]
```
[@cite337; @cite338]

**Options:**

- `--replace_existing`: Overwrite existing files [@cite337; @cite339].

### Convert-Word Command

```bash
python -m txtarchive convert-word <input_path> [output_path] [options]
```
[@cite364]

**Description:**
Converts a single `.docx` file or a directory of `.docx` files to Markdown [@cite259-@cite261; @cite367-@cite368].

**Key Options:**

- `input_path`: The `.docx` file or directory to convert [@cite364].
- `output_path`: The output file or directory (default: same as input, with .md extension) [@cite364; @cite367].
- `--method auto|mammoth|docx|pandoc|basic`: Specify the conversion method (default: auto) [@cite368; @cite254-@cite256].
- `--replace_existing`: Overwrite existing Markdown files [@cite368].

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
    --max-tokens 7500 \
    --ingestion-method archive
```
[@cite373]

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
    --max-tokens 50000
# Extract modified notebooks back
python -m txtarchive extract-notebooks "analysis.txt" "modified_notebooks/" \
    --replace_existing
```
[@cite374]

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
[@cite375]

### Example 4: Multi-Language Project

Archive a project with multiple languages:

```bash
# Archive full-stack project
python -m txtarchive archive "webapp/" "fullstack.txt" \
    --file_types .py .js .jsx .ts .tsx .css .yaml .md \
    --root-files package.json requirements.txt README.md \
    --exclude-dirs node_modules .venv dist build \
    --split-output \
    --max-tokens 100000
```
[@cite376]

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
[@cite377-@cite378]

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
[@cite378]

### Example 7: Documentation with Word Documents

Archive mixed documentation including Word documents. This is a two-step process:

```bash
# Step 1: Convert Word documents to Markdown
python -m txtarchive convert-word "documentation/" "docs_markdown/" \
    --method mammoth \
    --replace_existing
# Step 2: Archive the converted Markdown files
python -m txtarchive archive-and-ingest "docs_markdown/" "archive/docs.txt" \
    --file_types .md .txt \
    --llm-friendly \
    --ingestion-method auto \
    --max-tokens 50000
```

## Ingestion Methods Explained

### Auto Method (Recommended)

Automatically chooses the best ingestion strategy based on project size [@cite380; @cite307-@cite309]:

- Small projects (≤10 files, <1MB): Uses `directory` method [@cite308-@cite309].
- Larger projects: Uses `archive` method with splitting [@cite309].

### Directory Method

Ingests files one by one directly from the filesystem [@cite381; @cite309-@cite310]:

- **Best for**: Small projects, selective file sharing [@cite381].
- **Pros**: No intermediate archive, fine-grained control [@cite381].
- **Cons**: Many API calls for large projects [@cite381].

### Archive Method

Creates an archive first, then ingests it [@cite382; @cite311-@cite314]:

- **Best for**: Large projects, complete codebases [@cite382].
- **Pros**: Single or few API calls, preserves structure [@cite382].
- **Cons**: Creates intermediate files [@cite382].

## File Transfer Workflows

### Local to Cloud/Remote

1. **Archive locally**:
   ```bash
   python -m txtarchive archive "project/" "project.txt" \
       --file_types .py .yaml --root-files requirements.txt \
       --split-output
   ```
   [@cite383]

2. **Transfer**: Copy via clipboard, scp, or cloud storage [@cite383].
3. **Unpack remotely**:
   ```bash
   python -m txtarchive unpack "project.txt" "restored_project/" --replace_existing
   ```
   [@cite383]

### Cloud to Local with AI Analysis

1. **Archive and analyze in cloud**:
   ```bash
   python -m txtarchive archive-and-ingest "cloud_project/" "analysis.txt" \
       --llm-friendly --ingestion-method auto
   ```
   [@cite384]

2. **Download insights**: Get AI analysis from Ask Sage [@cite384].
3. **Apply changes locally**: Use insights to improve code [@cite384].

## AI Integration Features

### Ask Sage Integration

- **Automatic Ingestion**: Direct integration with Ask Sage API [@cite385; @cite301-@cite316].
- **Smart Chunking**: Automatically splits large codebases for optimal ingestion [@cite385; @cite312-@cite313].
- **Token Management**: Respects API limits with intelligent splitting [@cite385; @cite320].
- **Error Handling**: Robust error handling and response validation [@cite385; @cite301-@cite306].

### LLM-Friendly Formatting

- **Clean Code**: Strips unnecessary metadata and outputs [@cite385; @cite505-@cite507].
- **Structured Layout**: Clear file boundaries and table of contents [@cite385; @cite568-@cite574].
- **Token Optimization**: Efficient format to maximize content within token limits [@cite385].
- **Code Focus**: Emphasizes code and documentation over noise [@cite385].

## Configuration and Environment

### Environment Variables

```bash
# Required for Ask Sage integration
export ACCESS_TOKEN="your_ask_sage_api_token"
```
[@cite386; @cite403]

### Configuration Files

Create a `.txtarchive.yaml` in your project root for default settings (Note: this feature is described but not implemented in the provided code):

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
[@cite386]

## Advanced Usage

### Custom File Processing

(Note: This feature is described but not implemented in the provided code).

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
[@cite386]

### Batch Processing

Process multiple projects:

```bash
# Archive multiple subdirectories
python -m txtarchive archive_subdirectories "projects/" \
    --directories proj1 proj2 proj3 \
    --file_types .py .md \
    --combined_archive_name "all_projects.txt"
```
[@cite386; @cite334-@cite336]

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
[@cite386]

## Troubleshooting

### Common Issues

**Large Files or Token Limits** (common in AI ingestion):

- Use `--split-output --max-tokens 5000` to chunk archives [@cite387; @cite320].
- Check logs for "content too long" messages [@cite387; @cite303].
- Reduce file scope with `--file_types` or `--file_prefixes` [@cite387; @cite318-@cite319].

**Missing/Incomplete Files** (during transfer or extraction):

- Double-check `--file_types`, `--file_prefixes`, and `--include-subdirs` [@cite387; @cite318; @cite319; @cite322].
- Verify file permissions and paths [@cite387].

**Ask Sage Ingestion Errors**:

- Ensure `ACCESS_TOKEN` environment variable is set correctly [@cite387; @cite403].
- Check API connectivity and token validity [@cite387].
- Review error messages for "content too long" or other API errors [@cite387; @cite303].
- Try smaller `--max-tokens` values (e.g., 5000) [@cite387; @cite320].
- Use `--ingestion-method auto` for intelligent method selection [@cite387; @cite326].

**Permission/Output Errors** (unpacking remotely):

- Confirm write access to output directories [@cite387].
- Use `--replace_existing` to overwrite safely [@cite387; @cite328].

**LLM-Related Issues** (generated archives won't extract):

- Validate archive format (should have "# TABLE OF CONTENTS" and file sections) [@cite387; @cite568-@cite574].
- Test with `mock` mode in `generate` first [@cite387; @cite332; @cite181-@cite184].

**Performance Issues**:

- Use `--exclude-dirs` to skip unnecessary directories (.git, **pycache**, node_modules) [@cite387; @cite321].
- Enable `--split-output` for large projects [@cite387; @cite320].
- Choose appropriate `--ingestion-method` (`auto` recommended) [@cite387; @cite326].

### Error Handling Features

- **Response Validation**: Automatically checks API responses for success indicators [@cite388; @cite301-@cite306].
- **Content Size Management**: Intelligent chunking and splitting for API limits [@cite388; @cite320].
- **Detailed Logging**: Comprehensive logs in `txtarchve.log` [@cite388; @cite417-@cite420].

### Log Analysis

Check `txtarchve.log` for detailed information:

```bash
# View recent errors
grep "ERROR" txtarchve.log
```
[@cite388]

## Security Notice

TxtArchive does not encrypt or obfuscate content—archives are plain text [@cite386]. When handling sensitive data (e.g., in HIPAA-regulated environments or LLM-generated code that might include proprietary logic), you are solely responsible for compliance with all privacy and security regulations [@cite386]. Always inspect archives for sensitive information before transferring, sharing, or ingesting into AI systems [@cite387].

## Contributing

We welcome contributions! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

For bug reports and feature requests, please use GitHub Issues [@cite388].

## License

This project is licensed under the MIT License [@cite389].

## Changelog

### v0.1.0

- Initial release with basic archive/unpack functionality [@cite390].
- LLM-friendly format support [@cite390; @cite560-@cite596].
- Jupyter notebook handling [@cite390; @cite505-@cite507; @cite617-@cite620].
- Ask Sage integration [@cite390; @cite397-@cite408].
- Robust error handling and response validation [@cite390; @cite301-@cite306].
- Auto-detection of optimal ingestion methods [@cite390; @cite307-@cite309].
- Added Word (`.docx`) to Markdown conversion utility [@cite232-@cite268].
```