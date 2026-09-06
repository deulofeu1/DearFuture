from datetime import datetime, timedelta, timezone


def future_time() -> str:
    return (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()


def test_homepage_and_health_are_available(client):
    homepage = client.get("/")
    health = client.get("/health")

    assert homepage.status_code == 200
    assert "DearFuture" in homepage.text
    assert "交给慢递蜗牛" in homepage.text
    assert "约在哪个时刻" in homepage.text
    assert "黄昏" in homepage.text
    assert "12:00" in homepage.text
    assert "Agent 正在处理" not in homepage.text
    assert health.status_code == 200
    assert health.json()["database"] == "sqlite"


def test_public_question_round_trip_never_exposes_email(client):
    response = client.post(
        "/api/questions",
        json={
            "question": "AI 会在一个月内取代初级程序员吗？",
            "check_at": future_time(),
        },
    )

    assert response.status_code == 201
    created = response.json()
    assert created["status"] == "scheduled"
    assert created["category"] == "technology"
    assert created["public_request_approved"] is True
    assert "email" not in created
    assert datetime.fromisoformat(created["check_at"]).utcoffset() == timedelta(0)

    detail = client.get(f"/api/questions/{created['public_id']}")
    wall = client.get("/api/public/questions")
    stats = client.get("/api/public/stats")

    assert detail.status_code == 200
    assert wall.json()[0]["public_id"] == created["public_id"]
    assert "email" not in wall.text
    assert stats.json() == {
        "total_public": 1,
        "awaiting_future": 1,
        "resolved": 0,
        "happened": 0,
    }


def test_private_question_has_no_public_detail(client):
    response = client.post(
        "/api/questions",
        json={
            "question": "我的职业选择下个月会更好吗？",
            "email": "private@example.com",
            "check_at": future_time(),
            "is_public": False,
        },
    )
    public_id = response.json()["public_id"]

    assert client.get(f"/api/questions/{public_id}").status_code == 404
    assert client.get("/api/public/questions").json() == []


def test_past_verification_date_is_rejected(client):
    response = client.post(
        "/api/questions",
        json={
            "question": "这个预测会发生吗？",
            "email": "demo@example.com",
            "check_at": (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat(),
            "is_public": False,
        },
    )
    assert response.status_code == 422
