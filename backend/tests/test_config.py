import os

import presence_cv.config as config


def test_env_file_precedence_and_process_override(tmp_path, monkeypatch):
    backend = tmp_path / "backend"
    backend.mkdir()
    (tmp_path / ".env").write_text("DATABASE_URL=root\nFILE_ONLY_SETTING=present\n")
    (tmp_path / ".env.local").write_text("DATABASE_URL=root-local\n")
    (backend / ".env").write_text("DATABASE_URL=backend\n")
    (backend / ".env.local").write_text("DATABASE_URL=backend-local\n")
    monkeypatch.setattr(config, "BACKEND_ROOT", backend)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("FILE_ONLY_SETTING", raising=False)
    assert config.backend_environment()["DATABASE_URL"] == "backend-local"
    assert "DATABASE_URL" not in os.environ
    assert "FILE_ONLY_SETTING" not in os.environ
    monkeypatch.setenv("DATABASE_URL", "process")
    assert config.backend_environment()["DATABASE_URL"] == "process"
