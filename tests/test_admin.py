from datetime import datetime, timedelta, timezone

from app.config import Settings


def future_time() -> str:
    return (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()


def admin_headers() -> dict[str, str]:
    return {"Authorization": "Bearer test-admin-token"}


def create_public_question(client):
    response = client.post(
        "/api/questions",
        json={
            "question": "这封信可以被管理员移除吗？",
            "check_at": future_time(),
        },
    )
    assert response.status_code == 201
    return response.json()["public_id"]


def test_admin_api_requires_token(client, monkeypatch):
    monkeypatch.setattr("app.main.get_settings", lambda: Settings(admin_token="test-admin-token"))

    assert client.get("/api/admin/questions").status_code == 401
    assert (
        client.get(
            "/api/admin/questions",
            headers={"Authorization": "Bearer wrong-token"},
        ).status_code
        == 403
    )


def test_admin_can_hide_and_restore_a_question(client, monkeypatch):
    monkeypatch.setattr("app.main.get_settings", lambda: Settings(admin_token="test-admin-token"))
    public_id = create_public_question(client)

    admin_list = client.get("/api/admin/questions", headers=admin_headers())
    assert admin_list.status_code == 200
    assert admin_list.json()[0]["public_id"] == public_id
    assert "email" not in admin_list.text
    assert admin_list.json()[0]["model_used"] is False
    assert admin_list.json()[0]["intake_record"]["needs_clarification"] is False
    assert "claim" in admin_list.json()[0]["intake_record"]

    deleted = client.delete(f"/api/admin/questions/{public_id}", headers=admin_headers())
    assert deleted.status_code == 200
    assert deleted.json()["status"] == "deleted"
    assert client.get(f"/api/questions/{public_id}").status_code == 404
    assert client.get("/api/public/questions").json() == []

    deleted_list = client.get("/api/admin/questions?status=deleted", headers=admin_headers())
    assert deleted_list.status_code == 200
    assert deleted_list.json()[0]["is_deleted"] is True

    restored = client.post(f"/api/admin/questions/{public_id}/restore", headers=admin_headers())
    assert restored.status_code == 200
    assert restored.json()["status"] == "scheduled"
    assert client.get(f"/api/questions/{public_id}").status_code == 200


def test_admin_can_retry_an_unresolved_question(client, monkeypatch):
    monkeypatch.setattr("app.main.get_settings", lambda: Settings(admin_token="test-admin-token"))
    monkeypatch.setattr("app.main.run_manual_retry", lambda _public_id: None)
    public_id = create_public_question(client)

    response = client.post(f"/api/admin/questions/{public_id}/retry", headers=admin_headers())

    assert response.status_code == 200
    assert response.json()["status"] == "verifying"
    question = client.get("/api/admin/questions", headers=admin_headers()).json()[0]
    assert question["status"] == "verifying"
    assert question["attempt_count"] == 0
    assert question["next_attempt_at"] is None


def test_admin_page_is_available(client):
    response = client.get("/admin")

    assert response.status_code == 200
    assert "管理口令" in response.text
    assert "sessionStorage" in response.text
