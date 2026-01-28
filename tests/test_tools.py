"""Tests for tool implementations"""

import pytest
from unittest.mock import Mock, patch

from amber.tools.code_analysis import grep_codebase, read_file, git_log
from amber.tools.constitution import check_go_error_handling, check_commit_format


def test_read_file_success(tmp_path):
    """Test reading file successfully"""
    test_file = tmp_path / "test.py"
    test_file.write_text("def hello():\n    print('world')\n")

    result = read_file.invoke({"path": "test.py", "repo_path": str(tmp_path)})

    assert "error" not in result
    assert result["total_lines"] == 2
    assert "def hello():" in result["content"]


def test_read_file_not_found(tmp_path):
    """Test reading non-existent file"""
    result = read_file.invoke({"path": "missing.py", "repo_path": str(tmp_path)})

    assert "error" in result
    assert "not found" in result["error"].lower()


def test_check_go_error_handling_panic():
    """Test detecting panic() usage"""
    code = """
package main

func handler() {
    if err != nil {
        panic(err)  // Constitution violation
    }
}
"""

    result = check_go_error_handling.invoke({"code": code, "file_path": "test.go"})

    assert len(result["violations"]) > 0
    assert any("panic" in v["details"].lower() for v in result["violations"])


def test_check_go_error_handling_clean():
    """Test clean error handling"""
    code = """
package main

import "fmt"

func handler() error {
    if err := doSomething(); err != nil {
        return fmt.Errorf("failed to do something: %w", err)
    }
    return nil
}
"""

    result = check_go_error_handling.invoke({"code": code, "file_path": "test.go"})

    assert len(result["violations"]) == 0
    assert result["stats"]["wrapped_errors"] > 0


def test_check_commit_format_valid():
    """Test valid conventional commit"""
    message = "feat(backend): add structured logging to handlers"

    result = check_commit_format.invoke({"commit_message": message})

    assert len(result["violations"]) == 0


def test_check_commit_format_invalid():
    """Test invalid commit format"""
    message = "Added some stuff"

    result = check_commit_format.invoke({"commit_message": message})

    assert len(result["violations"]) > 0
    assert any("conventional commit" in v["details"].lower() for v in result["violations"])


def test_check_commit_format_short():
    """Test short commit message"""
    message = "fix: bug"

    result = check_commit_format.invoke({"commit_message": message})

    assert len(result["warnings"]) > 0
    assert any("short" in w["details"].lower() for w in result["warnings"])
