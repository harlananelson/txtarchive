"""Opt-in PHI skip-and-log. Default archive runs do not call the scanner.

Provenance flags stay in the normal archive flow with blocking off or on.
"""

import inspect
import os
import subprocess
import sys
from pathlib import Path

from txtarchive.packunpack import archive_files
from txtarchive.phi_block import scan_for_phi


SSN = "901-55-6789"
SENTINEL = "ZEBRA_PHI_SENTINEL"
PHI_REL = "docs/patient-note.qmd"


def _project(tmp_path: Path):
    src = tmp_path / "project"
    (src / "docs").mkdir(parents=True)
    (src / "src").mkdir()
    phi = src / "docs" / "patient-note.qmd"
    phi.write_text(f"note\n{SENTINEL}\nSSN {SSN}\n")
    clean = src / "src" / "helper.py"
    clean.write_text("def add(a, b):\n    return a + b\n")
    return src, phi, clean


def _freeze(path: Path):
    raw = path.read_bytes()
    mode = path.stat().st_mode
    fixed = 1_700_000_000_000_000_000
    os.utime(path, ns=(fixed, fixed))
    return raw, mode, fixed


def _outputs_text(paths):
    chunks = []
    for path in paths:
        path = Path(path)
        if path.is_file():
            chunks.append(path.read_text(encoding="utf-8", errors="replace"))
        elif path.is_dir():
            for child in path.rglob("*"):
                if child.is_file():
                    chunks.append(child.read_text(encoding="utf-8", errors="replace"))
    return "\n".join(chunks)


class TestScanner:
    def test_category_is_not_the_matched_text(self):
        assert scan_for_phi(f"SSN {SSN}\n") == "ssn"
        assert scan_for_phi("MRN: AB12CD\n") == "mrn"
        assert scan_for_phi("DOB: 1980-01-02\n") == "dob"
        assert scan_for_phi("patient_id: P100\n") == "patient-id"
        assert scan_for_phi("def add(a, b):\n    return a + b\n") is None
        assert SSN not in (scan_for_phi(f"SSN {SSN}\n") or "")

    def test_no_redaction_api(self):
        import txtarchive.phi_block as phi_block

        assert not hasattr(phi_block, "redact")
        assert "redact" not in inspect.signature(archive_files).parameters
        result = subprocess.run(
            [sys.executable, "-m", "txtarchive", "archive", "--help"],
            check=True,
            capture_output=True,
            text=True,
        )
        assert "--phi-block" in result.stdout
        assert "--phi-log" in result.stdout
        assert "--redact" not in result.stdout
        assert "--source-stamps" in result.stdout
        assert "--copilot-index" in result.stdout
        assert "--per-file" in result.stdout


class TestPassThrough:
    def test_stamps_and_index_with_blocking_off_never_calls_scanner(self, tmp_path, monkeypatch):
        calls = []

        def spy(text):
            calls.append(text)
            return "ssn"

        monkeypatch.setattr("txtarchive.phi_block.scan_for_phi", spy)
        src, phi, _clean = _project(tmp_path)
        raw, mode, fixed = _freeze(phi)
        archive = tmp_path / "archive.txt"
        archive_files(
            src,
            archive,
            file_types=[".py", ".qmd"],
            llm_friendly=True,
            source_stamps=True,
            copilot_index=True,
            per_file=True,
        )
        assert calls == []
        text = archive.read_text()
        index = (tmp_path / "archive_index.md").read_text()
        assert f"SOURCE FILE: {PHI_REL} (part 1)" in text
        assert "SOURCE FILE: src/helper.py (part 1)" in text
        assert SSN in text
        assert SENTINEL in text
        assert PHI_REL in index
        assert "src/helper.py" in index
        assert (tmp_path / "archive_files" / "docs__patient-note.qmd").is_file()
        assert (tmp_path / "archive_files" / "src__helper.py").is_file()
        assert not (tmp_path / "archive_phi_skipped.log").exists()
        st = phi.stat()
        assert st.st_mtime_ns == fixed
        assert st.st_mode == mode
        assert phi.read_bytes() == raw

    def test_phi_log_flag_does_not_enable_scanning(self, tmp_path, monkeypatch):
        calls = []

        def spy(text):
            calls.append(text)
            return "ssn"

        monkeypatch.setattr("txtarchive.phi_block.scan_for_phi", spy)
        src, _phi, _clean = _project(tmp_path)
        archive = tmp_path / "archive.txt"
        custom = tmp_path / "custom.log"
        archive_files(
            src,
            archive,
            file_types=[".py", ".qmd"],
            llm_friendly=True,
            source_stamps=True,
            copilot_index=True,
            phi_log=str(custom),
        )
        assert calls == []
        assert not custom.exists()
        assert SSN in archive.read_text()
        assert PHI_REL in (tmp_path / "archive_index.md").read_text()


class TestBlocking:
    def test_skipped_file_absent_from_index_and_other_outputs(self, tmp_path):
        src, phi, clean = _project(tmp_path)
        raw, mode, fixed = _freeze(phi)
        clean_raw, clean_mode, clean_fixed = _freeze(clean)
        archive = tmp_path / "archive.txt"
        split_dir = tmp_path / "parts"
        archive_files(
            src,
            archive,
            file_types=[".py", ".qmd"],
            llm_friendly=True,
            source_stamps=True,
            copilot_index=True,
            per_file=True,
            knowledge=True,
            split_output=True,
            max_tokens=1,
            split_output_dir=split_dir,
            phi_block=True,
        )
        text = archive.read_text()
        index = (tmp_path / "archive_index.md").read_text()
        assert "SOURCE FILE: src/helper.py (part 1)" in text
        assert f"SOURCE FILE: {PHI_REL}" not in text
        assert "src/helper.py" in index
        assert PHI_REL not in index
        assert "1.1 | src/helper.py |" in index

        per_dir = tmp_path / "archive_files"
        knowledge = tmp_path / "archive_knowledge"
        assert (per_dir / "src__helper.py").is_file()
        assert not (per_dir / "docs__patient-note.qmd").exists()
        kept = _outputs_text([archive, tmp_path / "archive_index.md", split_dir, per_dir, knowledge])
        assert SSN not in kept
        assert SENTINEL not in kept
        assert PHI_REL not in kept
        assert "def add(a, b):" in kept

        log = (tmp_path / "archive_phi_skipped.log").read_text()
        assert f"skipped | {PHI_REL} | ssn" in log
        assert SSN not in log
        assert SENTINEL not in log

        st = phi.stat()
        assert st.st_mtime_ns == fixed
        assert st.st_mode == mode
        assert phi.read_bytes() == raw
        clean_st = clean.stat()
        assert clean_st.st_mtime_ns == clean_fixed
        assert clean_st.st_mode == clean_mode
        assert clean.read_bytes() == clean_raw

    def test_clean_file_archived_when_blocking_on(self, tmp_path):
        src = tmp_path / "project"
        src.mkdir()
        (src / "main.py").write_text("print('hello')\n")
        archive = tmp_path / "archive.txt"
        archive_files(
            src,
            archive,
            file_types=[".py"],
            llm_friendly=True,
            source_stamps=True,
            copilot_index=True,
            per_file=True,
            phi_block=True,
        )
        text = archive.read_text()
        assert "SOURCE FILE: main.py (part 1)" in text
        assert "print('hello')" in text
        index = (tmp_path / "archive_index.md").read_text()
        assert "main.py" in index
        assert (tmp_path / "archive_files" / "main.py").is_file()
        log = (tmp_path / "archive_phi_skipped.log").read_text()
        assert [line for line in log.splitlines() if not line.startswith("#")] == []
