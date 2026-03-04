"""
Report extractor for Quarto-rendered HTML reports following report-spec.md format.

Parses structured sections (0-11), extracts metadata, tables, model cards,
and figures. Outputs YAML, JSON, or condensed markdown.
"""

import json
import logging
import re
import warnings
from pathlib import Path

logger = logging.getLogger(__name__)

# Section registry: maps section numbers to canonical names and ID patterns
SECTION_REGISTRY = {
    0: {
        "name": "Machine-Readable Metadata Header",
        "key": "metadata_header",
        "id_patterns": [r"section[\-_\s]*0", r"machine[\-_\s]*readable", r"metadata[\-_\s]*header"],
    },
    1: {
        "name": "Executive Summary",
        "key": "executive_summary",
        "id_patterns": [r"section[\-_\s]*1", r"executive[\-_\s]*summary"],
    },
    2: {
        "name": "Cohort Flow",
        "key": "cohort_flow",
        "id_patterns": [r"section[\-_\s]*2", r"cohort[\-_\s]*flow"],
    },
    3: {
        "name": "Variable Definitions",
        "key": "variable_definitions",
        "id_patterns": [r"section[\-_\s]*3", r"variable[\-_\s]*definitions"],
    },
    4: {
        "name": "Data Quality & Missingness",
        "key": "data_quality",
        "id_patterns": [r"section[\-_\s]*4", r"data[\-_\s]*quality"],
    },
    5: {
        "name": "Descriptive Statistics",
        "key": "descriptive_statistics",
        "id_patterns": [r"section[\-_\s]*5", r"descriptive[\-_\s]*statistics"],
    },
    6: {
        "name": "Primary Analysis",
        "key": "primary_analysis",
        "id_patterns": [r"section[\-_\s]*6", r"primary[\-_\s]*analysis"],
    },
    7: {
        "name": "Sensitivity Analyses",
        "key": "sensitivity_analyses",
        "id_patterns": [r"section[\-_\s]*7", r"sensitivity[\-_\s]*analyses"],
    },
    8: {
        "name": "Results for Manuscript Use",
        "key": "manuscript_results",
        "id_patterns": [r"section[\-_\s]*8", r"results[\-_\s]*for[\-_\s]*manuscript"],
    },
    9: {
        "name": "Limitations & Bias Assessment",
        "key": "limitations",
        "id_patterns": [r"section[\-_\s]*9", r"limitations"],
    },
    10: {
        "name": "Reproducibility & Traceability",
        "key": "reproducibility",
        "id_patterns": [r"section[\-_\s]*10", r"reproducibility"],
    },
    11: {
        "name": "Proposed Next Steps",
        "key": "proposed_next_steps",
        "id_patterns": [r"section[\-_\s]*11", r"proposed[\-_\s]*next"],
    },
}


def _parse_html(path):
    """Read HTML file and return BeautifulSoup of main content area."""
    from bs4 import BeautifulSoup

    html_content = Path(path).read_text(encoding="utf-8")
    try:
        import lxml  # noqa: F401
        parser = "lxml"
    except ImportError:
        parser = "html.parser"
    soup = BeautifulSoup(html_content, parser)

    # Remove script/style elements
    for tag in soup.find_all(["script", "style"]):
        tag.decompose()

    # Find main content: prefer #quarto-document-content, then <main>, then <body>
    main = soup.find(id="quarto-document-content")
    if main is None:
        main = soup.find("main")
    if main is None:
        main = soup.find("body")
    if main is None:
        main = soup

    return main, soup


def _match_section_number(text, element_id=""):
    """Try to match a section number from heading text or element ID.

    Returns section number (0-11) or None.
    """
    # Try heading text first: "Section N" pattern
    m = re.search(r"section\s+(\d+)", text, re.IGNORECASE)
    if m:
        num = int(m.group(1))
        if num in SECTION_REGISTRY:
            return num

    # Try element ID
    if element_id:
        m = re.search(r"section[\-_]?(\d+)", element_id, re.IGNORECASE)
        if m:
            num = int(m.group(1))
            if num in SECTION_REGISTRY:
                return num

    # Try keyword matching from registry
    combined = f"{text} {element_id}".lower()
    for sec_num, info in SECTION_REGISTRY.items():
        for pattern in info["id_patterns"]:
            if re.search(pattern, combined, re.IGNORECASE):
                return sec_num

    return None


def _find_sections(main_content):
    """Find and map <section> or <h1> elements to section numbers.

    Returns dict mapping section number -> BeautifulSoup element.
    """
    sections = {}

    # Strategy 1: Look for <section> elements with IDs
    for section_el in main_content.find_all("section", class_="level1"):
        heading = section_el.find(["h1", "h2"])
        heading_text = heading.get_text(strip=True) if heading else ""
        section_id = section_el.get("id", "")

        sec_num = _match_section_number(heading_text, section_id)
        if sec_num is not None and sec_num not in sections:
            sections[sec_num] = section_el

    # Strategy 2: If no level1 sections found, try h1 headings
    if not sections:
        for h1 in main_content.find_all("h1"):
            heading_text = h1.get_text(strip=True)
            parent = h1.parent
            sec_num = _match_section_number(heading_text, parent.get("id", "") if parent else "")
            if sec_num is not None and sec_num not in sections:
                sections[sec_num] = parent if parent and parent.name == "section" else h1

    # Special case: Section 0 might be in the title block header
    if 0 not in sections:
        title_block = main_content.find("header", id="title-block-header")
        if title_block:
            title_el = title_block.find("h1", class_="title")
            if title_el:
                title_text = title_el.get_text(strip=True)
                if _match_section_number(title_text) == 0:
                    # The YAML block may be a sibling of the header, not inside it.
                    # Create a virtual container with both the header and the next YAML block.
                    sections[0] = main_content

    return sections


def _extract_yaml_from_code_block(element):
    """Extract YAML from a Quarto-rendered syntax-highlighted code block.

    Quarto renders YAML as <pre class="sourceCode yaml"><code>
    with <span class="fu">key</span><span class="kw">:</span><span class="at"> value</span>.
    We call .get_text() to collapse all spans into plain text, then yaml.safe_load().
    """
    import yaml

    code_blocks = element.find_all("pre", class_=lambda c: c and "sourceCode" in c)
    for pre in code_blocks:
        classes = pre.get("class", [])
        # Check if this is a YAML block
        if "yaml" in " ".join(classes):
            code_el = pre.find("code")
            if code_el:
                raw_text = code_el.get_text()
                try:
                    return yaml.safe_load(raw_text)
                except yaml.YAMLError as e:
                    logger.warning(f"Failed to parse YAML block: {e}")
                    return {"_raw": raw_text, "_parse_error": str(e)}
    return None


def _extract_gt_table(table_el):
    """Extract a gt table into structured dict.

    Returns: {"title": str|None, "columns": [str], "rows": [{col: val}]}
    """
    result = {"title": None, "columns": [], "rows": []}

    # Title from gt_title cell
    title_cell = table_el.find("td", class_=lambda c: c and "gt_title" in c)
    if title_cell:
        result["title"] = title_cell.get_text(strip=True)

    # Column headers from <th> in gt_col_headings row
    header_row = table_el.find("tr", class_=lambda c: c and "gt_col_headings" in c)
    if header_row:
        for th in header_row.find_all("th"):
            col_id = th.get("id", "")
            col_text = th.get_text(strip=True)
            result["columns"].append(col_id if col_id else col_text)
    else:
        # Fallback: any <th> elements
        for th in table_el.find_all("th"):
            col_text = th.get_text(strip=True)
            if col_text and col_text != result.get("title"):
                result["columns"].append(col_text)

    # Rows from gt_table_body
    tbody = table_el.find("tbody", class_=lambda c: c and "gt_table_body" in c)
    if tbody is None:
        tbody = table_el.find("tbody")

    if tbody:
        for tr in tbody.find_all("tr"):
            row = {}
            cells = tr.find_all("td")
            for i, td in enumerate(cells):
                col_name = result["columns"][i] if i < len(result["columns"]) else f"col_{i}"
                # Get the headers attribute if available (BS4 may return list)
                headers_attr = td.get("headers", "")
                if headers_attr:
                    if isinstance(headers_attr, list):
                        headers_attr = headers_attr[0] if headers_attr else ""
                    col_name = str(headers_attr)
                row[col_name] = td.get_text(strip=True)
            if row:
                result["rows"].append(row)

    return result


def _extract_all_tables(element):
    """Extract all gt tables from an element."""
    tables = []
    for table_el in element.find_all("table", class_=lambda c: c and "gt_table" in c):
        tables.append(_extract_gt_table(table_el))

    # Also handle plain HTML tables (e.g., gtsummary)
    for table_el in element.find_all("table"):
        classes = " ".join(table_el.get("class", []))
        if "gt_table" in classes:
            continue  # Already handled above
        table_data = _extract_plain_table(table_el)
        if table_data["rows"]:
            tables.append(table_data)

    return tables


def _extract_plain_table(table_el):
    """Extract a non-gt HTML table."""
    result = {"title": None, "columns": [], "rows": []}

    # Caption
    caption = table_el.find("caption")
    if caption:
        result["title"] = caption.get_text(strip=True)

    # Headers
    thead = table_el.find("thead")
    if thead:
        for th in thead.find_all("th"):
            result["columns"].append(th.get_text(strip=True))

    # Body
    tbody = table_el.find("tbody")
    body = tbody if tbody else table_el
    for tr in body.find_all("tr"):
        cells = tr.find_all(["td", "th"])
        if not cells:
            continue
        row = {}
        for i, cell in enumerate(cells):
            col = result["columns"][i] if i < len(result["columns"]) else f"col_{i}"
            row[col] = cell.get_text(strip=True)
        if row:
            result["rows"].append(row)

    return result


def _extract_model_card(element):
    """Extract model card from <ul><li><strong>Label:</strong> value</li> pattern."""
    model_card = {}

    for li in element.find_all("li"):
        strong = li.find("strong")
        if strong:
            key = strong.get_text(strip=True).rstrip(":")
            # Value is everything after the <strong> tag
            value_parts = []
            for sibling in strong.next_siblings:
                text = sibling.get_text(strip=True) if hasattr(sibling, "get_text") else str(sibling).strip()
                if text:
                    value_parts.append(text)
            value = " ".join(value_parts).lstrip(": ")
            if key and value:
                model_card[key] = value

    return model_card if model_card else None


def _extract_figures(soup):
    """Extract figure metadata from the document."""
    figures = []

    # Look for <img> tags
    for img in soup.find_all("img"):
        src = img.get("src", "")
        alt = img.get("alt", "")
        if not src or src.startswith("data:image/svg"):
            continue  # Skip tiny SVG icons

        # Find parent cell for context
        cell_parent = img.find_parent(class_="cell")
        cell_id = cell_parent.get("id", "") if cell_parent else ""

        # Find parent section
        section_parent = img.find_parent("section", class_="level1")
        section_heading = ""
        if section_parent:
            h = section_parent.find(["h1", "h2"])
            section_heading = h.get_text(strip=True) if h else ""

        # Caption from figcaption or parent figure
        caption = ""
        fig_parent = img.find_parent("figure")
        if fig_parent:
            figcaption = fig_parent.find("figcaption")
            if figcaption:
                caption = figcaption.get_text(strip=True)

        figures.append({
            "section": section_heading,
            "src": src,
            "cell_id": cell_id,
            "alt": alt,
            "caption": caption,
        })

    return figures


def _extract_section_0(element):
    """Extract Section 0 — Machine-Readable Metadata Header."""
    result = {"section_name": SECTION_REGISTRY[0]["name"]}

    yaml_data = _extract_yaml_from_code_block(element)
    if yaml_data:
        result["metadata"] = yaml_data
    else:
        # Fallback: try to find any YAML-like content
        result["metadata"] = None
        result["_warning"] = "No YAML code block found in Section 0"

    return result


def _extract_section_1(element):
    """Extract Section 1 — Executive Summary."""
    result = {"section_name": SECTION_REGISTRY[1]["name"]}

    # Look for Results-at-a-Glance table
    tables = _extract_all_tables(element)
    glance_table = None
    for t in tables:
        title = (t.get("title") or "").lower()
        if "glance" in title or "results" in title:
            glance_table = t
            break

    if glance_table:
        # Convert to flat dict {metric: value}
        result["results_at_a_glance"] = {}
        for row in glance_table.get("rows", []):
            values = list(row.values())
            if len(values) >= 2:
                result["results_at_a_glance"][values[0]] = values[1]
    else:
        result["results_at_a_glance"] = None

    # Extract text content (structured summary)
    result["text"] = _extract_text_content(element)
    result["tables"] = tables

    return result


def _extract_section_6(element):
    """Extract Section 6 — Primary Analysis with model cards."""
    result = {"section_name": SECTION_REGISTRY[6]["name"]}

    # Look for model card subsection
    model_card_section = None
    for sub in element.find_all("section"):
        heading = sub.find(["h2", "h3"])
        if heading and "model card" in heading.get_text(strip=True).lower():
            model_card_section = sub
            break

    if model_card_section:
        result["model_card"] = _extract_model_card(model_card_section)
    else:
        # Try extracting from the whole section
        card = _extract_model_card(element)
        result["model_card"] = card

    result["tables"] = _extract_all_tables(element)
    result["text"] = _extract_text_content(element)

    return result


def _extract_text_content(element):
    """Extract meaningful text from an element, excluding code and tables."""
    texts = []
    for p in element.find_all("p", recursive=True):
        # Skip paragraphs inside code blocks
        if p.find_parent("pre"):
            continue
        text = p.get_text(strip=True)
        if text:
            texts.append(text)
    return "\n\n".join(texts) if texts else ""


def _extract_list_items(element):
    """Extract list items from an element."""
    items = []
    for li in element.find_all("li", recursive=True):
        # Skip items from nested tables
        if li.find_parent("table"):
            continue
        text = li.get_text(strip=True)
        if text:
            items.append(text)
    return items


def _extract_generic_section(element, section_num):
    """Generic extraction for any section."""
    info = SECTION_REGISTRY.get(section_num, {"name": f"Section {section_num}", "key": f"section_{section_num}"})
    result = {"section_name": info["name"]}

    # Subsections
    subsections = {}
    for sub in element.find_all("section", recursive=False):
        heading = sub.find(["h2", "h3"])
        if heading:
            sub_name = heading.get_text(strip=True)
            subsections[sub_name] = {
                "text": _extract_text_content(sub),
                "tables": _extract_all_tables(sub),
                "list_items": _extract_list_items(sub),
            }
            # Try model card extraction for subsections with bullet lists
            card = _extract_model_card(sub)
            if card:
                subsections[sub_name]["model_card"] = card

    if subsections:
        result["subsections"] = subsections

    result["tables"] = _extract_all_tables(element)
    result["text"] = _extract_text_content(element)
    result["list_items"] = _extract_list_items(element)

    return result


def extract_report(html_path, sections=None, strict=False):
    """Main entry point: extract structured data from a report-spec HTML file.

    Args:
        html_path: Path to the Quarto-rendered HTML file.
        sections: Optional list of section numbers to extract (e.g., [0, 1, 6]).
                  If None, extract all found sections.
        strict: If True, raise ValueError when expected sections are missing.

    Returns:
        dict with keys: title, author, date, sections, tables, figures
    """
    main_content, full_soup = _parse_html(html_path)

    # Extract document-level metadata
    title_el = full_soup.find("title")
    doc_title = title_el.get_text(strip=True) if title_el else ""

    # Try to get author/date from Quarto metadata
    author = ""
    date = ""
    for meta in full_soup.find_all("meta"):
        if meta.get("name") == "author":
            author = meta.get("content", "")
        if meta.get("name") == "date":
            date = meta.get("content", "")

    # Find sections
    found_sections = _find_sections(main_content)

    if strict:
        expected = set(sections) if sections else set(range(12))
        missing = expected - set(found_sections.keys())
        if missing:
            raise ValueError(f"Missing required sections: {sorted(missing)}")

    # Filter to requested sections
    if sections is not None:
        target_sections = {k: v for k, v in found_sections.items() if k in sections}
    else:
        target_sections = found_sections

    # Extract each section
    extracted_sections = {}
    for sec_num, element in sorted(target_sections.items()):
        try:
            if sec_num == 0:
                extracted_sections[sec_num] = _extract_section_0(element)
            elif sec_num == 1:
                extracted_sections[sec_num] = _extract_section_1(element)
            elif sec_num == 6:
                extracted_sections[sec_num] = _extract_section_6(element)
            else:
                extracted_sections[sec_num] = _extract_generic_section(element, sec_num)
        except Exception as e:
            logger.warning(f"Error extracting section {sec_num}: {e}")
            if strict:
                raise
            extracted_sections[sec_num] = {
                "section_name": SECTION_REGISTRY.get(sec_num, {}).get("name", f"Section {sec_num}"),
                "_error": str(e),
            }

    # Warn about missing sections in best-effort mode
    if not strict and sections is None:
        all_expected = set(range(12))
        found = set(extracted_sections.keys())
        missing = all_expected - found
        if missing:
            logger.info(f"Sections not found in document: {sorted(missing)}")

    # Extract all figures from the document
    figures = _extract_figures(main_content)

    # Collect all tables across all sections
    all_tables = []
    for sec_data in extracted_sections.values():
        if "tables" in sec_data:
            all_tables.extend(sec_data["tables"])

    return {
        "title": doc_title,
        "author": author,
        "date": date,
        "sections_found": sorted(extracted_sections.keys()),
        "sections": extracted_sections,
        "tables": all_tables,
        "figures": figures,
    }


def format_yaml(data):
    """Format extracted report data as YAML."""
    import yaml

    # Custom representer to handle multiline strings nicely
    def str_representer(dumper, data):
        if "\n" in data:
            return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
        return dumper.represent_scalar("tag:yaml.org,2002:str", data)

    yaml.add_representer(str, str_representer)
    return yaml.dump(data, default_flow_style=False, sort_keys=False, allow_unicode=True, width=120)


class _ReportEncoder(json.JSONEncoder):
    """JSON encoder that handles date/datetime from YAML parsing."""

    def default(self, obj):
        import datetime

        if isinstance(obj, (datetime.date, datetime.datetime)):
            return obj.isoformat()
        return super().default(obj)


def format_json(data):
    """Format extracted report data as JSON."""
    return json.dumps(data, indent=2, ensure_ascii=False, cls=_ReportEncoder)


def format_markdown(data):
    """Format as condensed markdown: metadata + results + model card + manuscript paragraph."""
    lines = []

    lines.append(f"# {data.get('title', 'Report Extraction')}")
    if data.get("author"):
        lines.append(f"**Author:** {data['author']}")
    if data.get("date"):
        lines.append(f"**Date:** {data['date']}")
    lines.append("")

    sections = data.get("sections", {})

    # Section 0: Metadata
    if 0 in sections:
        sec0 = sections[0]
        metadata = sec0.get("metadata")
        if metadata and isinstance(metadata, dict):
            lines.append("## Metadata")
            for k, v in metadata.items():
                if not k.startswith("_"):
                    lines.append(f"- **{k}:** {v}")
            lines.append("")

    # Section 1: Results at a Glance
    if 1 in sections:
        sec1 = sections[1]
        glance = sec1.get("results_at_a_glance")
        if glance:
            lines.append("## Results at a Glance")
            lines.append("")
            lines.append("| Metric | Value |")
            lines.append("|--------|-------|")
            for k, v in glance.items():
                lines.append(f"| {k} | {v} |")
            lines.append("")

    # Section 6: Model Card
    if 6 in sections:
        sec6 = sections[6]
        card = sec6.get("model_card")
        if card:
            lines.append("## Model Card")
            for k, v in card.items():
                lines.append(f"- **{k}:** {v}")
            lines.append("")

    # Section 8: Manuscript Results
    if 8 in sections:
        sec8 = sections[8]
        text = sec8.get("text", "")
        if text:
            lines.append("## Manuscript Results")
            lines.append(text)
            lines.append("")

    # Section 9: Limitations
    if 9 in sections:
        sec9 = sections[9]
        items = sec9.get("list_items", [])
        if items:
            lines.append("## Limitations")
            for item in items[:10]:  # Cap at 10
                lines.append(f"- {item}")
            lines.append("")

    # Figures summary
    figures = data.get("figures", [])
    if figures:
        lines.append(f"## Figures ({len(figures)} total)")
        for fig in figures:
            caption = fig.get("caption") or fig.get("alt") or "untitled"
            section = fig.get("section", "")
            lines.append(f"- [{section}] {caption}")
        lines.append("")

    return "\n".join(lines)
