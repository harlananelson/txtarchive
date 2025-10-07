#!/usr/bin/env python3
"""
Test script for Word to Markdown conversion functionality.
Creates sample Word documents and tests conversion methods.
"""

import os
import sys
import tempfile
import json
from pathlib import Path

def create_test_docx():
    """
    Create a simple test .docx file for testing conversion.
    This creates a minimal Word document structure.
    """
    test_dir = Path(tempfile.mkdtemp(prefix="word_test_"))
    docx_path = test_dir / "test_document.docx"

    # Create a minimal .docx file structure
    import zipfile

    # Basic Word document XML content
    document_xml = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
    <w:body>
        <w:p>
            <w:pPr>
                <w:pStyle w:val="Heading1"/>
            </w:pPr>
            <w:r>
                <w:t>Test Document</w:t>
            </w:r>
        </w:p>
        <w:p>
            <w:r>
                <w:t>This is a test paragraph with some </w:t>
            </w:r>
            <w:r>
                <w:rPr>
                    <w:b/>
                </w:rPr>
                <w:t>bold text</w:t>
            </w:r>
            <w:r>
                <w:t> and normal text.</w:t>
            </w:r>
        </w:p>
        <w:p>
            <w:pPr>
                <w:pStyle w:val="Heading2"/>
            </w:pPr>
            <w:r>
                <w:t>Section 2</w:t>
            </w:r>
        </w:p>
        <w:p>
            <w:r>
                <w:t>Another paragraph with more content for testing the conversion functionality.</w:t>
            </w:r>
        </w:p>
    </w:body>
</w:document>'''

    content_types_xml = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
    <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
    <Default Extension="xml" ContentType="application/xml"/>
    <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>'''

    app_xml = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">
    <Application>txtarchive test</Application>
</Properties>'''

    rels_xml = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
    <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>'''

    # Create the .docx file
    with zipfile.ZipFile(docx_path, 'w', zipfile.ZIP_DEFLATED) as docx:
        docx.writestr('[Content_Types].xml', content_types_xml)
        docx.writestr('_rels/.rels', rels_xml)
        docx.writestr('word/document.xml', document_xml)
        docx.writestr('docProps/app.xml', app_xml)

    print(f"Created test Word document: {docx_path}")
    return test_dir, docx_path

def test_conversion_methods():
    """Test different Word conversion methods."""
    print("\n=== Testing Word Conversion Methods ===")

    # Create test document
    test_dir, docx_path = create_test_docx()

    try:
        # Import the conversion functions
        try:
            from txtarchive.word_converter import convert_word_to_markdown, MAMMOTH_AVAILABLE, PYTHON_DOCX_AVAILABLE, PANDOC_AVAILABLE
        except ImportError as e:
            print(f"❌ Failed to import word_converter: {e}")
            print("Make sure you have the updated word_converter.py file in your txtarchive package")
            return False

        print(f"Available conversion libraries:")
        print(f"  - Mammoth: {'✅' if MAMMOTH_AVAILABLE else '❌'}")
        print(f"  - Python-docx: {'✅' if PYTHON_DOCX_AVAILABLE else '❌'}")
        print(f"  - Pandoc: {'✅' if PANDOC_AVAILABLE else '❌'}")

        # Test methods in order of preference
        methods_to_test = ['auto', 'basic']

        if MAMMOTH_AVAILABLE:
            methods_to_test.append('mammoth')
        if PYTHON_DOCX_AVAILABLE:
            methods_to_test.append('docx')
        if PANDOC_AVAILABLE:
            methods_to_test.append('pandoc')

        results = []

        for method in methods_to_test:
            print(f"\nTesting method: {method}")
            try:
                markdown_content = convert_word_to_markdown(docx_path, method=method)

                # Save result
                output_path = test_dir / f"output_{method}.md"
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(markdown_content)

                print(f"✅ Method '{method}' succeeded")
                print(f"   Output length: {len(markdown_content)} characters")
                print(f"   Output file: {output_path}")

                # Show first few lines
                lines = markdown_content.split('\n')[:5]
                print(f"   Preview: {' | '.join(line.strip() for line in lines if line.strip())}")

                results.append((method, True, len(markdown_content)))

            except Exception as e:
                print(f"❌ Method '{method}' failed: {e}")
                results.append((method, False, 0))

        return results

    finally:
        # Clean up
        import shutil
        shutil.rmtree(test_dir)
        print(f"\nCleaned up test directory: {test_dir}")

def test_cli_integration():
    """Test the CLI integration for Word conversion."""
    print("\n=== Testing CLI Integration ===")

    # Create test document
    test_dir, docx_path = create_test_docx()

    try:
        import subprocess

        # Test convert-word command
        output_path = test_dir / "cli_output.md"

        cmd = [
            "python", "-m", "txtarchive", "convert-word",
            str(docx_path),
            str(output_path),
            "--method", "auto"
        ]

        print(f"Running command: {' '.join(cmd)}")

        result = subprocess.run(cmd, capture_output=True, text=True)

        print(f"Return code: {result.returncode}")
        if result.stdout:
            print(f"Stdout: {result.stdout}")
        if result.stderr:
            print(f"Stderr: {result.stderr}")

        if result.returncode == 0 and output_path.exists():
            content = output_path.read_text()
            print(f"✅ CLI conversion succeeded")
            print(f"   Output length: {len(content)} characters")
            print(f"   First 200 chars: {content[:200]}...")
            return True
        else:
            print(f"❌ CLI conversion failed")
            return False

    except Exception as e:
        print(f"❌ CLI test failed: {e}")
        return False

    finally:
        import shutil
        shutil.rmtree(test_dir)

def run_word_conversion_tests():
    """Run all Word conversion tests."""
    print("Starting Word Conversion Tests for TxtArchive")
    print("=" * 50)

    # The "Archive Integration" test has been removed as it tested a
    # feature that does not exist (--convert-word flag on the archive command).
    tests = [
        ("Conversion Methods", test_conversion_methods),
        ("CLI Integration", test_cli_integration)
    ]

    results = []

    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = test_func()
            results.append((test_name, result))
            print(f"✅ {test_name}: {'PASS' if result else 'FAIL'}")
        except Exception as e:
            print(f"❌ {test_name}: FAILED with exception: {e}")
            results.append((test_name, False))

    # Print summary
    print("\n" + "=" * 50)
    print("WORD CONVERSION TEST SUMMARY")
    print("=" * 50)

    passed = sum(1 for _, result in results if result)
    failed = len(results) - passed

    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{test_name}: {status}")

    print(f"\nTotal: {len(results)} tests")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")

    if failed == 0:
        print("\n🎉 All Word conversion tests passed!")
    else:
        print(f"\n⚠️ {failed} test(s) failed")

def check_dependencies():
    """Check which Word conversion dependencies are available."""
    print("Checking Word Conversion Dependencies")
    print("=" * 40)

    dependencies = [
        ("mammoth", "High-quality Word conversion"),
        ("docx", "Basic Word document handling (python-docx)"),
        ("pypandoc", "Pandoc-based conversion"),
        ("zipfile", "Basic XML extraction (built-in)"),
        ("xml.etree.ElementTree", "XML parsing (built-in)")
    ]

    available = []
    missing = []

    for dep, description in dependencies:
        try:
            if dep == "docx":
                import docx
            elif dep == "zipfile":
                import zipfile
            elif dep == "xml.etree.ElementTree":
                import xml.etree.ElementTree
            else:
                __import__(dep)

            available.append((dep, description))
            print(f"✅ {dep}: {description}")
        except ImportError:
            missing.append((dep, description))
            print(f"❌ {dep}: {description}")

    print(f"\nSummary: {len(available)} available, {len(missing)} missing")

    if missing:
        print("\nTo install missing dependencies:")
        for dep, _ in missing:
            if dep == "docx":
                print(f"  pip install python-docx")
            elif dep in ["zipfile", "xml.etree.ElementTree"]:
                print(f"  {dep} is built-in (should not be missing)")
            else:
                print(f"  pip install {dep}")

    return len(missing) == 0

if __name__ == "__main__":
    print("TxtArchive Word Conversion Test Suite")
    print("=" * 60)

    # First check dependencies
    deps_ok = check_dependencies()

    if not deps_ok:
        print("\n⚠️ Some dependencies are missing, but tests will continue")
        print("Basic conversion should still work with built-in modules")

    # Run the tests
    run_word_conversion_tests()

    print("\n" + "=" * 60)
    print("Test complete! Check the results above.")
    print("For production use, install mammoth for best Word conversion quality.")
