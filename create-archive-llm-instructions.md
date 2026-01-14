# txtarchive Format Specification

> **For AI Systems Generating Archives**: This document specifies the exact syntax required
> for txtarchive to parse your output. The parser uses **literal string matching**—any 
> deviation will cause silent failures.

---

## CRITICAL: Do Not Mix Formats

txtarchive has **two distinct formats** that must NOT be combined:

| Format | File Separator | Notebook Content | Unpack Command |
|--------|----------------|------------------|----------------|
| **Standard** | `---\nFilename: path\n---` | Full JSON | `unpack` |
| **LLM-Friendly** | `# FILE N: path\n###...` | `# Cell N` markers | `extract-notebooks` |

**Fatal Error:** Using standard separators with cell-marker content (or vice versa) will produce corrupt output.

---

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

---

## Notation Convention in This Document

This documentation uses **`~~~` instead of `---`** in examples to prevent a **quoting problem**:
when this document is archived, the parser would interpret example `---\nFilename:` 
patterns as actual file boundaries, creating spurious files.

| In this document | In actual archives |
|------------------|-------------------|
| `~~~` | `---` (exactly 3 hyphens) |

**When generating actual archives:** Always use `---` (three hyphens), never `~~~`.

This is analogous to escaping backticks in markdown documentation about markdown.

---

## Standard Format Specification

### Parser Logic (Why Precision Matters)

The txtarchive unpack function uses this exact split:

```python
sections = combined_content.split("---\nFilename: ")[1:]
```

This means:
- `---\nFilename: ` must appear **exactly** as written
- 3 dashes, newline, the word "Filename", colon, space
- Any variation = zero files extracted

### Correct Format Template

```
# Archive created on: YYYY-MM-DD HH:MM:SS

# Standard Archive Format

# TABLE OF CONTENTS
1. path/to/file1.py
2. path/to/file2.py

~~~
Filename: path/to/file1.py
~~~
<file1 content here>

~~~
Filename: path/to/file2.py
~~~
<file2 content here>

```

**Remember:** Replace `~~~` with `---` in actual output.

### Separator Rules

| Element | Exact Requirement | Common Mistakes |
|---------|-------------------|-----------------|
| Opening separator | Exactly `---` (3 hyphens) | `--------`, `-----`, `- - -`, `***` |
| Newline after opener | Single `\n` | Missing newline, extra spaces |
| Filename line | `Filename: ` (with space after colon) | `Filename:` (no space), `File:`, `## Filename:` |
| Path format | Forward slashes, no quotes | Backslashes, wrapped in quotes |
| Closing separator | Exactly `---` (3 hyphens) | Same as opener mistakes |
| Newline after closer | Single `\n` | Missing newline |

### Example: Multiple Files

```
# Archive created on: 2025-12-16 16:40:00

# Standard Archive Format

# TABLE OF CONTENTS
1. README.md
2. src/main.py

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

```

### Anti-Patterns (Standard Format)

All examples below show **INCORRECT** patterns. The error is described, not the `~~~` notation.

```
# WRONG: Too many dashes (must be exactly 3)
--------
Filename: file.py
--------

# WRONG: Missing space after colon
~~~
Filename:file.py
~~~

# WRONG: Markdown header syntax mixed in
## Filename: file.py

# WRONG: Escaped underscores in filename
~~~
Filename: test\_file.py
~~~

# WRONG: Backslashes in path
~~~
Filename: src\main.py
~~~
```

### Content Escaping (Standard Format)

**Important:** If file content contains the literal string `---\nFilename: `, it will corrupt parsing.

The archiver automatically escapes this pattern:
- **During archiving:** `---\nFilename: ` → `---\nFilename: ` (escaped backslash-n)
- **During unpacking:** The escape is reversed

If you are generating archives manually, escape any occurrences of `---\nFilename: ` in file content.

---

## LLM-Friendly Format Specification

Use this format when:
- Creating archives for LLM analysis (token-efficient)
- Using `--llm-friendly --extract-code-only` flags
- Notebooks should be extractable via `extract-notebooks` command

### Parser Logic (LLM-Friendly)

```python
sections = content.split("################################################################################\n# FILE ")
```

This means:
- Exactly 80 `#` characters, newline, `# FILE ` (with space)
- The file number and path follow: `1: path/to/file.py`

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
| File info line | `# FILE N: path/to/file.ext` (space after colon) |
| Second header | Exactly 80 `#` characters on one line |
| Blank line | Required after second header before content |

### Cell Marker Rules (Notebooks)

The parser looks for lines starting with `# Cell ` or `# Markdown Cell `.

**Code cells:**
```python
# Cell 1
import pandas as pd
print("hello")

# Cell 2
x = 1 + 1
```

**Markdown cells** - content is wrapped in triple quotes:
```python
# Markdown Cell 3
"""
## Section Header
This is markdown content.
- bullet 1
- bullet 2
"""

# Cell 4
# Back to code
```

### Cell Numbering

- Cell numbers reflect **original notebook cell indices**
- Numbers may have gaps (empty cells are skipped during archiving)
- **Do not "fix" gaps** - they are intentional and preserve original structure
- Example: `# Cell 2`, `# Cell 3`, `# Cell 5` is valid (cells 1 and 4 were empty)

### Markdown Cell Format (Critical)

The parser expects this exact structure:

```
# Markdown Cell N
"""
<content here>
"""
```

**Rules:**
1. `# Markdown Cell N` on its own line
2. Opening `"""` on the **next line** (not same line as marker)
3. Markdown content follows
4. Closing `"""` on its own line
5. Content inside quotes becomes the cell source

**WRONG:**
```python
# Markdown Cell 3 """   # NO - quotes must be on next line
content
"""

# Markdown Cell 3
"""content here"""      # NO - closing quotes must be on own line
```

**CORRECT:**
```python
# Markdown Cell 3
"""
content here
"""
```

### Anti-Patterns (LLM-Friendly Format)

```
# WRONG: Not enough # characters (must be exactly 80)
##################################################
# FILE 1: notebook.ipynb
##################################################

# WRONG: Missing space after FILE N:
################################################################################
# FILE 1:notebook.ipynb
################################################################################

# WRONG: Wrong spacing in cell marker
#Cell 1          # Missing space after #
# Cell1          # Missing space before number
```

### Hybrid Format Error

**NEVER** mix standard separators with cell markers:

```
# FATAL ERROR - This breaks BOTH parsers:
~~~
Filename: notebook.ipynb
~~~
# Cell 1
import pandas

# Cell 2
print("broken")
```

The standard parser expects JSON notebook content after `---\nFilename:`.
The LLM-friendly parser expects `################################################################################\n# FILE `.

---

## Validation Checklist

### Standard Format
- [ ] Header includes `# Archive created on:` timestamp
- [ ] Header includes `# TABLE OF CONTENTS`
- [ ] Each file section starts with exactly `---` (3 hyphens)
- [ ] Line after `---` is `Filename: <path>` (with space after colon)
- [ ] Line after filename is exactly `---` (3 hyphens)
- [ ] Paths use forward slashes
- [ ] No markdown formatting in separators
- [ ] Content containing `---\nFilename: ` is escaped

### LLM-Friendly Format
- [ ] Header includes `# LLM-FRIENDLY CODE ARCHIVE`
- [ ] Header includes `# TABLE OF CONTENTS`
- [ ] File separators are exactly 80 `#` characters
- [ ] File info line is `# FILE N: path` (space after colon)
- [ ] Blank line after second separator before content
- [ ] Code cells marked with `# Cell N`
- [ ] Markdown cells marked with `# Markdown Cell N`
- [ ] Markdown content wrapped in `"""` on separate lines
- [ ] Cell numbers may have gaps (this is correct)

---

## Quick Reference for AI Generation

**If asked to create a Standard archive:**
```
---
Filename: example.py
---
<content>
```

**If asked to create an LLM-Friendly archive:**
```
################################################################################
# FILE 1: example.py
################################################################################

<content>
```

**For notebooks in LLM-Friendly format:**
```
# Cell 1
code here

# Markdown Cell 2
"""
markdown here
"""

# Cell 3
more code
```