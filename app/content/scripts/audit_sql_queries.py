#!/usr/bin/env python3
"""
Security audit script to find potential SQL injection vulnerabilities.

This script searches through the codebase for SQL queries that use
string formatting or concatenation instead of parameterized queries.
"""

import ast
import os
import re
from pathlib import Path
from typing import List, Tuple


class SQLAuditVisitor(ast.NodeVisitor):
    """AST visitor to find SQL injection vulnerabilities."""

    def __init__(self, filename: str):
        self.filename = filename
        self.issues: List[Tuple[int, str, str]] = []
        self.in_sql_context = False

    def visit_Call(self, node: ast.Call) -> None:
        """Check for SQL-related function calls."""
        # Check for text() calls that might contain SQL
        if isinstance(node.func, ast.Name) and node.func.id == "text":
            # Check if the argument uses f-string or format
            if node.args and isinstance(node.args[0], ast.JoinedStr):
                self.issues.append(
                    (
                        node.lineno,
                        "F-string in SQL query",
                        "Use parameterized queries instead of f-strings",
                    )
                )

        # Check for execute() calls
        if isinstance(node.func, ast.Attribute) and node.func.attr in (
            "execute",
            "exec",
            "executemany",
        ):
            # Check if SQL uses string formatting
            if node.args:
                self._check_sql_arg(node.args[0], node.lineno)

        self.generic_visit(node)

    def _check_sql_arg(self, arg: ast.AST, lineno: int) -> None:
        """Check if SQL argument uses unsafe patterns."""
        if isinstance(arg, ast.JoinedStr):
            self.issues.append(
                (
                    lineno,
                    "F-string in SQL execute",
                    "Use parameterized queries with :param syntax",
                )
            )
        elif isinstance(arg, ast.Call):
            # Check for .format() calls
            if isinstance(arg.func, ast.Attribute) and arg.func.attr == "format":
                self.issues.append(
                    (
                        lineno,
                        ".format() in SQL query",
                        "Use parameterized queries instead of .format()",
                    )
                )
        elif isinstance(arg, ast.Mod):
            # Old-style % formatting
            self.issues.append(
                (
                    lineno,
                    "%-formatting in SQL query",
                    "Use parameterized queries instead of % formatting",
                )
            )
        elif isinstance(arg, ast.BinOp) and isinstance(arg.op, ast.Add):
            # String concatenation
            self.issues.append(
                (
                    lineno,
                    "String concatenation in SQL query",
                    "Use parameterized queries instead of concatenation",
                )
            )


def check_regex_patterns(content: str, filename: str) -> List[Tuple[int, str, str]]:
    """Check for SQL injection patterns using regex."""
    issues = []

    # Patterns that indicate potential SQL injection
    patterns = [
        # f-strings with SQL keywords
        (
            r'f["\'].*\b(SELECT|INSERT|UPDATE|DELETE|FROM|WHERE|JOIN)\b.*{.*}',
            "F-string SQL query",
        ),
        # .format() with SQL
        (
            r'["\'].*\b(SELECT|INSERT|UPDATE|DELETE|FROM|WHERE|JOIN)\b.*["\']\.format\(',
            ".format() SQL query",
        ),
        # String concatenation with SQL
        (
            r'["\'].*\b(SELECT|INSERT|UPDATE|DELETE|FROM|WHERE|JOIN)\b.*["\'].*\+',
            "SQL string concatenation",
        ),
        # Direct table name interpolation
        (r'FROM\s+["\']?\s*\+\s*\w+|FROM\s+{\w+}|FROM\s+%s', "Dynamic table name"),
    ]

    lines = content.split("\n")
    for i, line in enumerate(lines, 1):
        for pattern, issue_type in patterns:
            if re.search(pattern, line, re.IGNORECASE):
                issues.append((i, issue_type, "Potential SQL injection risk"))

    return issues


def audit_file(filepath: Path) -> List[Tuple[str, int, str, str]]:
    """Audit a single Python file for SQL injection vulnerabilities."""
    try:
        content = filepath.read_text(encoding="utf-8")

        # Skip test files
        if "test_" in filepath.name or "/tests/" in str(filepath):
            return []

        # Parse AST
        try:
            tree = ast.parse(content)
            visitor = SQLAuditVisitor(str(filepath))
            visitor.visit(tree)
            ast_issues = visitor.issues
        except SyntaxError:
            ast_issues = []

        # Also check with regex for patterns AST might miss
        regex_issues = check_regex_patterns(content, str(filepath))

        # Combine and format results
        all_issues = []
        for lineno, issue_type, recommendation in ast_issues:
            all_issues.append((str(filepath), lineno, issue_type, recommendation))

        for lineno, issue_type, recommendation in regex_issues:
            # Avoid duplicates
            if not any(i[1] == lineno for i in all_issues):
                all_issues.append((str(filepath), lineno, issue_type, recommendation))

        return all_issues

    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        return []


def main() -> None:
    """Run SQL injection audit on the codebase."""
    print("SQL Injection Security Audit")
    print("=" * 50)

    # Define directories to scan
    app_dir = Path(__file__).parent.parent / "app"
    scripts_dir = Path(__file__).parent

    # Collect all Python files
    py_files: List[Path] = []
    for directory in [app_dir, scripts_dir]:
        if directory.exists():
            py_files.extend(directory.rglob("*.py"))

    # Audit each file
    all_issues = []
    for py_file in py_files:
        issues = audit_file(py_file)
        all_issues.extend(issues)

    # Report results
    if not all_issues:
        print("\n✅ No SQL injection vulnerabilities found!")
        return

    print(f"\n⚠️  Found {len(all_issues)} potential SQL injection vulnerabilities:\n")

    # Group by file
    issues_by_file: dict[str, List[Tuple[str, int, str, str]]] = {}
    for filepath, lineno, issue_type, recommendation in all_issues:
        if filepath not in issues_by_file:
            issues_by_file[filepath] = []
        issues_by_file[filepath].append((filepath, lineno, issue_type, recommendation))

    # Print grouped results
    for filepath, issues in issues_by_file.items():
        # Make path relative for cleaner output
        try:
            rel_path = Path(filepath).relative_to(Path.cwd())
        except ValueError:
            rel_path = Path(filepath)

        print(f"\n📄 {rel_path}")
        for _, lineno, issue_type, recommendation in sorted(issues, key=lambda x: x[1]):
            print(f"   Line {lineno}: {issue_type}")
            print(f"   → {recommendation}")

    print(f"\n\nTotal issues: {len(all_issues)}")
    print("\nRecommendations:")
    print("1. Use parameterized queries with :param_name syntax")
    print("2. Sanitize table names using a whitelist approach")
    print("3. Never use f-strings, .format(), or concatenation for SQL")
    print("4. Consider using SQLAlchemy query builder for complex queries")


if __name__ == "__main__":
    main()
