from meshcfo_control_tower.llm import parse_json_content


def test_parse_strips_think_and_fence():
    raw = """<think>scratchpad</think>
```json
{"board_line": "Remediate cutoff before the next 10-Q."}
```
"""
    assert parse_json_content(raw)["board_line"].startswith("Remediate")
