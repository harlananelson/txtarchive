# txtarchive/html_converter.py
"""
HTML to Markdown converter for txtarchive.
Converts Quarto-rendered HTML files to clean markdown, with optional
base64 image extraction. Follows the word_converter.py pattern.
"""

import os
import re
import base64
from pathlib import Path
from .header import logger

# Optional dependency - pypandoc (already in pyproject.toml)
try:
    import pypandoc
    PANDOC_AVAILABLE = True
except ImportError:
    PANDOC_AVAILABLE = False


def strip_html_boilerplate(html):
    """
    Extract meaningful content from Quarto-rendered HTML by removing
    CSS, JS, navigation, and other boilerplate.

    Looks for Quarto's #quarto-content div first, then <main>, then <body>.
    Strips <script>, <style>, <nav>, <header>, <footer> tags.

    Args:
        html (str): Raw HTML content.

    Returns:
        str: Cleaned HTML with boilerplate removed.
    """
    if not html:
        return ""

    # Try to extract the main content area (Quarto-specific first)
    # Look for <div id="quarto-content" ...>...</div>
    quarto_match = re.search(
        r'<div[^>]*id=["\']quarto-content["\'][^>]*>(.*)</div>\s*(?:<div[^>]*id=["\']quarto-back-to-top|<script|<footer|$)',
        html, flags=re.DOTALL | re.IGNORECASE
    )
    if quarto_match:
        html = quarto_match.group(1)
        logger.info("Extracted Quarto content div")
    else:
        # Try <main> tag
        main_match = re.search(r'<main[^>]*>(.*?)</main>', html, flags=re.DOTALL | re.IGNORECASE)
        if main_match:
            html = main_match.group(1)
            logger.info("Extracted <main> content")
        else:
            # Fall back to <body>
            body_match = re.search(r'<body[^>]*>(.*?)</body>', html, flags=re.DOTALL | re.IGNORECASE)
            if body_match:
                html = body_match.group(1)
                logger.info("Extracted <body> content")

    # Remove script tags and their contents
    html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)

    # Remove style tags and their contents
    html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)

    # Remove nav elements
    html = re.sub(r'<nav[^>]*>.*?</nav>', '', html, flags=re.DOTALL | re.IGNORECASE)

    # Remove header elements (page headers, not content headings)
    html = re.sub(r'<header[^>]*>.*?</header>', '', html, flags=re.DOTALL | re.IGNORECASE)

    # Remove footer elements
    html = re.sub(r'<footer[^>]*>.*?</footer>', '', html, flags=re.DOTALL | re.IGNORECASE)

    # Remove Quarto-specific sidebar/TOC
    html = re.sub(r'<div[^>]*id=["\']quarto-sidebar["\'][^>]*>.*?</div>', '', html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r'<div[^>]*id=["\']quarto-margin-sidebar["\'][^>]*>.*?</div>', '', html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r'<div[^>]*id=["\']TOC["\'][^>]*>.*?</div>', '', html, flags=re.DOTALL | re.IGNORECASE)

    # Remove link tags (CSS includes)
    html = re.sub(r'<link[^>]*/?>', '', html, flags=re.IGNORECASE)

    # Remove meta tags
    html = re.sub(r'<meta[^>]*/?>', '', html, flags=re.IGNORECASE)

    return html.strip()


def extract_base64_images(html, output_dir, base_name="image"):
    """
    Find base64-encoded images in HTML, decode them to files,
    and replace with markdown image references.

    Args:
        html (str): HTML content potentially containing base64 images.
        output_dir (str or Path): Directory to save extracted image files.
        base_name (str): Base name for extracted image files.

    Returns:
        tuple: (modified_html, list_of_extracted_paths)
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    extracted_paths = []
    image_counter = 0

    def replace_image(match):
        nonlocal image_counter
        image_counter += 1

        mime_type = match.group(1)  # e.g., "png", "jpeg", "svg+xml"
        b64_data = match.group(2)

        # Determine file extension from MIME type
        ext_map = {
            'png': '.png',
            'jpeg': '.jpg',
            'jpg': '.jpg',
            'gif': '.gif',
            'svg+xml': '.svg',
            'webp': '.webp',
        }
        ext = ext_map.get(mime_type, '.png')

        filename = f"{base_name}_{image_counter:03d}{ext}"
        filepath = output_dir / filename

        try:
            image_data = base64.b64decode(b64_data)
            with open(filepath, 'wb') as f:
                f.write(image_data)
            extracted_paths.append(filepath)
            logger.info(f"Extracted image: {filepath} ({len(image_data)} bytes)")
        except Exception as e:
            logger.error(f"Failed to decode image {image_counter}: {e}")
            return match.group(0)  # Return original on failure

        # Get alt text if available
        alt_match = re.search(r'alt=["\']([^"\']*)["\']', match.group(0)[:200])
        alt_text = alt_match.group(1) if alt_match else f"Image {image_counter}"

        return f'![{alt_text}]({filename})'

    # Match <img> tags with base64 src
    pattern = r'<img[^>]*src=["\']data:image/([^;]+);base64,([^"\']+)["\'][^>]*/?\s*>'
    modified_html = re.sub(pattern, replace_image, html, flags=re.IGNORECASE)

    if image_counter > 0:
        logger.info(f"Extracted {image_counter} base64 images to {output_dir}")

    return modified_html, extracted_paths


def _replace_base64_with_placeholders(html):
    """
    Replace base64-encoded images with descriptive placeholders.
    Used for in-memory/archive mode where saving files isn't appropriate.

    Args:
        html (str): HTML content with base64 images.

    Returns:
        str: HTML with base64 images replaced by placeholders.
    """
    image_counter = 0

    def replace_with_placeholder(match):
        nonlocal image_counter
        image_counter += 1

        mime_type = match.group(1)
        b64_data = match.group(2)

        # Calculate approximate decoded size
        try:
            size_bytes = len(base64.b64decode(b64_data))
            if size_bytes >= 1024:
                size_str = f"{size_bytes / 1024:.0f}KB"
            else:
                size_str = f"{size_bytes} bytes"
        except Exception:
            size_str = "unknown size"

        ext_upper = mime_type.upper().replace('+XML', '')

        # Get alt text if available
        alt_match = re.search(r'alt=["\']([^"\']*)["\']', match.group(0)[:200])
        alt_text = alt_match.group(1) if alt_match else ""
        alt_suffix = f": {alt_text}" if alt_text else ""

        return f'[Image {image_counter}{alt_suffix}: {ext_upper}, {size_str}]'

    pattern = r'<img[^>]*src=["\']data:image/([^;]+);base64,([^"\']+)["\'][^>]*/?\s*>'
    result = re.sub(pattern, replace_with_placeholder, html, flags=re.IGNORECASE)

    if image_counter > 0:
        logger.info(f"Replaced {image_counter} base64 images with placeholders")

    return result


def convert_html_with_pandoc(html_content):
    """
    Convert HTML to markdown using pandoc (primary method).

    Args:
        html_content (str): HTML content to convert.

    Returns:
        str: Markdown content.
    """
    if not PANDOC_AVAILABLE:
        raise ImportError("pypandoc library is required for pandoc conversion")

    try:
        markdown_content = pypandoc.convert_text(
            html_content,
            'markdown',
            format='html',
            extra_args=['--wrap=none', '--markdown-headings=atx']
        )
        return markdown_content
    except Exception as e:
        logger.error(f"Error converting with pandoc: {e}")
        raise


def convert_html_with_regex(html_content):
    """
    Convert HTML to markdown using regex-based conversion.
    Fallback method when pandoc is not available.
    Enhanced version of word_converter.html_to_markdown().

    Args:
        html_content (str): HTML content to convert.

    Returns:
        str: Markdown content.
    """
    if not html_content:
        return ""

    content = html_content

    # Code blocks (pre > code) - do this before other transformations
    content = re.sub(
        r'<pre[^>]*>\s*<code[^>]*(?:class=["\']([^"\']*)["\'])?[^>]*>(.*?)</code>\s*</pre>',
        lambda m: f'\n```{_extract_language(m.group(1) or "")}\n{_unescape_html(m.group(2))}\n```\n',
        content, flags=re.DOTALL | re.IGNORECASE
    )

    # Inline code
    content = re.sub(r'<code[^>]*>(.*?)</code>', r'`\1`', content, flags=re.DOTALL | re.IGNORECASE)

    # Headers
    for i in range(6, 0, -1):
        content = re.sub(
            rf'<h{i}[^>]*>(.*?)</h{i}>',
            rf'\n{"#" * i} \1\n',
            content, flags=re.IGNORECASE | re.DOTALL
        )

    # Bold and italic
    content = re.sub(r'<strong[^>]*>(.*?)</strong>', r'**\1**', content, flags=re.IGNORECASE | re.DOTALL)
    content = re.sub(r'<b[^>]*>(.*?)</b>', r'**\1**', content, flags=re.IGNORECASE | re.DOTALL)
    content = re.sub(r'<em[^>]*>(.*?)</em>', r'*\1*', content, flags=re.IGNORECASE | re.DOTALL)
    content = re.sub(r'<i[^>]*>(.*?)</i>', r'*\1*', content, flags=re.IGNORECASE | re.DOTALL)

    # Links
    content = re.sub(
        r'<a[^>]*href=["\']([^"\']*)["\'][^>]*>(.*?)</a>',
        r'[\2](\1)', content, flags=re.IGNORECASE | re.DOTALL
    )

    # Images (non-base64, already handled separately)
    content = re.sub(
        r'<img[^>]*src=["\']([^"\']*)["\'][^>]*alt=["\']([^"\']*)["\'][^>]*/?\s*>',
        r'![\2](\1)', content, flags=re.IGNORECASE
    )
    content = re.sub(
        r'<img[^>]*alt=["\']([^"\']*)["\'][^>]*src=["\']([^"\']*)["\'][^>]*/?\s*>',
        r'![\1](\2)', content, flags=re.IGNORECASE
    )

    # Tables
    content = _convert_tables_regex(content)

    # Blockquotes
    content = re.sub(
        r'<blockquote[^>]*>(.*?)</blockquote>',
        lambda m: '\n' + '\n'.join('> ' + line for line in m.group(1).strip().split('\n')) + '\n',
        content, flags=re.DOTALL | re.IGNORECASE
    )

    # Paragraphs
    content = re.sub(r'<p[^>]*>(.*?)</p>', r'\1\n\n', content, flags=re.IGNORECASE | re.DOTALL)

    # Line breaks
    content = re.sub(r'<br[^>]*/?>', '\n', content, flags=re.IGNORECASE)

    # Horizontal rules
    content = re.sub(r'<hr[^>]*/?\s*>', '\n---\n', content, flags=re.IGNORECASE)

    # Lists
    content = re.sub(r'<ul[^>]*>', '\n', content, flags=re.IGNORECASE)
    content = re.sub(r'</ul>', '\n', content, flags=re.IGNORECASE)
    content = re.sub(r'<ol[^>]*>', '\n', content, flags=re.IGNORECASE)
    content = re.sub(r'</ol>', '\n', content, flags=re.IGNORECASE)
    content = re.sub(r'<li[^>]*>(.*?)</li>', r'- \1\n', content, flags=re.IGNORECASE | re.DOTALL)

    # Definition lists
    content = re.sub(r'<dl[^>]*>', '\n', content, flags=re.IGNORECASE)
    content = re.sub(r'</dl>', '\n', content, flags=re.IGNORECASE)
    content = re.sub(r'<dt[^>]*>(.*?)</dt>', r'**\1**\n', content, flags=re.IGNORECASE | re.DOTALL)
    content = re.sub(r'<dd[^>]*>(.*?)</dd>', r': \1\n', content, flags=re.IGNORECASE | re.DOTALL)

    # Remove remaining div/span tags but keep their content
    content = re.sub(r'</?(?:div|span|section|article|aside)[^>]*>', '', content, flags=re.IGNORECASE)

    # Remove remaining HTML tags
    content = re.sub(r'<[^>]+>', '', content)

    # Unescape HTML entities
    content = _unescape_html(content)

    # Clean up extra whitespace
    content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
    content = re.sub(r' +', ' ', content)
    content = content.strip()

    return content


def _extract_language(class_str):
    """Extract programming language from code block class attribute."""
    if not class_str:
        return ""
    # Common patterns: "language-python", "sourceCode python", "highlight-python"
    lang_match = re.search(r'(?:language-|sourceCode\s+|highlight-)(\w+)', class_str)
    if lang_match:
        return lang_match.group(1)
    # Just return first word if it looks like a language
    parts = class_str.split()
    for part in parts:
        if part in ('python', 'r', 'R', 'javascript', 'js', 'bash', 'sh', 'sql',
                     'json', 'yaml', 'html', 'css', 'cpp', 'java', 'ruby', 'go',
                     'rust', 'typescript', 'ts', 'markdown', 'xml'):
            return part
    return ""


def _unescape_html(text):
    """Unescape common HTML entities."""
    text = text.replace('&amp;', '&')
    text = text.replace('&lt;', '<')
    text = text.replace('&gt;', '>')
    text = text.replace('&quot;', '"')
    text = text.replace('&#39;', "'")
    text = text.replace('&apos;', "'")
    text = text.replace('&nbsp;', ' ')
    # Numeric entities
    text = re.sub(r'&#(\d+);', lambda m: chr(int(m.group(1))), text)
    text = re.sub(r'&#x([0-9a-fA-F]+);', lambda m: chr(int(m.group(1), 16)), text)
    return text


def _convert_tables_regex(html):
    """Convert HTML tables to markdown tables."""
    def table_to_markdown(match):
        table_html = match.group(0)

        rows = re.findall(r'<tr[^>]*>(.*?)</tr>', table_html, flags=re.DOTALL | re.IGNORECASE)
        if not rows:
            return table_html

        md_rows = []
        for row_idx, row in enumerate(rows):
            # Extract cells (th or td)
            cells = re.findall(r'<(?:th|td)[^>]*>(.*?)</(?:th|td)>', row, flags=re.DOTALL | re.IGNORECASE)
            # Clean cell content
            cleaned_cells = []
            for cell in cells:
                cell_text = re.sub(r'<[^>]+>', '', cell).strip()
                cell_text = cell_text.replace('|', '\\|')
                cell_text = ' '.join(cell_text.split())
                cleaned_cells.append(cell_text)

            if cleaned_cells:
                md_rows.append('| ' + ' | '.join(cleaned_cells) + ' |')

                # Add separator after first row (header)
                if row_idx == 0:
                    md_rows.append('| ' + ' | '.join(['---'] * len(cleaned_cells)) + ' |')

        return '\n' + '\n'.join(md_rows) + '\n'

    return re.sub(r'<table[^>]*>.*?</table>', table_to_markdown, html, flags=re.DOTALL | re.IGNORECASE)


def convert_html_to_markdown(html_path, method='auto', extract_images=True, image_output_dir=None):
    """
    Convert an HTML file to markdown format.

    Args:
        html_path (str or Path): Path to the .html file.
        method (str): Conversion method - 'auto', 'pandoc', or 'regex'.
        extract_images (bool): Whether to extract base64 images to files.
        image_output_dir (str or Path): Directory for extracted images
            (default: same directory as HTML file).

    Returns:
        str: Markdown content.
    """
    html_path = Path(html_path)

    if not html_path.exists():
        raise FileNotFoundError(f"HTML file not found: {html_path}")

    logger.info(f"Converting HTML to markdown: {html_path}")

    # Read HTML file
    with html_path.open("r", encoding="utf-8", errors="replace") as f:
        html_content = f.read()

    # Strip boilerplate
    html_content = strip_html_boilerplate(html_content)

    # Handle base64 images
    if extract_images:
        if image_output_dir is None:
            image_output_dir = html_path.parent / f"{html_path.stem}_images"
        base_name = html_path.stem
        html_content, extracted_paths = extract_base64_images(
            html_content, image_output_dir, base_name
        )
        if extracted_paths:
            logger.info(f"Extracted {len(extracted_paths)} images to {image_output_dir}")
    else:
        html_content = _replace_base64_with_placeholders(html_content)

    # Select conversion method
    if method == 'auto':
        if PANDOC_AVAILABLE:
            method = 'pandoc'
        else:
            method = 'regex'
        logger.info(f"Auto-selected conversion method: {method}")

    try:
        if method == 'pandoc':
            return convert_html_with_pandoc(html_content)
        elif method == 'regex':
            return convert_html_with_regex(html_content)
        else:
            raise ValueError(f"Unknown conversion method: {method}")
    except ImportError as e:
        logger.error(f"Required library not available for method '{method}': {e}")
        if method != 'regex':
            logger.info("Falling back to regex conversion")
            return convert_html_with_regex(html_content)
        else:
            raise


def convert_html_to_markdown_text(html_content, method='auto'):
    """
    Convert HTML content to markdown in memory (no file I/O).
    Base64 images are replaced with descriptive placeholders.
    Used for inline conversion during archiving.

    Args:
        html_content (str): Raw HTML content.
        method (str): Conversion method - 'auto', 'pandoc', or 'regex'.

    Returns:
        str: Markdown content with image placeholders.
    """
    if not html_content:
        return ""

    # Strip boilerplate
    html_content = strip_html_boilerplate(html_content)

    # Replace base64 images with placeholders
    html_content = _replace_base64_with_placeholders(html_content)

    # Select conversion method
    if method == 'auto':
        if PANDOC_AVAILABLE:
            method = 'pandoc'
        else:
            method = 'regex'

    try:
        if method == 'pandoc':
            return convert_html_with_pandoc(html_content)
        elif method == 'regex':
            return convert_html_with_regex(html_content)
        else:
            raise ValueError(f"Unknown conversion method: {method}")
    except ImportError:
        if method != 'regex':
            return convert_html_with_regex(html_content)
        raise


def convert_html_documents_in_directory(directory, output_dir=None, method='auto',
                                        replace_existing=False, extract_images=True):
    """
    Convert all HTML files in a directory to markdown files.

    Args:
        directory (str or Path): Directory containing .html files.
        output_dir (str or Path): Output directory for markdown files
            (default: same as input).
        method (str): Conversion method.
        replace_existing (bool): Whether to overwrite existing markdown files.
        extract_images (bool): Whether to extract base64 images.

    Returns:
        list: List of (input_path, output_path) tuples for successful conversions.
    """
    directory = Path(directory)
    if output_dir is None:
        output_dir = directory
    else:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

    converted_files = []

    for html_file in directory.rglob("*.html"):
        if html_file.name.startswith("."):
            continue

        # Create output path
        relative_path = html_file.relative_to(directory)
        output_path = output_dir / relative_path.with_suffix('.md')

        # Create output directory if needed
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Check if output already exists
        if output_path.exists() and not replace_existing:
            logger.info(f"Skipping existing file: {output_path}")
            continue

        try:
            logger.info(f"Converting: {html_file} -> {output_path}")

            # Set image output dir relative to output
            image_dir = output_path.parent / f"{output_path.stem}_images" if extract_images else None

            markdown_content = convert_html_to_markdown(
                html_file, method=method,
                extract_images=extract_images,
                image_output_dir=image_dir
            )

            # Write markdown file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)

            converted_files.append((html_file, output_path))
            logger.info(f"Successfully converted: {output_path}")

        except Exception as e:
            logger.error(f"Failed to convert {html_file}: {e}")
            continue

    logger.info(f"Converted {len(converted_files)} HTML documents to markdown")
    return converted_files
