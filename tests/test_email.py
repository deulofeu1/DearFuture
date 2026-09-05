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
    assert captured["timeout"] == 20
