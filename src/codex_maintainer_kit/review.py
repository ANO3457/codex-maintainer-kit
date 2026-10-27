from __future__ import annotations

from dataclasses import dataclass

from codex_maintainer_kit.scanner import RepositoryScan


@dataclass(frozen=True)
class ChangedFileReview:
    path: str
    category: str
    review_note: str


@dataclass(frozen=True)
class ReviewReport:
    repository: str
    git_state: str
    risk_level: str
    summary: str
    changed_files: list[ChangedFileReview]
    review_checklist: list[str]
    verification_commands: list[str]


def build_review_report(scan: RepositoryScan, verification_command: str | None = None) -> ReviewReport:
    changed_files = [_classify_changed_file(path) for path in scan.git_state.changed_files]
    risk_level = _risk_level(changed_files)
    review_checklist = _review_checklist(changed_files)
    verification_commands = _verification_commands(scan, verification_command)

    return ReviewReport(
        repository=str(scan.root),
        git_state=scan.git_state.status,
        risk_level=risk_level,
        summary=_summary(changed_files),
        changed_files=changed_files,
        review_checklist=review_checklist,
        verification_commands=verification_commands,
    )


def render_review_markdown(report: ReviewReport) -> str:
    lines = [
        "# Codex Change Review",
        "",
        f"Repository: `{report.repository}`",
        f"Git state: `{report.git_state}`",
        f"Risk level: **{report.risk_level}**",
        "",
        report.summary,
        "",
        "## Changed Files",
        "",
    ]

    if report.changed_files:
        lines.extend(["| File | Category | Review note |", "| --- | --- | --- |"])
        for item in report.changed_files:
            lines.append(f"| `{item.path}` | {item.category} | {item.review_note} |")
    else:
        lines.append("No changed files detected.")

    lines.extend(["", "## Maintainer Review Checklist", ""])
    lines.extend(f"- [ ] {item}" for item in report.review_checklist)

    lines.extend(["", "## Verification Commands", ""])
    lines.extend(f"- `{command}`" for command in report.verification_commands)

    lines.extend(
        [
            "",
            "## Suggested Codex Review Prompt",
            "",
            "Review the changed files above as an OSS maintainer. Focus on correctness, scope control, tests, documentation accuracy, security-sensitive changes, and whether the diff is small enough for human review. Do not approve the change unless the verification commands are practical and the remaining risks are named.",
            "",
            "## Human Review Rule",
            "",
            "This report is a review aid, not an approval. A human maintainer must inspect the actual diff before merge.",
            "",
        ]
    )
    return "\n".join(lines)


def _classify_changed_file(path: str) -> ChangedFileReview:
    normalized = path.lower()
    if _is_ci_path(normalized):
        return ChangedFileReview(path, "ci", "Confirm the workflow does not require unexpected secrets or broad permissions.")
    if _is_security_sensitive_path(normalized):
        return ChangedFileReview(path, "security-sensitive", "Inspect auth, token, permission, or secret-handling behavior carefully.")
    if _is_test_path(normalized):
        return ChangedFileReview(path, "tests", "Confirm tests cover behavior and would fail for a real regression.")
    if _is_docs_path(normalized):
        return ChangedFileReview(path, "docs", "Confirm documentation matches shipped behavior and does not overpromise.")
    if _is_config_path(normalized):
        return ChangedFileReview(path, "config", "Confirm dependency, package, release, or tool configuration changes are intentional.")
    if _is_source_path(normalized):
        return ChangedFileReview(path, "source", "Review behavior, edge cases, and whether tests cover the changed path.")
    return ChangedFileReview(path, "other", "Confirm the change is expected and belongs in this maintenance task.")


def _risk_level(changed_files: list[ChangedFileReview]) -> str:
    categories = {item.category for item in changed_files}
    if not changed_files:
        return "low"
    if categories & {"ci", "security-sensitive"}:
        return "high"
    if categories & {"source", "config"}:
        return "medium"
    return "low"


def _summary(changed_files: list[ChangedFileReview]) -> str:
    if not changed_files:
        return "No changed files detected."
    categories = sorted({item.category for item in changed_files})
    return f"{len(changed_files)} changed file(s) detected across: {', '.join(categories)}."


def _review_checklist(changed_files: list[ChangedFileReview]) -> list[str]:
    if not changed_files:
        return ["Confirm the working tree is clean before starting new maintenance work."]

    categories = {item.category for item in changed_files}
    checklist = [
        "Read the actual diff, not only this generated summary.",
        "Confirm the change is scoped to one maintenance goal.",
        "Run the verification command or explain why it cannot be run.",
    ]
    if "source" in categories:
        checklist.append("Source files changed: confirm behavior, edge cases, and tests.")
    if "tests" in categories:
        checklist.append("Tests were changed: confirm they would fail for the bug or missing behavior.")
    if "docs" in categories:
        checklist.append("Docs changed: confirm examples and claims match the current code.")
    if "config" in categories:
        checklist.append("Config changed: confirm dependencies, package metadata, and release settings are intentional.")
    if categories & {"ci", "security-sensitive"}:
        checklist.append("CI or security-sensitive files changed: confirm permissions, secrets, tokens, and external calls.")
    checklist.append("Do not auto-merge AI-generated changes without human review.")
    return checklist


def _verification_commands(scan: RepositoryScan, verification_command: str | None) -> list[str]:
    if verification_command:
        return [verification_command]
    if scan.files.get("tests", False):
        if "python" in scan.project_hints:
            return ["python3 -m pytest -p no:cacheprovider -q"]
        if "javascript" in scan.project_hints:
            return ["npm test"]
        if "go" in scan.project_hints:
            return ["go test ./..."]
        if "rust" in scan.project_hints:
            return ["cargo test"]
        if "ruby" in scan.project_hints:
            return ["bundle exec rake test"]
        if "java" in scan.project_hints:
            return ["mvn test"]
        if "swift" in scan.project_hints:
            return ["swift test"]
    return ["No automated test command detected. Perform manual review and add tests before risky changes."]


def _is_ci_path(path: str) -> bool:
    return path.startswith(".github/workflows/") or path in {".gitlab-ci.yml", "azure-pipelines.yml", ".circleci/config.yml"}


def _is_security_sensitive_path(path: str) -> bool:
    markers = ["auth", "token", "secret", "credential", "permission", "security", ".env"]
    return any(marker in path for marker in markers)


def _is_test_path(path: str) -> bool:
    return path.startswith(("tests/", "test/", "__tests__/", "spec/")) or any(
        marker in path for marker in ["test_", "_test.", ".test.", ".spec."]
    )


def _is_docs_path(path: str) -> bool:
    return path.endswith((".md", ".rst", ".txt")) or path.startswith(("docs/", "examples/"))


def _is_config_path(path: str) -> bool:
    names = [
        "pyproject.toml",
        "package.json",
        "package-lock.json",
        "pnpm-lock.yaml",
        "yarn.lock",
        "cargo.toml",
        "go.mod",
        "go.sum",
        "gemfile",
        "composer.json",
        "pom.xml",
        "build.gradle",
        "setup.py",
    ]
    return path in names or path.endswith((".toml", ".yaml", ".yml", ".json", ".ini", ".cfg"))


def _is_source_path(path: str) -> bool:
    return path.startswith(("src/", "lib/", "app/")) or path.endswith(
        (".py", ".js", ".ts", ".tsx", ".jsx", ".go", ".rs", ".rb", ".php", ".java", ".cs", ".swift")
    )
