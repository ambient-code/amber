"""GitHub API integration tools"""

from typing import Any

from github import Auth, Github
from langchain.tools import tool

from amber.config import get_settings

_github_client: Github | None = None


def get_github_client() -> Github:
    """Get or create GitHub client instance"""
    global _github_client
    if _github_client is None:
        settings = get_settings()
        auth = Auth.Token(settings.github_token)
        _github_client = Github(auth=auth)
    return _github_client


@tool
def github_list_issues(
    repo_full_name: str,
    state: str = "open",
    labels: list[str] | None = None,
    max_results: int = 50,
) -> dict[str, Any]:
    """List GitHub issues with filters.

    Args:
        repo_full_name: Repository full name (owner/repo)
        state: Issue state (open, closed, all)
        labels: List of label names to filter by
        max_results: Maximum number of issues to return

    Returns:
        Dictionary with list of issues
    """
    try:
        client = get_github_client()
        repo = client.get_repo(repo_full_name)

        issues_iter = repo.get_issues(state=state, labels=labels or [])
        issues = []

        for i, issue in enumerate(issues_iter):
            if i >= max_results:
                break

            issues.append(
                {
                    "number": issue.number,
                    "title": issue.title,
                    "state": issue.state,
                    "labels": [label.name for label in issue.labels],
                    "created_at": issue.created_at.isoformat(),
                    "updated_at": issue.updated_at.isoformat(),
                    "author": issue.user.login if issue.user else None,
                    "url": issue.html_url,
                }
            )

        return {
            "repo": repo_full_name,
            "state": state,
            "labels": labels,
            "count": len(issues),
            "issues": issues,
        }

    except Exception as e:
        return {"error": f"Failed to list issues: {str(e)}"}


@tool
def github_get_issue(repo_full_name: str, issue_number: int) -> dict[str, Any]:
    """Get detailed information about a specific issue.

    Args:
        repo_full_name: Repository full name (owner/repo)
        issue_number: Issue number

    Returns:
        Dictionary with issue details
    """
    try:
        client = get_github_client()
        repo = client.get_repo(repo_full_name)
        issue = repo.get_issue(issue_number)

        return {
            "number": issue.number,
            "title": issue.title,
            "body": issue.body,
            "state": issue.state,
            "labels": [label.name for label in issue.labels],
            "assignees": [assignee.login for assignee in issue.assignees],
            "created_at": issue.created_at.isoformat(),
            "updated_at": issue.updated_at.isoformat(),
            "closed_at": issue.closed_at.isoformat() if issue.closed_at else None,
            "author": issue.user.login if issue.user else None,
            "comments_count": issue.comments,
            "url": issue.html_url,
        }

    except Exception as e:
        return {"error": f"Failed to get issue: {str(e)}"}


@tool
def github_create_issue_comment(
    repo_full_name: str, issue_number: int, comment: str
) -> dict[str, Any]:
    """Post comment to GitHub issue.

    Args:
        repo_full_name: Repository full name (owner/repo)
        issue_number: Issue number
        comment: Comment text (markdown supported)

    Returns:
        Dictionary with comment details
    """
    try:
        client = get_github_client()
        repo = client.get_repo(repo_full_name)
        issue = repo.get_issue(issue_number)

        created_comment = issue.create_comment(comment)

        return {
            "id": created_comment.id,
            "issue_number": issue_number,
            "body": created_comment.body,
            "created_at": created_comment.created_at.isoformat(),
            "url": created_comment.html_url,
        }

    except Exception as e:
        return {"error": f"Failed to create comment: {str(e)}"}


@tool
def github_create_pr(
    repo_full_name: str, title: str, body: str, head: str, base: str = "main"
) -> dict[str, Any]:
    """Create GitHub pull request.

    Args:
        repo_full_name: Repository full name (owner/repo)
        title: PR title
        body: PR description (markdown supported)
        head: Head branch name
        base: Base branch name (default: main)

    Returns:
        Dictionary with PR details
    """
    try:
        client = get_github_client()
        repo = client.get_repo(repo_full_name)

        pr = repo.create_pull(title=title, body=body, head=head, base=base)

        return {
            "number": pr.number,
            "title": pr.title,
            "state": pr.state,
            "head": pr.head.ref,
            "base": pr.base.ref,
            "created_at": pr.created_at.isoformat(),
            "url": pr.html_url,
        }

    except Exception as e:
        return {"error": f"Failed to create PR: {str(e)}"}


@tool
def github_update_issue_labels(
    repo_full_name: str, issue_number: int, labels: list[str]
) -> dict[str, Any]:
    """Update labels on a GitHub issue.

    Args:
        repo_full_name: Repository full name (owner/repo)
        issue_number: Issue number
        labels: List of label names to set

    Returns:
        Dictionary with updated labels
    """
    try:
        client = get_github_client()
        repo = client.get_repo(repo_full_name)
        issue = repo.get_issue(issue_number)

        issue.set_labels(*labels)

        return {
            "issue_number": issue_number,
            "labels": labels,
            "success": True,
        }

    except Exception as e:
        return {"error": f"Failed to update labels: {str(e)}"}


@tool
def github_list_prs(
    repo_full_name: str, state: str = "open", max_results: int = 50
) -> dict[str, Any]:
    """List GitHub pull requests.

    Args:
        repo_full_name: Repository full name (owner/repo)
        state: PR state (open, closed, all)
        max_results: Maximum number of PRs to return

    Returns:
        Dictionary with list of pull requests
    """
    try:
        client = get_github_client()
        repo = client.get_repo(repo_full_name)

        prs_iter = repo.get_pulls(state=state)
        prs = []

        for i, pr in enumerate(prs_iter):
            if i >= max_results:
                break

            prs.append(
                {
                    "number": pr.number,
                    "title": pr.title,
                    "state": pr.state,
                    "head": pr.head.ref,
                    "base": pr.base.ref,
                    "created_at": pr.created_at.isoformat(),
                    "updated_at": pr.updated_at.isoformat(),
                    "author": pr.user.login if pr.user else None,
                    "url": pr.html_url,
                }
            )

        return {"repo": repo_full_name, "state": state, "count": len(prs), "prs": prs}

    except Exception as e:
        return {"error": f"Failed to list PRs: {str(e)}"}
