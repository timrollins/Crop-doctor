from __future__ import annotations

import re
from pathlib import Path

from fastapi.testclient import TestClient

from backend.main import app


def test_frontend_static_contract() -> None:
    index_html = Path("frontend/index.html").read_text(encoding="utf-8")
    app_js = Path("frontend/app.js").read_text(encoding="utf-8")

    for content in (index_html, app_js):
        assert "http://" not in content
        assert "https://" not in content

    assert 'value="lug"' in index_html
    assert 'value="lg"' not in index_html
    assert 'method: "POST"' in app_js
    assert '/api/speak' in app_js
    assert not re.search(r'<textarea[^>]*id="question"[^>]*required', index_html)


def test_frontend_served_at_root() -> None:
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    assert "Crop Doctor" in response.text
