from contextlib import contextmanager
import logging
import subprocess
from pathlib import Path
from typing import Generator

import pytest
import os
from utils import (
    assert_tool_used,
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


@pytest.fixture(scope="class", name="orchestrate_template_dir")
def fixture_orchestrate_template_dir(
    test_venv_path: Path, tmp_path_factory: pytest.TempPathFactory
) -> Generator[Path, None, None]:
    """Clone the Orchestrate AutoAI template into a class-scoped temp directory
    and ``chdir`` into it for the lifetime of the entire test class.

    Using ``os.chdir`` (rather than ``monkeypatch.chdir``) ensures the working
    directory persists across all test methods — ``monkeypatch`` is
    function-scoped and resets the CWD after every individual test.
    """
    import shutil as _shutil

    template_name = "mcp/mcp-orchestrate-autoai-template-generic"
    tmp_dir = tmp_path_factory.mktemp("orchestrate_template", numbered=True)
    target_dir = tmp_dir / template_name

    from utils import AGENTS_PATH, use_cli

    if use_cli():
        run_cli(
            test_venv_path, ["template", "new", template_name], input=str(target_dir)
        )
        run_cli(test_venv_path, ["install", "--with", "dev"], exec_name="poetry")
    else:
        _shutil.copytree(AGENTS_PATH / template_name, target_dir)

    original_cwd = Path.cwd()
    os.chdir(target_dir)

    yield target_dir

    os.chdir(original_cwd)


@pytest.mark.usefixtures("orchestrate_template_dir", "orchestrate_env_name")
class TestOrchestrateMCPAutoAITemplate:
    """End-to-end tests for the MCP Orchestrate AutoAI template.

    Each test method covers one logical step of the flow. pytest runs methods
    in definition order within a class, which matches the step sequence below.

    The ``orchestrate_template_dir`` fixture clones the template once for the
    whole class and permanently sets the CWD to it, so every subsequent bash
    script call (``scripts/deploy.sh``, ``scripts/cleanup.sh``) resolves
    correctly regardless of which test method is running.
    """

    AGENT_NAME = "autoai_prediction_agent"
    TEMPLATE_PATH = "mcp/mcp-orchestrate-autoai-template-generic"
    AUTOAI_DEPLOYMENT_ID = "019e8259-1d14-7361-9509-c89f174cce0d"

    # Prompts sent to the agent during the chat interaction test.
    CHAT_PROMPTS = [
        "hello",
        "sepal_length=0.1, sepal_width=0.1, petal_length=0.15, species=satosa",
        "sepal_length=5.1, sepal_width=3.5, petal_length=1.4, species=setosa",
        "q",
    ]

    # ---------------------------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------------------------

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

    # ---------------------------------------------------------------------------
    # Step 1 – install dependencies
    # ---------------------------------------------------------------------------

    def test_01_install_dependencies(self, test_venv_path: Path) -> None:
        """Install the template's dev dependencies into the test venv."""
        result = run_cli(
            test_venv_path, ["install", "-r", "requirements-dev.txt"], "pip"
        )

        stdout = result.stdout.decode()
        assert (
            "Successfully installed" in stdout or "already satisfied" in stdout.lower()
        ), f"pip install did not report a successful installation.\nStdout:\n{stdout}"

    # ---------------------------------------------------------------------------
    # Step 2 – create .env file
    # ---------------------------------------------------------------------------

    def test_02_create_env_file(self) -> None:
        """Populate the .env file with required credentials."""
        env_vars = get_env_vars(
            {"WATSONX_AUTOAI_DEPLOYMENT_ID": self.AUTOAI_DEPLOYMENT_ID}
        )
        create_env_file(env_vars)

        assert os.path.isfile(".env"), ".env file was not created"

        # with open(".env", encoding="utf-8") as fh:
        #     content = fh.read()

        # assert f"WATSONX_AUTOAI_DEPLOYMENT_ID={self.AUTOAI_DEPLOYMENT_ID}" in content, (
        #     "WATSONX_AUTOAI_DEPLOYMENT_ID was not written to .env correctly"
        # )

    # ---------------------------------------------------------------------------
    # Step 3 – register and activate the Orchestrate environment
    # ---------------------------------------------------------------------------

    def test_03_register_orchestrate_env(
        self,
        test_venv_path: Path,
        orchestrate_env_name: str,
    ) -> None:
        """Register a uniquely-named Orchestrate environment."""
        orch_url = os.environ["ORCHESTRATE_URL"]

        result = run_cli(
            test_venv_path,
            ["env", "add", "-n", orchestrate_env_name, "-u", orch_url],
            "orchestrate",
        )

        stdout = result.stdout.decode()
        assert result.returncode == 0, f"orchestrate env add failed.\nStdout:\n{stdout}"

    def test_04_activate_orchestrate_env(
        self,
        test_venv_path: Path,
        orchestrate_env_name: str,
    ) -> None:
        """Activate the registered Orchestrate environment with an API key."""
        orch_api_key = os.environ["ORCHESTRATE_API_KEY"]

        result = run_cli(
            test_venv_path,
            ["env", "activate", orchestrate_env_name, f"--api-key={orch_api_key}"],
            "orchestrate",
        )

        assert result.returncode == 0, (
            f"orchestrate env activate failed.\nStdout:\n{result.stdout.decode()}"
        )

    # ---------------------------------------------------------------------------
    # Step 4 – pre-deployment cleanup (idempotency guard)
    # ---------------------------------------------------------------------------

    def test_05_pre_deployment_cleanup(self, test_venv_path: Path) -> None:
        """Run the cleanup script before deploying to ensure a pristine state."""
        self._run_cleanup(test_venv_path)

    # ---------------------------------------------------------------------------
    # Step 5 – deploy
    # ---------------------------------------------------------------------------

    def test_06_deploy(self, test_venv_path: Path) -> None:
        """Deploy the agent via the template deploy script."""
        result = run_cli(
            test_venv_path,
            ["scripts/deploy.sh"],
            "bash",
        )

        stdout = result.stdout.decode()
        assert result.returncode == 0, (
            f"deploy.sh exited with a non-zero code.\nStdout:\n{stdout}"
        )

    # ---------------------------------------------------------------------------
    # Step 6 – chat interaction and tool-use assertions
    # ---------------------------------------------------------------------------

    def test_07_chat_calls_autoai_tool(self, test_venv_path: Path) -> None:
        """Interact with the deployed agent and verify the AutoAI tool is invoked."""
        result = run_cli(
            test_venv_path,
            ["chat", "ask", "-n", self.AGENT_NAME, "-r"],
            "orchestrate",
            input="\n".join(self.CHAT_PROMPTS).encode(),
        )

        assert result.returncode == 0, (
            f"orchestrate chat ask failed.\nStdout:\n{result.stdout.decode()}"
        )

        assert_tool_used(result, "get_autoai_prediction")

    # ---------------------------------------------------------------------------
    # Teardown – cleanup after all steps (also registered as a dedicated step)
    # ---------------------------------------------------------------------------

    def test_08_post_test_cleanup(self, test_venv_path: Path) -> None:
        """Undeploy the agent by running the cleanup script."""
        self._run_cleanup(test_venv_path)

    def test_09_remove_orchestrate_env(
        self,
        test_venv_path: Path,
        orchestrate_env_name: str,
    ) -> None:
        """Remove the Orchestrate environment that was created for this test run."""
        result = run_cli(
            test_venv_path,
            ["env", "remove", "-n", orchestrate_env_name],
            "orchestrate",
            input=b"y",
        )

        assert result.returncode == 0, (
            f"orchestrate env remove failed.\nStdout:\n{result.stdout.decode()}"
        )
