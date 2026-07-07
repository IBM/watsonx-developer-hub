from contextlib import contextmanager
import logging
import subprocess
from pathlib import Path
from typing import Generator

import pytest
from utils import clone_agent_template, create_env_file, run_cli

logger = logging.getLogger(__name__)


class TestMCPAutoAITemplate:
    EXPECTED_OUTPUTS_BY_PROMPT = {
        "help": ["The following commands are supported:\n"],
        "list_questions": [
            "Simple addition",
            "Subtraction example",
            "No Risk question",
            "Risk question",
        ],
        "1": ["add", "2"],
        "2": ["sub", "99"],
        "3": ["invoke_credit_risk_deployment"],
        "4": ["invoke_credit_risk_deployment"],
    }

    @contextmanager
    def _run_server(self, venv_path: Path) -> Generator[None, None, None]:
        process = subprocess.Popen(
            [venv_path / "bin" / "python", "mcp_server.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        yield

        process.terminate()

    def _interact_with_mcp(self, venv_path: Path, prompt: str) -> str:
        result = run_cli(
            venv_path,
            ["interact_with_mcp.py"],
            exec_name="python",
            input=f"{prompt}\nq\n".encode(),
        )

        return result.stdout.decode()

    def _assert_interaction_output(
        self, venv_path: Path, prompt: str, expected_outputs: list[str]
    ) -> None:
        output = self._interact_with_mcp(venv_path, prompt)

        for expected_output in expected_outputs:
            assert expected_output in output

    def test_mcp_autoai_template(
        self,
        test_venv_path: Path,
        tmp_dir: str,
        env_file_values: dict[str, str],
        credit_risk_deployment_id: str,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        clone_agent_template(
            test_venv_path, tmp_dir, "community/mcp-autoai-template", monkeypatch
        )

        run_cli(test_venv_path, ["install", "-r", "requirements.txt"], "pip")

        create_env_file(
            env_file_values
            | {"WATSONX_CREDIT_RISK_DEPLOYMENT_ID": credit_risk_deployment_id}
        )

        with self._run_server(test_venv_path):
            for prompt, expected_outputs in self.EXPECTED_OUTPUTS_BY_PROMPT.items():
                self._assert_interaction_output(
                    test_venv_path, prompt, expected_outputs
                )
