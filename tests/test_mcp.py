from contextlib import contextmanager
import logging
import re
import subprocess
import uuid
from pathlib import Path
from typing import Generator

import pytest
import os
from utils import (
    clone_agent_template,
    create_env_file,
    get_env_vars,
    run_cli,
)

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
        credit_risk_deployment_id: str,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        clone_agent_template(
            test_venv_path, tmp_dir, "community/mcp-autoai-template", monkeypatch
        )

        run_cli(test_venv_path, ["install", "-r", "requirements.txt"], "pip")

        env_vars = get_env_vars(
            {"WATSONX_CREDIT_RISK_DEPLOYMENT_ID": credit_risk_deployment_id}
        )
        create_env_file(env_vars)

        with self._run_server(test_venv_path):
            for prompt, expected_outputs in self.EXPECTED_OUTPUTS_BY_PROMPT.items():
                self._assert_interaction_output(
                    test_venv_path, prompt, expected_outputs
                )


class TestOrchestrateMCPAutoAITemplate:
    """End-to-end tests for the MCP Orchestrate AutoAI template."""

    AGENT_NAME = "autoai_prediction_agent"
    TEMPLATE_NAME = "mcp/mcp-orchestrate-autoai-template-generic"

    # Greeting-only prompts — the AutoAI tool must NOT be invoked.
    CHAT_PROMPTS_GREETING_ONLY = [
        "hello",
        "q",
    ]

    # Single prediction request — the AutoAI tool MUST be invoked.
    CHAT_PROMPTS_SINGLE_PREDICTION = [
        "CheckingStatus=0_to_200, LoanDuration=31, CreditHistory=credits_paid_to_date, LoanPurpose=other, LoanAmount=1889, ExistingSavings=100_to_500, EmploymentDuration=less_1, InstallmentPercent=3, Sex=female, OthersOnLoan=none, CurrentResidenceDuration=3, OwnsProperty=savings_insurance, Age=32, InstallmentPlans=none, Housing=own, ExistingCreditsCount=1, Job=skilled, Dependents=1, Telephone=none, ForeignWorker=yes",
        "q",
    ]

    # ---------------------------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------------------------

    _ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-9;]*m")

    def _strip_ansi(self, text: str) -> str:
        return self._ANSI_ESCAPE_RE.sub("", text)

    def _assert_tool_used(
        self, result: subprocess.CompletedProcess[bytes], tool_name: str
    ) -> None:
        output = self._strip_ansi(result.stdout.decode())
        assert f"Called tool '{tool_name}'" in output, (
            f"Expected tool '{tool_name}' to be called, but it was not found in output.\n\n"
            f"Stdout:\n{output}"
        )
        assert f"Tool '{tool_name}' responded" in output, (
            f"Expected tool '{tool_name}' to respond, but it was not found in output.\n\n"
            f"Stdout:\n{output}"
        )

    def _assert_tool_not_used(
        self, result: subprocess.CompletedProcess[bytes], tool_name: str
    ) -> None:
        output = self._strip_ansi(result.stdout.decode())
        assert f"Called tool '{tool_name}'" not in output, (
            f"Tool '{tool_name}' was called but should not have been for this input.\n\n"
            f"Stdout:\n{output}"
        )

    def _setup_template(
        self,
        venv_path: Path,
        tmp_dir: str,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        clone_agent_template(venv_path, tmp_dir, self.TEMPLATE_NAME, monkeypatch)
        run_cli(venv_path, ["install", "-r", "requirements-dev.txt"], "pip")

    def _create_env_file(self, credit_risk_deployment_id: str) -> None:
        env_vars = get_env_vars(
            {"WATSONX_AUTOAI_DEPLOYMENT_ID": credit_risk_deployment_id}
        )
        create_env_file(env_vars)

    def _register_orchestrate_env(self, venv_path: Path, env_name: str) -> None:
        orchestrate_url = os.environ["WATSONX_ORCHESTRATE_URL"]
        run_cli(
            venv_path,
            ["env", "add", "-n", env_name, "-u", orchestrate_url],
            "orchestrate",
        )

    def _activate_orchestrate_env(self, venv_path: Path, env_name: str) -> None:
        orchestrate_api_key = os.environ["WATSONX_ORCHESTRATE_API_KEY"]
        run_cli(
            venv_path,
            ["env", "activate", env_name, f"--api-key={orchestrate_api_key}"],
            "orchestrate",
        )

    def _run_cleanup(self, venv_path: Path) -> None:
        """Run the template cleanup script.

        Exit codes 0 and 1 are both accepted — 0 for a clean undeployment,
        1 for a script-level "nothing to remove" result (idempotent runs).
        """
        run_cli(
            venv_path,
            ["scripts/cleanup.sh"],
            "bash",
            allowed_exit_codes={0, 1},
        )

    def _deploy(self, venv_path: Path) -> None:
        run_cli(venv_path, ["scripts/deploy.sh"], "bash")

    def _chat(
        self, venv_path: Path, prompts: list[str]
    ) -> subprocess.CompletedProcess[bytes]:
        """Send *prompts* to the deployed agent and return the raw CLI result."""
        return run_cli(
            venv_path,
            ["chat", "ask", "-n", self.AGENT_NAME, "-r"],
            "orchestrate",
            input="\n".join(prompts).encode(),
        )

    def _remove_orchestrate_env(self, venv_path: Path, env_name: str) -> None:
        run_cli(
            venv_path,
            ["env", "remove", "-n", env_name],
            "orchestrate",
            input=b"y",
        )

    # ---------------------------------------------------------------------------
    # Test
    # ---------------------------------------------------------------------------

    def test_orchestrate_mcp_autoai_template(
        self,
        test_venv_path: Path,
        tmp_dir: str,
        credit_risk_deployment_id: str,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        env_name = f"test_env_{uuid.uuid4().hex[:8]}"

        self._setup_template(test_venv_path, tmp_dir, monkeypatch)
        self._create_env_file(credit_risk_deployment_id)
        self._register_orchestrate_env(test_venv_path, env_name)
        self._activate_orchestrate_env(test_venv_path, env_name)

        try:
            self._run_cleanup(test_venv_path)
            self._deploy(test_venv_path)

            result = self._chat(test_venv_path, self.CHAT_PROMPTS_GREETING_ONLY)
            self._assert_tool_not_used(result, "get_autoai_prediction")

            result = self._chat(test_venv_path, self.CHAT_PROMPTS_SINGLE_PREDICTION)
            self._assert_tool_used(result, "get_autoai_prediction")
        finally:
            self._run_cleanup(test_venv_path)
            self._remove_orchestrate_env(test_venv_path, env_name)
