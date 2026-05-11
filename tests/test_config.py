from __future__ import annotations

from pathlib import Path

from ood.config import load_settings


SUPPORTED_ENV_VARS = {
    "OOD_KNOWLEDGE_DIR",
    "OOD_DATA_DIR",
    "OOD_STORAGE_DIR",
    "OOD_LLM_PROVIDER",
    "OOD_LLM_API_KEY",
    "OOD_LLM_MODEL",
    "OOD_ALLOW_CLOUD_LLM",
    "OOD_VERBOSE",
    "OOD_QUIET",
}


def test_settings_defaults_use_project_directory_contract(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    for name in (
        "OOD_KNOWLEDGE_DIR",
        "OOD_DATA_DIR",
        "OOD_STORAGE_DIR",
        "OOD_LLM_PROVIDER",
        "OOD_LLM_API_KEY",
        "OOD_LLM_MODEL",
    ):
        monkeypatch.delenv(name, raising=False)

    settings = load_settings()

    assert settings.knowledge_dir == Path("knowledge")
    assert settings.data_dir == Path("data")
    assert settings.storage_dir == Path("data") / "storage"
    assert settings.llm_provider is None
    assert settings.llm_api_key is None
    assert settings.llm_model is None
    assert settings.has_llm_credentials is False
    assert settings.allow_cloud_llm is False
    assert settings.can_use_cloud_llm is False


def test_settings_load_llm_credentials_from_environment(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("OOD_LLM_PROVIDER", "openai")
    monkeypatch.setenv("OOD_LLM_API_KEY", "test-api-key")
    monkeypatch.setenv("OOD_LLM_MODEL", "gpt-test")

    settings = load_settings()

    assert settings.llm_provider == "openai"
    assert settings.llm_api_key is not None
    assert settings.llm_api_key.get_secret_value() == "test-api-key"
    assert settings.llm_model == "gpt-test"
    assert settings.has_llm_credentials is True
    assert settings.allow_cloud_llm is False
    assert settings.can_use_cloud_llm is False


def test_cloud_llm_usage_requires_credentials_and_explicit_approval(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("OOD_LLM_API_KEY", "test-api-key")
    monkeypatch.setenv("OOD_ALLOW_CLOUD_LLM", "true")

    settings = load_settings()

    assert settings.has_llm_credentials is True
    assert settings.allow_cloud_llm is True
    assert settings.can_use_cloud_llm is True


def test_cloud_llm_approval_without_credentials_is_insufficient(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("OOD_LLM_API_KEY", raising=False)
    monkeypatch.setenv("OOD_ALLOW_CLOUD_LLM", "true")

    settings = load_settings()

    assert settings.has_llm_credentials is False
    assert settings.allow_cloud_llm is True
    assert settings.can_use_cloud_llm is False


def test_settings_load_llm_credentials_from_dotenv(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    for name in ("OOD_LLM_PROVIDER", "OOD_LLM_API_KEY", "OOD_LLM_MODEL"):
        monkeypatch.delenv(name, raising=False)
    (tmp_path / ".env").write_text(
        "OOD_LLM_PROVIDER=anthropic\n"
        "OOD_LLM_API_KEY=dotenv-api-key\n"
        "OOD_LLM_MODEL=claude-test\n",
        encoding="utf-8",
    )

    settings = load_settings()

    assert settings.llm_provider == "anthropic"
    assert settings.llm_api_key is not None
    assert settings.llm_api_key.get_secret_value() == "dotenv-api-key"
    assert settings.llm_model == "claude-test"
    assert settings.has_llm_credentials is True


def test_explicit_overrides_win_over_environment(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("OOD_LLM_PROVIDER", "env-provider")
    monkeypatch.setenv("OOD_LLM_API_KEY", "env-api-key")
    monkeypatch.setenv("OOD_LLM_MODEL", "env-model")

    settings = load_settings(
        llm_provider="override-provider",
        llm_api_key="override-api-key",
        llm_model="override-model",
    )

    assert settings.llm_provider == "override-provider"
    assert settings.llm_api_key is not None
    assert settings.llm_api_key.get_secret_value() == "override-api-key"
    assert settings.llm_model == "override-model"


def test_path_overrides_can_point_outside_repository(monkeypatch, tmp_path: Path) -> None:
    repo_dir = tmp_path / "repo"
    external_dir = tmp_path / "external"
    repo_dir.mkdir()
    external_dir.mkdir()
    monkeypatch.chdir(repo_dir)
    monkeypatch.setenv("OOD_KNOWLEDGE_DIR", "env-knowledge")
    monkeypatch.setenv("OOD_DATA_DIR", "env-data")
    monkeypatch.setenv("OOD_STORAGE_DIR", "env-storage")

    settings = load_settings(
        knowledge_dir=external_dir / "kb",
        data_dir=external_dir / "idx",
        storage_dir=external_dir / "store",
    )

    assert settings.knowledge_dir == external_dir / "kb"
    assert settings.data_dir == external_dir / "idx"
    assert settings.storage_dir == external_dir / "store"


def test_storage_dir_derives_from_overridden_data_dir(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("OOD_DATA_DIR", "env-data")
    monkeypatch.delenv("OOD_STORAGE_DIR", raising=False)

    settings = load_settings(
        knowledge_dir=tmp_path / "kb",
        data_dir=tmp_path / "idx",
    )

    assert settings.knowledge_dir == tmp_path / "kb"
    assert settings.data_dir == tmp_path / "idx"
    assert settings.storage_dir == tmp_path / "idx" / "storage"


def test_eval_dataset_path_defaults_to_committed_mock_v1_fixture(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("OOD_EVAL_DATASET", raising=False)

    settings = load_settings()

    assert settings.eval_dataset_path == Path("evaluation/datasets/mock-v1.json")


def test_eval_dataset_path_binds_to_environment_variable(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("OOD_EVAL_DATASET", "/tmp/custom-dataset.json")

    settings = load_settings()

    assert settings.eval_dataset_path == Path("/tmp/custom-dataset.json")


def test_env_example_documents_all_supported_variables() -> None:
    env_example = Path(".env.example").read_text(encoding="utf-8")

    for env_var in SUPPORTED_ENV_VARS:
        assert env_var in env_example
