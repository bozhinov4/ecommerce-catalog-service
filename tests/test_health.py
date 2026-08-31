import pytest
from fastapi.testclient import TestClient

from ecommerce_catalog_service import main
from ecommerce_catalog_service.main import app


def test_health_returns_service_status() -> None:
    response = TestClient(app).get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": "0.1.1"}


def test_run_starts_development_server(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[dict[str, object]] = []

    def fake_run(*_args: object, **kwargs: object) -> None:
        calls.append(kwargs)

    monkeypatch.setattr(main.uvicorn, "run", fake_run)

    main.run()

    assert calls == [{"host": "0.0.0.0", "port": 8000, "reload": True}]  # noqa: S104
