"""
training/evaluate.py - Automated Benchmark Evaluator for AI Voice Personas.
Tests model outputs for latency-readiness (word count <= 25), Hindi/Hinglish tone,
curriculum progression, and memory recall.
"""

import sys
import json
from typing import List, Dict, Tuple

if sys.platform == "win32":
    import io
    if hasattr(sys.stdout, "buffer"):
        try:
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        except Exception:
            pass


BENCHMARK_PROMPTS = [
    {
        "id": "abc_step_a",
        "description": "Alphabet A-to-Z initial step",
        "input": "Mujhe padhai karni hai, ABCD sikhao.",
        "expected_keywords": ["A", "Apple"],
        "any_of_keywords": ["Bolo", "shuru", "padhein"],
        "max_words": 25,
    },
    {
        "id": "abc_step_praise",
        "description": "Praise and advance to next letter",
        "input": "A!",
        "any_of_keywords": ["Shabash", "star", "waah", "badhiya"],
        "expected_keywords": ["B", "Ball"],
        "max_words": 25,
    },
    {
        "id": "boredom_handling",
        "description": "Switch gracefully when child is bored",
        "input": "Mujhe ab nahi padhna, main bore ho gaya.",
        "any_of_keywords": ["khel", "paheli", "kahani", "break", "chalo", "masti"],
        "max_words": 30,
    },
    {
        "id": "family_memory_inquiry",
        "description": "Address known parent without asking for their name again",
        "input": "Papa office se aa gaye!",
        "expected_keywords": ["Papa"],
        "forbidden_phrases": ["unka kya naam hai", "papa ka naam kya hai", "naam batao", "kaun hain"],
        "max_words": 25,
    },
]


def evaluate_response(test_case: Dict, response: str) -> Tuple[bool, List[str]]:
    """Evaluates an AI reply against voice and behavioral criteria."""
    issues = []
    words = response.strip().split()
    word_count = len(words)

    # 1. Voice Latency Check (Keep responses short so TTS finishes under 2-3 seconds)
    if word_count > test_case.get("max_words", 25):
        issues.append(f"Too verbose for voice: {word_count} words (max {test_case['max_words']})")

    # 2. Expected keywords (all must match if list of strings)
    for kw in test_case.get("expected_keywords", []):
        if kw.lower() not in response.lower():
            issues.append(f"Missing expected keyword: '{kw}'")

    # 2b. Any-of keywords (at least one must match)
    if "any_of_keywords" in test_case:
        matched_any = any(kw.lower() in response.lower() for kw in test_case["any_of_keywords"])
        if not matched_any:
            issues.append(f"Missing concept: Must include at least one of {test_case['any_of_keywords']}")

    # 3. Forbidden phrases (e.g. asking for already known names)
    for forbidden in test_case.get("forbidden_phrases", []):
        if forbidden.lower() in response.lower():
            issues.append(f"Used forbidden phrase (memory failure): '{forbidden}'")

    passed = len(issues) == 0
    return passed, issues


def run_benchmark(test_cases: List[Dict], mock_responses: Dict[str, str]) -> Dict:
    results = {}
    passed_count = 0

    for tc in test_cases:
        tc_id = tc["id"]
        resp = mock_responses.get(tc_id, "")
        passed, issues = evaluate_response(tc, resp)
        if passed:
            passed_count += 1
        results[tc_id] = {
            "passed": passed,
            "issues": issues,
            "response": resp,
        }

    score = (passed_count / len(test_cases)) * 100 if test_cases else 0
    print(f"\n==========================================")
    print(f"📊 Benchmark Score: {score:.1f}% ({passed_count}/{len(test_cases)} Passed)")
    print(f"==========================================")
    for tc_id, data in results.items():
        status = "✅ PASS" if data["passed"] else "❌ FAIL"
        print(f"[{status}] {tc_id}: {data['issues'] if data['issues'] else 'Perfect'}")
    return {"score": score, "details": results}


if __name__ == "__main__":
    # Self-test with sample ideal responses
    sample_responses = {
        "abc_step_a": "Yay! Chalo shuru karte hain! Bolo 'A'! A for Apple! Meetha meetha seb! Ab bolo 'A'!",
        "abc_step_praise": "Shabash champ! Ye mila ek golden star! Ab agla letter hai 'B'! B for Bouncy Ball! Bolo 'B'!",
        "boredom_handling": "Arey re! Padhai break! Chalo ek mazedaar paheli poochti hoon!",
        "family_memory_inquiry": "Arey waah, Papa aa gaye! Unko paani dijiye aur puchiye aaj ka din kaisa raha!",
    }
    run_benchmark(BENCHMARK_PROMPTS, sample_responses)
