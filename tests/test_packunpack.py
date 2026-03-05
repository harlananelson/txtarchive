import json
import pytest
from pathlib import Path
from txtarchive.packunpack import (
    run_concat,
    archive_files,
    unpack_files,
    unpack_files_auto,
    extract_notebooks_to_ipynb,
    _reconstruct_notebook_from_cells,
    _read_archive_content,
    _parse_archive_sections,
)

# how to run the test from the bash command line
# make sure you are in the root directory of the package
# such as cd /home/runner/work/txtarchive/txtarchive
# pytest tests/test_packunpack.py


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def temp_dir(tmp_path):
    # Create some test files in the temporary directory
    (tmp_path / 'test1.yaml').write_text('content of test1.yaml')
    (tmp_path / 'test2.py').write_text('content of test2.py')
    (tmp_path / 'test3.r').write_text('content of test3.r')
    (tmp_path / 'ignore.log').write_text('this should be ignored')
    return tmp_path


@pytest.fixture
def sample_project(tmp_path):
    """Create a sample project structure for archive/unpack tests."""
    src = tmp_path / "project"
    src.mkdir()
    (src / "main.py").write_text("print('hello')\n")
    (src / "utils.py").write_text("def add(a, b):\n    return a + b\n")
    sub = src / "subdir"
    sub.mkdir()
    (sub / "helper.py").write_text("# helper module\n")
    (src / "README.md").write_text("# My Project\n")
    return src


# ---------------------------------------------------------------------------
# run_concat tests (existing)
# ---------------------------------------------------------------------------

def test_run_concat_with_strings(temp_dir):
    combined_file = str(temp_dir / 'combined_files.txt')
    run_concat(str(temp_dir), combined_files=combined_file, file_types=['.yaml', '.py', '.r'])
    assert (temp_dir / 'combined_files.txt').exists()

def test_run_concat_with_paths(temp_dir):
    combined_file = temp_dir / 'combined_files.txt'
    run_concat(temp_dir, combined_files=combined_file, file_types=['.yaml', '.py', '.r'])
    content = combined_file.read_text()
    assert 'content of test1.yaml' in content
    assert 'content of test2.py' in content
    assert 'content of test3.r' in content
    assert 'this should be ignored' not in content


# ---------------------------------------------------------------------------
# archive_files tests
# ---------------------------------------------------------------------------

class TestArchiveFiles:
    def test_standard_format(self, sample_project, tmp_path):
        output = tmp_path / "archive.txt"
        archive_files(sample_project, output, file_types=[".py", ".md"])
        content = output.read_text()
        assert "---\nFilename: " in content
        assert "main.py" in content
        assert "utils.py" in content

    def test_llm_friendly_format(self, sample_project, tmp_path):
        output = tmp_path / "archive.txt"
        archive_files(sample_project, output, file_types=[".py", ".md"], llm_friendly=True)
        content = output.read_text()
        assert "LLM-FRIENDLY CODE ARCHIVE" in content
        assert "# FILE " in content
        assert "TABLE OF CONTENTS" in content
        assert "main.py" in content

    def test_exclude_dirs(self, sample_project, tmp_path):
        output = tmp_path / "archive.txt"
        archive_files(sample_project, output, file_types=[".py"], exclude_dirs=["subdir"])
        content = output.read_text()
        assert "main.py" in content
        assert "helper.py" not in content

    def test_explicit_files(self, sample_project, tmp_path):
        output = tmp_path / "archive.txt"
        archive_files(
            sample_project, output,
            file_types=[".py"],
            explicit_files=["main.py"],
            llm_friendly=True,
        )
        content = output.read_text()
        assert "main.py" in content
        assert "utils.py" not in content

    def test_dry_run(self, sample_project, tmp_path, capsys):
        output = tmp_path / "archive.txt"
        result = archive_files(sample_project, output, file_types=[".py"], dry_run=True)
        assert result is None
        assert not output.exists()
        captured = capsys.readouterr()
        assert "DRY RUN" in captured.out

    def test_root_files(self, sample_project, tmp_path):
        output = tmp_path / "archive.txt"
        archive_files(
            sample_project, output,
            file_types=[".py"],
            root_files=["README.md"],
            llm_friendly=True,
        )
        content = output.read_text()
        # README.md should appear first (root files processed first)
        assert "README.md" in content

    def test_no_subdirectories(self, sample_project, tmp_path):
        output = tmp_path / "archive.txt"
        archive_files(
            sample_project, output,
            file_types=[".py"],
            include_subdirectories=False,
        )
        content = output.read_text()
        assert "main.py" in content
        assert "helper.py" not in content

    def test_llm_friendly_no_delimiter_escaping(self, sample_project, tmp_path):
        """LLM-friendly format should NOT escape ---\\nFilename: patterns."""
        # Create a file that contains the standard delimiter pattern
        (sample_project / "tricky.py").write_text("x = '---\\nFilename: foo'\\n")
        output = tmp_path / "archive.txt"
        archive_files(sample_project, output, file_types=[".py"], llm_friendly=True)
        content = output.read_text()
        assert "LLM-FRIENDLY CODE ARCHIVE" in content
        # Verify the escaped form does NOT appear (no unnecessary escaping)
        assert "---\\\\nFilename: " not in content


# ---------------------------------------------------------------------------
# unpack tests
# ---------------------------------------------------------------------------

class TestUnpack:
    def test_standard_roundtrip(self, sample_project, tmp_path):
        """Archive in standard format, then unpack and verify content matches."""
        archive_path = tmp_path / "archive.txt"
        restore_dir = tmp_path / "restored"
        archive_files(sample_project, archive_path, file_types=[".py", ".md"])
        unpack_files(restore_dir, archive_path)
        # Archive format adds trailing newlines between sections; strip for comparison
        assert (restore_dir / "main.py").read_text().strip() == "print('hello')"
        assert (restore_dir / "utils.py").read_text().strip() == "def add(a, b):\n    return a + b"

    def test_unpack_auto_standard(self, sample_project, tmp_path):
        """unpack_files_auto detects standard format."""
        archive_path = tmp_path / "archive.txt"
        restore_dir = tmp_path / "restored"
        archive_files(sample_project, archive_path, file_types=[".py"])
        unpack_files_auto(restore_dir, archive_path)
        assert (restore_dir / "main.py").exists()

    def test_unpack_auto_llm_friendly_requires_force(self, sample_project, tmp_path):
        """unpack_files_auto refuses LLM-friendly without --force."""
        archive_path = tmp_path / "archive.txt"
        restore_dir = tmp_path / "restored"
        archive_files(sample_project, archive_path, file_types=[".py"], llm_friendly=True)
        with pytest.raises(SystemExit):
            unpack_files_auto(restore_dir, archive_path)

    def test_unpack_auto_llm_friendly_with_force(self, sample_project, tmp_path):
        """unpack_files_auto works with --force for LLM-friendly."""
        archive_path = tmp_path / "archive.txt"
        restore_dir = tmp_path / "restored"
        archive_files(sample_project, archive_path, file_types=[".py"], llm_friendly=True)
        unpack_files_auto(restore_dir, archive_path, force=True)
        assert (restore_dir / "main.py").exists()


# ---------------------------------------------------------------------------
# _reconstruct_notebook_from_cells tests
# ---------------------------------------------------------------------------

class TestReconstructNotebook:
    def test_basic_code_cells(self):
        content = (
            "# Cell 1\n"
            "import pandas as pd\n"
            "\n"
            "# Cell 2\n"
            "df = pd.read_csv('data.csv')\n"
        )
        nb = _reconstruct_notebook_from_cells(content, "test.ipynb")
        assert nb is not None
        assert len(nb["cells"]) == 2
        assert nb["cells"][0]["cell_type"] == "code"
        assert nb["cells"][1]["cell_type"] == "code"

    def test_markdown_cells(self):
        content = (
            '# Markdown Cell 1\n'
            '"""\n'
            '# Title\n'
            'Description here\n'
            '"""\n'
            '\n'
            '# Cell 1\n'
            'x = 1\n'
        )
        nb = _reconstruct_notebook_from_cells(content, "test.ipynb")
        assert nb is not None
        assert nb["cells"][0]["cell_type"] == "markdown"
        assert nb["cells"][1]["cell_type"] == "code"

    def test_raw_cells(self):
        content = (
            '# Raw Cell 1\n'
            '"""\n'
            '---\n'
            'title: Test\n'
            '---\n'
            '"""\n'
            '\n'
            '# Cell 1\n'
            'x = 1\n'
        )
        nb = _reconstruct_notebook_from_cells(content, "test.ipynb")
        assert nb is not None
        assert nb["cells"][0]["cell_type"] == "raw"

    def test_custom_kernel(self):
        content = "# Cell 1\nx = 1\n"
        nb = _reconstruct_notebook_from_cells(content, "test.ipynb", kernel="r_env")
        assert nb["metadata"]["kernelspec"]["name"] == "r_env"

    def test_empty_content_returns_empty_notebook(self):
        nb = _reconstruct_notebook_from_cells("", "test.ipynb")
        assert nb is not None
        assert nb["cells"] == []
        assert nb["nbformat"] == 4


# ---------------------------------------------------------------------------
# Shared helper tests
# ---------------------------------------------------------------------------

class TestArchiveHelpers:
    def test_read_archive_content_single_file(self, sample_project, tmp_path):
        archive_path = tmp_path / "archive.txt"
        archive_files(sample_project, archive_path, file_types=[".py"], llm_friendly=True)
        content = _read_archive_content(archive_path)
        assert content is not None
        assert "TABLE OF CONTENTS" in content

    def test_read_archive_content_missing_toc(self, tmp_path):
        bad_file = tmp_path / "bad.txt"
        bad_file.write_text("no table of contents here")
        content = _read_archive_content(bad_file)
        assert content is None

    def test_parse_archive_sections_llm_friendly(self, sample_project, tmp_path):
        archive_path = tmp_path / "archive.txt"
        archive_files(sample_project, archive_path, file_types=[".py"], llm_friendly=True)
        content = _read_archive_content(archive_path)
        sections = list(_parse_archive_sections(content))
        filenames = [s[0] for s in sections]
        assert any("main.py" in f for f in filenames)
        assert all(s[2] is True for s in sections)  # all LLM-friendly

    def test_parse_archive_sections_standard(self, sample_project, tmp_path):
        archive_path = tmp_path / "archive.txt"
        archive_files(sample_project, archive_path, file_types=[".py"])
        content = _read_archive_content(archive_path)
        sections = list(_parse_archive_sections(content))
        filenames = [s[0] for s in sections]
        assert any("main.py" in f for f in filenames)
        assert all(s[2] is False for s in sections)  # all standard


# ---------------------------------------------------------------------------
# extract_notebooks_to_ipynb tests
# ---------------------------------------------------------------------------

class TestExtractNotebooks:
    def test_extract_from_llm_archive(self, tmp_path):
        """Create an LLM-friendly archive with a fake notebook, extract it."""
        archive_content = (
            "# Archive created on: 2025-01-01\n\n"
            "# LLM-FRIENDLY CODE ARCHIVE\n"
            "# TABLE OF CONTENTS\n"
            "1. test.ipynb\n\n"
            "################################################################################\n"
            "# FILE 1: test.ipynb\n"
            "################################################################################\n\n"
            "# Cell 1\n"
            "import pandas as pd\n\n"
            "# Cell 2\n"
            "df = pd.DataFrame()\n"
        )
        archive_path = tmp_path / "archive.txt"
        archive_path.write_text(archive_content)
        output_dir = tmp_path / "output"

        extract_notebooks_to_ipynb(archive_path, output_dir)

        notebook_path = output_dir / "test.ipynb"
        assert notebook_path.exists()
        nb = json.loads(notebook_path.read_text())
        assert len(nb["cells"]) == 2
        assert nb["cells"][0]["cell_type"] == "code"
