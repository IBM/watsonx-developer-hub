import logging
from pathlib import Path

import pytest

from utils import AGENTS_PATH, clone_agent_template, create_env_file, use_cli, run_cli


logger = logging.getLogger(__name__)


class TestAgents:
    SKIPPED_TESTS = {
        "community/langgraph-graph-rag": "Neo4j credentials required to run the AI service on the Cloud",
        "community/langgraph-tavily-tool": "Tavily credentials required to run the AI service on the Cloud",
    }

    CONFIG_TOML_REPLACEMENTS = {
        'url = "{}"': ("WATSONX_URL", "env"),
        'postgres_db_connection_id = "{}"': ("psql_connection_id", "fixture"),
        'tool_config_connection_id = "{}"': ("psql_connection_id", "fixture"),
        'tool_config_dialect = "{}"': ("PostgreSQL", "text"),
        'tool_config_schema = "{}"': ("public", "text"),
        'tool_config_spaceId = "{}"': ("space_id", "fixture"),
        'tool_config_vectorIndexId = "{}"': ("vector_index_id", "fixture"),
    }

    @staticmethod
    def _get_agent_names(dir_name: str) -> list[str]:
        agents_path = AGENTS_PATH / dir_name

        return [
            f"{dir_name}/{item.name}"
            for item in agents_path.iterdir()
            if item.is_dir()
            and "mcp" not in item.name  # MCP templates tested in separate class
        ]

    def _create_config_toml_file(
        self, env_file_values: dict[str, str], request: pytest.FixtureRequest
    ) -> None:
        with open("config.toml.example", encoding="utf-8") as file:
            config_toml_content = file.read()

        for pattern, replacement in self.CONFIG_TOML_REPLACEMENTS.items():
            if pattern.format("") not in config_toml_content:
                continue

            value, value_type = replacement
            match value_type:
                case "env":
                    value = env_file_values[value]
                case "fixture":
                    value = request.getfixturevalue(value)

            config_toml_content = config_toml_content.replace(
                pattern.format(""), pattern.format(value)
            )

        with open("config.toml", "w+", encoding="utf-8") as file:
            file.write(config_toml_content)

    def _get_deployment_id_from_env(self) -> str:
        with open(".env", encoding="utf-8") as file:
            for line in file:
                if not line.startswith("WATSONX_DEPLOYMENT_ID="):
                    continue

                return line.split("=", 1)[1].strip().strip("'")

        pytest.fail("Deployment ID not found in .env file")

    def _run_template_list(self, venv_path: Path, agent_name: str | None) -> None:
        result = run_cli(venv_path, ["template", "list"])
        assert f" {agent_name}\n" in result.stdout.decode()

    def _run_template_unit_tests(self, venv_path: Path) -> None:
        run_cli(venv_path, ["tests"], exec_name="pytest", allowed_exit_codes={0, 5})

    def _run_template_invoke(self, venv_path: Path) -> None:
        run_cli(
            venv_path,
            [
                "template",
                "invoke",
                "Call your tool with some example value and tell me what you asked for and what you received.",
            ],
            input=b"y",  # for package installation
        )

    def _run_service_new(self, venv_path: Path) -> str:
        run_cli(venv_path, ["service", "new"], input=b"\n")
        return self._get_deployment_id_from_env()

    def _run_service_list(self, venv_path: Path) -> None:
        run_cli(venv_path, ["service", "list"])

    def _run_service_get(self, venv_path: Path, deployment_id: str) -> None:
        run_cli(venv_path, ["service", "get", deployment_id])

    def _run_service_invoke(self, venv_path: Path) -> None:
        run_cli(venv_path, ["service", "invoke", "Hello"])

    def _run_service_delete(self, venv_path: Path, deployment_id: str) -> None:
        run_cli(
            venv_path,
            ["service", "delete", deployment_id],
            input=b"y",  # Confirm removal of AI service asset
        )

    def _setup_template(
        self,
        venv_path: Path,
        agent_name: str,
        tmp_dir: str,
        env_file_values: dict[str, str],
        monkeypatch: pytest.MonkeyPatch,
        request: pytest.FixtureRequest,
    ) -> None:
        if agent_name in self.SKIPPED_TESTS:
            pytest.skip(self.SKIPPED_TESTS[agent_name])

        clone_agent_template(venv_path, tmp_dir, agent_name, monkeypatch)
        create_env_file(env_file_values)

        self._create_config_toml_file(env_file_values, request)

    def _template_tests(self, venv_path: Path, agent_name: str) -> None:
        if use_cli():
            # New templates will not be included in the list, so we
            # have to skip this check when not testing via the CLI
            self._run_template_list(venv_path, agent_name)

        self._run_template_invoke(venv_path)
        self._run_template_unit_tests(venv_path)

    def _service_tests(self, venv_path: Path) -> None:
        deployment_id = self._run_service_new(venv_path)
        self._run_service_list(venv_path)
        self._run_service_get(venv_path, deployment_id)
        self._run_service_invoke(venv_path)
        self._run_service_delete(venv_path, deployment_id)

    @pytest.mark.parametrize("agent_name", _get_agent_names("base"))
    def test_base_agent(
        self,
        agent_name: str,
        env_file_values: dict[str, str],
        tmp_dir: str,
        test_venv_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        request: pytest.FixtureRequest,
    ) -> None:
        self._setup_template(
            test_venv_path,
            agent_name,
            tmp_dir,
            env_file_values,
            monkeypatch,
            request,
        )
        self._template_tests(test_venv_path, agent_name)
        self._service_tests(test_venv_path)

    @pytest.mark.parametrize("agent_name", _get_agent_names("community"))
    def test_community_agent(
        self,
        agent_name: str,
        env_file_values: dict[str, str],
        tmp_dir: str,
        test_venv_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        request: pytest.FixtureRequest,
    ) -> None:
        self._setup_template(
            test_venv_path,
            agent_name,
            tmp_dir,
            env_file_values,
            monkeypatch,
            request,
        )
        self._template_tests(test_venv_path, agent_name)
        self._service_tests(test_venv_path)
