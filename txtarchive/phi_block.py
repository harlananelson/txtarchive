"""Opt-in PHI skip-and-log.

Default archive runs do not import this module. ``archive_files`` calls
:func:`scan_for_phi` only when ``phi_block`` is true.

A match returns a rule category. The matched text is not returned and must
not be written to a log. This module has no redaction path: callers skip the
whole file and leave the source untouched.
"""

from __future__ import annotations

import re
from pathlib import Path


# Fixed categories. ``skip_line`` refuses any other category string so a
# matched snippet cannot be passed through as the "reason".
_RULES: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("ssn", re.compile(r"\b\d{3}-\d{2}-\d{4}\b")),
    (
        "mrn",
        re.compile(
            r"(?i)\b(?:mrn|medical record number)\b\s*[:#-]?\s*[A-Za-z0-9][A-Za-z0-9-]{2,}"
        ),
    ),
    (
        "dob",
        re.compile(
            r"(?i)\b(?:dob|date of birth)\b\s*[:#-]?\s*(?:\d{4}|\d{1,2})[-/]\d{1,2}[-/](?:\d{4}|\d{1,2})\b"
        ),
    ),
    (
        "patient-id",
        re.compile(r"(?i)\bpatient(?:\s+id|_id)\b\s*[:=#]\s*\S+"),
    ),
)

_CATEGORIES = frozenset(name for name, _pattern in _RULES)


def scan_for_phi(text: str) -> str | None:
    """Return a rule category, or None.

    The return value is one of ``ssn``, ``mrn``, ``dob``, or ``patient-id``.
    It is never the matched text.
    """
    if not text:
        return None
    for category, pattern in _RULES:
        if pattern.search(text):
            return category
    return None


def skip_line(source: str, category: str) -> str:
    """One log line: path and category only."""
    safe_source = source.replace("\r", " ").replace("\n", " ").strip()
    if category not in _CATEGORIES:
        category = "phi"
    return f"skipped | {safe_source} | {category}"


def render_skip_log(skips: list[tuple[str, str]]) -> str:
    """Full skip log. Header plus one line per file. No file contents."""
    lines = [
        "# txtarchive phi-block",
        "# skipped | <repo-relative path> | <rule category>",
    ]
    for source, category in skips:
        lines.append(skip_line(source, category))
    return "\n".join(lines) + "\n"


def default_log_path(output_file_path: Path | str) -> Path:
    """``archive/repo.txt`` -> ``archive/repo_phi_skipped.log``."""
    output_file_path = Path(output_file_path)
    return output_file_path.with_name(f"{output_file_path.stem}_phi_skipped.log")
