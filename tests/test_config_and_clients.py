import importlib
import sys
from pathlib import Path

import pytest


class _FakeResponse:
    def __init__(self, text: str = "<html>not json</html>", status_code: int = 200):
        self._text = text
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError("boom")

    def json(self):
        raise ValueError("not json")

    def text(self):
        return self._text


def test_config_loads_dotenv_values(tmp_path, monkeypatch):
    repo_root = Path(__file__).resolve().parents[1]
    dotenv_path = repo_root / ".env"
    original = dotenv_path.read_text(encoding="utf-8") if dotenv_path.exists() else None

    try:
        dotenv_path.write_text("LLM_PROVIDER=groq\nGROQ_API_KEY=test-key\n", encoding="utf-8")
        monkeypatch.delenv("LLM_PROVIDER", raising=False)
        monkeypatch.delenv("GROQ_API_KEY", raising=False)
        sys.modules.pop("shared.utils.config", None)
        import shared.utils.config as config

        reloaded = importlib.reload(config)
        assert reloaded.LLM_PROVIDER == "groq"
        assert reloaded.GROQ_API_KEY == "test-key"
        assert reloaded.DRY_RUN is False
    finally:
        if original is None:
            dotenv_path.unlink(missing_ok=True)
        else:
            dotenv_path.write_text(original, encoding="utf-8")
        sys.modules.pop("shared.utils.config", None)
        import shared.utils.config as config
        importlib.reload(config)


def test_paperswithcode_returns_empty_on_invalid_json(monkeypatch):
    import requests

    def fake_get(*args, **kwargs):
        return _FakeResponse()

    monkeypatch.setattr(requests, "get", fake_get)
    from person_3_dataset_planner.dataset.paperswithcode import PapersWithCodeClient

    client = PapersWithCodeClient()
    assert client.search_datasets("foo") == []
