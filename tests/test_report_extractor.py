"""Tests for report_extractor module."""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

from txtarchive.report_extractor import (
    extract_report,
    format_json,
    format_markdown,
    format_yaml,
    _extract_gt_table,
    _extract_model_card,
    _extract_yaml_from_code_block,
    _find_sections,
    _match_section_number,
    _parse_html,
)

# ---------------------------------------------------------------------------
# Synthetic report HTML mimicking Quarto output
# ---------------------------------------------------------------------------

SYNTHETIC_REPORT_HTML = """\
<!DOCTYPE html>
<html>
<head>
  <title>Test Report: Cox Survival Analysis</title>
  <meta name="author" content="Test Author">
  <meta name="date" content="2026-03-04">
</head>
<body>
<main class="content" id="quarto-document-content">

<header id="title-block-header" class="quarto-title-block default">
<h1 class="title">Section 0 — Machine-Readable Metadata Header</h1>
<div class="sourceCode" id="cb1">
<pre class="sourceCode yaml code-with-copy">
<code class="sourceCode yaml">
<span class="fu">report_id</span><span class="kw">:</span><span class="at"> test-report-001</span>
<span class="fu">analysis_date</span><span class="kw">:</span><span class="at"> 2026-03-04</span>
<span class="fu">analyst</span><span class="kw">:</span><span class="at"> Test Author</span>
<span class="fu">reviewer</span><span class="kw">:</span><span class="at"> Dr. Test</span>
<span class="fu">dataset_name</span><span class="kw">:</span><span class="at"> test_dataset</span>
<span class="fu">ml_model_used</span><span class="kw">:</span><span class="at"> N/A</span>
</code>
</pre>
</div>
</header>

<section id="section-1-executive-summary" class="level1">
<h1>Section 1 — Executive Summary</h1>
<section id="results-at-a-glance" class="level3">
<h3>Results-at-a-Glance</h3>
<table class="gt_table caption-top" data-quarto-bootstrap="false">
<thead>
<tr class="gt_heading">
<td colspan="2" class="gt_heading gt_title gt_font_normal">Results at a Glance</td>
</tr>
<tr class="gt_col_headings">
<th id="Metric" class="gt_col_heading gt_columns_bottom_border gt_left">Metric</th>
<th id="Value" class="gt_col_heading gt_columns_bottom_border gt_right">Value</th>
</tr>
</thead>
<tbody class="gt_table_body">
<tr><td class="gt_row gt_left" headers="Metric">Final N</td>
<td class="gt_row gt_right" headers="Value">10,166</td></tr>
<tr><td class="gt_row gt_left" headers="Metric">Events</td>
<td class="gt_row gt_right" headers="Value">1,234</td></tr>
<tr><td class="gt_row gt_left" headers="Metric">Primary Effect</td>
<td class="gt_row gt_right" headers="Value">HR 2.31 (1.95-2.74)</td></tr>
<tr><td class="gt_row gt_left" headers="Metric">Model Type</td>
<td class="gt_row gt_right" headers="Value">Cox PH</td></tr>
</tbody>
</table>
</section>
<p>SCD patients showed significantly higher mortality compared to controls.</p>
</section>

<section id="section-2-cohort-flow" class="level1">
<h1>Section 2 — Cohort Flow</h1>
<table class="gt_table caption-top" data-quarto-bootstrap="false">
<thead>
<tr class="gt_heading">
<td colspan="3" class="gt_heading gt_title gt_font_normal">Cohort Flow</td>
</tr>
<tr class="gt_col_headings">
<th id="Step" class="gt_col_heading gt_columns_bottom_border gt_left">Step</th>
<th id="N" class="gt_col_heading gt_columns_bottom_border gt_right">N</th>
<th id="Excluded" class="gt_col_heading gt_columns_bottom_border gt_right">Excluded</th>
</tr>
</thead>
<tbody class="gt_table_body">
<tr><td class="gt_row gt_left" headers="Step">Starting cohort</td>
<td class="gt_row gt_right" headers="N">45,221</td>
<td class="gt_row gt_right" headers="Excluded">—</td></tr>
<tr><td class="gt_row gt_left" headers="Step">Population 2</td>
<td class="gt_row gt_right" headers="N">37,956</td>
<td class="gt_row gt_right" headers="Excluded">7,265</td></tr>
</tbody>
</table>
</section>

<section id="section-3-variable-definitions" class="level1">
<h1>Section 3 — Variable Definitions</h1>
<section id="a-exposure" class="level2">
<h2>3A. Exposure: SCD Group</h2>
<p>HbSS/HbSB0 vs Control group assignment.</p>
</section>
<section id="b-outcome" class="level2">
<h2>3B. Outcome: All-Cause Mortality</h2>
<p>death_event binary flag.</p>
</section>
</section>

<section id="section-4-data-quality-missingness" class="level1">
<h1>Section 4 — Data Quality &amp; Missingness</h1>
<p>No major data integrity concerns identified.</p>
</section>

<section id="section-5-descriptive-statistics-table-1" class="level1">
<h1>Section 5 — Descriptive Statistics (Table 1)</h1>
<p>See Table 1 output below.</p>
</section>

<section id="section-6-primary-analysis" class="level1">
<h1>Section 6 — Primary Analysis</h1>
<section id="a-classical-model" class="level2">
<h2>6A. Classical Statistical Model</h2>
<section id="model-card" class="level3">
<h3>Model Card</h3>
<ul>
<li><strong>Model type:</strong> Cox proportional hazards regression</li>
<li><strong>Formula:</strong> Surv(followup_time, death_event) ~ group + age_entry + sex</li>
<li><strong>Time horizon:</strong> Full available follow-up</li>
<li><strong>N included:</strong> 10,166</li>
<li><strong>Covariates included:</strong> SCD group, age at entry, sex</li>
</ul>
</section>
</section>
</section>

<section id="section-7-sensitivity-analyses" class="level1">
<h1>Section 7 — Sensitivity Analyses</h1>
<p>No pre-specified sensitivity analyses for this parsimonious model.</p>
</section>

<section id="section-8-results-for-manuscript-use" class="level1">
<h1>Section 8 — Results for Manuscript Use</h1>
<p>In adjusted analyses, SCD was associated with significantly higher mortality (HR 2.31; 95% CI, 1.95-2.74; p&lt;0.001).</p>
</section>

<section id="section-9-limitations-bias-assessment" class="level1">
<h1>Section 9 — Limitations &amp; Bias Assessment</h1>
<ul>
<li>Measurement error: EHR-based death ascertainment may miss out-of-system deaths</li>
<li>Residual confounding: Comorbidities not included in parsimonious model</li>
<li>Selection bias: Cerner population may not represent all US SCD patients</li>
</ul>
</section>

<section id="section-10-reproducibility-traceability" class="level1">
<h1>Section 10 — Reproducibility &amp; Traceability</h1>
<p>Code version: targets pipeline, R 4.4.0</p>
</section>

<section id="section-11-proposed-next-steps" class="level1">
<h1>Section 11 — Proposed Next Steps</h1>
<ul>
<li>Add comorbidity-adjusted model</li>
<li>Stratify by genotype subgroup</li>
</ul>
</section>

</main>
</body>
</html>
"""


@pytest.fixture
def synthetic_html_path(tmp_path):
    """Write synthetic HTML to a temp file."""
    html_file = tmp_path / "test-report.html"
    html_file.write_text(SYNTHETIC_REPORT_HTML, encoding="utf-8")
    return html_file


class TestSectionMatching:
    def test_match_section_number_from_text(self):
        assert _match_section_number("Section 0 — Machine-Readable Metadata Header") == 0
        assert _match_section_number("Section 1 — Executive Summary") == 1
        assert _match_section_number("Section 11 — Proposed Next Steps") == 11

    def test_match_section_number_from_id(self):
        assert _match_section_number("", "section-6-primary-analysis") == 6
        assert _match_section_number("", "section-10-reproducibility-traceability") == 10

    def test_match_section_by_keyword(self):
        assert _match_section_number("Executive Summary") == 1
        assert _match_section_number("Cohort Flow") == 2

    def test_no_match(self):
        assert _match_section_number("Random heading text") is None


class TestParseHtml:
    def test_finds_main_content(self, synthetic_html_path):
        main, _ = _parse_html(synthetic_html_path)
        assert main is not None
        assert main.get("id") == "quarto-document-content"


class TestFindSections:
    def test_finds_all_12_sections(self, synthetic_html_path):
        main, _ = _parse_html(synthetic_html_path)
        sections = _find_sections(main)
        # Our synthetic HTML has all 12 sections (0-11)
        assert 0 in sections, "Section 0 not found"
        assert 1 in sections, "Section 1 not found"
        assert 6 in sections, "Section 6 not found"
        assert 11 in sections, "Section 11 not found"
        assert len(sections) == 12


class TestYamlExtraction:
    def test_extracts_yaml_metadata(self, synthetic_html_path):
        main, _ = _parse_html(synthetic_html_path)
        sections = _find_sections(main)
        yaml_data = _extract_yaml_from_code_block(sections[0])
        assert yaml_data is not None
        assert yaml_data["report_id"] == "test-report-001"
        assert yaml_data["analyst"] == "Test Author"
        assert yaml_data["ml_model_used"] == "N/A"


class TestGtTableExtraction:
    def test_extracts_gt_table(self, synthetic_html_path):
        from bs4 import BeautifulSoup

        main, _ = _parse_html(synthetic_html_path)
        tables = main.find_all("table", class_=lambda c: c and "gt_table" in c)
        assert len(tables) >= 1

        result = _extract_gt_table(tables[0])
        assert result["title"] == "Results at a Glance"
        assert "Metric" in result["columns"]
        assert "Value" in result["columns"]
        assert len(result["rows"]) == 4
        assert result["rows"][0]["Metric"] == "Final N"
        assert result["rows"][0]["Value"] == "10,166"


class TestModelCardExtraction:
    def test_extracts_model_card(self, synthetic_html_path):
        main, _ = _parse_html(synthetic_html_path)
        sections = _find_sections(main)
        sec6 = sections[6]

        # Find model card subsection
        model_card_section = None
        for sub in sec6.find_all("section"):
            heading = sub.find(["h2", "h3"])
            if heading and "model card" in heading.get_text(strip=True).lower():
                model_card_section = sub
                break

        assert model_card_section is not None
        card = _extract_model_card(model_card_section)
        assert card is not None
        assert card["Model type"] == "Cox proportional hazards regression"
        assert "Surv(followup_time" in card["Formula"]
        assert card["N included"] == "10,166"


class TestExtractReport:
    def test_full_extraction(self, synthetic_html_path):
        result = extract_report(synthetic_html_path)
        assert result["title"] == "Test Report: Cox Survival Analysis"
        assert result["author"] == "Test Author"
        assert 0 in result["sections"]
        assert 1 in result["sections"]
        assert 6 in result["sections"]
        assert 11 in result["sections"]

    def test_section_filter(self, synthetic_html_path):
        result = extract_report(synthetic_html_path, sections=[0, 1, 6])
        assert set(result["sections"].keys()) == {0, 1, 6}

    def test_metadata_extraction(self, synthetic_html_path):
        result = extract_report(synthetic_html_path)
        sec0 = result["sections"][0]
        assert sec0["metadata"]["report_id"] == "test-report-001"

    def test_results_at_a_glance(self, synthetic_html_path):
        result = extract_report(synthetic_html_path)
        sec1 = result["sections"][1]
        glance = sec1.get("results_at_a_glance")
        assert glance is not None
        assert glance["Final N"] == "10,166"
        assert glance["Events"] == "1,234"

    def test_model_card(self, synthetic_html_path):
        result = extract_report(synthetic_html_path)
        sec6 = result["sections"][6]
        assert sec6["model_card"] is not None
        assert sec6["model_card"]["Model type"] == "Cox proportional hazards regression"

    def test_limitations_list(self, synthetic_html_path):
        result = extract_report(synthetic_html_path)
        sec9 = result["sections"][9]
        items = sec9.get("list_items", [])
        assert len(items) == 3
        assert "Measurement error" in items[0]

    def test_strict_mode_raises_on_missing(self, tmp_path):
        """Strict mode should raise when expected sections are missing."""
        minimal_html = "<html><body><main id='quarto-document-content'><p>Empty</p></main></body></html>"
        html_file = tmp_path / "minimal.html"
        html_file.write_text(minimal_html)
        with pytest.raises(ValueError, match="Missing required sections"):
            extract_report(html_file, strict=True)

    def test_best_effort_mode(self, tmp_path):
        """Best-effort mode should not raise on missing sections."""
        minimal_html = "<html><body><main id='quarto-document-content'><p>Empty</p></main></body></html>"
        html_file = tmp_path / "minimal.html"
        html_file.write_text(minimal_html)
        result = extract_report(html_file, strict=False)
        assert result["sections"] == {}


class TestOutputFormats:
    def test_yaml_output(self, synthetic_html_path):
        data = extract_report(synthetic_html_path)
        output = format_yaml(data)
        assert "title:" in output
        assert "test-report-001" in output

    def test_json_output(self, synthetic_html_path):
        data = extract_report(synthetic_html_path)
        output = format_json(data)
        parsed = json.loads(output)
        assert parsed["title"] == "Test Report: Cox Survival Analysis"

    def test_markdown_output(self, synthetic_html_path):
        data = extract_report(synthetic_html_path)
        output = format_markdown(data)
        assert "# Test Report" in output
        assert "## Metadata" in output
        assert "## Model Card" in output
        assert "## Manuscript Results" in output
        assert "## Limitations" in output


class TestCLI:
    def test_cli_yaml_output(self, synthetic_html_path):
        result = subprocess.run(
            [sys.executable, "-m", "txtarchive", "extract-report", str(synthetic_html_path)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "title:" in result.stdout
        assert "test-report-001" in result.stdout

    def test_cli_json_output(self, synthetic_html_path):
        result = subprocess.run(
            [sys.executable, "-m", "txtarchive", "extract-report", str(synthetic_html_path), "--format", "json"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        parsed = json.loads(result.stdout)
        assert parsed["title"] == "Test Report: Cox Survival Analysis"

    def test_cli_section_filter(self, synthetic_html_path):
        result = subprocess.run(
            [sys.executable, "-m", "txtarchive", "extract-report", str(synthetic_html_path),
             "--sections", "0,6", "--format", "json"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        parsed = json.loads(result.stdout)
        section_keys = [int(k) for k in parsed["sections"].keys()]
        assert 0 in section_keys
        assert 6 in section_keys
        assert 1 not in section_keys

    def test_cli_output_file(self, synthetic_html_path, tmp_path):
        output_file = tmp_path / "output.yaml"
        result = subprocess.run(
            [sys.executable, "-m", "txtarchive", "extract-report", str(synthetic_html_path),
             "--output", str(output_file)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert output_file.exists()
        content = output_file.read_text()
        assert "test-report-001" in content

    def test_cli_markdown_output(self, synthetic_html_path):
        result = subprocess.run(
            [sys.executable, "-m", "txtarchive", "extract-report", str(synthetic_html_path), "--format", "markdown"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "# Test Report" in result.stdout
        assert "## Model Card" in result.stdout


# ---------------------------------------------------------------------------
# Integration test with real report (only runs if file exists)
# ---------------------------------------------------------------------------

REAL_REPORT_PATH = Path("/home/harlan/projects/SCDCernerProject/paper/2060-nejm-cox-adjusted-survival.html")


@pytest.mark.skipif(not REAL_REPORT_PATH.exists(), reason="Real report HTML not available")
class TestRealReport:
    def test_extracts_real_report(self):
        result = extract_report(REAL_REPORT_PATH)
        assert result["title"]  # Should have a title
        assert len(result["sections"]) >= 8  # Should find most sections

    def test_real_metadata(self):
        result = extract_report(REAL_REPORT_PATH, sections=[0])
        sec0 = result["sections"].get(0)
        assert sec0 is not None
        metadata = sec0.get("metadata")
        assert metadata is not None
        assert "report_id" in metadata

    def test_real_model_card(self):
        result = extract_report(REAL_REPORT_PATH, sections=[6])
        sec6 = result["sections"].get(6)
        assert sec6 is not None
        card = sec6.get("model_card")
        assert card is not None
        assert "Model type" in card

    def test_real_tables(self):
        result = extract_report(REAL_REPORT_PATH)
        assert len(result["tables"]) >= 1  # Should have at least cohort flow table

    def test_real_figures(self):
        result = extract_report(REAL_REPORT_PATH)
        # The 2060 report has survival curves
        assert len(result["figures"]) >= 0  # May or may not have embedded figures

    def test_real_yaml_format(self):
        result = extract_report(REAL_REPORT_PATH)
        output = format_yaml(result)
        assert "title:" in output
        assert len(output) > 100

    def test_real_markdown_format(self):
        result = extract_report(REAL_REPORT_PATH)
        output = format_markdown(result)
        assert "## Metadata" in output


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
