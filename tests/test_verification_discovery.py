from pathlib import Path
import shlex
import subprocess
import sys

import pytest

from codex_maintainer_kit.config import MaintainerConfig
from codex_maintainer_kit.review import build_review_report
from codex_maintainer_kit.scanner import scan_repository
from codex_maintainer_kit.tasks import build_tasks


@pytest.mark.parametrize("layout", ["test", ".", "configured"])
@pytest.mark.parametrize("kind", ["review", "tasks"])
def test_generated_python_verification_discovers_existing_suite(tmp_path: Path, layout: str, kind: str) -> None:
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "example"\nversion = "0.0.0"\n', encoding="utf-8")
    directory = tmp_path / ("checks" if layout == "configured" else layout)
    directory.mkdir(exist_ok=True)
    if layout == "configured":
        (tmp_path / "pytest.ini").write_text("[pytest]\ntestpaths = checks\n", encoding="utf-8")
    (directory / "test_example.py").write_text(
        'from pathlib import Path\ndef test_example():\n    Path("ran").write_text("ok")\n',
        encoding="utf-8",
    )
    scan = scan_repository(tmp_path)
    assert scan.files["tests"]
    if kind == "review":
        command = build_review_report(scan).verification_commands[0]
    else:
        command = build_tasks(scan)[0].verification_command
    result = subprocess.run(
        [sys.executable, *shlex.split(command)[1:]], cwd=tmp_path,
        capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert (tmp_path / "ran").read_text() == "ok"


def test_explicit_verification_command_is_preserved(tmp_path: Path) -> None:
    scan = scan_repository(tmp_path)
    command = "python3 -m pytest custom_tests -q"
    assert build_review_report(scan, verification_command=command).verification_commands == [command]
    task = build_tasks(scan, MaintainerConfig(verification_command=command))[0]
    assert task.verification_command == command
