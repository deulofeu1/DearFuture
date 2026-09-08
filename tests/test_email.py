import json
from types import SimpleNamespace

from app.email import send_result_email


class FakeResponse:
    status = 200

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None


def test_resend_api_delivery(monkeypatch):
    settings = SimpleNamespace(
        mail_enabled=True,
        mail_from="DearFuture <hello@letters.example.com>",
        resend_api_key="re_test",
        smtp_host=None,
    )
    captured = {}

    def fake_urlopen(request, timeout):
        captured["request"] = request
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr("app.email.get_settings", lambda: settings)
    monkeypatch.setattr("app.email.urlopen", fake_urlopen)

    result = send_result_email(
        recipient="reader@example.com",
        question="明天会下雨吗？",
        outcome="uncertain",
        summary="未来还没有说清楚。",
        letter="请安心等待。",
        public_url="https://example.com/q/letter",
    )

    payload = json.loads(captured["request"].data)
    assert result.status == "sent"
    assert captured["request"].full_url == "https://api.resend.com/emails"
    assert captured["request"].get_header("Authorization") == "Bearer re_test"
    assert payload["to"] == ["reader@example.com"]
    assert "明天会下雨吗？" in payload["text"]
    assert "亲爱的过去的你：" in payload["text"]
    assert captured["timeout"] == 20


def test_resend_api_uses_english_salutation_for_english_question(monkeypatch):
    settings = SimpleNamespace(
        mail_enabled=True,
        mail_from="DearFuture <hello@letters.example.com>",
        resend_api_key="re_test",
        smtp_host=None,
    )
    captured = {}

    def fake_urlopen(request, timeout):
        captured["request"] = request
        return FakeResponse()

    monkeypatch.setattr("app.email.get_settings", lambda: settings)
    monkeypatch.setattr("app.email.urlopen", fake_urlopen)

    send_result_email(
        recipient="reader@example.com",
        question="Will AI replace me one day?",
        outcome="uncertain",
        summary="The evidence remains mixed.",
        letter="The future is still unfolding.",
        public_url=None,
    )

    payload = json.loads(captured["request"].data)
    assert "Dear past you," in payload["text"]
    assert "亲爱的过去的你：" not in payload["text"]
