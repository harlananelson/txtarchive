#!/bin/bash
# Word to Markdown Conversion Examples for TxtArchive

echo "=== TxtArchive Word to Markdown Conversion Examples ==="

# Install optional dependencies for better conversion quality
echo "Installing optional dependencies for Word conversion..."
echo "pip install mammoth python-docx pypandoc"
echo ""

# 1. Convert a single Word document
echo "1. Converting a single Word document to markdown..."
python -m txtarchive convert-word "document.docx" "document.md" --method auto

echo ""
echo "2. Convert with specific method (mammoth for best quality)..."
python -m txtarchive convert-word "document.docx" "document.md" --method mammoth

echo ""
echo "3. Convert all Word documents in a directory..."
python -m txtarchive convert-word "documents/" "markdown_output/" --replace_existing

echo ""
echo "4. Archive with automatic Word document conversion..."
python -m txtarchive archive "project_with_docs/" "archive/project.txt" \
    --file_types .py .md .docx \
    --convert-word \
    --word-method auto \
    --llm-friendly

echo ""
echo "5. Archive and ingest with Word conversion..."
python -m txtarchive archive-and-ingest "documentation/" "archive/docs.txt" \
    --file_types .md .docx \
    --convert-word \
    --word-method mammoth \
    --llm-friendly \
    --ingestion-method auto

echo ""
echo "6. Convert Word docs and archive for LLM analysis..."
python -m txtarchive archive "research_project/" "archive/research.txt" \
    --file_types .py .ipynb .docx .md \
    --convert-word \
    --llm-friendly \
    --split-output \
    --max-tokens 50000

echo ""
echo "=== Word Conversion Methods Explained ==="
echo ""
echo "auto     - Automatically select best available method"
echo "mammoth  - Best quality, preserves formatting (requires: pip install mammoth)"
echo "pandoc   - High quality, requires pandoc installed (pip install pypandoc)" 
echo "docx     - Good for text extraction (requires: pip install python-docx)"
echo "basic    - Fallback method, no dependencies required"

echo ""
echo "=== Use Cases for Word Conversion ==="
echo ""
echo "📄 Documentation Projects:"
echo "   Convert Word docs to markdown for better version control"
echo "   python -m txtarchive convert-word \"docs/\" \"docs_md/\" --method mammoth"
echo ""
echo "🔬 Research Projects:"
echo "   Archive research with mixed Word/code content for AI analysis"
echo "   python -m txtarchive archive-and-ingest \"research/\" \"archive/research.txt\" \\"
echo "       --file_types .py .ipynb .docx .md --convert-word --llm-friendly"
echo ""
echo "📊 Business Reports:"
echo "   Convert Word reports to markdown for text processing"
echo "   python -m txtarchive convert-word \"reports/quarterly.docx\" --method auto"
echo ""
echo "📚 Knowledge Base:"
echo "   Archive Word documentation for AI-powered search"
echo "   python -m txtarchive archive-and-ingest \"knowledge_base/\" \"archive/kb.txt\" \\"
echo "       --file_types .docx .md --convert-word --split-output --max-tokens 25000"

echo ""
echo "=== Installation Requirements ==="
echo ""
echo "For best Word conversion quality, install these optional packages:"
echo ""
echo "# High-quality conversion (recommended)"
echo "pip install mammoth"
echo ""
echo "# Alternative high-quality conversion"
echo "pip install pypandoc"
echo "# Note: pypandoc also requires pandoc system installation"
echo "# See: https://pandoc.org/installing.html"
echo ""
echo "# Basic Word document handling"
echo "pip install python-docx"
echo ""
echo "# All optional dependencies at once"
echo "pip install mammoth python-docx pypandoc"

echo ""
echo "=== Testing Word Conversion ==="
echo ""
echo "Create a test Word document and try conversion:"
echo ""
echo "# Test with a sample document"
echo "python -m txtarchive convert-word \"test.docx\" \"test.md\" --method auto"
echo ""
echo "# Check what methods are available"
echo "python -c \"from txtarchive.word_converter import *; print('Available methods based on installed packages')\""

echo ""
echo "=== Troubleshooting ==="
echo ""
echo "If conversion fails:"
echo "• Check that the .docx file is not corrupted"
echo "• Try different conversion methods (auto, mammoth, docx, basic)"
echo "• Install additional dependencies for better support"
echo "• Use --method basic as last resort (no dependencies)"
echo ""
echo "Common issues:"
echo "• 'mammoth not available' - Install with: pip install mammoth"
echo "• 'pandoc not found' - Install pandoc system-wide"
echo "• 'python-docx not available' - Install with: pip install python-docx"
echo "• File access errors - Check file permissions and that file isn't open"

echo ""
echo "=== Integration with Existing Workflows ==="
echo ""
echo "Add Word conversion to your existing txtarchive commands:"
echo ""
echo "# Add to existing archive command"
echo "python -m txtarchive archive \"my_project/\" \"archive/project.txt\" \\"
echo "    --file_types .py .md .docx \\"
echo "    --convert-word \\"
echo "    --exclude-dirs .venv __pycache__"
echo ""
echo "# Add to existing ingestion workflow"
echo "python -m txtarchive archive-and-ingest \"documentation/\" \"archive/docs.txt\" \\"
echo "    --file_types .md .docx \\"
echo "    --convert-word \\"
echo "    --ingestion-method auto \\"
echo "    --max-tokens 75000"

echo ""
echo "=== Advanced Usage ==="
echo ""
echo "Batch convert multiple directories:"
echo "for dir in project1 project2 project3; do"
echo "    python -m txtarchive convert-word \"\$dir/\" \"\$dir/markdown/\" --replace_existing"
echo "done"
echo ""
echo "Convert and immediately archive:"
echo "python -m txtarchive archive \"mixed_content/\" \"archive/mixed.txt\" \\"
echo "    --file_types .py .ipynb .docx .md \\"
echo "    --convert-word --word-method mammoth \\"
echo "    --llm-friendly --split-output"

echo ""
echo "=== Performance Notes ==="
echo ""
echo "Conversion speed by method (fastest to slowest):"
echo "1. basic    - Very fast, basic text extraction"
echo "2. docx     - Fast, good structure preservation" 
echo "3. mammoth  - Medium, excellent formatting"
echo "4. pandoc   - Slower, comprehensive conversion"
echo ""
echo "For large document sets, consider:"
echo "• Using 'docx' method for speed"
echo "• Converting incrementally"
echo "• Using --replace_existing to avoid re-conversion"

echo ""
echo "=== Complete Example: Research Project ==="
echo ""
echo "# Example: Archive a mixed research project with Word docs, code, and notebooks"
echo "python -m txtarchive archive-and-ingest \"research_project/\" \"archive/research.txt\" \\"
echo "    --file_types .py .ipynb .docx .md .yaml \\"
echo "    --root-files README.md requirements.txt \\"
echo "    --exclude-dirs .venv __pycache__ .git \\"
echo "    --convert-word \\"
echo "    --word-method mammoth \\"
echo "    --llm-friendly \\"
echo "    --extract-code-only \\"
echo "    --split-output \\"
echo "    --max-tokens 50000 \\"
echo "    --ingestion-method auto"
echo ""
echo "This command will:"
echo "1. Convert all .docx files to markdown"
echo "2. Extract code-only from Jupyter notebooks" 
echo "3. Create an LLM-friendly archive"
echo "4. Split into 50k token chunks"
echo "5. Automatically ingest into Ask Sage"
echo "6. Include root files and exclude build directories"

echo ""
echo "=== Done ==="