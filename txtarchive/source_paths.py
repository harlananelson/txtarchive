"""Repository-relative paths for txtarchive outputs.

Every packed file records the checkout path an LLM must use in a unified diff
(``--- a/<path>`` / ``+++ b/<path>``). Paths are POSIX and relative to the git
root when the archive directory sits inside a work tree, otherwise relative to
the archive root. Absolute paths — including home directories — are never written
into an archive.
"""

from __future__ import annotations

import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Iterable, Optional


PATCH_INSTRUCTION = (
    "When proposing changes, output a unified diff using the exact `path:` values "
    "as a/ and b/ paths, with enough unchanged context lines; do not invent paths."
)

_LLM_SPLIT = "################################################################################\n# FILE "
_HASH_LINE = re.compile(r"^#{10,}\s*$")
_SOURCE_RE = re.compile(
    r"^# source:\s+(.+?)\s+\(repo\s+(.+?)(?:\s+@\s+([0-9a-fA-F]+))?\)\s*$"
)
# Provenance lines inserted for Copilot retrieval. Unpack drops them.
# A whole-line stamp is ``SOURCE FILE: <path> (part N)``. A stamp inserted
# inside a line longer than the interval has the same text and no extra newline.
STAMP_LINE_RE = re.compile(r"^SOURCE FILE: .+ \(part \d+\)\s*$")
STAMP_INLINE_RE = re.compile(r"SOURCE FILE: .+? \(part \d+\)")
DEFAULT_STAMP_INTERVAL = 2000
INDEX_INSTRUCTION_LIMIT = 8000
_MANIFEST_ROW = re.compile(r"^#\s+(.+?)\s+\|\s+(.+?)\s+\|\s+(\d+)\s*$")
_LINE_NUMBER = re.compile(r"^\s*\d+\|(.*)$")


@dataclass(frozen=True)
class GitContext:
    """Identity of the work tree being archived.

    ``root`` is used only to compute relative paths. It is never serialized.
    ``repo_name`` is the directory name of that root (a single path component),
    or the archive directory name when there is no git metadata.
    """

    root: Optional[Path]
    repo_name: str
    commit: Optional[str]
    branch: Optional[str]

    @property
    def in_git(self) -> bool:
        return self.root is not None


@dataclass
class ArchiveEntry:
    """One file inside an archive."""

    alias: str
    source: str
    content: str
    numbered: str = ""
    line_count: int = 0

    def with_number(self, index: int) -> "ArchiveEntry":
        return ArchiveEntry(
            alias=self.alias,
            source=self.source,
            content=self.content,
            numbered=numbered_name(index, self.alias),
            line_count=len(self.content.splitlines()),
        )


def _git(cwd: Path, *args: str) -> Optional[str]:
    """Run git in ``cwd``. Return stripped stdout, or None on any failure."""
    try:
        result = subprocess.run(
            ["git", "-C", str(cwd), *args],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
            env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def git_context(archive_root: Path) -> GitContext:
    """Describe the git work tree that contains ``archive_root``, if any."""
    archive_root = Path(archive_root)
    fallback = archive_root.name or "archive"
    toplevel = _git(archive_root, "rev-parse", "--show-toplevel")
    if not toplevel:
        return GitContext(root=None, repo_name=fallback, commit=None, branch=None)
    root = Path(toplevel)
    commit = _git(archive_root, "rev-parse", "--short", "HEAD") or None
    branch = _git(archive_root, "branch", "--show-current")
    if not branch:
        branch = None
    repo_name = root.name or fallback
    return GitContext(root=root, repo_name=repo_name, commit=commit, branch=branch)


def _guard_rel(posix_path: str) -> str:
    """Return a safe relative POSIX path. Never an absolute or home path."""
    text = posix_path.replace("\\", "/").strip()
    if re.match(r"^[A-Za-z]:", text):
        text = text.split(":", 1)[1]
    parts = []
    for part in text.split("/"):
        if part in ("", "."):
            continue
        if part == "..":
            # A checkout path must stay inside the root. Fall back to the basename
            # rather than emit a traversal or an absolute location.
            name = PurePosixPath(text).name
            return name or "file"
        parts.append(part)
    if not parts:
        return "file"
    return "/".join(parts)


def archive_alias(rel_path: Path | str) -> str:
    """Archive-relative name stored in Filename / FILE headers (unpack target)."""
    return _guard_rel(Path(str(rel_path)).as_posix())


def repo_relative_posix(file_path: Path, archive_root: Path, git: GitContext) -> str:
    """Checkout path for ``file_path``.

    Inside a git work tree this is relative to ``git rev-parse --show-toplevel``.
    Otherwise it is relative to ``archive_root``. The original suffix is kept.
    """
    try:
        resolved = Path(file_path).resolve()
    except OSError:
        resolved = Path(file_path)
    if git.root is not None:
        try:
            return _guard_rel(resolved.relative_to(git.root.resolve()).as_posix())
        except ValueError:
            pass
    try:
        return _guard_rel(resolved.relative_to(Path(archive_root).resolve()).as_posix())
    except ValueError:
        return _guard_rel(Path(file_path).name)


def numbered_name(index: int, alias: str) -> str:
    """Flattened knowledge filename, e.g. ``29-status-validity.txt``."""
    stem = PurePosixPath(alias.replace("\\", "/")).stem
    safe = re.sub(r"[^A-Za-z0-9._-]+", "-", stem).strip(".-")
    if not safe:
        safe = "file"
    return f"{index}-{safe}.txt"


def number_entries(entries: Iterable[ArchiveEntry]) -> list[ArchiveEntry]:
    return [entry.with_number(idx) for idx, entry in enumerate(entries, 1)]


def format_identity_lines(git: GitContext) -> list[str]:
    return [
        f"# repo: {git.repo_name}",
        f"# commit: {git.commit or 'none'}",
        f"# branch: {git.branch or 'none'}",
    ]


def format_manifest(entries: Iterable[ArchiveEntry]) -> str:
    """Comment block mapping numbered name -> repo path -> line count."""
    lines = [
        "# SOURCE MANIFEST",
        "# path is the repository-relative checkout path (POSIX) for git apply.",
        "# numbered-name | path | lines",
    ]
    for entry in entries:
        lines.append(f"# {entry.numbered} | {entry.source} | {entry.line_count}")
    lines.append("")
    return "\n".join(lines) + "\n"


def format_knowledge_manifest(entries: Iterable[ArchiveEntry], git: GitContext) -> str:
    lines = ["# SOURCE MANIFEST", *format_identity_lines(git)]
    # Reuse the column legend and rows from the in-archive manifest.
    block = format_manifest(entries)
    # format_manifest starts with "# SOURCE MANIFEST\n"; drop that duplicate title.
    rest = block.split("\n", 1)[1]
    return "\n".join(lines) + "\n" + rest


def parse_manifest(text: str) -> list[tuple[str, str, int]]:
    """Parse manifest rows. Returns (numbered_name, path, line_count)."""
    rows = []
    for line in text.splitlines():
        match = _MANIFEST_ROW.match(line)
        if not match:
            continue
        numbered, path, count = match.group(1), match.group(2), match.group(3)
        if not count.isdigit():
            continue
        # Skip the column legend itself ("numbered-name | path | lines").
        if numbered == "numbered-name":
            continue
        rows.append((numbered, path, int(count)))
    return rows


def add_line_numbers(content: str) -> str:
    """Prefix each content line with its 1-based line number (``   1|text``)."""
    ends_nl = content.endswith("\n")
    lines = content.splitlines()
    width = max(4, len(str(max(len(lines), 1))))
    numbered = [f"{i:>{width}}|{line}" for i, line in enumerate(lines, 1)]
    text = "\n".join(numbered)
    if ends_nl:
        text += "\n"
    return text


def strip_line_numbers(content: str) -> str:
    """Inverse of :func:`add_line_numbers`. Lines without the prefix are kept."""
    ends_nl = content.endswith("\n")
    out = []
    for line in content.splitlines():
        match = _LINE_NUMBER.match(line)
        out.append(match.group(1) if match else line)
    text = "\n".join(out)
    if ends_nl:
        text += "\n"
    return text


def render_archive(
    entries: list[ArchiveEntry],
    *,
    llm_friendly: bool,
    git: GitContext,
    created: str,
    include_patch_instructions: bool,
    line_numbers: bool,
) -> str:
    """Render a complete standard or LLM-friendly archive."""
    origin = git.repo_name
    chunks: list[str] = [f"# Archive created on: {created}\n\n"]
    if llm_friendly:
        chunks.append("# LLM-FRIENDLY CODE ARCHIVE\n")
        chunks.append(f"# Generated from: {origin}\n")
        chunks.append(f"# Date: {created}\n\n")
    else:
        chunks.append("# Standard Archive Format\n\n")
    for line in format_identity_lines(git):
        chunks.append(line + "\n")
    chunks.append("\n")
    if include_patch_instructions and llm_friendly:
        chunks.append("# PATCH INSTRUCTIONS\n")
        chunks.append(f"# {PATCH_INSTRUCTION}\n")
        if line_numbers:
            chunks.append(
                "# Line-number prefixes (digits followed by |) are not part of the file. "
                "Do not copy them into the diff.\n"
            )
        chunks.append("\n")
    chunks.append(format_manifest(entries))
    chunks.append("# TABLE OF CONTENTS\n")
    if entries:
        chunks.append("\n".join(f"{idx}. {entry.alias}" for idx, entry in enumerate(entries, 1)))
        chunks.append("\n\n")
    else:
        chunks.append("\n")
    if llm_friendly:
        for idx, entry in enumerate(entries, 1):
            chunks.append(_format_llm_section(idx, entry, line_numbers=line_numbers))
    else:
        for entry in entries:
            chunks.append(_format_standard_section(entry))
    return "".join(chunks)


def _format_standard_section(entry: ArchiveEntry) -> str:
    escaped = entry.content.replace("---\nFilename: ", "---\\nFilename: ")
    return (
        "---\n"
        f"Filename: {entry.alias}\n"
        f"path: {entry.source}\n"
        f"alias: {entry.alias}\n"
        f"numbered: {entry.numbered}\n"
        f"lines: {entry.line_count}\n"
        "---\n"
        f"{escaped}\n\n"
    )


def _format_llm_section(idx: int, entry: ArchiveEntry, *, line_numbers: bool) -> str:
    body = add_line_numbers(entry.content) if line_numbers else entry.content
    meta = [
        "#" * 80,
        f"# FILE {idx}: {entry.alias}",
        f"# path: {entry.source}",
        f"# alias: {entry.alias}",
        f"# numbered: {entry.numbered}",
        f"# lines: {entry.line_count}",
    ]
    if line_numbers:
        meta.append("# line-numbers: on")
    meta.append("#" * 80)
    return "\n".join(meta) + "\n\n" + body + "\n\n"


def knowledge_file_text(entry: ArchiveEntry, git: GitContext) -> str:
    """Flattened knowledge file. First line is the checkout path.

    The blank line after the source header is metadata. Callers that unpack
    strip both so the remaining bytes are the archived content.
    """
    if git.commit:
        first = f"# source: {entry.source} (repo {git.repo_name} @ {git.commit})\n"
    else:
        first = f"# source: {entry.source} (repo {git.repo_name})\n"
    return first + "\n" + entry.content


def source_stamp(source: str, part: int) -> str:
    """One provenance line: ``SOURCE FILE: <path> (part N)``."""
    return f"SOURCE FILE: {source} (part {int(part)})"


def strip_source_stamps(text: str) -> str:
    """Remove provenance stamps so unpack restores the archived bytes.

    Whole-line stamps are dropped. A stamp inserted in the middle of a long
    line is removed as a substring and does not leave an extra newline.
    Text with no ``SOURCE FILE:`` marker is returned unchanged.
    """
    if not text or "SOURCE FILE:" not in text:
        return text
    kept: list[str] = []
    for line in text.splitlines(keepends=True):
        if STAMP_LINE_RE.match(line.rstrip("\r\n")):
            continue
        if "SOURCE FILE:" in line:
            line = STAMP_INLINE_RE.sub("", line)
        kept.append(line)
    return "".join(kept)


def insert_source_stamps(
    content: str,
    source: str,
    part: int,
    interval: int = DEFAULT_STAMP_INTERVAL,
) -> str:
    """Stamp ``content`` so a retrieved chunk can name its origin.

    A stamp line is placed at the start. Further stamps follow every
    ``interval`` characters of the original text, on line boundaries when the
    text has them. A line longer than the gap gets the stamp inline so the
    line can be restored by deleting that substring.

    ``interval`` counts original characters only. Stamps themselves are not
    counted, and removing them with :func:`strip_source_stamps` returns
    ``content``.
    """
    if interval <= 0:
        interval = DEFAULT_STAMP_INTERVAL
    stamp = source_stamp(source, part)
    if content == "":
        return stamp + "\n"
    out: list[str] = [stamp + "\n"]
    since = 0
    index = 0
    length = len(content)
    while index < length:
        remaining = interval - since
        if remaining <= 0:
            out.append(stamp + "\n")
            since = 0
            continue
        window = content[index : index + remaining]
        newline_at = window.find("\n")
        if newline_at != -1:
            take = newline_at + 1
            out.append(window[:take])
            index += take
            since += take
            if since >= interval and index < length:
                out.append(stamp + "\n")
                since = 0
            continue
        if index + remaining < length:
            out.append(window)
            out.append(stamp)
            index += remaining
            since = 0
            continue
        out.append(content[index:])
        break
    return "".join(out)


def stamp_llm_archive(
    content: str,
    part_numbers: list[int],
    interval: int = DEFAULT_STAMP_INTERVAL,
) -> str:
    """Insert provenance stamps into each LLM-friendly file body.

    ``part_numbers`` aligns with file sections in order. The archive header,
    manifest, and ``# FILE`` metadata stay untouched. Standard archives are
    returned unchanged.
    """
    pieces = content.split(_LLM_SPLIT)
    if len(pieces) <= 1:
        return content
    header, tails = pieces[0], pieces[1:]
    if len(tails) != len(part_numbers):
        return content
    stamped = [header]
    for tail, part in zip(tails, part_numbers):
        stamped.append(_LLM_SPLIT + _stamp_section_tail(tail, part, interval))
    return "".join(stamped)


def _source_from_section_tail(tail: str) -> str:
    """Repo path from an LLM section tail, else the archive-relative name."""
    alias = ""
    for line in tail.splitlines():
        if line.startswith("# path:"):
            value = line.split(": ", 1)[1].strip()
            if value:
                return value
        if not alias and ": " in line and not line.startswith("#"):
            alias = line.split(": ", 1)[1].strip()
    return alias or "unknown"


def _stamp_section_tail(tail: str, part: int, interval: int) -> str:
    """Stamp the body of one LLM section tail (text after ``# FILE ``)."""
    lines = tail.splitlines(keepends=True)
    close = None
    for index, line in enumerate(lines):
        if index == 0:
            continue
        if _HASH_LINE.match(line.rstrip("\r\n")):
            close = index
            break
    if close is None:
        return tail
    head = "".join(lines[: close + 1])
    body = "".join(lines[close + 1 :])
    lead_len = len(body) - len(body.lstrip("\n"))
    payload = body[lead_len:]
    stamped = insert_source_stamps(
        payload, _source_from_section_tail(tail), part, interval
    )
    return head + body[:lead_len] + stamped


def flattened_source_name(source: str) -> str:
    """Flatten a repo-relative path into one filename.

    ``docs/status-validity.qmd`` becomes ``docs__status-validity.qmd``.
    Directory separators become ``__`` so ``a/b`` and ``a_b`` stay distinct.
    """
    text = source.replace("\\", "/").strip()
    parts = [part for part in text.split("/") if part not in ("", ".", "..")]
    flat = "__".join(parts) if parts else "file"
    flat = re.sub(r"[^A-Za-z0-9._-]+", "-", flat).strip(".-")
    return flat or "file"


def unique_flattened_name(source: str, used: set[str]) -> str:
    """Return a flattened name that is not already in ``used``."""
    base = flattened_source_name(source)
    if base not in used:
        used.add(base)
        return base
    if "." in base:
        stem, ext = base.rsplit(".", 1)
        ext = "." + ext
    else:
        stem, ext = base, ""
    number = 2
    while True:
        candidate = f"{stem}-{number}{ext}"
        if candidate not in used:
            used.add(candidate)
            return candidate
        number += 1


def one_line_description(content: str, width: int = 72) -> str:
    """First informative line of a file, collapsed and truncated."""
    for raw in content.splitlines():
        line = raw.strip()
        if not line or line.strip("-#=*`\"' ") == "":
            continue
        if line.startswith("SOURCE FILE:"):
            continue
        if line.startswith(("# Cell", "# Markdown Cell", "# Raw Cell", "# MAGIC")):
            continue
        if line in ('"""', "'''"):
            continue
        line = re.sub(r"\s+", " ", line).replace("|", "/")
        if len(line) > width:
            line = line[: width - 3].rstrip() + "..."
        return line
    return ""


def render_copilot_index(
    entries: list[ArchiveEntry],
    part_numbers: list[int],
    git: GitContext,
    *,
    terse: bool = False,
    stamped: bool = False,
    side_stamped: bool = False,
    stamp_interval: int = DEFAULT_STAMP_INTERVAL,
    per_file: Optional[list[tuple[str, ArchiveEntry]]] = None,
) -> str:
    """Compact index an agent can paste into its instructions.

    Each row is ``part.section | path | description``. ``section`` is the
    ``# FILE N`` number (global, not restarted per part).
    """
    lines = [
        "# txtarchive copilot index",
        f"# repo: {git.repo_name} @ {git.commit or 'none'} ({git.branch or 'none'})",
    ]
    if stamped:
        lines.append(
            "# Archive chunks include a line `SOURCE FILE: <path> (part N)`, "
            f"repeated about every {stamp_interval} characters."
        )
    elif side_stamped:
        lines.append(
            "# Per-file and knowledge exports include `SOURCE FILE:` stamps. "
            "The bundled archive text does not."
        )
    else:
        lines.append("# Map part.section (the archive part and # FILE number) to a path.")
    if not terse:
        lines.append("# part.section | path | description")
    lines.append("")
    for index, entry in enumerate(entries, 1):
        part = part_numbers[index - 1] if index - 1 < len(part_numbers) else 1
        if terse:
            lines.append(f"{part}.{index} {entry.source}")
        else:
            desc = one_line_description(entry.content)
            lines.append(f"{part}.{index} | {entry.source} | {desc}")
    if per_file:
        lines.append("")
        lines.append("# per-file" if terse else "# per-file | path | description")
        for name, entry in per_file:
            if terse:
                lines.append(f"{name} {entry.source}")
            else:
                lines.append(
                    f"{name} | {entry.source} | {one_line_description(entry.content)}"
                )
    text = "\n".join(lines)
    if not text.endswith("\n"):
        text += "\n"
    return text


def parse_knowledge_text(text: str) -> Optional[dict]:
    """Parse a knowledge file. None when the first line is not a source header."""
    if not text:
        return None
    lines = text.splitlines(keepends=True)
    match = _SOURCE_RE.match(lines[0].rstrip("\r\n"))
    if not match:
        return None
    rest = "".join(lines[1:])
    if rest.startswith("\r\n"):
        rest = rest[2:]
    elif rest.startswith("\n"):
        rest = rest[1:]
    return {
        "path": match.group(1),
        "repo": match.group(2),
        "commit": match.group(3),
        "content": strip_source_stamps(rest),
    }


def iter_standard_sections(content: str):
    """Yield (archive_relative_name, body, meta) for a standard archive.

    Extra header lines (``path:``, ``alias:``, ``numbered:``, ``lines:``) are
    metadata. Archives that only have ``Filename:`` still yield that name.
    """
    if "---\nFilename: " not in content:
        return
    for section in content.split("---\nFilename: ")[1:]:
        if "\n---\n" not in section:
            continue
        header, body = section.split("\n---\n", 1)
        header_lines = header.splitlines() or [""]
        filename = header_lines[0].strip()
        meta: dict[str, str] = {}
        for line in header_lines[1:]:
            if ": " in line:
                key, value = line.split(": ", 1)
                meta[key.strip().lower()] = value.strip()
        yield filename, body, meta


def iter_llm_sections(content: str):
    """Yield (archive_relative_name, body, meta) for an LLM-friendly archive.

    Metadata lines between ``# FILE N:`` and the closing hash rule are not part
    of the file body. When a section declares ``line-numbers: on``, prefixes are
    removed so unpack restores the original lines.
    """
    parts = content.split(_LLM_SPLIT)
    if len(parts) <= 1:
        return
    for section in parts[1:]:
        newline = section.find("\n")
        if newline == -1:
            continue
        first = section[:newline]
        if ": " not in first:
            continue
        filename = first.split(": ", 1)[1].strip()
        rest = section[newline + 1 :]
        meta: dict[str, str] = {}
        while rest:
            newline = rest.find("\n")
            line = rest if newline == -1 else rest[:newline]
            if _HASH_LINE.match(line):
                rest = "" if newline == -1 else rest[newline + 1 :]
                break
            if line.startswith("# ") and ": " in line:
                key, value = line[2:].split(": ", 1)
                meta[key.strip().lower()] = value.strip()
                rest = "" if newline == -1 else rest[newline + 1 :]
                continue
            break
        body = rest.lstrip("\n")
        # Copilot provenance lines are not file content.
        body = strip_source_stamps(body)
        if meta.get("line-numbers") == "on":
            body = strip_line_numbers(body)
        yield filename, body, meta


def safe_child(output_directory: Path, relative: str) -> Optional[Path]:
    """Resolve ``relative`` under ``output_directory``, or None if it escapes.

    Absolute paths and ``..`` components are rejected so an archive cannot write
    outside the unpack destination (and cannot be steered at a home directory).
    """
    normalized = relative.strip().replace("\\\\", "/").replace("\\", "/")
    if not normalized or normalized.startswith(("/", "~")):
        return None
    if re.match(r"^[A-Za-z]:", normalized):
        return None
    output_directory = Path(output_directory).resolve()
    candidate = (output_directory / normalized).resolve()
    try:
        candidate.relative_to(output_directory)
    except ValueError:
        return None
    return candidate
