# ============================================================================
# src/evaluate_assistant.py – Evaluate the assistant against the golden set
# ============================================================================

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
from collections import defaultdict

from src.assistant import ask, AssistantResponse


GOLDEN_SET_PATH = Path(__file__).parent.parent / 'data' / 'golden_set.json'
RESULTS_PATH = Path(__file__).parent.parent / 'artifacts' / 'assistant_evaluation.json'


def load_golden_set():
    with open(GOLDEN_SET_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)['questions']


def evaluate():
    print("=" * 60)
    print("Head C – Assistant Evaluation")
    print("=" * 60)

    questions = load_golden_set()
    print(f"\n📋 Loaded {len(questions)} questions")

    results = []
    tool_correct = 0
    tool_total = 0
    refusal_correct = 0
    refusal_total = 0
    grounded_correct = 0
    grounded_total = 0

    for q in questions:
        response = ask(
            question=q['question'],
            provider="rule",
            language=q.get('language', 'en')
        )

        # ---------- Tool-choice accuracy ----------
        expected_tool = q.get('expected_tool')
        if expected_tool is not None:
            tool_total += 1
            if response.tool_used == expected_tool:
                tool_correct += 1
                tool_ok = True
            else:
                tool_ok = False
        else:
            tool_ok = None

        # ---------- Refusal correctness ----------
        must_refuse = q.get('must_refuse', False)
        if must_refuse:
            refusal_total += 1
            if response.refused:
                refusal_correct += 1
                refusal_ok = True
            else:
                refusal_ok = False
        else:
            refusal_ok = None

        # ---------- Groundedness (for policy questions) ----------
        if q['type'] == 'policy_question':
            grounded_total += 1
            if response.grounded and response.citations:
                grounded_correct += 1
                grounded_ok = True
            else:
                grounded_ok = False
        else:
            grounded_ok = None

        results.append({
            'id': q['id'],
            'question': q['question'],
            'type': q['type'],
            'expected_tool': expected_tool,
            'actual_tool': response.tool_used,
            'tool_ok': tool_ok,
            'must_refuse': must_refuse,
            'refused': response.refused,
            'refusal_ok': refusal_ok,
            'grounded': response.grounded,
            'grounded_ok': grounded_ok,
            'provider': response.provider,
            'reason': response.reason
        })

    # ---------- Summary ----------
    tool_acc = (tool_correct / tool_total * 100) if tool_total > 0 else 0
    refusal_rate = (refusal_correct / refusal_total * 100) if refusal_total > 0 else 0
    grounded_rate = (grounded_correct / grounded_total * 100) if grounded_total > 0 else 0

    print("\n" + "=" * 60)
    print("📊 Evaluation Summary")
    print("=" * 60)
    print(f"\n🎯 Tool-choice accuracy: {tool_correct}/{tool_total} = {tool_acc:.1f}%")
    print(f"🚫 Refusal rate (out-of-scope): {refusal_correct}/{refusal_total} = {refusal_rate:.1f}%")
    print(f"📚 Groundedness (policy questions): {grounded_correct}/{grounded_total} = {grounded_rate:.1f}%")

    # ---------- Per-question results ----------
    print("\n" + "=" * 60)
    print("📋 Detailed Results")
    print("=" * 60)
    print(f"\n{'ID':<6}{'Type':<18}{'Tool OK':<10}{'Refused OK':<12}{'Grounded OK':<12}")
    print("-" * 60)
    for r in results:
        t = "✅" if r['tool_ok'] else ("—" if r['tool_ok'] is None else "❌")
        rf = "✅" if r['refusal_ok'] else ("—" if r['refusal_ok'] is None else "❌")
        g = "✅" if r['grounded_ok'] else ("—" if r['grounded_ok'] is None else "❌")
        print(f"{r['id']:<6}{r['type']:<18}{t:<10}{rf:<12}{g:<12}")

    # ---------- Failures ----------
    failures = [r for r in results if
                r['tool_ok'] is False or r['refusal_ok'] is False or r['grounded_ok'] is False]

    if failures:
        print("\n" + "=" * 60)
        print(f"⚠️ {len(failures)} Failures")
        print("=" * 60)
        for r in failures:
            print(f"\n{r['id']}: {r['question']}")
            if r['tool_ok'] is False:
                print(f"   Expected tool: {r['expected_tool']}, got: {r['actual_tool']}")
            if r['refusal_ok'] is False:
                print(f"   Should have refused but did not")
            if r['grounded_ok'] is False:
                print(f"   Should be grounded but was not")
    else:
        print("\n✅ No failures!")

    # ---------- Save results ----------
    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(RESULTS_PATH, 'w', encoding='utf-8') as f:
        json.dump({
            'summary': {
                'total_questions': len(questions),
                'tool_choice_accuracy': round(tool_acc, 2),
                'refusal_rate': round(refusal_rate, 2),
                'groundedness': round(grounded_rate, 2)
            },
            'details': results
        }, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Results saved to {RESULTS_PATH}")
    print("\n✅ Evaluation complete!")


if __name__ == "__main__":
    evaluate()