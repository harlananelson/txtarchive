You should use `unpack`, not `extract-notebooks` or `extract-notebooks-and-quarto`.

**The issue:**

| Command | Format Required | Files Extracted |
|---------|-----------------|-----------------|
| `unpack` | Standard (`---\nFilename:`) | **All files** |
| `extract-notebooks` | LLM-friendly (`# FILE N:`) | `.ipynb` only |
| `extract-notebooks-and-quarto` | Either | `.ipynb` and `.qmd` only |

Your archive:
- **Format:** Standard (`---\nFilename:`)  ✓
- **Contains:** `.py`, `.toml`, `.csv` files (no notebooks)

**Correct command:**

```bash
python -m txtarchive unpack ../.archive/scd-phenotyping.txt ../SCDCernerProject/scd-phenotyping/python --replace_existing
```

The `extract-notebooks-and-quarto` command correctly identified all the files but skipped them because they weren't `.ipynb` or `.qmd` — that's working as designed.

**Quick reference:**

| Your Archive Type | Command |
|-------------------|---------|
| Standard format, any files | `unpack` |
| LLM-friendly, notebooks only | `extract-notebooks` |
| LLM-friendly, notebooks + quarto | `extract-notebooks-and-quarto` |
| Standard format, want only notebooks | Convert to LLM-friendly first, or use `unpack` and delete non-notebook files |