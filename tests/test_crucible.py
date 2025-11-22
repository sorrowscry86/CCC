"""
Unit tests for the Crucible Protocol
"""

import pytest
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crucible import CrucibleEnvironment, verify_code


class TestCrucibleEnvironment:
    """Test the CrucibleEnvironment class"""

    def test_workspace_creation(self):
        """Test that workspace is created successfully"""
        with CrucibleEnvironment() as crucible:
            assert crucible.workspace is not None
            assert os.path.exists(crucible.workspace)
            assert 'crucible_' in crucible.workspace
            assert '_workspace' in crucible.workspace

    def test_workspace_cleanup(self):
        """Test that workspace is cleaned up after context exit"""
        crucible = CrucibleEnvironment()
        crucible.create_workspace()
        workspace_path = crucible.workspace
        assert os.path.exists(workspace_path)

        crucible.cleanup_workspace()
        assert not os.path.exists(workspace_path)

    def test_file_writing(self):
        """Test writing files to workspace"""
        with CrucibleEnvironment() as crucible:
            test_content = "print('Hello, World!')"
            crucible.write_file('test.py', test_content)

            file_path = os.path.join(crucible.workspace, 'test.py')
            assert os.path.exists(file_path)

            with open(file_path, 'r') as f:
                assert f.read() == test_content

    def test_write_without_workspace_raises_error(self):
        """Test that writing without workspace raises error"""
        crucible = CrucibleEnvironment()
        with pytest.raises(RuntimeError, match="Workspace not created"):
            crucible.write_file('test.py', 'content')


class TestVerifyCode:
    """Test the verify_code function"""

    def test_passing_code(self):
        """Test code that passes all tests"""
        code = """
def add(a, b):
    return a + b
"""
        test = """
from main import add

def test_add():
    assert add(2, 3) == 5
    assert add(0, 0) == 0
    assert add(-1, 1) == 0
"""
        result = verify_code(code, test)

        assert result['success'] is True
        assert result['returncode'] == 0
        assert 'passed' in result['stdout'].lower()

    def test_failing_code(self):
        """Test code that fails tests"""
        code = """
def add(a, b):
    return a - b  # Wrong implementation
"""
        test = """
from main import add

def test_add():
    assert add(2, 3) == 5
"""
        result = verify_code(code, test)

        assert result['success'] is False
        assert result['returncode'] != 0

    def test_syntax_error_code(self):
        """Test code with syntax errors"""
        code = """
def add(a, b
    return a + b  # Missing closing parenthesis
"""
        test = """
from main import add

def test_add():
    assert add(2, 3) == 5
"""
        result = verify_code(code, test)

        assert result['success'] is False

    def test_timeout_handling(self):
        """Test that timeout is enforced"""
        code = """
import time

def slow_function():
    time.sleep(100)
    return True
"""
        test = """
from main import slow_function

def test_slow():
    assert slow_function() is True
"""
        result = verify_code(code, test, timeout=1)

        assert result['success'] is False
        assert 'timed out' in result['stderr'].lower()

    def test_import_error(self):
        """Test handling of import errors"""
        code = """
def add(a, b):
    return a + b
"""
        test = """
from nonexistent_module import something

def test_add():
    assert True
"""
        result = verify_code(code, test)

        assert result['success'] is False


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
