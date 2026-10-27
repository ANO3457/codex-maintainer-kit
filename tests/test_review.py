from pathlib import Path
from typing import Optional

from codex_maintainer_kit.review import build_review_report, render_review_markdown
from codex_maintainer_kit.scanner import GitState, RepositoryScan


def _scan(changed_files: list[str], project_hints: Optional[list[str]] = None, has_tests: bool = True) -> RepositoryScan:
    return RepositoryScan(
        root=Path("/repo/demo"),
        files={
            "readme": True,
            "license": True,
            "contributing": True,
            "code_of_conduct": True,
            "security": True,
            "changelog": True,
            "agents": True,
            "issue_templates": True,
            "ci": True,
            "tests": has_tests,
        },
        project_hints=project_hints or ["python"],
        git_state=GitState(status="dirty" if changed_files else "clean", changed_files=changed_files),
    )


def test_build_review_report_handles_clean_repository() -> None:
    report = build_review_report(_scan([]))

    assert report.risk_level == "low"
    assert report.summary == "No changed files detected."
    assert report.changed_files == []
    assert report.review_checklist == ["Confirm the working tree is clean before starting new maintenance work."]


def test_build_review_report_classifies_source_and_test_changes() -> None:
    report = build_review_report(_scan(["src/demo.py", "tests/test_demo.py", "README.md"]))

    assert report.risk_level == "medium"
    assert [item.category for item in report.changed_files] == ["source", "tests", "docs"]
    assert "python3 -m pytest -p no:cacheprovider -q" in report.verification_commands
    assert any("Tests were changed" in item for item in report.review_checklist)


def test_build_review_report_flags_ci_and_security_sensitive_changes() -> None:
    report = build_review_report(_scan([".github/workflows/tests.yml", "src/auth/token_store.py"]))

    assert report.risk_level == "high"
    assert [item.category for item in report.changed_files] == ["ci", "security-sensitive"]
    assert any("CI or security-sensitive files changed" in item for item in report.review_checklist)


def test_render_review_markdown_is_human_review_ready() -> None:
    report = build_review_report(_scan(["src/demo.py", "pyproject.toml"]))

    markdown = render_review_markdown(report)

    assert markdown.startswith("# Codex Change Review")
    assert "Risk level: **medium**" in markdown
    assert "## Changed Files" in markdown
    assert "| `src/demo.py` | source |" in markdown
    assert "## Maintainer Review Checklist" in markdown
    assert "## Suggested Codex Review Prompt" in markdown
