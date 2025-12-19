# txtarchive Format Specification

> **DOCUMENTATION NOTE:** Examples in this document use `~~~` instead of `---` to prevent
> the parser from treating example snippets as real file boundaries when this document
> is itself archived. In actual archives, use exactly `---` (three hyphens).

## CRITICAL: Do Not Mix Formats

txtarchive has **two distinct formats** that must NOT be combined:

| Format | File Separator | Notebook Content | Unpack Command |
|--------|----------------|------------------|----------------|
| **Standard** | `---\nFilename: path\n---` | Full JSON | `unpack` |
| **LLM-Friendly** | `# FILE N: path\n###...` | `# Cell N` markers | `extract-notebooks` |

**Fatal Error:** Using standard separators with cell-marker content (or vice versa) will produce corrupt output.

~~~

## Standard Format Specification

### Critical Requirement

When generating archives for use with `txtarchive unpack`, you MUST use the **exact separator pattern** shown below. The parser uses literal string matching—any deviation will cause extraction to fail silently.

## Correct Format Template

**NOTE:** Replace `~~~` with `---` in actual archives.

```
# Archive created on: YYYY-MM-DD HH:MM:SS

# TABLE OF CONTENTS
1. path/to/file1.py
2. path/to/file2.ipynb

~~~
Filename: path/to/file1.py
~~~
<file1 content here>

~~~
Filename: path/to/file2.ipynb
~~~
<file2 content here>

```

## Separator Rules

| Element | Exact Requirement | Common Mistakes |
|---------|-------------------|-----------------|
| Opening separator | Exactly `---` (3 hyphens) | `--------`, `-----`, `- - -`, `***` |
| Newline after opener | Single `\n` | Missing newline, extra spaces |
| Filename line | `Filename: ` (with space, no quotes) | `Filename:`, `File:`, `## Filename:` |
| Path format | Forward slashes, no quotes | Backslashes, wrapped in quotes |
| Closing separator | Exactly `---` (3 hyphens) | Same as opener mistakes |
| Newline after closer | Single `\n` | Missing newline |

## Parser Logic (Why This Matters)

The txtarchive unpack function uses this exact split:

```python
sections = combined_content.split("---\nFilename: ")[1:]
```

This means:
- `---\nFilename: ` must appear **exactly** as written
- 3 dashes, newline, the word "Filename", colon, space
- Any variation = zero files extracted

## Example: Single Jupyter Notebook

**NOTE:** Replace `~~~` with `---` in actual archives.

```
# Archive created on: 2025-12-16 16:40:00

# TABLE OF CONTENTS
1. 015-Prepare-Phenotyping-Data.ipynb

~~~
Filename: 015-Prepare-Phenotyping-Data.ipynb
~~~
# Cell 1
import pandas as pd

# Cell 2
df = pd.read_csv("data.csv")

```

## Example: Multiple Files with Subdirectories

**NOTE:** Replace `~~~` with `---` in actual archives.

```
# Archive created on: 2025-12-16 16:40:00

# TABLE OF CONTENTS
1. README.md
2. src/main.py
3. tests/test_main.py

~~~
Filename: README.md
~~~
# My Project

This is the readme.

~~~
Filename: src/main.py
~~~
def main():
    print("Hello")

if __name__ == "__main__":
    main()

~~~
Filename: tests/test_main.py
~~~
import unittest
from src.main import main

class TestMain(unittest.TestCase):
    def test_runs(self):
        main()  # Should not raise

```

## Checklist Before Output

- [ ] Each file section starts with exactly `---` (3 hyphens, NOT `~~~`)
- [ ] Line immediately after `---` is `Filename: <path>`
- [ ] Line immediately after filename is exactly `---` (3 hyphens)
- [ ] No markdown formatting in separators (no `##`, no `**`)
- [ ] No escaped characters in filenames (`\_` should be `_`)
- [ ] Paths use forward slashes (`tests/file.py` not `tests\file.py`)
- [ ] Empty line between end of one file's content and next `---` separator

## Anti-Patterns to Avoid

**NOTE:** These show WRONG patterns. Correct pattern uses exactly `---` (3 hyphens).

```
# WRONG: Too many dashes
--------
Filename: file.py
~~~

# WRONG: Markdown header syntax
## Filename: file.py

# WRONG: Missing space after colon
~~~
Filename:file.py
~~~

# WRONG: Escaped underscores
~~~
Filename: test\_file.py
~~~

# WRONG: Five dashes as closer
~~~
Filename: file.py
-----
```

## Validation (Standard Format)

After generating an archive, verify the first file separator appears exactly as:

```
---
Filename: 
```

(That's 3 hyphens, newline, "Filename:", space)

If you see anything else at the start of a file section, the archive will not unpack correctly.

~~~

## LLM-Friendly Format Specification

Use this format when:
- Creating archives for LLM analysis (token-efficient)
- Using `--llm-friendly --extract-code-only` flags
- Notebooks should be extractable via `extract-notebooks` command

### Correct LLM-Friendly Template

```
# Archive created on: YYYY-MM-DD HH:MM:SS
# LLM-FRIENDLY CODE ARCHIVE
# Generated from: /path/to/source
# Date: YYYY-MM-DD HH:MM:SS

# TABLE OF CONTENTS
1. notebook1.ipynb
2. script.py

################################################################################
# FILE 1: notebook1.ipynb
################################################################################

# Cell 1
import pandas as pd

# Cell 2
df = pd.read_csv("data.csv")

# Markdown Cell 3
"""
## Analysis Section
This cell contains documentation.
"""

# Cell 4
print(df.head())

################################################################################
# FILE 2: script.py
################################################################################

def main():
    print("Hello")

if __name__ == "__main__":
    main()

```

### LLM-Friendly Separator Rules

| Element | Exact Requirement |
|---------|-------------------|
| File header | Exactly 80 `#` characters on one line |
| File info line | `# FILE N: path/to/file.ext` (with space after colon) |
| Second header | Exactly 80 `#` characters on one line |
| Blank line | Required after second header |
| Cell markers | `# Cell N` for code, `# Markdown Cell N` for markdown |

### LLM-Friendly Cell Marker Rules

```python
# Cell 1           # Code cell - content follows directly
import pandas

# Markdown Cell 2  # Markdown cell - wrap content in triple quotes
"""
# Header
This is markdown content.
"""

# Cell 3           # Next code cell
x = 1 + 1
```

### Common LLM-Friendly Mistakes

```
# WRONG: Not enough # characters (should be 80)
##################################################
# FILE 1: notebook.ipynb
##################################################

# WRONG: Missing space after FILE N:
################################################################################
# FILE 1:notebook.ipynb
################################################################################

# WRONG: Using standard separators with cell content (HYBRID - BREAKS BOTH PARSERS)
~~~
Filename: notebook.ipynb
~~~
# Cell 1
import pandas  # This hybrid format breaks both parsers!
```

## Format Selection Decision Tree

```
Creating an archive?
├─ Need to reconstruct exact files later?
│   └─ YES → Standard format (no --llm-friendly flag)
│       └─ Notebooks stored as full JSON
│       └─ Use `unpack` to extract
│
└─ Optimizing for LLM token efficiency?
    └─ YES → LLM-friendly format (--llm-friendly flag)
        └─ Notebooks stored as # Cell N markers
        └─ Use `extract-notebooks` to reconstruct .ipynb
```

## Quoting Problem Warning

This documentation uses `~~~` instead of `---` in examples to avoid a **quoting problem**:
when this document is archived, the parser would interpret example `---\nFilename:` 
patterns as actual file boundaries, creating spurious files like `path/to/file1.py`.

**When generating actual archives:** Always use `---` (three hyphens), not `~~~`.

This is analogous to:
- Escaping backticks in markdown documentation about markdown
- Using heredocs with custom delimiters in shell scripts
- SQL injection prevention through parameterized queries