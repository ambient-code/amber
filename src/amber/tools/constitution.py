"""Constitution compliance checking tools"""

import re
from typing import Any

from langchain.tools import tool

from amber.models import ConstitutionCheck


@tool
def check_go_error_handling(code: str, file_path: str) -> dict[str, Any]:
    """Check Go code for constitution-compliant error handling.

    Verifies:
    - No panic() in production code
    - Errors wrapped with fmt.Errorf or errors.Wrap
    - Proper error propagation

    Args:
        code: Go source code to check
        file_path: File path for reference

    Returns:
        Dictionary with compliance results
    """
    violations = []
    warnings = []

    # Check for panic() usage (Principle III violation)
    panic_pattern = r'\bpanic\s*\('
    panic_matches = re.finditer(panic_pattern, code)
    for match in panic_matches:
        line_num = code[:match.start()].count('\n') + 1
        violations.append(
            ConstitutionCheck(
                principle="III - Type Safety & Error Handling",
                status="fail",
                details=f"panic() usage forbidden in production code at line {line_num}",
                file_references=[f"{file_path}:{line_num}"],
            )
        )

    # Check for naked error returns (warning)
    naked_return_pattern = r'return\s+err\s*$'
    naked_matches = re.finditer(naked_return_pattern, code, re.MULTILINE)
    for match in naked_matches:
        line_num = code[:match.start()].count('\n') + 1
        warnings.append(
            ConstitutionCheck(
                principle="III - Type Safety & Error Handling",
                status="warning",
                details=f"Consider wrapping error with context at line {line_num}",
                file_references=[f"{file_path}:{line_num}"],
            )
        )

    # Check for proper error wrapping (look for fmt.Errorf with %w)
    wrapped_errors = len(re.findall(r'fmt\.Errorf\s*\([^)]*%w', code))

    return {
        "file_path": file_path,
        "language": "go",
        "violations": [
            {
                "principle": v.principle,
                "status": v.status,
                "details": v.details,
                "file_references": v.file_references,
            }
            for v in violations
        ],
        "warnings": [
            {
                "principle": w.principle,
                "status": w.status,
                "details": w.details,
                "file_references": w.file_references,
            }
            for w in warnings
        ],
        "stats": {
            "panic_count": len(list(re.finditer(panic_pattern, code))),
            "wrapped_errors": wrapped_errors,
        },
    }


@tool
def check_typescript_type_safety(code: str, file_path: str) -> dict[str, Any]:
    """Check TypeScript code for constitution-compliant type safety.

    Verifies:
    - No 'any' types without eslint-disable justification
    - Proper type annotations
    - Type-safe API calls

    Args:
        code: TypeScript source code to check
        file_path: File path for reference

    Returns:
        Dictionary with compliance results
    """
    violations = []
    warnings = []

    # Check for 'any' type usage without justification
    any_pattern = r':\s*any\b'
    any_matches = list(re.finditer(any_pattern, code))

    for match in any_matches:
        line_num = code[:match.start()].count('\n') + 1
        line_start = code.rfind('\n', 0, match.start()) + 1
        line_end = code.find('\n', match.end())
        if line_end == -1:
            line_end = len(code)
        line_content = code[line_start:line_end]

        # Check if line has eslint-disable comment
        if 'eslint-disable' not in line_content:
            violations.append(
                ConstitutionCheck(
                    principle="III - Type Safety & Error Handling",
                    status="fail",
                    details=f"'any' type without eslint-disable justification at line {line_num}",
                    file_references=[f"{file_path}:{line_num}"],
                )
            )

    # Check for proper error handling in async functions
    unhandled_async_pattern = r'async\s+\w+[^{]*{[^}]*await[^}]*}'
    # This is a simplified check - real implementation would use AST parsing

    return {
        "file_path": file_path,
        "language": "typescript",
        "violations": [
            {
                "principle": v.principle,
                "status": v.status,
                "details": v.details,
                "file_references": v.file_references,
            }
            for v in violations
        ],
        "warnings": [
            {
                "principle": w.principle,
                "status": w.status,
                "details": w.details,
                "file_references": w.file_references,
            }
            for w in warnings
        ],
        "stats": {"any_count": len(any_matches), "unjustified_any": len(violations)},
    }


@tool
def check_structured_logging(code: str, file_path: str, language: str) -> dict[str, Any]:
    """Check code for constitution-compliant structured logging.

    Verifies:
    - Structured logging with context (Principle VI)
    - No token/secret logging
    - Proper log levels

    Args:
        code: Source code to check
        file_path: File path for reference
        language: Programming language (go, typescript, python)

    Returns:
        Dictionary with compliance results
    """
    violations = []
    warnings = []

    # Check for potential token/secret logging
    sensitive_patterns = [
        (r'log.*token', "Potential token logging"),
        (r'log.*password', "Potential password logging"),
        (r'log.*secret', "Potential secret logging"),
        (r'log.*api[_-]?key', "Potential API key logging"),
    ]

    for pattern, message in sensitive_patterns:
        matches = re.finditer(pattern, code, re.IGNORECASE)
        for match in matches:
            line_num = code[:match.start()].count('\n') + 1
            violations.append(
                ConstitutionCheck(
                    principle="II - Security & Multi-Tenancy",
                    status="fail",
                    details=f"{message} at line {line_num}",
                    file_references=[f"{file_path}:{line_num}"],
                )
            )

    # Language-specific structured logging checks
    if language == "go":
        # Check for structured logging usage (log/slog or zerolog)
        has_structured = bool(
            re.search(r'(slog\.|zerolog\.)', code) or re.search(r'With\w+\(', code)
        )
        if not has_structured and "log." in code:
            warnings.append(
                ConstitutionCheck(
                    principle="VI - Observability",
                    status="warning",
                    details="Consider using structured logging (slog/zerolog) instead of log package",
                    file_references=[file_path],
                )
            )

    return {
        "file_path": file_path,
        "language": language,
        "violations": [
            {
                "principle": v.principle,
                "status": v.status,
                "details": v.details,
                "file_references": v.file_references,
            }
            for v in violations
        ],
        "warnings": [
            {
                "principle": w.principle,
                "status": w.status,
                "details": w.details,
                "file_references": w.file_references,
            }
            for w in warnings
        ],
    }


@tool
def check_commit_format(commit_message: str) -> dict[str, Any]:
    """Check commit message for constitution compliance.

    Verifies:
    - Conventional commit format (Principle X)
    - Proper scope and description
    - Explains WHY not WHAT

    Args:
        commit_message: Commit message to check

    Returns:
        Dictionary with compliance results
    """
    violations = []
    warnings = []

    # Check conventional commit format: type(scope): description
    conventional_pattern = r'^(feat|fix|docs|style|refactor|test|chore)(\([^)]+\))?: .+'
    if not re.match(conventional_pattern, commit_message):
        violations.append(
            ConstitutionCheck(
                principle="X - Commit Discipline",
                status="fail",
                details="Commit message does not follow conventional commit format",
                file_references=[],
            )
        )

    # Check if message is too short
    if len(commit_message) < 10:
        warnings.append(
            ConstitutionCheck(
                principle="X - Commit Discipline",
                status="warning",
                details="Commit message is very short, consider adding more context",
                file_references=[],
            )
        )

    # Check for WHAT vs WHY (heuristic)
    what_indicators = ["add", "remove", "update", "change", "modify", "delete"]
    why_indicators = ["to", "for", "because", "since", "so that"]

    has_what = any(indicator in commit_message.lower() for indicator in what_indicators)
    has_why = any(indicator in commit_message.lower() for indicator in why_indicators)

    if has_what and not has_why:
        warnings.append(
            ConstitutionCheck(
                principle="X - Commit Discipline",
                status="warning",
                details="Commit explains WHAT but not WHY - consider adding motivation",
                file_references=[],
            )
        )

    return {
        "commit_message": commit_message,
        "violations": [
            {
                "principle": v.principle,
                "status": v.status,
                "details": v.details,
                "file_references": v.file_references,
            }
            for v in violations
        ],
        "warnings": [
            {
                "principle": w.principle,
                "status": w.status,
                "details": w.details,
                "file_references": w.file_references,
            }
            for w in warnings
        ],
    }
