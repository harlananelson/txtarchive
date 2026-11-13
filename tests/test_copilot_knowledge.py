"""Copilot retrieval aids: provenance stamps, a pasteable index, per-file exports.

Defaults stay put. Stamps are ignored on unpack and notebook extraction.
"""

import json
import logging
import subprocess
import sys
from pathlib import Path

import pytest

from txtarchive.packunpack import archive_files, extract_notebooks_to_ipynb, unpack_files_auto
from txtarchive.source_paths import (
    INDEX_INSTRUCTION_LIMIT,
    flattened_source_name,
    insert_source_stamps,
    strip_source_stamps,
    unique_flattened_name,
)


def _git(repo, *args):
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _init_repo(repo: Path):
    repo.mkdir(parents=True)
    subprocess.run(["git", "init", "-b", "main", str(repo)], check=True, capture_output=True)
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test User")


def _commit_all(repo: Path):
    _git(repo, "add", "-A")
    _git(repo, "commit", "-m", "init")


class TestStampText:
    def test_line_boundary_stamps_round_trip(self):
        content = "aaaa\nbbbb\ncccc\n"
        stamped = insert_source_stamps(content, "src/a.py", 1, interval=5)
        assert stamped == (
            "SOURCE FILE: src/a.py (part 1)\n"
            "aaaa\n"
            "SOURCE FILE: src/a.py (part 1)\n"
            "bbbb\n"
            "SOURCE FILE: src/a.py (part 1)\n"
            "cccc\n"
        )
        assert strip_source_stamps(stamped) == content

    def test_long_line_stamps_are_inline_and_round_trip(self):
        content = "abcdefghij"
        stamped = insert_source_stamps(content, "a.py", 1, interval=4)
        assert stamped == (
            "SOURCE FILE: a.py (part 1)\n"
            "abcdSOURCE FILE: a.py (part 1)"
            "efghSOURCE FILE: a.py (part 1)"
            "ij"
        )
        assert strip_source_stamps(stamped) == content

    def test_short_file_has_one_leading_stamp(self):
        content = "print('hello')\n"
        stamped = insert_source_stamps(content, "main.py", 3, interval=2000)
        assert stamped.startswith("SOURCE FILE: main.py (part 3)\n")
        assert stamped.count("SOURCE FILE:") == 1
        assert strip_source_stamps(stamped) == content

    def test_spacing_never_exceeds_interval(self):
        content = "".join(f"line {i:03d} ........\n" for i in range(300))
        interval = 400
        stamped = insert_source_stamps(content, "pkg/mod.py", 2, interval=interval)
        stamp = "SOURCE FILE: pkg/mod.py (part 2)"
        assert stamped.startswith(stamp + "\n")
        assert strip_source_stamps(stamped) == content
        assert stamped.count(stamp) >= 1 + (len(content) - 1) // interval

    def test_flatten_keeps_directories_distinct(self):
        assert flattened_source_name("docs/status-validity.qmd") == "docs__status-validity.qmd"
        assert flattened_source_name("src/pkg/helper.py") == "src__pkg__helper.py"
        used = set()
        assert unique_flattened_name("a/b.py", used) == "a__b.py"
        assert unique_flattened_name("a__b.py", used) == "a__b-2.py"


class TestArchiveIntegration:
    def test_default_archive_is_unchanged(self, tmp_path):
        src = tmp_path / "project"
        src.mkdir()
        (src / "main.py").write_text("print('hello')\n")
        archive = tmp_path / "archive.txt"
        archive_files(src, archive, file_types=[".py"], llm_friendly=True)
        text = archive.read_text()
        assert "SOURCE FILE:" not in text
        assert not (tmp_path / "archive_index.md").exists()
        assert not (tmp_path / "archive_files").exists()

    def test_stamps_use_repo_relative_path_and_unpack(self, tmp_path):
        repo = tmp_path / "demo"
        _init_repo(repo)
        docs = repo / "docs"
        docs.mkdir()
        original = "title: example\nvalue: 1\n"
        (docs / "status-validity.qmd").write_text(original)
        _commit_all(repo)

        archive = tmp_path / "llm.txt"
        archive_files(
            repo, archive, file_types=[".qmd"], llm_friendly=True, source_stamps=True,
        )
        text = archive.read_text()
        assert "SOURCE FILE: docs/status-validity.qmd (part 1)\n" in text
        assert str(repo.resolve()) not in text
        plain = tmp_path / "plain.txt"
        archive_files(repo, plain, file_types=[".qmd"], llm_friendly=True)
        restored = tmp_path / "restored"
        unpack_files_auto(restored, archive, force=True)
        plain_restored = tmp_path / "plain_restored"
        unpack_files_auto(plain_restored, plain, force=True)
        got = (restored / "docs" / "status-validity.qmd").read_text()
        assert got == (plain_restored / "docs" / "status-validity.qmd").read_text()
        assert got.strip() == original.strip()
        assert "SOURCE FILE:" not in got

    def test_repeated_stamps_round_trip_with_line_numbers(self, tmp_path):
        src = tmp_path / "project"
        src.mkdir()
        original = "".join(f"value_{i} = {i}\n" for i in range(80))
        (src / "main.py").write_text(original)
        archive = tmp_path / "llm.txt"
        archive_files(
            src,
            archive,
            file_types=[".py"],
            llm_friendly=True,
            source_stamps=True,
            stamp_interval=80,
            line_numbers=True,
        )
        text = archive.read_text()
        assert text.count("SOURCE FILE: main.py (part 1)") >= 3
        assert "# line-numbers: on" in text
        plain = tmp_path / "plain.txt"
        archive_files(
            src, plain, file_types=[".py"], llm_friendly=True, line_numbers=True,
        )
        restored = tmp_path / "restored"
        unpack_files_auto(restored, archive, force=True)
        plain_restored = tmp_path / "plain_restored"
        unpack_files_auto(plain_restored, plain, force=True)
        got = (restored / "main.py").read_text()
        assert got == (plain_restored / "main.py").read_text()
        assert got.strip() == original.strip()
        assert "SOURCE FILE:" not in got

    def test_split_parts_carry_their_own_part_number(self, tmp_path):
        src = tmp_path / "project"
        src.mkdir()
        (src / "a.py").write_text("print('a')\n")
        (src / "b.py").write_text("print('b')\n")
        (src / "c.py").write_text("print('c')\n")
        archive = tmp_path / "archive.txt"
        split_dir = tmp_path / "parts"
        archive_files(
            src,
            archive,
            file_types=[".py"],
            llm_friendly=True,
            source_stamps=True,
            split_output=True,
            max_tokens=1,
            split_output_dir=split_dir,
            copilot_index=True,
        )
        combined = archive.read_text()
        assert "SOURCE FILE: a.py (part 1)" in combined
        assert "SOURCE FILE: b.py (part 2)" in combined
        assert "SOURCE FILE: c.py (part 3)" in combined
        parts = sorted(split_dir.glob("archive_part*.txt"))
        assert len(parts) >= 3
        part2 = parts[1].read_text()
        assert "SOURCE FILE: b.py (part 2)" in part2
        assert "SOURCE FILE: a.py (part 1)" not in part2

        index = (tmp_path / "archive_index.md").read_text()
        assert "1.1 | a.py | print('a')" in index
        assert "2.2 | b.py | print('b')" in index
        assert "3.3 | c.py | print('c')" in index
        assert len(index) <= INDEX_INSTRUCTION_LIMIT

        restored = tmp_path / "restored"
        unpack_files_auto(restored, split_dir, force=True)
        assert (restored / "a.py").read_text().strip() == "print('a')"
        assert (restored / "b.py").read_text().strip() == "print('b')"
        assert (restored / "c.py").read_text().strip() == "print('c')"
        assert "SOURCE FILE" not in (restored / "b.py").read_text()

    def test_index_terse_and_over_limit_warning(self, tmp_path, caplog):
        src = tmp_path / "project"
        src.mkdir()
        description = "D" * 70
        for i in range(130):
            (src / f"file_{i:04d}.py").write_text(f"{description}\n")
        archive = tmp_path / "archive.txt"
        caplog.set_level(logging.WARNING, logger="txtarchive")
        archive_files(
            src, archive, file_types=[".py"], llm_friendly=True, copilot_index=True,
        )
        full = (tmp_path / "archive_index.md").read_text()
        assert len(full) > INDEX_INSTRUCTION_LIMIT
        assert description in full
        assert any("8000" in rec.message and "--index-terse" in rec.message for rec in caplog.records)

        caplog.clear()
        archive_files(
            src, archive, file_types=[".py"], llm_friendly=True, index_terse=True,
        )
        terse = (tmp_path / "archive_index.md").read_text()
        assert len(terse) < len(full)
        assert description not in terse
        assert "1.1 file_0000.py" in terse
        assert not any("--index-terse" in rec.message for rec in caplog.records)

    def test_terse_index_still_warns_when_huge(self, tmp_path, caplog):
        src = tmp_path / "project"
        nested = src / "a_reasonably_long_directory_name"
        nested.mkdir(parents=True)
        for i in range(250):
            (nested / f"component_{i:04d}_with_a_long_stem.py").write_text("x = 1\n")
        archive = tmp_path / "archive.txt"
        caplog.set_level(logging.WARNING, logger="txtarchive")
        archive_files(
            src, archive, file_types=[".py"], llm_friendly=True, index_terse=True,
        )
        terse = (tmp_path / "archive_index.md").read_text()
        assert len(terse) > INDEX_INSTRUCTION_LIMIT
        assert any("even in terse mode" in rec.message for rec in caplog.records)

    def test_per_file_round_trip_and_stamps(self, tmp_path):
        src = tmp_path / "project"
        (src / "docs").mkdir(parents=True)
        original = "alpha\nbeta\n"
        (src / "docs" / "status-validity.qmd").write_text(original)
        (src / "notes.txt").write_text("leave me\n")
        archive = tmp_path / "archive.txt"
        archive_files(
            src,
            archive,
            file_types=[".qmd"],
            llm_friendly=True,
            per_file=True,
            source_stamps=True,
            stamp_interval=4,
        )
        # The bundled archive is stamped too. The per-file export is separate.
        assert "SOURCE FILE: docs/status-validity.qmd (part 1)" in archive.read_text()
        exported = tmp_path / "archive_files" / "docs__status-validity.qmd"
        body = exported.read_text()
        assert body.startswith("# source: docs/status-validity.qmd (repo project)\n")
        assert "SOURCE FILE: docs/status-validity.qmd (part 1)" in body
        # A previous export with a source header is removed; unrelated files stay.
        stale = tmp_path / "archive_files" / "old-export.qmd"
        stale.write_text("# source: gone.qmd (repo project)\n\nold\n")
        (tmp_path / "archive_files" / "notes.txt").write_text("leave me\n")
        archive_files(
            src,
            archive,
            file_types=[".qmd"],
            llm_friendly=True,
            per_file=True,
        )
        assert not stale.exists()
        assert (tmp_path / "archive_files" / "notes.txt").read_text() == "leave me\n"
        restored = tmp_path / "restored"
        unpack_files_auto(restored, tmp_path / "archive_files")
        assert (restored / "docs" / "status-validity.qmd").read_text() == original

    def test_knowledge_stamps_round_trip(self, tmp_path):
        src = tmp_path / "project"
        src.mkdir()
        original = "keep = True\n"
        (src / "main.py").write_text(original)
        archive = tmp_path / "archive.txt"
        archive_files(
            src,
            archive,
            file_types=[".py"],
            llm_friendly=True,
            knowledge=True,
            source_stamps=True,
        )
        numbered = (tmp_path / "archive_knowledge" / "1-main.txt").read_text()
        assert numbered.startswith("# source: main.py (repo project)\n")
        assert "SOURCE FILE: main.py (part 1)\n" in numbered
        restored = tmp_path / "restored"
        unpack_files_auto(restored, tmp_path / "archive_knowledge")
        assert (restored / "main.py").read_text() == original

    def test_standard_archive_is_not_stamped(self, tmp_path, caplog):
        src = tmp_path / "project"
        src.mkdir()
        (src / "main.py").write_text("print('hello')\n")
        archive = tmp_path / "archive.txt"
        caplog.set_level(logging.WARNING, logger="txtarchive")
        archive_files(src, archive, file_types=[".py"], source_stamps=True)
        assert "SOURCE FILE:" not in archive.read_text()
        assert any("standard archive text is unchanged" in rec.message for rec in caplog.records)

    def test_extract_notebooks_ignores_stamps(self, tmp_path):
        src = tmp_path / "notebooks"
        src.mkdir()
        cell = "".join(f"value_{i} = {i}\n" for i in range(40))
        notebook = {
            "nbformat": 4,
            "nbformat_minor": 5,
            "metadata": {},
            "cells": [
                {
                    "cell_type": "code",
                    "execution_count": 1,
                    "metadata": {},
                    "outputs": [{"output_type": "stream", "name": "stdout", "text": ["hidden\n"]}],
                    "source": [cell],
                }
            ],
        }
        (src / "analysis.ipynb").write_text(json.dumps(notebook))
        archive = tmp_path / "notebooks.txt"
        archive_files(
            src,
            archive,
            file_types=[".ipynb"],
            llm_friendly=True,
            extract_code_only=True,
            source_stamps=True,
            stamp_interval=30,
        )
        assert "SOURCE FILE: analysis.ipynb (part 1)" in archive.read_text()
        out = tmp_path / "out"
        extract_notebooks_to_ipynb(archive, out)
        restored = json.loads((out / "analysis.ipynb").read_text())
        source = "".join(restored["cells"][0]["source"])
        assert "SOURCE FILE:" not in source
        assert "value_0 = 0" in source
        assert "value_39 = 39" in source
        assert "hidden" not in source


def test_cli_copilot_flags_present():
    result = subprocess.run(
        [sys.executable, "-m", "txtarchive", "archive", "--help"],
        check=True,
        capture_output=True,
        text=True,
    )
    for flag in (
        "--source-stamps",
        "--stamp-interval",
        "--copilot-index",
        "--index-terse",
        "--per-file",
        "--per-file-dir",
    ):
        assert flag in result.stdout


def test_stamp_interval_flag_enables_stamps(tmp_path):
    src = tmp_path / "project"
    src.mkdir()
    (src / "main.py").write_text("print('hello')\n")
    archive = tmp_path / "llm.txt"
    subprocess.run(
        [
            sys.executable,
            "-m",
            "txtarchive",
            "archive",
            str(src),
            str(archive),
            "--file_types",
            ".py",
            "--llm-friendly",
            "--stamp-interval",
            "50",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    assert "SOURCE FILE: main.py (part 1)" in archive.read_text()
