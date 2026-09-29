import argparse
import ssl
import httpx

parser = argparse.ArgumentParser()
parser.add_argument("--ca", required=True)
args = parser.parse_args()
context = ssl.create_default_context(cafile=args.ca)
with httpx.Client(
    base_url="https://localhost:8443",
    verify=context,
    timeout=15,
    follow_redirects=False,
    trust_env=False,
) as client:
    health = client.get("/health")
    assert health.status_code == 200 and health.json()["environment"] == "production"
    assert "max-age=" in health.headers["strict-transport-security"]
    assert client.get("/api/config").json()["demo"] is False
    assert client.get("/api/catalog").json() == []
    assert (
        client.post(
            "/api/auth/demo", json={"persona": "editor"}, headers={"X-App-Request": "1"}
        ).status_code
        == 404
    )
    assert client.get("/api/profile").status_code == 401
    assert client.post("/api/max/webhook", json={}).status_code == 403
    assert client.post("/api/profile", content=b"x" * 262145).status_code == 413
    responses = [
        client.post(
            "/api/auth/max",
            json={"init_data": "synthetic"},
            headers={"X-App-Request": "1"},
        )
        for _ in range(15)
    ]
    assert any(r.status_code == 429 for r in responses)
with httpx.Client(follow_redirects=False, trust_env=False) as client:
    redirect = client.get("http://localhost:8088/health")
    assert (
        redirect.status_code == 308
        and redirect.headers["location"] == "https://localhost/health"
    )
print(
    "HTTPS: 10 проверок пройдены; доверие только тестовому сертификату, публикации нет."
)
