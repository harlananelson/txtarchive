"""Synthetic, PHI-free Databricks HTML export conversion tests.

The fixtures are built in this file. Do not load real notebook exports.
"""
import json
import os
import subprocess
import sys
import urllib.parse
from base64 import b64encode
from pathlib import Path

import pytest

from txtarchive.html_converter import (
    convert_html_to_markdown,
    convert_html_to_markdown_text,
    databricks_html_to_markdown,
    is_databricks_notebook_html,
)


REPO_ROOT = Path(__file__).resolve().parents[1]


def _encode_model(model, encoding="b64_unquote"):
    raw = json.dumps(model, separators=(",", ":"))
    if encoding == "raw":
        return raw
    if encoding == "unquote":
        return urllib.parse.quote(raw)
    # Default: base64(URL-encoded JSON), as used by Databricks HTML exports.
    return b64encode(urllib.parse.quote(raw).encode("utf-8")).decode("ascii")


def _mini_model():
    """A tiny NotebookV1-shaped model. No person-level values."""
    return {
        "version": "NotebookV1",
        "name": "synthetic-probe-access",
        "language": "python",
        "commands": [
            {
                "position": 2.0,
                "commandType": "auto",
                "command": "display(summary)",
                "results": {
                    "type": "table",
                    "data": [
                        ["region", "n"],
                        ["north", "10"],
                        ["south", "12"],
                    ],
                },
            },
            {
                "position": 1.0,
                "commandType": "auto",
                "command": "print('region_counts')",
                "results": {"type": "listResults", "data": ["ok", "n=3"]},
            },
            {
                "position": 3.0,
                "commandType": "auto",
                "command": "display(fig)",
                "results": {"type": "image", "data": "not-a-real-image"},
            },
            {
                "position": 4.0,
                "commandType": "auto",
                "command": "raise RuntimeError('synthetic failure')",
                "errorSummary": "RuntimeError: synthetic failure",
                "error": "RuntimeError: synthetic failure",
                "results": {},
            },
        ],
    }


def _databricks_html(model=None, encoding="b64_unquote", include_meta=True, payload=None):
    if model is None:
        model = _mini_model()
    if payload is None:
        payload = _encode_model(model, encoding)
    # Raw JSON contains double quotes; put it in a double-quoted JS string.
    # Base64 / percent-encoded payloads are quote-safe in single quotes.
    if encoding == "raw" or (payload and '"' in payload and "'" not in payload):
        escaped = payload.replace("\\", "\\\\").replace('"', '\\"')
        assignment = f'var __DATABRICKS_NOTEBOOK_MODEL = "{escaped}"'
    else:
        assignment = f"var __DATABRICKS_NOTEBOOK_MODEL = '{payload}'"
    meta = '  <meta name="databricks-html-version" content="1">\n' if include_meta else ""
    title = model.get("name", "Fixture")
    return (
        "<!DOCTYPE html>\n<html>\n<head>\n"
        f"{meta}<title>{title} - Databricks</title>\n"
        "</head>\n<body>\n  <div id=\"content\"></div>\n"
        f"  <script>{assignment}</script>\n"
        "</body>\n</html>\n"
    )


def _quarto_html():
    return """<!DOCTYPE html>
<html>
<head>
<title>Quarto Analysis</title>
<style>body { font-family: sans-serif; }</style>
<script>console.log("quarto-boilerplate");</script>
</head>
<body>
<div id="quarto-content">
<main>
<h1>Analysis Results</h1>
<h2>Introduction</h2>
<p>This is a Quarto report about region counts, not a Databricks export.</p>
<pre><code class="language-python">import pandas as pd</code></pre>
</main>
</div>
<script>/* more JS */</script>
<footer>boilerplate footer</footer>
</body>
</html>
"""


def _assert_expected_cells(md):
    assert "# synthetic-probe-access" in md
    assert "Language: python" in md
    # Cells are ordered by position: print, display(summary), display(fig), raise
    assert md.index("print('region_counts')") < md.index("display(summary)")
    assert "```python" in md
    assert "print('region_counts')" in md
    assert "ok" in md and "n=3" in md
    assert "display(summary)" in md
    assert "| region | n |" in md
    assert "| north | 10 |" in md
    assert "| south | 12 |" in md
    assert "display(fig)" in md
    assert "[Databricks image output omitted]" in md
    assert "not-a-real-image" not in md
    assert "### Error" in md
    assert "RuntimeError: synthetic failure" in md


def test_detects_databricks_export():
    html = _databricks_html()
    assert is_databricks_notebook_html(html)
    assert not is_databricks_notebook_html(_quarto_html())
    assert not is_databricks_notebook_html("<html><body><p>hi</p></body></html>")


@pytest.mark.parametrize("encoding", ["b64_unquote", "unquote", "raw"])
def test_decode_payload_encodings(encoding):
    md = databricks_html_to_markdown(_databricks_html(encoding=encoding))
    _assert_expected_cells(md)


def test_convert_html_to_markdown_and_text_variant(tmp_path):
    html = _databricks_html()
    path = tmp_path / "synthetic-probe-access.html"
    path.write_text(html, encoding="utf-8")
    file_md = convert_html_to_markdown(path, extract_images=False)
    text_md = convert_html_to_markdown_text(html)
    _assert_expected_cells(file_md)
    _assert_expected_cells(text_md)


def test_decode_failure_raises():
    garbage = _databricks_html(payload="!!!!not-a-notebook-model!!!!")
    with pytest.raises(ValueError, match="could not decode __DATABRICKS_NOTEBOOK_MODEL"):
        databricks_html_to_markdown(garbage)
    with pytest.raises(ValueError, match="could not decode __DATABRICKS_NOTEBOOK_MODEL"):
        convert_html_to_markdown_text(garbage)

    meta_only = (
        "<!DOCTYPE html><html><head>"
        '<meta name="databricks-html-version" content="1">'
        "<title>Empty Shell</title></head>"
        "<body><div id=\"content\"></div></body></html>"
    )
    assert is_databricks_notebook_html(meta_only)
    with pytest.raises(ValueError, match="no __DATABRICKS_NOTEBOOK_MODEL payload"):
        databricks_html_to_markdown(meta_only)


def _run_convert_html(html_path, output_path):
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT) + os.pathsep + env.get("PYTHONPATH", "")
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "txtarchive",
            "convert-html",
            str(html_path),
            str(output_path),
            "--no-extract-images",
            "--replace-existing",
        ],
        cwd=str(REPO_ROOT),
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )


def test_cli_success_and_nonzero_on_decode_failure(tmp_path):
    good = tmp_path / "good.html"
    good.write_text(_databricks_html(), encoding="utf-8")
    good_out = tmp_path / "good.md"
    ok = _run_convert_html(good, good_out)
    assert ok.returncode == 0, ok.stderr
    assert good_out.exists() and good_out.stat().st_size > 0
    _assert_expected_cells(good_out.read_text(encoding="utf-8"))

    bad = tmp_path / "bad.html"
    bad.write_text(_databricks_html(payload="!!!!not-a-notebook-model!!!!"), encoding="utf-8")
    bad_out = tmp_path / "bad.md"
    failed = _run_convert_html(bad, bad_out)
    assert failed.returncode != 0
    assert "Failed to convert" in (failed.stderr + failed.stdout)
    assert not bad_out.exists() or bad_out.stat().st_size == 0


def test_quarto_html_is_unchanged(tmp_path):
    """Normal Quarto HTML still goes through the existing boilerplate+pandoc/regex path."""
    html = _quarto_html()
    assert not is_databricks_notebook_html(html)
    path = tmp_path / "analysis.html"
    path.write_text(html, encoding="utf-8")
    md = convert_html_to_markdown(path, extract_images=False)
    assert "Analysis Results" in md
    assert "Introduction" in md
    assert "import pandas as pd" in md
    assert "console.log" not in md
    assert "quarto-boilerplate" not in md
    assert "synthetic-probe-access" not in md
    assert "Language: python" not in md
    assert "## Cell 1" not in md
