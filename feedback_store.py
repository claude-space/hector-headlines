import json
from pathlib import Path
from datetime import datetime

FEEDBACK_FILE = Path(__file__).parent / "feedback.json"


def _load() -> list:
    if not FEEDBACK_FILE.exists():
        return []
    with open(FEEDBACK_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _save(entries: list):
    with open(FEEDBACK_FILE, "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2, ensure_ascii=False)


def save_feedback(user: str, headline: str, reason: str, positive: bool):
    entries = _load()
    entries.append({
        "type": "headline",
        "timestamp": datetime.now().isoformat(),
        "user": user,
        "headline": headline,
        "positive": positive,
        "reason": reason,
    })
    _save(entries)


def save_category_feedback(user: str, story: str, correct_category: str, wrong_category: str):
    entries = _load()
    entries.append({
        "type": "category",
        "timestamp": datetime.now().isoformat(),
        "user": user,
        "story": story,
        "correct_category": correct_category.upper(),
        "wrong_category": wrong_category.upper(),
    })
    _save(entries)


def get_feedback_context(limit: int = 20) -> str:
    entries = _load()
    if not entries:
        return ""
    recent = entries[-limit:]
    lines = []
    for e in recent:
        if e.get("type") == "category":
            lines.append(
                f'- [CATEGORY CORRECTION] Story: "{e["story"]}" — '
                f'correct category is {e["correct_category"]}, not {e["wrong_category"]}'
            )
        else:
            sentiment = "GOOD" if e.get("positive") else "BAD"
            lines.append(f'- [{sentiment} HEADLINE] "{e.get("headline", "")}" — {e.get("reason", "")}')
    return "\n".join(lines)
