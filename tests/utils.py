import logging
import os
from pathlib import Path
import shutil
import subprocess
import re

import pytest

AGENTS_PATH = Path(__file__).parents[1] / "agents"

logger = logging.getLogger(__name__)


def use_cli() -> bool:
    return os.environ.get("USE_CLI", "").lower() == "true"


def assert_exit_code(
    result: subprocess.CompletedProcess[bytes], allowed_exit_codes: set[int]
) -> subprocess.CompletedProcess[bytes]:
    assert result.returncode in allowed_exit_codes, (
        f"Command {result.args} failed with exit code {result.returncode}.\n\n\n"
        f"Stdout:\n{result.stdout.decode().strip()}\n\n\n"
        f"Stderr:\n{result.stderr.decode().strip()}"
    )

    logger.info("Command: %s", result.args)

    if result.stdout:
        logger.info("Stdout:\n%s", result.stdout.decode())
    if result.stderr:
        logger.info("Stderr:\n%s", result.stderr.decode())

    return result


def run_cli(
    venv_path: Path,
    command: list[str],
    exec_name: str = "watsonx-ai",
    allowed_exit_codes: set[int] | None = None,
    **kwargs,
) -> subprocess.CompletedProcess[bytes]:
    result = subprocess.run(
        [venv_path / "bin" / exec_name, *command],
        check=False,
        capture_output=True,
        **kwargs,
    )

    return assert_exit_code(result, allowed_exit_codes or {0})


def clone_agent_template(
    venv_path: Path, tmp_dir: str, name: str, monkeypatch: pytest.MonkeyPatch
) -> str:
    target_dir = f"{tmp_dir}/{name}"

    if use_cli():
        run_cli(venv_path, ["template", "new", name], input=target_dir)
        run_cli(venv_path, ["install", "--with", "dev"], exec_name="poetry")
    else:
        shutil.copytree(AGENTS_PATH / name, target_dir)

    monkeypatch.chdir(target_dir)

    return target_dir


def create_env_file(env_vars: dict[str, str]) -> None:
    with open("template.env", encoding="utf-8") as file:
        env_file_content = file.read()

    for key, value in env_vars.items():
        env_file_content = re.sub(
            rf"{key}=[^\n]*\n", f"{key}={value}\n", env_file_content
        )

    with open(".env", "w+", encoding="utf-8") as file:
        file.write(env_file_content)
