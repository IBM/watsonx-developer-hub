import traceback
from typer.testing import CliRunner
from ibm_watsonx_ai_cli.cli import cli


import pytest


class TestAgents:
    def _clone_agent_template(self, runner: CliRunner, tmp_dir: str, name: str) -> str:
        target_dir = f"{tmp_dir}/{name}"
        runner.invoke(cli, ["template", "new", name], input=target_dir)
        return target_dir

    def _create_config_toml_file(self, env_file_values: dict[str, str]) -> None:
        with open("config.toml.example", encoding="utf-8") as file:
            config_toml_content = file.read()

        config_toml_content = config_toml_content.replace(
            'url = ""', f'url = "{env_file_values["WATSONX_URL"]}"'
        )

        with open("config.toml", "w+", encoding="utf-8") as file:
            file.write(config_toml_content)

    def _create_env_file(self, env_file_values: dict[str, str]) -> None:
        with open("template.env", encoding="utf-8") as file:
            env_file_content = file.read()

        for key, value in env_file_values.items():
            env_file_content = env_file_content.replace(f"{key}=\n", f"{key}={value}\n")

        with open(".env", "w+", encoding="utf-8") as file:
            file.write(env_file_content)

    def test_autogen_agent(
        self,
        env_file_values: dict[str, str],
        tmp_dir: str,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        runner = CliRunner()

        template_dir = self._clone_agent_template(runner, tmp_dir, "base/autogen-agent")
        monkeypatch.chdir(template_dir)

        self._create_config_toml_file(env_file_values)
        self._create_env_file(env_file_values)

        result = runner.invoke(cli, ["template", "invoke", "Hello"], "y")
        assert result.exit_code == 0 or result.exc_info is None, "".join(
            traceback.format_exception(*result.exc_info)
        )
