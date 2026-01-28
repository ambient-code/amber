"""Amber tool implementations"""

from amber.tools.code_analysis import (
    git_diff,
    git_log,
    grep_codebase,
    list_files,
    read_file,
)
from amber.tools.constitution import (
    check_commit_format,
    check_go_error_handling,
    check_structured_logging,
    check_typescript_type_safety,
)
from amber.tools.github_tools import (
    github_create_issue_comment,
    github_create_pr,
    github_get_issue,
    github_list_issues,
    github_list_prs,
    github_update_issue_labels,
)

# All tools available to LangGraph workflows
ALL_TOOLS = [
    # Code analysis
    grep_codebase,
    read_file,
    list_files,
    git_log,
    git_diff,
    # Constitution checking
    check_go_error_handling,
    check_typescript_type_safety,
    check_structured_logging,
    check_commit_format,
    # GitHub integration
    github_list_issues,
    github_get_issue,
    github_create_issue_comment,
    github_create_pr,
    github_update_issue_labels,
    github_list_prs,
]

__all__ = [
    "ALL_TOOLS",
    "grep_codebase",
    "read_file",
    "list_files",
    "git_log",
    "git_diff",
    "check_go_error_handling",
    "check_typescript_type_safety",
    "check_structured_logging",
    "check_commit_format",
    "github_list_issues",
    "github_get_issue",
    "github_create_issue_comment",
    "github_create_pr",
    "github_update_issue_labels",
    "github_list_prs",
]
