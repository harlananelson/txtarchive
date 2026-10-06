"""Checkout paths in every txtarchive pack mode.

An LLM should be able to write a unified diff whose ``a/`` and ``b/`` paths
come from the archive, and ``git apply --check`` should accept that diff.
"""

import re
import subprocess
import sys
from pathlib import Path

import pytest

from txtarchive.packunpack import (
    archive_files,
    unpack_files,
    unpack_files_auto,
)
from txtarchive.source_paths import PATCH_INSTRUCTION, parse_manifest


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


def _commit_all(repo: Path, message="init"):
    _git(repo, "add", "-A")
    _git(repo, "commit", "-m", message)


def _paths_in(text: str):
    return re.findall(r"(?m)^# path: (.+)$", text) + re.findall(
        r"(?m)^path: (.+)$", text
    )


class TestRoundTrip:
    def test_standard_round_trip_restores_relative_paths(self, tmp_path):
        src = tmp_path / "project"
        (src / "pkg").mkdir(parents=True)
        (src / "pkg" / "status-validity.qmd").write_text("title: old\nvalue: 1\n")
        (src / "src").mkdir()
        (src / "src" / "helper.py").write_text("def add(a, b):\n    return a + b\n")
        (src / ".env").write_text("SECRET_TOKEN=do-not-pack\n")

        archive = tmp_path / "archive.txt"
        archive_files(src, archive, file_types=[".py", ".qmd", ".env", ".txt"])
        text = archive.read_text()

        assert "path: pkg/status-validity.qmd" in text
        assert "path: src/helper.py" in text
        assert "SECRET_TOKEN" not in text
        assert "/home/" not in text
        assert str(src.resolve()) not in text

        restored = tmp_path / "restored"
        unpack_files(restored, archive)
        assert (restored / "pkg" / "status-validity.qmd").read_text().strip() == "title: old\nvalue: 1"
        assert (restored / "src" / "helper.py").read_text().strip() == "def add(a, b):\n    return a + b"
        assert not (restored / ".env").exists()

    def test_llm_round_trip(self, tmp_path):
        src = tmp_path / "project"
        src.mkdir()
        (src / "main.py").write_text("print('hello')\n")
        archive = tmp_path / "archive.txt"
        archive_files(src, archive, file_types=[".py"], llm_friendly=True)
        restored = tmp_path / "restored"
        unpack_files_auto(restored, archive, force=True)
        assert (restored / "main.py").read_text().strip() == "print('hello')"


class TestPathHeaders:
    def test_standard_llm_and_manifest(self, tmp_path):
        src = tmp_path / "project"
        src.mkdir()
        (src / "a.py").write_text("a1\na2\n")
        (src / "b.py").write_text("b\n")

        standard = tmp_path / "standard.txt"
        archive_files(src, standard, file_types=[".py"])
        std = standard.read_text()
        assert "---\nFilename: a.py\npath: a.py\n" in std
        assert "# repo: project" in std
        assert "# commit: none" in std
        assert "# branch: none" in std
        rows = parse_manifest(std)
        assert rows == [("1-a.txt", "a.py", 2), ("2-b.txt", "b.py", 1)]
        assert PATCH_INSTRUCTION not in std

        llm = tmp_path / "llm.txt"
        archive_files(src, llm, file_types=[".py"], llm_friendly=True)
        text = llm.read_text()
        assert "# FILE 1: a.py\n# path: a.py\n" in text
        assert "# numbered: 1-a.txt" in text
        assert PATCH_INSTRUCTION in text
        assert parse_manifest(text) == rows

    def test_patch_instructions_can_be_disabled(self, tmp_path):
        src = tmp_path / "project"
        src.mkdir()
        (src / "a.py").write_text("x = 1\n")
        archive = tmp_path / "llm.txt"
        archive_files(
            src, archive, file_types=[".py"], llm_friendly=True, patch_instructions=False,
        )
        text = archive.read_text()
        assert PATCH_INSTRUCTION not in text
        assert "path: a.py" in text

    def test_line_numbers_round_trip(self, tmp_path):
        src = tmp_path / "project"
        src.mkdir()
        (src / "main.py").write_text("print('hello')\nkeep = True\n")
        archive = tmp_path / "llm.txt"
        archive_files(
            src, archive, file_types=[".py"], llm_friendly=True, line_numbers=True,
        )
        text = archive.read_text()
        assert re.search(r"(?m)^\s*1\|print\('hello'\)$", text)
        assert re.search(r"(?m)^\s*2\|keep = True$", text)
        assert "# line-numbers: on" in text
        assert "Do not copy them into the diff." in text
        restored = tmp_path / "restored"
        unpack_files_auto(restored, archive, force=True)
        assert (restored / "main.py").read_text().strip() == "print('hello')\nkeep = True"

    def test_split_parts_carry_manifest(self, tmp_path):
        src = tmp_path / "project"
        src.mkdir()
        (src / "a.py").write_text("print('a')\n")
        (src / "b.py").write_text("print('b')\n")
        (src / "c.py").write_text("print('c')\n")
        archive = tmp_path / "archive.txt"
        split_dir = tmp_path / "parts"
        archive_files(
            src, archive, file_types=[".py"], llm_friendly=True,
            split_output=True, max_tokens=1, split_output_dir=split_dir,
        )
        parts = sorted(split_dir.glob("archive_part*.txt"))
        assert len(parts) >= 2
        for part in parts:
            body = part.read_text()
            assert "# SOURCE MANIFEST" in body
            assert "1-a.txt | a.py | 1" in body
            assert "2-b.txt | b.py | 1" in body
            assert "3-c.txt | c.py | 1" in body
            assert "path:" in body
        later = parts[-1].read_text()
        assert "same index as part 1" in later

        std_archive = tmp_path / "std.txt"
        std_dir = tmp_path / "std_parts"
        archive_files(
            src, std_archive, file_types=[".py"],
            split_output=True, max_tokens=1, split_output_dir=std_dir,
        )
        std_parts = sorted(std_dir.glob("std_part*.txt"))
        assert len(std_parts) >= 2
        assert all("1-a.txt | a.py |" in p.read_text() for p in std_parts)
        assert all("# SOURCE MANIFEST" in p.read_text() for p in std_parts)
        std_restored = tmp_path / "std_restored"
        unpack_files_auto(std_restored, std_dir)
        assert (std_restored / "a.py").read_text().strip() == "print('a')"
        assert "SOURCE MANIFEST" not in (std_restored / "a.py").read_text()
        # Rejoining must not glue the repeated manifest into a source file.
        restored = tmp_path / "restored"
        unpack_files_auto(restored, split_dir, force=True)
        assert (restored / "a.py").read_text().strip() == "print('a')"
        assert (restored / "b.py").read_text().strip() == "print('b')"
        assert "SOURCE MANIFEST" not in (restored / "a.py").read_text()

    def test_knowledge_files_and_round_trip(self, tmp_path):
        src = tmp_path / "project"
        (src / "docs").mkdir(parents=True)
        original = "alpha\nbeta\n"
        (src / "docs" / "status-validity.qmd").write_text(original)
        archive = tmp_path / "archive.txt"
        archive_files(
            src, archive, file_types=[".qmd"], llm_friendly=True, knowledge=True,
        )
        knowledge = tmp_path / "archive_knowledge"
        numbered = knowledge / "1-status-validity.txt"
        assert numbered.is_file()
        body = numbered.read_text()
        assert body.startswith("# source: docs/status-validity.qmd (repo project)\n")
        manifest = (knowledge / "MANIFEST.txt").read_text()
        assert parse_manifest(manifest) == [("1-status-validity.txt", "docs/status-validity.qmd", 2)]
        assert "/home/" not in body
        assert str(src.resolve()) not in body

        restored = tmp_path / "restored"
        unpack_files_auto(restored, knowledge)
        assert (restored / "docs" / "status-validity.qmd").read_text() == original


class TestGitCheckoutPaths:
    def test_path_is_relative_to_git_root_not_archive_subdir(self, tmp_path):
        repo = tmp_path / "demo"
        _init_repo(repo)
        docs = repo / "docs"
        docs.mkdir()
        (docs / "status-validity.qmd").write_text("alpha\nbeta\n")
        (repo / "src").mkdir()
        (repo / "src" / "helper.py").write_text("x = 1\n")
        _commit_all(repo)
        sha = _git(repo, "rev-parse", "--short", "HEAD")
        branch = _git(repo, "branch", "--show-current")

        archive = tmp_path / "archive.txt"
        # Archive only the docs subdirectory. Unpack must restore that tree,
        # while path: stays relative to the git root.
        archive_files(docs, archive, file_types=[".qmd"])
        text = archive.read_text()
        assert "Filename: status-validity.qmd\npath: docs/status-validity.qmd\n" in text
        assert f"# repo: demo" in text
        assert f"# commit: {sha}" in text
        assert f"# branch: {branch}" in text
        assert str(repo.resolve()) not in text
        assert "/home/" not in text

        restored = tmp_path / "restored"
        unpack_files(restored, archive)
        assert (restored / "status-validity.qmd").read_text().strip() == "alpha\nbeta"
        assert not (restored / "docs").exists()

    def test_diff_against_recorded_path_applies(self, tmp_path):
        repo = tmp_path / "demo"
        _init_repo(repo)
        target = repo / "pkg"
        target.mkdir()
        qmd = target / "status-validity.qmd"
        qmd.write_text("title: old\nvalue: 1\nkeep: yes\n")
        (repo / ".env").write_text("SECRET_TOKEN=do-not-pack\n")
        _commit_all(repo)

        archive = tmp_path / "llm.txt"
        archive_files(repo, archive, file_types=[".qmd", ".py", ".env"], llm_friendly=True)
        text = archive.read_text()
        recorded = re.findall(r"(?m)^# path: (.+)$", text)
        assert recorded == ["pkg/status-validity.qmd"]
        assert "SECRET_TOKEN" not in text
        sha = _git(repo, "rev-parse", "--short", "HEAD")
        assert f"# commit: {sha}" in text

        path = recorded[0]
        diff = (
            f"diff --git a/{path} b/{path}\n"
            f"--- a/{path}\n"
            f"+++ b/{path}\n"
            "@@ -1,3 +1,3 @@\n"
            " title: old\n"
            "-value: 1\n"
            "+value: 2\n"
            " keep: yes\n"
        )
        patch = tmp_path / "patch.diff"
        patch.write_text(diff)
        checked = subprocess.run(
            ["git", "-C", str(repo), "apply", "--check", str(patch)],
            capture_output=True,
            text=True,
        )
        assert checked.returncode == 0, checked.stderr

        knowledge_archive = tmp_path / "knowledge.txt"
        archive_files(
            repo, knowledge_archive, file_types=[".qmd"], llm_friendly=True, knowledge=True,
        )
        kfile = tmp_path / "knowledge_knowledge" / "1-status-validity.txt"
        first = kfile.read_text().splitlines()[0]
        assert first == f"# source: pkg/status-validity.qmd (repo demo @ {sha})"


class TestBackwardCompatible:
    def test_old_standard_archive(self, tmp_path):
        archive = tmp_path / "old.txt"
        archive.write_text(
            "# Archive created on: 2020-01-01\n\n"
            "# Standard Archive Format\n\n"
            "# TABLE OF CONTENTS\n"
            "1. docs/notes.qmd\n\n"
            "---\n"
            "Filename: docs/notes.qmd\n"
            "---\n"
            "hello from old archive\n"
        )
        restored = tmp_path / "restored"
        unpack_files_auto(restored, archive)
        assert (restored / "docs" / "notes.qmd").read_text().strip() == "hello from old archive"

    def test_old_llm_archive(self, tmp_path):
        archive = tmp_path / "old_llm.txt"
        archive.write_text(
            "# Archive created on: 2020-01-01\n\n"
            "# LLM-FRIENDLY CODE ARCHIVE\n"
            "# TABLE OF CONTENTS\n"
            "1. src/helper.py\n\n"
            "################################################################################\n"
            "# FILE 1: src/helper.py\n"
            "################################################################################\n\n"
            "def helper():\n"
            "    return 1\n"
        )
        restored = tmp_path / "restored"
        unpack_files_auto(restored, archive, force=True)
        assert (restored / "src" / "helper.py").read_text().strip() == "def helper():\n    return 1"

    def test_knowledge_path_traversal_is_blocked(self, tmp_path):
        knowledge = tmp_path / "knowledge"
        knowledge.mkdir()
        (knowledge / "1-evil.txt").write_text(
            "# source: ../outside.txt (repo evil)\n\n"
            "nope\n"
        )
        abs_target = tmp_path / "abs-escape.txt"
        (knowledge / "2-abs.txt").write_text(
            f"# source: {abs_target} (repo evil @ abc)\n\n"
            "nope\n"
        )
        restored = tmp_path / "restored"
        unpack_files_auto(restored, knowledge)
        assert not (tmp_path / "outside.txt").exists()
        assert not abs_target.exists()
        assert not any(p.is_file() for p in restored.rglob("*"))


def test_cli_flags_present():
    result = subprocess.run(
        [sys.executable, "-m", "txtarchive", "archive", "--help"],
        check=True,
        capture_output=True,
        text=True,
    )
    for flag in ("--no-patch-instructions", "--line-numbers", "--knowledge", "--knowledge-dir"):
        assert flag in result.stdout
