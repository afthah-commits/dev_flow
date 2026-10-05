with open('backend/tests/test_delivery.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('assert "explanations" in readiness', 'assert "checks" in readiness\n    assert "ready" in readiness\n    assert "score" in readiness')

with open('backend/tests/test_delivery.py', 'w', encoding='utf-8') as f:
    f.write(text)
