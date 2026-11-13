"""Tests for qmd <-> LLM-friendly cell conversion (txtarchive.quarto_cells)."""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from txtarchive.quarto_cells import (  # noqa: E402
    qmd_to_llm_cells,
    llm_cells_to_qmd,
    has_cell_markers,
    _parse_chunk_header,
    get_cell,
    set_cell,
    list_cell_labels,
    CellLookupError,
)

SAMPLE_QMD = '''---
title: "Demo"
format: html
---

# Intro

Some **prose** here.

```{r setup, include=FALSE}
library(dplyr)
```

More text.

```{r, fig.width=7}
plot(1:10)
```
'''


def test_chunk_header_label_and_opts():
    lang, label, opts = _parse_chunk_header("r setup, include=FALSE")
    assert lang == "r"
    assert label == "setup"
    assert opts == [("include", "FALSE")]


def test_chunk_header_no_label():
    lang, label, opts = _parse_chunk_header("r, fig.width=7")
    assert lang == "r"
    assert label is None
    assert opts == [("fig.width", "7")]


def test_chunk_header_paren_value_not_split():
    # comma inside c(6,4) must not split the option list
    _lang, _label, opts = _parse_chunk_header("r, fig.dim=c(6,4), echo=TRUE")
    assert ("fig.dim", "c(6,4)") in opts
    assert ("echo", "TRUE") in opts


def test_qmd_to_cells_structure_and_hashpipe():
    cells = qmd_to_llm_cells(SAMPLE_QMD)
    assert has_cell_markers(cells)
    # YAML becomes a raw cell
    assert "# Raw Cell 1" in cells
    assert 'title: "Demo"' in cells
    # knitr options normalized to #| (booleans lowercased, dots -> dashes)
    assert "#| label: setup" in cells
    assert "#| include: false" in cells
    assert "#| fig-width: 7" in cells
    # code survives
    assert "library(dplyr)" in cells
    assert "plot(1:10)" in cells


def test_cells_to_qmd_roundtrip_idempotent():
    # qmd -> cells -> qmd -> cells should be stable on the second pass
    cells1 = qmd_to_llm_cells(SAMPLE_QMD)
    qmd2 = llm_cells_to_qmd(cells1, default_lang="r")
    cells2 = qmd_to_llm_cells(qmd2)
    assert cells1.strip() == cells2.strip()


def test_cells_to_qmd_emits_fences_and_yaml():
    cells = qmd_to_llm_cells(SAMPLE_QMD)
    qmd = llm_cells_to_qmd(cells, default_lang="r")
    assert qmd.startswith("---\n")
    assert "```{r}" in qmd
    assert "#| label: setup" in qmd
    assert "#| include: false" in qmd


def test_qmd_to_cells_to_ipynb_via_reconstruct():
    from txtarchive.packunpack import _reconstruct_notebook_from_cells
    cells = qmd_to_llm_cells(SAMPLE_QMD)
    nb = _reconstruct_notebook_from_cells(cells, "demo.ipynb", kernel="r_env")
    kinds = [c["cell_type"] for c in nb["cells"]]
    assert kinds[0] == "raw"               # YAML front matter
    assert "markdown" in kinds
    assert "code" in kinds
    code = "".join("".join(c["source"]) for c in nb["cells"] if c["cell_type"] == "code")
    assert "library(dplyr)" in code
    assert "#| include: false" in code     # hash-pipe carried into the ipynb cell


def test_no_yaml_qmd():
    cells = qmd_to_llm_cells("Just prose\n\n```{r}\n1+1\n```\n")
    assert "# Raw Cell" not in cells       # no front matter -> no raw cell
    assert "# Markdown Cell" in cells
    assert "1+1" in cells


def test_archive_extract_roundtrip_qmd_to_ipynb(tmp_path):
    """End-to-end: archive a .qmd (llm-friendly) then extract to .ipynb."""
    from txtarchive.packunpack import archive_files, extract_notebooks_to_ipynb
    qmd = tmp_path / "demo.qmd"
    qmd.write_text(SAMPLE_QMD)
    archive = tmp_path / "demo_archive.txt"
    archive_files(
        str(tmp_path), str(archive),
        explicit_files=["demo.qmd"],
        llm_friendly=True, extract_code_only=True,
    )
    out = tmp_path / "extracted"
    extract_notebooks_to_ipynb(str(archive), str(out), replace_existing=True, kernel="r_env")
    ipynb = out / "demo.ipynb"
    assert ipynb.exists(), "cell-form .qmd should extract to .ipynb"
    nb = json.loads(ipynb.read_text())
    assert nb["cells"][0]["cell_type"] == "raw"
    assert any("library(dplyr)" in "".join(c["source"]) for c in nb["cells"])


# --------------------------------------------------------------------------- #
# get_cell / set_cell by label
# --------------------------------------------------------------------------- #
QMD_HASHPIPE = """---
title: "Demo"
---

# Intro

```{r}
#| label: setup
#| include: false
library(dplyr)
```

More text.

```{r}
#| label: plot
plot(1:10)
```
"""


def test_list_cell_labels_from_knitr_and_hashpipe():
    assert list_cell_labels(SAMPLE_QMD) == ["setup"]
    assert list_cell_labels(QMD_HASHPIPE) == ["setup", "plot"]
    cells = qmd_to_llm_cells(SAMPLE_QMD)
    assert list_cell_labels(cells) == ["setup"]


def test_get_cell_knitr_style():
    cell = get_cell(SAMPLE_QMD, label="setup")
    assert cell["kind"] == "code"
    assert cell["label"] == "setup"
    assert "library(dplyr)" in cell["body"]
    assert ("include", "false") in cell["options"]
    assert "#| label: setup" in cell["source"]
    assert isinstance(cell["index"], int)


def test_get_cell_hashpipe_style():
    cell = get_cell(QMD_HASHPIPE, label="setup")
    assert cell["body"] == "library(dplyr)"
    assert ("include", "false") in cell["options"]
    assert get_cell(QMD_HASHPIPE, label="plot")["body"] == "plot(1:10)"


def test_get_cell_from_cell_markers():
    cells = qmd_to_llm_cells(SAMPLE_QMD)
    cell = get_cell(cells, label="setup")
    assert "library(dplyr)" in cell["body"]


def test_get_cell_missing_label():
    with pytest.raises(CellLookupError, match="No code cell"):
        get_cell(SAMPLE_QMD, label="nope")


def test_get_cell_duplicate_label():
    dup = """
```{r}
#| label: setup
1
```

```{r}
#| label: setup
2
```
"""
    with pytest.raises(CellLookupError, match="Duplicate"):
        get_cell(dup, label="setup")


def test_set_cell_preserves_include_false():
    updated = set_cell(
        QMD_HASHPIPE,
        label="setup",
        source="library(tidyr)\nlibrary(dplyr)",
    )
    assert "#| label: setup" in updated
    assert "#| include: false" in updated
    assert "library(tidyr)" in updated
    assert "library(dplyr)" in updated
    assert "#| label: plot" in updated
    assert "plot(1:10)" in updated
    assert "# Intro" in updated
    assert "More text." in updated
    cell = get_cell(updated, label="setup")
    assert cell["body"] == "library(tidyr)\nlibrary(dplyr)"
    assert ("include", "false") in cell["options"]


def test_set_cell_knitr_style_preserves_header_opts():
    updated = set_cell(SAMPLE_QMD, label="setup", source="library(tidyr)")
    assert "```{r setup, include=FALSE}" in updated
    assert "library(tidyr)" in updated
    assert "library(dplyr)" not in updated
    cell = get_cell(updated, label="setup")
    assert "library(tidyr)" in cell["body"]
    assert ("include", "false") in cell["options"]


def test_set_cell_option_override_from_source():
    updated = set_cell(
        QMD_HASHPIPE,
        label="setup",
        source="#| echo: false\nlibrary(ggplot2)",
        keep_options=True,
    )
    cell = get_cell(updated, label="setup")
    assert cell["body"] == "library(ggplot2)"
    assert ("include", "false") in cell["options"]
    assert ("echo", "false") in cell["options"]


def test_set_cell_keep_options_false():
    updated = set_cell(
        QMD_HASHPIPE,
        label="setup",
        source="library(only)",
        keep_options=False,
    )
    cell = get_cell(updated, label="setup")
    assert cell["body"] == "library(only)"
    assert cell["options"] == [("label", "setup")]


def test_set_cell_missing_and_duplicate():
    with pytest.raises(CellLookupError, match="No code cell"):
        set_cell(SAMPLE_QMD, label="missing", source="x")
    dup = """
```{r}
#| label: setup
1
```

```{r}
#| label: setup
2
```
"""
    with pytest.raises(CellLookupError, match="Duplicate"):
        set_cell(dup, label="setup", source="x")


def test_set_cell_roundtrip_via_cells():
    updated = set_cell(QMD_HASHPIPE, label="plot", source="hist(rnorm(100))")
    cells = qmd_to_llm_cells(updated)
    qmd2 = llm_cells_to_qmd(cells, default_lang="r")
    cell = get_cell(qmd2, label="plot")
    assert "hist(rnorm(100))" in cell["body"]
    setup = get_cell(qmd2, label="setup")
    assert ("include", "false") in setup["options"]
