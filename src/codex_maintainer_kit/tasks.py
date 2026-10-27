from __future__ import annotations

from dataclasses import asdict, dataclass, replace
import json

from codex_maintainer_kit.config import MaintainerConfig
from codex_maintainer_kit.scanner import RepositoryScan


@dataclass(frozen=True)
class MaintenanceTask:
    id: str
    title: str
    priority: str
    summary: str
    codex_prompt: str
    completion_criteria: list[str]
    review_notes: str
    suggested_labels: list[str]
    verification_command: str


TASK_DEFINITIONS = {
    "license": MaintenanceTask(
        id="add-license",
        title="Add LICENSE",
        priority="high",
        summary="Add a clear license so users know how the project can be reused.",
        codex_prompt="Add an MIT LICENSE file if the project owner approves MIT, then update README license references if needed.",
        completion_criteria=["A LICENSE file exists.", "README license references are accurate.", "No source files are changed unnecessarily."],
        review_notes="Human review must confirm the intended license before merge.",
        suggested_labels=["maintenance", "documentation"],
        verification_command="python3 -m pytest -p no:cacheprovider -q",
    ),
    "agents": MaintenanceTask(
        id="add-agents",
        title="Add AGENTS.md",
        priority="high",
        summary="Add repository instructions for Codex and other coding agents.",
        codex_prompt="Create AGENTS.md with the project purpose, development commands, testing command, and human review rule.",
        completion_criteria=["AGENTS.md exists.", "The test command is documented.", "The file says AI-generated changes require human review."],
        review_notes="Human review should confirm the instructions match the real repository workflow.",
        suggested_labels=["maintenance", "documentation", "codex"],
        verification_command="python3 -m pytest -p no:cacheprovider -q",
    ),
    "tests": MaintenanceTask(
        id="add-tests",
        title="Add Test Suite",
        priority="high",
        summary="Add a minimal automated test suite for public behavior.",
        codex_prompt="Identify the smallest user-visible behavior in this repo and add tests that cover it before changing implementation code.",
        completion_criteria=["A test directory or test files exist.", "The documented test command passes.", "Tests cover behavior rather than implementation details."],
        review_notes="Human review should inspect whether tests would fail for a real regression.",
        suggested_labels=["testing", "maintenance"],
        verification_command="python3 -m pytest -p no:cacheprovider -q",
    ),
    "ci": MaintenanceTask(
        id="add-ci",
        title="Add CI Workflow",
        priority="medium",
        summary="Run tests automatically on pull requests.",
        codex_prompt="Add a GitHub Actions workflow that installs the project and runs the documented test command on pull requests.",
        completion_criteria=["A CI workflow exists.", "It runs on pull_request.", "It executes the documented test command."],
        review_notes="Human review should confirm the workflow matches the project language and does not require secrets.",
        suggested_labels=["ci", "maintenance"],
        verification_command="gh run list --limit 1",
    ),
    "readme": MaintenanceTask(
        id="update-readme",
        title="Update README",
        priority="medium",
        summary="Document purpose, install steps, usage, and maintenance status.",
        codex_prompt="Update README with a concise project description, installation instructions, usage examples, and maintainer workflow.",
        completion_criteria=["README explains who the project is for.", "README includes install and usage examples.", "README names the verification command."],
        review_notes="Human review should confirm claims are accurate and not overstated.",
        suggested_labels=["documentation"],
        verification_command="python3 -m pytest -p no:cacheprovider -q",
    ),
    "contributing": MaintenanceTask(
        id="add-contributing",
        title="Add CONTRIBUTING",
        priority="medium",
        summary="Explain how contributors should set up, test, and submit changes.",
        codex_prompt="Add CONTRIBUTING.md with local setup, test command, pull request expectations, and AI-assisted contribution rules.",
        completion_criteria=["CONTRIBUTING.md exists.", "Local setup is documented.", "Pull request expectations are clear."],
        review_notes="Human review should confirm the workflow is realistic for new contributors.",
        suggested_labels=["documentation", "maintenance"],
        verification_command="python3 -m pytest -p no:cacheprovider -q",
    ),
    "security": MaintenanceTask(
        id="add-security",
        title="Add SECURITY",
        priority="medium",
        summary="Document how security issues should be reported.",
        codex_prompt="Add SECURITY.md with vulnerability reporting instructions and scope notes for this project.",
        completion_criteria=["SECURITY.md exists.", "It explains how to report vulnerabilities.", "It avoids asking users to disclose sensitive issues publicly."],
        review_notes="Human review should confirm the contact path is correct before publishing.",
        suggested_labels=["security", "documentation"],
        verification_command="python3 -m pytest -p no:cacheprovider -q",
    ),
    "issue_templates": MaintenanceTask(
        id="add-issue-templates",
        title="Add Issue Templates",
        priority="low",
        summary="Make maintenance issues easier to scope and verify.",
        codex_prompt="Add GitHub issue templates for bugs, documentation improvements, and maintenance tasks with verification fields.",
        completion_criteria=["Issue templates exist.", "Templates ask for expected behavior or goal.", "Templates include a verification section."],
        review_notes="Human review should confirm templates reduce ambiguity instead of adding process overhead.",
        suggested_labels=["maintenance", "github"],
        verification_command="python3 -m pytest -p no:cacheprovider -q",
    ),
    "changelog": MaintenanceTask(
        id="add-changelog",
        title="Add CHANGELOG",
        priority="low",
        summary="Create release history before public tags accumulate.",
        codex_prompt="Add CHANGELOG.md with an initial unreleased or v0.1.0 section summarizing the current public behavior.",
        completion_criteria=["CHANGELOG.md exists.", "The first section matches the current project state.", "No future features are claimed as shipped."],
        review_notes="Human review should confirm the release notes match actual code.",
        suggested_labels=["release", "documentation"],
        verification_command="python3 -m pytest -p no:cacheprovider -q",
    ),
    "code_of_conduct": MaintenanceTask(
        id="add-code-of-conduct",
        title="Add Code of Conduct",
        priority="low",
        summary="Set collaboration expectations if the project accepts outside contributions.",
        codex_prompt="Add a concise CODE_OF_CONDUCT.md that sets respectful collaboration expectations for contributors.",
        completion_criteria=["CODE_OF_CONDUCT.md exists.", "It sets behavior expectations.", "It names how maintainers can respond to violations."],
        review_notes="Human review should confirm the policy fits the maintainer's actual moderation capacity.",
        suggested_labels=["documentation", "community"],
        verification_command="python3 -m pytest -p no:cacheprovider -q",
    ),
}


ORDER = ["license", "agents", "tests", "ci", "readme", "contributing", "security", "issue_templates", "changelog", "code_of_conduct"]


def build_tasks(scan: RepositoryScan, config: MaintainerConfig | None = None) -> list[MaintenanceTask]:
    tasks = [TASK_DEFINITIONS[key] for key in ORDER if not scan.files.get(key, False)]
    if not tasks:
        tasks = [
        MaintenanceTask(
            id="codex-maintenance-review",
            title="Run Codex Maintenance Review",
            priority="medium",
            summary="Use Codex to review the repository for stale docs, missing edge-case tests, and unclear contributor workflow.",
            codex_prompt="Review this repository as an open source maintainer. Look for stale documentation, missing edge-case tests, unclear setup instructions, and small safe improvements. Propose one focused change and explain how to verify it.",
            completion_criteria=["One focused improvement is proposed.", "The relevant test or verification command is identified.", "A human maintainer reviews the diff before merge."],
            review_notes="Human review should confirm the proposed change is useful and small enough to merge safely.",
            suggested_labels=["maintenance", "codex"],
            verification_command="python3 -m pytest -p no:cacheprovider -q",
        )
        ]
    return [_apply_config(task, config) for task in tasks]


def _apply_config(task: MaintenanceTask, config: MaintainerConfig | None) -> MaintenanceTask:
    if config is None:
        return task
    verification_command = config.verification_command or task.verification_command
    suggested_labels = list(dict.fromkeys([*task.suggested_labels, *config.default_labels]))
    return replace(task, verification_command=verification_command, suggested_labels=suggested_labels)


def render_tasks_markdown(scan: RepositoryScan, tasks: list[MaintenanceTask]) -> str:
    lines = [
        "# Codex Maintenance Tasks",
        "",
        f"Repository: `{scan.root}`",
        f"Project hints: {', '.join(scan.project_hints)}",
        "",
    ]
    for index, task in enumerate(tasks, start=1):
        lines.extend(
            [
                f"## Task {index}: {task.title}",
                "",
                f"Priority: `{task.priority}`",
                "",
                task.summary,
                "",
                "### Codex Prompt",
                "",
                task.codex_prompt,
                "",
                "### Completion Criteria",
                "",
            ]
        )
        lines.extend(f"- [ ] {criterion}" for criterion in task.completion_criteria)
        lines.extend(["", "### Verification Command", "", f"`{task.verification_command}`", "", "### Human Review", "", task.review_notes, ""])
    return "\n".join(lines)


def render_tasks_json(scan: RepositoryScan, tasks: list[MaintenanceTask]) -> str:
    payload = {
        "repository": str(scan.root),
        "project_hints": scan.project_hints,
        "tasks": [asdict(task) for task in tasks],
    }
    return json.dumps(payload, indent=2)


def render_issue_markdown(task: MaintenanceTask) -> str:
    lines = [
        f"# {task.title}",
        "",
        f"Priority: `{task.priority}`",
        "",
        "## Suggested Labels",
        "",
        ", ".join(f"`{label}`" for label in task.suggested_labels),
        "",
        "## Summary",
        "",
        task.summary,
        "",
        "## Codex Prompt",
        "",
        task.codex_prompt,
        "",
        "## Completion Criteria",
        "",
    ]
    lines.extend(f"- [ ] {criterion}" for criterion in task.completion_criteria)
    lines.extend(
        [
            "",
            "## Verification Command",
            "",
            f"`{task.verification_command}`",
            "",
            "## Maintainer Checklist",
            "",
            "- [ ] The Codex prompt is scoped to one change.",
            "- [ ] The verification command is practical for this repository.",
            "- [ ] The final diff is reviewed by a human maintainer before merge.",
            "",
            "## Human Review",
            "",
            task.review_notes,
            "",
        ]
    )
    return "\n".join(lines)
