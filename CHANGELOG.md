# Changelog

## Unreleased

- Let generated Python verification commands use pytest discovery instead of requiring a `tests/` directory.

- Updated CI to use minimal read permissions and Node 24-compatible GitHub Actions.
- Added Dependabot coverage for non-major GitHub Actions and Python packaging updates.
- Removed local absolute paths from generated example artifacts.
- Added a regression test so public generated examples do not include `/Users/` paths.

## 0.3.0 - 2026-06-15

- Add `codex-maintainer-kit review` for human maintainer review briefs from current working-tree changes.

## 0.2.0 - 2026-06-15

- Add `codex-maintainer-kit audit` for OSS maintenance health scoring and prioritized next actions.
- Improve generated issue drafts with suggested labels, verification commands, and maintainer checklists.
- Add a human-reviewed release workflow for Codex-assisted maintenance releases.
- Add Java, .NET, and Swift project hint detection.
- Add a JSON schema for `tasks --format json` output.
- Add `codex-maintainer-kit.toml` support for configured verification commands and default labels.
- Link to the companion `codex-maintainer-action` GitHub Action.

## 0.1.1 - 2026-06-14

- Fix GitHub Actions test dependency installation by adding the `dev` extra.

## 0.1.0 - 2026-06-14

- Add repository scanner for maintainer files, project hints, tests, CI, and Git state.
- Add Markdown maintainer brief renderer.
- Add CLI commands for `brief`, `tasks`, and `init`.
- Add Codex-ready task generation in Markdown, JSON, and GitHub issue draft formats.
- Add tests, examples, and public repository documentation.
