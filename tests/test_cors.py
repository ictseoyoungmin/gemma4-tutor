from fastapi.testclient import TestClient

from gemma_tutor_edge.app import app


def test_chat_preflight_allows_vite_origin():
    client = TestClient(app)
    response = client.options(
        "/v1/chat",
        headers={
            "Origin": "http://127.0.0.1:5173",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:5173"
