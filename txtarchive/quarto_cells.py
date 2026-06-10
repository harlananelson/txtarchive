"""Quarto/R-Markdown <-> LLM-friendly cell conversion.

All `.qmd`/`.Rmd` <-> cell-marker conversion lives here so other projects can
reuse it from one place. The cell-marker form (``# Raw Cell N`` / ``# Markdown
Cell N`` / ``# Cell N``) is the *canonical, source-agnostic* intermediate used by
``packunpack`` for ``.ipynb`` archives. Routing ``.qmd`` through the same cell
form makes the LLM-friendly archive a true neutral hub: any source -> cells ->
any target (``.ipynb`` or ``.qmd``), with the target chosen at extract time
rather than baked in at archive time.

Chunk options are normalized to Quarto ``#|`` hash-pipe directives, which are
valid in BOTH ``.ipynb`` and ``.qmd`` code cells. So a knitr chunk header like
``{r setup, include=FALSE}`` becomes::

    #| label: setup
    #| include: false

inside the code cell. This makes qmd -> cells -> {ipynb, qmd} lossless for the
options (knitr dotted names are mapped to Quarto dashed names, e.g.
``fig.width`` -> ``fig-width``; ``TRUE``/``FALSE`` -> ``true``/``false``).

Known v1 limitations (documented, not silent):
  - The cell form, like ``.ipynb``, does not store a per-cell language, so a
    notebook is assumed single-language. ``llm_cells_to_qmd`` emits one fence
    language for all code cells (``default_lang``, inferred from the kernel).
    Multi-language ``.qmd`` would need the cell form extended to carry language.
  - Complex R-expression option values (e.g. ``fig.dim=c(6,4)``) are passed
    through verbatim after the key is dashed; they are not translated to YAML.
"""

import re

# Opening fence:  ```{r ...}   /   ````{python}   (3+ backticks, a {lang ...} spec)
_FENCE_OPEN = re.compile(r"^(`{3,})\s*\{([^}]*)\}\s*$")
_CELL_MARKER = re.compile(r"^# (?:Raw |Markdown )?Cell \d+\s*$")


def has_cell_markers(text):
    """True if ``text`` contains LLM-friendly cell markers (``# Cell N`` etc.)."""
    return any(_CELL_MARKER.match(ln) for ln in text.splitlines())


# --------------------------------------------------------------------------- #
# chunk-header parsing
# --------------------------------------------------------------------------- #
def _split_top_commas(s):
    """Split on commas that are not inside (), [], {} or quotes."""
    parts, buf, depth, quote = [], [], 0, None
    for ch in s:
        if quote:
            buf.append(ch)
            if ch == quote:
                quote = None
            continue
        if ch in "\"'":
            quote = ch
            buf.append(ch)
        elif ch in "([{":
            depth += 1
            buf.append(ch)
        elif ch in ")]}":
            depth = max(0, depth - 1)
            buf.append(ch)
        elif ch == "," and depth == 0:
            parts.append("".join(buf))
            buf = []
        else:
            buf.append(ch)
    if buf:
        parts.append("".join(buf))
    return [p.strip() for p in parts if p.strip()]


def _r_value_to_yaml(v):
    """Map an R/knitr option value to its Quarto YAML form where unambiguous."""
    v = v.strip()
    if v in ("TRUE", "T"):
        return "true"
    if v in ("FALSE", "F"):
        return "false"
    return v


def _parse_chunk_header(inner):
    """Parse the text inside ``{...}``.

    Returns ``(lang, label_or_None, [(key, value), ...])``.
    e.g. ``"r setup, include=FALSE"`` -> ``("r", "setup", [("include", "FALSE")])``.
    """
    inner = inner.strip()
    m = re.match(r"^([A-Za-z][\w-]*)\s*(.*)$", inner, re.DOTALL)
    if not m:
        return "r", None, []
    lang = m.group(1)
    rest = m.group(2).strip().lstrip(",").strip()
    label, opts = None, []
    for tok in _split_top_commas(rest):
        if "=" in tok:
            k, val = tok.split("=", 1)
            opts.append((k.strip(), val.strip()))
        elif label is None:
            label = tok.strip()
    return lang, label, opts


def _opts_to_hashpipe(label, opts):
    """Render label + knitr options as Quarto ``#|`` directive lines."""
    lines = []
    if label:
        lines.append(f"#| label: {label}")
    for k, v in opts:
        lines.append(f"#| {k.replace('.', '-')}: {_r_value_to_yaml(v)}")
    return lines


# --------------------------------------------------------------------------- #
# qmd  ->  cells
# --------------------------------------------------------------------------- #
def qmd_to_llm_cells(qmd_text):
    """Convert a ``.qmd``/``.Rmd`` string to the LLM-friendly cell-marker body.

    Output matches what ``packunpack._read_file_content`` emits for ``.ipynb``:
    a ``# Raw Cell``/``# Markdown Cell``/``# Cell`` body (no archive header).
    """
    lines = qmd_text.split("\n")
    cells = []  # list of (kind, source_text)
    pos = 0

    # 1. YAML front matter -> raw cell (delimiters included)
    if lines and lines[0].strip() == "---":
        end = next((j for j in range(1, len(lines)) if lines[j].strip() == "---"), None)
        if end is not None:
            cells.append(("raw", "\n".join(lines[: end + 1])))
            pos = end + 1

    # 2. walk the body splitting on code fences
    buf, in_code, fence, hdr = [], False, "", (None, [])

    def flush_md():
        text = "\n".join(buf).strip("\n")
        if text.strip():
            cells.append(("markdown", text))

    def flush_code():
        body = "\n".join(buf).strip("\n")
        hp = _opts_to_hashpipe(hdr[0], hdr[1])
        if hp:
            src = "\n".join(hp + ([body] if body else []))
        else:
            src = body
        cells.append(("code", src))

    j = pos
    while j < len(lines):
        ln = lines[j]
        if not in_code:
            mo = _FENCE_OPEN.match(ln)
            if mo:
                flush_md()
                buf = []
                fence = mo.group(1)
                _lang, label, opts = _parse_chunk_header(mo.group(2))
                hdr = (label, opts)
                in_code = True
            else:
                buf.append(ln)
        else:
            if re.match(r"^" + re.escape(fence) + r"\s*$", ln):
                flush_code()
                buf = []
                in_code = False
                hdr = (None, [])
            else:
                buf.append(ln)
        j += 1
    if in_code:
        flush_code()
    else:
        flush_md()

    return _cells_to_llm_text(cells)


def _cells_to_llm_text(cells):
    """Render ``[(kind, src), ...]`` to the cell-marker body (matches _read_file_content)."""
    content = ""
    n = 0
    for kind, src in cells:
        n += 1
        if kind == "code":
            content += f"# Cell {n}\n{src}\n\n"
        else:
            label = "Markdown Cell" if kind == "markdown" else "Raw Cell"
            content += f'# {label} {n}\n"""\n{src}'
            if not src.endswith("\n"):
                content += "\n"
            content += '"""\n\n'
    return content


# --------------------------------------------------------------------------- #
# cells  ->  qmd
# --------------------------------------------------------------------------- #
def _iter_llm_cells(cell_text):
    """Parse a cell-marker body into ``[(kind, source_text), ...]``.

    Mirrors ``packunpack._reconstruct_notebook_from_cells`` parsing so the two
    stay in agreement.
    """
    cells = []
    lines = cell_text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("# Markdown Cell ") or line.startswith("# Raw Cell "):
            kind = "markdown" if line.startswith("# Markdown Cell ") else "raw"
            i += 1
            if i < len(lines) and lines[i].strip() == '"""':
                i += 1
                body = []
                while i < len(lines) and lines[i].strip() != '"""':
                    body.append(lines[i])
                    i += 1
                cells.append((kind, "\n".join(body)))
            i += 1
        elif line.startswith("# Cell "):
            i += 1
            body = []
            while i < len(lines) and not (
                lines[i].startswith("# Cell ")
                or lines[i].startswith("# Markdown Cell ")
                or lines[i].startswith("# Raw Cell ")
            ):
                body.append(lines[i])
                i += 1
            while body and not body[-1].strip():
                body.pop()
            if any(b.strip() for b in body):
                cells.append(("code", "\n".join(body)))
        else:
            i += 1
    return cells


def llm_cells_to_qmd(cell_text, default_lang="r"):
    """Reconstruct a ``.qmd`` string from the LLM-friendly cell-marker body.

    Args:
        cell_text: the cell-marker body (``# Raw/Markdown/Cell N``).
        default_lang: fence language for code cells (single-language assumption).
    """
    parts = []
    for kind, src in _iter_llm_cells(cell_text):
        src = src.rstrip("\n")
        if kind in ("raw", "markdown"):
            parts.append(src)
        else:
            parts.append(f"```{{{default_lang}}}\n{src}\n```")
    return "\n\n".join(parts) + "\n"
