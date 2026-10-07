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

Targeted cell edit API (fills a Posit gap — no official edit-cell-by-ID):
  - ``get_cell(text, label=...)`` / ``set_cell(qmd, label=..., source=...)``
  - ``list_cell_labels(text)``; missing/duplicate labels raise ``CellLookupError``
  - Labels match Quarto ``#| label:`` and knitr-style ``{r setup, ...}`` headers
  - ``set_cell`` mutates one fence in place (preserves ``#|`` options by default)

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


# --------------------------------------------------------------------------- #
# get / set cell by label
# --------------------------------------------------------------------------- #
_HASHPIPE_LABEL = re.compile(r"^#\|\s*label:\s*(.+?)\s*$")
_HASHPIPE_OPT = re.compile(r"^#\|\s*([^:]+):\s*(.*?)\s*$")


class CellLookupError(LookupError):
    """Raised when a cell label is missing or appears more than once."""


def _normalize_label_value(raw):
    return raw.strip().strip("\"'")


def _label_from_code_source(src):
    """Return ``#| label:`` value from a code-cell source, or ``None``."""
    for line in src.splitlines():
        m = _HASHPIPE_LABEL.match(line)
        if m:
            return _normalize_label_value(m.group(1))
    return None


def _split_options_and_body(src):
    """Split leading ``#|`` option lines from the executable body.

    Returns ``(options, body)`` where ``options`` is a list of ``(key, value)``
    pairs (keys are the Quarto option names, e.g. ``"include"``) and ``body``
    is the remaining source with a trailing newline stripped.
    """
    lines = src.split("\n")
    opts = []
    i = 0
    while i < len(lines):
        ln = lines[i]
        if not ln.startswith("#|"):
            break
        m = _HASHPIPE_OPT.match(ln)
        if m:
            opts.append((m.group(1).strip(), m.group(2)))
        i += 1
    body = "\n".join(lines[i:]).strip("\n")
    return opts, body


def _render_options_and_body(opts, body):
    lines = [f"#| {k}: {v}" for k, v in opts]
    if body:
        lines.append(body)
    return "\n".join(lines)


def _merge_options(base_opts, override_opts, label):
    """Merge option lists by key; ``override_opts`` wins. Ensure ``label``."""
    by_key = {k: v for k, v in base_opts}
    order = [k for k, _v in base_opts]
    for k, v in override_opts:
        if k not in by_key:
            order.append(k)
        by_key[k] = v
    by_key["label"] = label
    if "label" not in order:
        order.insert(0, "label")
    return [(k, by_key[k]) for k in order]


def _cells_as_list(qmd_text_or_cells):
    """Normalize ``.qmd`` or cell-marker text to ``[(kind, src), ...]``."""
    if has_cell_markers(qmd_text_or_cells):
        return _iter_llm_cells(qmd_text_or_cells)
    return _iter_llm_cells(qmd_to_llm_cells(qmd_text_or_cells))


def _iter_qmd_fences(qmd_text):
    """Yield metadata for each fenced code cell in a ``.qmd``/``.Rmd`` string.

    Label resolution: prefer a body ``#| label:`` directive; fall back to a
    knitr-style label in the fence header (``{r setup, ...}``).
    """
    lines = qmd_text.split("\n")
    j = 0
    while j < len(lines):
        mo = _FENCE_OPEN.match(lines[j])
        if not mo:
            j += 1
            continue
        fence = mo.group(1)
        lang, header_label, header_opts = _parse_chunk_header(mo.group(2))
        open_idx = j
        j += 1
        body = []
        while j < len(lines) and not re.match(
            r"^" + re.escape(fence) + r"\s*$", lines[j]
        ):
            body.append(lines[j])
            j += 1
        close_idx = j if j < len(lines) else None
        body_src = "\n".join(body)
        yield {
            "open_idx": open_idx,
            "close_idx": close_idx,
            "fence": fence,
            "lang": lang,
            "header_label": header_label,
            "header_opts": header_opts,
            "body_lines": body,
            "source": body_src,
            "label": _label_from_code_source(body_src) or header_label,
        }
        j += 1  # advance past closing fence (or stay at EOF)


def list_cell_labels(qmd_text_or_cells):
    """Return ordered labels of code cells (``.qmd`` or cell-marker text).

    Only cells that carry a ``#| label:`` (after normalization) are included.
    Knitr-style header labels are visible because ``.qmd`` input is routed
    through :func:`qmd_to_llm_cells` first.
    """
    labels = []
    for kind, src in _cells_as_list(qmd_text_or_cells):
        if kind != "code":
            continue
        lab = _label_from_code_source(src)
        if lab:
            labels.append(lab)
    return labels


def get_cell(qmd_text_or_cells, label):
    """Return the code cell with ``#| label: <label>`` (or knitr equivalent).

    ``qmd_text_or_cells`` may be a ``.qmd``/``.Rmd`` string or an LLM cell-marker
    body. Raises :class:`CellLookupError` if the label is missing or duplicated.

    Returns a dict::

        {
            "label": str,
            "kind": "code",
            "index": int,       # 0-based index among all cells
            "source": str,      # full cell source including #| options
            "body": str,        # executable body without leading #| lines
            "options": [(k, v), ...],
        }
    """
    cells = _cells_as_list(qmd_text_or_cells)
    hits = [
        i
        for i, (kind, src) in enumerate(cells)
        if kind == "code" and _label_from_code_source(src) == label
    ]
    if not hits:
        raise CellLookupError(f"No code cell with label {label!r}")
    if len(hits) > 1:
        raise CellLookupError(
            f"Duplicate label {label!r}: found in {len(hits)} code cells "
            f"(indices {hits})"
        )
    idx = hits[0]
    _kind, src = cells[idx]
    opts, body = _split_options_and_body(src)
    return {
        "label": label,
        "kind": "code",
        "index": idx,
        "source": src,
        "body": body,
        "options": opts,
    }


def set_cell(qmd_text, label, source, keep_options=True):
    """Replace the body of the labeled code cell; return the updated ``.qmd``.

    Args:
        qmd_text: full ``.qmd``/``.Rmd`` document string.
        label: cell label to target (``#| label:`` or knitr header label).
        source: new cell body. Leading ``#|`` lines in ``source`` are treated as
            option overrides (merged when ``keep_options`` is True).
        keep_options: if True (default), preserve existing ``#|`` options (and
            knitr header options when the cell has no hash-pipes yet) unless
            overwritten by ``source``. If False, replace the cell interior with
            ``source``, ensuring a ``#| label:`` line is present.

    Raises:
        CellLookupError: label missing or duplicated, or fence unclosed.

    The opening fence line and the rest of the document are left untouched, so
    this is a targeted edit rather than a full qmd↔cells roundtrip.
    """
    fences = [f for f in _iter_qmd_fences(qmd_text) if f["label"] == label]
    if not fences:
        raise CellLookupError(f"No code cell with label {label!r}")
    if len(fences) > 1:
        raise CellLookupError(
            f"Duplicate label {label!r}: found in {len(fences)} code cells"
        )
    cell = fences[0]
    if cell["close_idx"] is None:
        raise CellLookupError(f"Unclosed code fence for label {label!r}")

    old_opts, _old_body = _split_options_and_body(cell["source"])
    new_opts_from_source, new_body = _split_options_and_body(source)
    had_hashpipes = any(ln.startswith("#|") for ln in cell["body_lines"])

    if keep_options:
        if had_hashpipes or new_opts_from_source:
            if had_hashpipes:
                base = list(old_opts)
            else:
                # Promote knitr header label/opts into hash-pipes in the body.
                base = []
                if cell["header_label"]:
                    base.append(("label", cell["header_label"]))
                for k, v in cell["header_opts"]:
                    base.append((k.replace(".", "-"), _r_value_to_yaml(v)))
            final_opts = _merge_options(base, new_opts_from_source, label)
            new_cell_src = _render_options_and_body(final_opts, new_body)
        else:
            # Pure knitr-style cell: keep the fence header, replace body only.
            new_cell_src = new_body
    else:
        if new_opts_from_source:
            final_opts = _merge_options([], new_opts_from_source, label)
            new_cell_src = _render_options_and_body(final_opts, new_body)
        elif new_body:
            new_cell_src = f"#| label: {label}\n{new_body}"
        else:
            new_cell_src = f"#| label: {label}"

    new_body_lines = new_cell_src.split("\n") if new_cell_src else []
    lines = qmd_text.split("\n")
    out = (
        lines[: cell["open_idx"] + 1]
        + new_body_lines
        + lines[cell["close_idx"] :]
    )
    return "\n".join(out)
