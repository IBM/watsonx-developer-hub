import logging
import os
from pathlib import Path
import shutil
import subprocess
import re

import pytest

ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-9;]*m")

AGENTS_PATH = Path(__file__).parents[1] / "agents"

ENV_VARS_MAPPING = {
    "WATSONX_APIKEY": "WATSONX_API_KEY",  # pragma: allowlist secret
    "WATSONX_API_KEY": "WATSONX_API_KEY",  # pragma: allowlist secret
    "WATSONX_URL": "WATSONX_URL",
    "WATSONX_SPACE_ID": "WATSONX_SPACE_ID",
}

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
    venv_exec = venv_path / "bin" / exec_name
    executable = (
        venv_exec if venv_exec.exists() else shutil.which(exec_name) or exec_name
    )
    result = subprocess.run(
        [executable, *command],
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


def get_env_vars(additional_env_vars: dict[str, str] | None = None) -> dict[str, str]:
    env_vars = {cli: os.environ[env] for cli, env in ENV_VARS_MAPPING.items()}

    if additional_env_vars:
        env_vars.update(additional_env_vars)

    return env_vars


def create_env_file(env_vars: dict[str, str]) -> None:
    with open("template.env", encoding="utf-8") as file:
        env_file_content = file.read()

    for key, value in env_vars.items():
        env_file_content = re.sub(
            rf"{key}=[^\n]*\n", f"{key}={value}\n", env_file_content
        )

    with open(".env", "w+", encoding="utf-8") as file:
        file.write(env_file_content)


def strip_ansi(text: str) -> str:
    return ANSI_ESCAPE_RE.sub("", text)


def assert_tool_used(
    result: subprocess.CompletedProcess[bytes], tool_name: str
) -> None:
    output = strip_ansi(result.stdout.decode())
    assert f"Called tool '{tool_name}'" in output, (
        f"Expected tool '{tool_name}' to be called, but it was not found in output.\n\n"
        f"Stdout:\n{output}"
    )
    assert f"Tool '{tool_name}' responded" in output, (
        f"Expected tool '{tool_name}' to respond, but it was not found in output.\n\n"
        f"Stdout:\n{output}"
    )


def assert_tool_not_used(
    result: subprocess.CompletedProcess[bytes], tool_name: str
) -> None:
    output = strip_ansi(result.stdout.decode())
    assert f"Called tool '{tool_name}'" not in output, (
        f"Tool '{tool_name}' was called but should not have been for this input.\n\n"
        f"Stdout:\n{output}"
    )
