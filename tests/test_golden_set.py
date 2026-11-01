# ============================================================================
# tests/test_golden_set.py – Runs the Assistant Golden Set in CI
# ============================================================================
import json
from pathlib import Path
import pytest
from src.assistant import ask

GOLDEN_SET_PATH = Path(__file__).parent.parent / 'data' / 'golden_set.json'

@pytest.fixture(scope="module")
def golden_set():
    with open(GOLDEN_SET_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)['questions']

def test_golden_set_tool_choice(golden_set):
    """
    Evaluate the assistant's tool-choice accuracy and refusal rate.
    This satisfies the requirement to run the tool-choice portion in CI.
    """
    tool_correct = 0
    tool_total = 0
    refusal_correct = 0
    refusal_total = 0

    for q in golden_set:
        response = ask(
            question=q['question'],
            provider="rule",
            language=q.get('language', 'en')
        )

        # 1. Check Tool Choice
        expected_tool = q.get('expected_tool')
        if expected_tool is not None:
            tool_total += 1
            if response.tool_used == expected_tool:
                tool_correct += 1

        # 2. Check Refusal (for out-of-scope questions)
        must_refuse = q.get('must_refuse', False)
        if must_refuse:
            refusal_total += 1
            if response.refused:
                refusal_correct += 1

    # Calculate accuracies
    tool_accuracy = (tool_correct / tool_total) * 100 if tool_total > 0 else 0
    refusal_rate = (refusal_correct / refusal_total) * 100 if refusal_total > 0 else 0

    print(f"\nTool-choice accuracy: {tool_accuracy:.1f}%")
    print(f"Refusal rate: {refusal_rate:.1f}%")

    # Assert targets (we got 100% locally, so 90% is a safe CI threshold)
    assert tool_accuracy >= 90.0, f"Tool-choice accuracy too low: {tool_accuracy}%"
    assert refusal_rate == 100.0, f"Refusal rate too low: {refusal_rate}%"