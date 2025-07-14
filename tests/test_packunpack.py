import pytest
from pathlib import Path
from txtarchive.packunpack import run_concat

# how to run the test from the bash command line
# make sure you are in the root directory of the package
# such as cd /home/runner/work/txtarchive/txtarchive
# pytest tests/test_packunpack.py

@pytest.fixture
def temp_dir(tmp_path):
    # Create some test files in the temporary directory
    (tmp_path / 'test1.yaml').write_text('content of test1.yaml')
    (tmp_path / 'test2.py').write_text('content of test2.py')
    (tmp_path / 'test3.r').write_text('content of test3.r')
    (tmp_path / 'ignore.log').write_text('this should be ignored')
    return tmp_path

def test_run_concat_with_strings(temp_dir):
    combined_file = str(temp_dir / 'combined_files.txt')
    run_concat(str(temp_dir), combined_files = combined_file, file_types=['.yaml', '.py', '.r'])    
    assert (temp_dir / 'combined_files.txt').exists()
    
def test_run_concate_with_paths(temp_dir):
    combined_file = temp_dir / 'combined_files.txt'
    run_concat(temp_dir, combined_files = combined_file, file_types=['.yaml', '.py', '.r'])    
    content = combined_file.read_text()
    assert 'content of test1.yaml' in content
    assert 'content of test2.py' in content
    assert 'content of test3.r' in content
    assert 'this should be ignored' not in content