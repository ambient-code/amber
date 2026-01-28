"""Code analysis tools for codebase exploration"""

import os
import re
import subprocess
from pathlib import Path
from typing import Any

from langchain.tools import tool


@tool
def grep_codebase(pattern: str, file_glob: str = "*", repo_path: str = ".") -> list[dict[str, Any]]:
    """Search codebase for pattern with file references.

    Args:
        pattern: Regular expression pattern to search for
        file_glob: File glob pattern to filter files (default: "*")
        repo_path: Path to repository root (default: ".")

    Returns:
        List of matches with file path, line number, and content
    """
    try:
        cmd = [
            "grep",
            "-rn",
            "--include",
            file_glob,
            "-E",
            pattern,
            repo_path,
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
        )

        matches = []
        for line in result.stdout.splitlines():
            # Parse grep output: filepath:line_number:content
            match = re.match(r"^(.+?):(\d+):(.+)$", line)
            if match:
                filepath, line_num, content = match.groups()
                matches.append(
                    {
                        "file_path": filepath,
                        "line_number": int(line_num),
                        "content": content.strip(),
                    }
                )

        return matches

    except subprocess.TimeoutExpired:
        return [{"error": "grep operation timed out"}]
    except Exception as e:
        return [{"error": f"grep failed: {str(e)}"}]


@tool
def read_file(
    path: str, start_line: int = 0, end_line: int = -1, repo_path: str = "."
) -> dict[str, Any]:
    """Read file contents with optional line range.

    Args:
        path: Relative path to file within repository
        start_line: Starting line number (0-indexed, default: 0)
        end_line: Ending line number (-1 for end of file, default: -1)
        repo_path: Path to repository root (default: ".")

    Returns:
        Dictionary with file content and metadata
    """
    try:
        full_path = Path(repo_path) / path

        if not full_path.exists():
            return {"error": f"File not found: {path}"}

        if not full_path.is_file():
            return {"error": f"Not a file: {path}"}

        with open(full_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # Handle line range
        if end_line == -1:
            end_line = len(lines)

        selected_lines = lines[start_line:end_line]

        return {
            "path": path,
            "total_lines": len(lines),
            "start_line": start_line,
            "end_line": end_line,
            "content": "".join(selected_lines),
            "lines": [
                {"number": start_line + i + 1, "content": line.rstrip()}
                for i, line in enumerate(selected_lines)
            ],
        }

    except Exception as e:
        return {"error": f"Failed to read file: {str(e)}"}


@tool
def list_files(directory: str = ".", pattern: str = "*", repo_path: str = ".") -> dict[str, Any]:
    """List files in directory matching pattern.

    Args:
        directory: Directory path relative to repo root (default: ".")
        pattern: Glob pattern to match files (default: "*")
        repo_path: Path to repository root (default: ".")

    Returns:
        Dictionary with list of matching files
    """
    try:
        full_path = Path(repo_path) / directory

        if not full_path.exists():
            return {"error": f"Directory not found: {directory}"}

        if not full_path.is_dir():
            return {"error": f"Not a directory: {directory}"}

        # Use glob to find matching files
        files = []
        for file_path in full_path.rglob(pattern):
            if file_path.is_file():
                relative_path = file_path.relative_to(repo_path)
                stat = file_path.stat()
                files.append(
                    {
                        "path": str(relative_path),
                        "size": stat.st_size,
                        "modified": stat.st_mtime,
                    }
                )

        # Sort by modification time (newest first)
        files.sort(key=lambda x: x["modified"], reverse=True)

        return {"directory": directory, "pattern": pattern, "count": len(files), "files": files}

    except Exception as e:
        return {"error": f"Failed to list files: {str(e)}"}


@tool
def git_log(
    path: str = ".", since: str = "1 week ago", max_count: int = 50, repo_path: str = "."
) -> dict[str, Any]:
    """Get git history for path.

    Args:
        path: File or directory path relative to repo root (default: ".")
        since: Time specification for commit history (default: "1 week ago")
        max_count: Maximum number of commits to return (default: 50)
        repo_path: Path to repository root (default: ".")

    Returns:
        Dictionary with commit history
    """
    try:
        full_path = Path(repo_path) / path

        cmd = [
            "git",
            "-C",
            repo_path,
            "log",
            f"--since={since}",
            f"--max-count={max_count}",
            "--pretty=format:%H|%an|%ae|%ad|%s",
            "--date=iso",
            str(path),
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode != 0:
            return {"error": f"git log failed: {result.stderr}"}

        commits = []
        for line in result.stdout.splitlines():
            if not line:
                continue

            parts = line.split("|", 4)
            if len(parts) == 5:
                sha, author, email, date, message = parts
                commits.append(
                    {
                        "sha": sha,
                        "author": author,
                        "email": email,
                        "date": date,
                        "message": message,
                    }
                )

        return {
            "path": path,
            "since": since,
            "count": len(commits),
            "commits": commits,
        }

    except subprocess.TimeoutExpired:
        return {"error": "git log operation timed out"}
    except Exception as e:
        return {"error": f"git log failed: {str(e)}"}


@tool
def git_diff(
    base: str = "main", head: str = "HEAD", path: str = ".", repo_path: str = "."
) -> dict[str, Any]:
    """Get git diff between two references.

    Args:
        base: Base reference (default: "main")
        head: Head reference (default: "HEAD")
        path: Path to diff (default: ".")
        repo_path: Path to repository root (default: ".")

    Returns:
        Dictionary with diff content
    """
    try:
        cmd = [
            "git",
            "-C",
            repo_path,
            "diff",
            f"{base}...{head}",
            "--",
            path,
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode != 0:
            return {"error": f"git diff failed: {result.stderr}"}

        return {
            "base": base,
            "head": head,
            "path": path,
            "diff": result.stdout,
            "lines_changed": len(result.stdout.splitlines()),
        }

    except subprocess.TimeoutExpired:
        return {"error": "git diff operation timed out"}
    except Exception as e:
        return {"error": f"git diff failed: {str(e)}"}
