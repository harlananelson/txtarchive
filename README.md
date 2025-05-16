# TxtArchive: Code Archiving and Preparation Toolkit

TxtArchive is a Python utility designed to help manage and prepare code, particularly from Jupyter Notebooks and Quarto files. It facilitates creating text-based archives for various purposes including backup, version control in environments with data sensitivities, and efficient input into Large Language Models (LLMs).

Its core functionalities revolve around two main types of "stripping":

1.  **Output Stripping:** Removing the output cells from Jupyter Notebooks. This is crucial in environments handling sensitive data (e.g., under HIPAA regulations) to prevent inadvertent exposure or storage of actual data values within the notebook file.
2.  **Markup & Non-Code Element Stripping (`--llm-friendly`, `--extract-code-only`):** Reducing Jupyter Notebooks and other file types to their core code components. This significantly minimizes the number of tokens when preparing content for Large Language Models, making prompts more efficient and cost-effective.

## !! IMPORTANT: Usage in Sensitive Data Environments (e.g., HIPAA) !!

This tool is designed with features (like output stripping) that can be beneficial when working in environments that handle sensitive data, such as those governed by the Health Insurance Portability and Accountability Act (HIPAA). However, **users of TxtArchive bear the SOLE RESPONSIBILITY for ensuring their use of this tool, and the handling of any data or code, complies with HIPAA and all other applicable data privacy, security regulations, and institutional policies.**

**Please be aware of the following:**

* **User Responsibility is Key:** Your organization's security and compliance requirements always supersede the functionality of any tool. This tool aids a process; it does not guarantee compliance.
* **No Guarantees:** TxtArchive is provided "AS-IS" without any warranty, express or implied, regarding its fitness for HIPAA compliance in your specific use case or its ability to perfectly strip all forms of sensitive data or markup in every scenario.
* **Verify Output Stripping:** If using the output stripping feature for Jupyter Notebooks, **ALWAYS MANUALLY VERIFY** that it has effectively removed all sensitive data from your notebooks *before* further processing, committing to version control, or sharing.
* **Verify Markup/Code Extraction:** If using `--llm-friendly` or `--extract-code-only` options, review the output to ensure it meets your needs for LLM input and hasn't inadvertently removed essential contextual information that *should* be included (while still excluding actual data).
* **Code Content is Your Responsibility:** Ensure that no Protected Health Information (PHI) or other sensitive data is present in your code comments, variable names, string literals, file names, or any part of the code logic itself that gets processed by this tool.
* **Submissions to Large Language Models (LLMs):**
    * You are responsible for any data (including source code) you send to any third-party LLM.
    * Ensure you have appropriate Business Associate Agreements (BAAs) or equivalent data processing agreements in place with LLM providers if any data, even code, could be considered ePHI, is derived from systems handling ePHI, or is otherwise sensitive.
    * Thoroughly understand the data handling, privacy, security policies, and terms of service of the LLM provider before submitting any content.
* **Analysis Plans for AI Code Generation:** If using features that involve generating code from "analysis plans" or similar descriptive documents:
    * Ensure these plans **DO NOT** contain any PHI or overly specific sensitive operational details that could compromise privacy or security.
    * Treat these analysis plans as potentially sensitive documents themselves.
* **Secure Your Environment:** You are responsible for securing your local and remote environments where you use this tool and store your code and data.
* **This Tool Does Not "Understand" PHI:** TxtArchive operates on the structure of code and notebooks. It does not identify or understand the *content* of your data.

**By using TxtArchive, you acknowledge and agree to these terms and responsibilities.**

## Features

* Convert Jupyter Notebooks (`.ipynb`) and Quarto files (`.qmd`) to plain text archives.
* **Strip outputs from Jupyter Notebooks:** Essential for removing potentially sensitive data.
* **LLM-Friendly Archiving (`--llm-friendly`):** Optimizes content for LLMs by removing markdown, raw cells, and other non-essential elements from notebooks, focusing on code and a summary.
* **Extract Code Only (`--extract-code-only`):** A more aggressive mode for LLMs, aiming to extract only the executable code blocks from notebooks.
* Process individual files or entire directories.
* Generate a table of contents within the archive for easier navigation (standard mode).
* Extract files from a previously created text archive back into their original file structure.
* Optionally exclude subdirectories from processing.
* Optionally replace existing files during extraction.

## Installation

1.  Clone the repository:
    ```bash
    git clone [https://github.com/harlananelson/txtarchive.git](https://github.com/harlananelson/txtarchive.git)
    cd txtarchive
    ```
2.  Install dependencies (primarily `nbformat`):
    ```bash
    pip install nbformat
    # If you plan to use LLM functionalities that directly call APIs through this tool
    # (if such features are added), you might need additional packages:
    # pip install openai # or other relevant LLM SDKs
    ```
3.  The tool is typically run as a module: `python -m txtarchive ...`

## Usage Examples

All examples assume you are running the commands from the root directory of the cloned `txtarchive` repository, or that the `txtarchive` module is otherwise in your Python path.

### 1. Archiving for LLM Input (Code-Focused)

**Scenario:** You want to create a highly condensed text archive of Jupyter notebooks and Quarto files from a specific project directory, containing only the code, to minimize tokens for an LLM prompt. You want to process only the top-level directory.

```bash
# Archive Jupyter notebooks and Quarto files, LLM-friendly, code-only
python -m txtarchive archive "path/to/your_project_directory" "output/project_llm_code_only.txt" \
    --file_types .ipynb .qmd \
    --no-subdirectories \
    --llm-friendly \
    --extract-code-only

# What this does:
# - "path/to/your_project_directory": Specifies the source directory.
# - "output/project_llm_code_only.txt": Specifies the output archive file.
# - --file_types .ipynb .qmd: Processes only these file extensions.
# - --no-subdirectories: Ignores any subfolders within the source directory.
# - --llm-friendly: Applies LLM-specific formatting (e.g., strips markdown, raw cells from notebooks).
#                   Implies output stripping for notebooks.
# - --extract-code-only: Further refines --llm-friendly by aiming to include *only* code cells from notebooks.

# REMEMBER:
# - Always review the generated .txt file to ensure it meets your LLM input requirements.
# - Ensure no sensitive data was present in the code itself.