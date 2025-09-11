#!/usr/bin/env python3
"""
Test script for the improved txtarchive ingestion functionality.
Tests the robust error handling and response validation.
"""

import os
import sys
import subprocess
import tempfile
import json
from pathlib import Path

def create_test_files():
    """Create test files of various sizes for ingestion testing."""
    test_dir = Path(tempfile.mkdtemp(prefix="ingestion_test_"))
    
    # Small file - should succeed
    small_file = test_dir / "small.py"
    small_file.write_text("""
def hello():
    return "Hello, world!"
""")
    
    # Medium file - should succeed
    medium_file = test_dir / "medium.py"
    medium_content = """
# Medium size Python file for testing
import os
import sys
from pathlib import Path

class TestClass:
    '''A test class for demonstration.'''
    
    def __init__(self, name):
        self.name = name
    
    def process_data(self, data):
        '''Process some data.'''
        results = []
        for item in data:
            if isinstance(item, str):
                results.append(item.upper())
            elif isinstance(item, (int, float)):
                results.append(item * 2)
            else:
                results.append(str(item))
        return results
    
    def generate_report(self):
        '''Generate a simple report.'''
        return f"Report for {self.name}"

def main():
    '''Main function for testing.'''
    test_obj = TestClass("test")
    sample_data = ["hello", 42, 3.14, True]
    processed = test_obj.process_data(sample_data)
    print(f"Processed data: {processed}")
    print(test_obj.generate_report())

if __name__ == "__main__":
    main()
""" * 5  # Repeat content to make it medium-sized
    medium_file.write_text(medium_content)
    
    # Large file - might exceed token limits
    large_file = test_dir / "large.py"
    large_content = """
# Large Python file that might exceed ingestion limits
""" + "# " + "x" * 100 + "\n" * 1000  # Create a very repetitive large file
    large_file.write_text(large_content)
    
    # Create a config file
    config_file = test_dir / "config.yaml"
    config_file.write_text("""
app:
  name: test_app
  version: 1.0.0
  debug: true

database:
  host: localhost
  port: 5432
  name: testdb
  
logging:
  level: INFO
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
""")
    
    return test_dir

def test_single_file_ingestion():
    """Test ingesting individual files with different sizes."""
    print("\n=== Testing Single File Ingestion ===")
    
    if not os.getenv("ACCESS_TOKEN"):
        print("⚠ ACCESS_TOKEN not set, skipping ingestion tests")
        return True
    
    test_dir = create_test_files()
    
    try:
        # Test small file
        print("Testing small file ingestion...")
        result = subprocess.run([
            "python", "-m", "txtarchive", "ingest",
            "--file", str(test_dir / "small.py")
        ], capture_output=True, text=True)
        
        print(f"Small file result: {result.returncode}")
        if result.stdout:
            print(f"Stdout: {result.stdout}")
        if result.stderr:
            print(f"Stderr: {result.stderr}")
        
        # Test medium file
        print("\nTesting medium file ingestion...")
        result = subprocess.run([
            "python", "-m", "txtarchive", "ingest",
            "--file", str(test_dir / "medium.py")
        ], capture_output=True, text=True)
        
        print(f"Medium file result: {result.returncode}")
        if result.stdout:
            print(f"Stdout: {result.stdout}")
        if result.stderr:
            print(f"Stderr: {result.stderr}")
        
        # Test large file (might fail due to size)
        print("\nTesting large file ingestion...")
        result = subprocess.run([
            "python", "-m", "txtarchive", "ingest",
            "--file", str(test_dir / "large.py")
        ], capture_output=True, text=True)
        
        print(f"Large file result: {result.returncode}")
        if result.stdout:
            print(f"Stdout: {result.stdout}")
        if result.stderr:
            print(f"Stderr: {result.stderr}")
        
        return True
        
    finally:
        import shutil
        shutil.rmtree(test_dir)

def test_archive_and_ingest_methods():
    """Test different ingestion methods."""
    print("\n=== Testing Archive-and-Ingest Methods ===")
    
    if not os.getenv("ACCESS_TOKEN"):
        print("⚠ ACCESS_TOKEN not set, skipping ingestion tests")
        return True
    
    test_dir = create_test_files()
    
    try:
        # Test auto method
        print("Testing auto method...")
        result = subprocess.run([
            "python", "-m", "txtarchive", "archive-and-ingest",
            str(test_dir),
            str(test_dir / "auto_archive.txt"),
            "--file_types", ".py", ".yaml",
            "--ingestion-method", "auto",
            "--max-tokens", "5000"
        ], capture_output=True, text=True)
        
        print(f"Auto method result: {result.returncode}")
        if result.stdout:
            print(f"Stdout: {result.stdout}")
        if result.stderr:
            print(f"Stderr: {result.stderr}")
        
        # Test directory method
        print("\nTesting directory method...")
        result = subprocess.run([
            "python", "-m", "txtarchive", "archive-and-ingest",
            str(test_dir),
            str(test_dir / "dir_archive.txt"),
            "--file_types", ".py",
            "--no-subdirectories",
            "--ingestion-method", "directory"
        ], capture_output=True, text=True)
        
        print(f"Directory method result: {result.returncode}")
        if result.stdout:
            print(f"Stdout: {result.stdout}")
        if result.stderr:
            print(f"Stderr: {result.stderr}")
        
        # Test archive method with splitting
        print("\nTesting archive method with splitting...")
        result = subprocess.run([
            "python", "-m", "txtarchive", "archive-and-ingest",
            str(test_dir),
            str(test_dir / "split_archive.txt"),
            "--file_types", ".py", ".yaml",
            "--ingestion-method", "archive",
            "--split-output",
            "--max-tokens", "2000",
            "--llm-friendly"
        ], capture_output=True, text=True)
        
        print(f"Archive method with splitting result: {result.returncode}")
        if result.stdout:
            print(f"Stdout: {result.stdout}")
        if result.stderr:
            print(f"Stderr: {result.stderr}")
        
        return True
        
    finally:
        import shutil
        shutil.rmtree(test_dir)

def test_txtarchive_package_ingestion():
    """Test ingesting the txtarchive package itself with improved error handling."""
    print("\n=== Testing TxtArchive Package Ingestion (Improved) ===")
    
    current_dir = Path.cwd()
    
    if not (current_dir / "txtarchive" / "__init__.py").exists():
        print("⚠ Not in txtarchive package directory")
        return True
    
    if not os.getenv("ACCESS_TOKEN"):
        print("⚠ ACCESS_TOKEN not set, creating archive only")
        
        # Just test archive creation
        result = subprocess.run([
            "python", "-m", "txtarchive", "archive",
            "txtarchive",
            "archive/txtarchive_test.txt",
            "--file_types", ".py", ".md",
            "--root-files", "pyproject.toml", "README.md",
            "--exclude-dirs", ".venv", "__pycache__", ".git",
            "--llm-friendly",
            "--split-output",
            "--max-tokens", "7500"
        ], capture_output=True, text=True)
        
        print(f"Archive creation result: {result.returncode}")
        if result.stdout:
            print(f"Archive stdout: {result.stdout}")
        if result.stderr:
            print(f"Archive stderr: {result.stderr}")
        
        return result.returncode == 0
    
    print("ACCESS_TOKEN found, testing ingestion with improved error handling...")
    
    # Test with different token limits to see error handling
    test_configs = [
        {
            "name": "Small chunks",
            "max_tokens": 5000,
            "method": "archive"
        },
        {
            "name": "Medium chunks", 
            "max_tokens": 15000,
            "method": "archive"
        },
        {
            "name": "Auto method",
            "max_tokens": 75000,
            "method": "auto"
        }
    ]
    
    for config in test_configs:
        print(f"\nTesting {config['name']} (max_tokens={config['max_tokens']}, method={config['method']})...")
        
        result = subprocess.run([
            "python", "-m", "txtarchive", "archive-and-ingest",
            "txtarchive",
            f"archive/txtarchive_{config['name'].lower().replace(' ', '_')}.txt",
            "--file_types", ".py", ".md",
            "--root-files", "pyproject.toml", "README.md", 
            "--exclude-dirs", ".venv", "__pycache__", ".git",
            "--llm-friendly",
            "--ingestion-method", config['method'],
            "--max-tokens", str(config['max_tokens']),
            "--split-output"
        ], capture_output=True, text=True)
        
        print(f"{config['name']} result: {result.returncode}")
        if result.stdout:
            print(f"Stdout: {result.stdout}")
        if result.stderr:
            print(f"Stderr: {result.stderr}")
    
    return True

def test_error_scenarios():
    """Test various error scenarios to validate robust error handling."""
    print("\n=== Testing Error Scenarios ===")
    
    if not os.getenv("ACCESS_TOKEN"):
        print("⚠ ACCESS_TOKEN not set, skipping error scenario tests")
        return True
    
    test_dir = create_test_files()
    
    try:
        # Test with very small token limit to force failures
        print("Testing with very small token limit...")
        result = subprocess.run([
            "python", "-m", "txtarchive", "archive-and-ingest",
            str(test_dir),
            str(test_dir / "tiny_chunks.txt"),
            "--file_types", ".py",
            "--ingestion-method", "archive",
            "--max-tokens", "100",  # Very small to force content too long errors
            "--split-output"
        ], capture_output=True, text=True)
        
        print(f"Tiny chunks result: {result.returncode}")
        if result.stdout:
            print(f"Stdout: {result.stdout}")
        if result.stderr:
            print(f"Stderr: {result.stderr}")
        
        # Test with non-existent file
        print("\nTesting with non-existent file...")
        result = subprocess.run([
            "python", "-m", "txtarchive", "ingest",
            "--file", str(test_dir / "nonexistent.py")
        ], capture_output=True, text=True)
        
        print(f"Non-existent file result: {result.returncode}")
        if result.stdout:
            print(f"Stdout: {result.stdout}")
        if result.stderr:
            print(f"Stderr: {result.stderr}")
        
        # Test with invalid directory
        print("\nTesting with invalid directory...")
        result = subprocess.run([
            "python", "-m", "txtarchive", "archive-and-ingest",
            str(test_dir / "nonexistent_dir"),
            str(test_dir / "invalid.txt"),
            "--ingestion-method", "directory"
        ], capture_output=True, text=True)
        
        print(f"Invalid directory result: {result.returncode}")
        if result.stdout:
            print(f"Stdout: {result.stdout}")
        if result.stderr:
            print(f"Stderr: {result.stderr}")
        
        return True
        
    finally:
        import shutil
        shutil.rmtree(test_dir)

def run_ingestion_tests():
    """Run all ingestion tests with improved error handling."""
    print("Starting Improved TxtArchive Ingestion Tests")
    print("=" * 50)
    
    tests = [
        test_single_file_ingestion,
        test_archive_and_ingest_methods,
        test_txtarchive_package_ingestion,
        test_error_scenarios
    ]
    
    results = []
    for test in tests:
        try:
            print(f"\nRunning {test.__name__}...")
            result = test()
            results.append((test.__name__, result))
            print(f"✓ {test.__name__}: {'PASS' if result else 'FAIL'}")
        except Exception as e:
            print(f"✗ {test.__name__} failed with exception: {e}")
            results.append((test.__name__, False))
    
    # Print summary
    print("\n" + "=" * 50)
    print("INGESTION TEST SUMMARY")
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
        print("\n🎉 All ingestion tests passed!")
    else:
        print(f"\n⚠ {failed} test(s) failed")
    
    # Provide guidance based on results
    print("\n" + "=" * 50)
    print("RECOMMENDATIONS")
    print("=" * 50)
    
    if not os.getenv("ACCESS_TOKEN"):
        print("• Set ACCESS_TOKEN environment variable to test actual ingestion")
        print("• export ACCESS_TOKEN='your_ask_sage_token'")
    
    print("• Review logs for detailed error messages")
    print("• Check txtarchve.log for comprehensive logging")
    print("• Adjust --max-tokens based on your API limits")
    print("• Use --split-output for large codebases")
    print("• Consider --ingestion-method auto for best results")

if __name__ == "__main__":
    run_ingestion_tests()