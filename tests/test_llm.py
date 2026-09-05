from app.llm import _load_json


def test_load_json_accepts_strict_json():
    assert _load_json('{"answer": true}') == {"answer": True}


def test_load_json_accepts_fenced_tool_output():
    output = '```json\n{"answer": true}\n```'
    assert _load_json(output) == {"answer": True}
