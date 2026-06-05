import re
import logging
from datetime import date
from pathlib import Path
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from config import SLACK_BOT_TOKEN, SLACK_APP_TOKEN
from analyzer import suggest_headlines
from feedback_store import save_feedback, save_category_feedback, get_feedback_context

logging.basicConfig(level=logging.INFO)

app = App(token=SLACK_BOT_TOKEN)

_current_frameworks: str = ""
FRAMEWORKS_CACHE = Path(__file__).parent / "frameworks_cache.txt"


def set_frameworks(frameworks: str):
    global _current_frameworks
    _current_frameworks = frameworks
    FRAMEWORKS_CACHE.write_text(frameworks, encoding="utf-8")


def _load_cached_frameworks():
    global _current_frameworks
    if FRAMEWORKS_CACHE.exists():
        _current_frameworks = FRAMEWORKS_CACHE.read_text(encoding="utf-8")
        logging.info("Loaded frameworks from cache.")


def post_digest(frameworks: str):
    # Persist + load frameworks FIRST, so suggestions work even if posting to
    # the channel below fails (e.g. #hector-headlines missing, or the bot isn't
    # a member). A posting failure must not look like a digest failure.
    set_frameworks(frameworks)
    today = date.today().strftime("%B %#d, %Y")
    text = (
        f":newspaper: *Hector's Daily Headline Frameworks — {today}*\n\n"
        f"{frameworks}\n\n"
        f"_Tip: mention me with a story description and I'll suggest headlines. "
        f"e.g. `@Hector Jeremy Renner is being cast in a new NBC western`_\n"
        f"_Headline feedback: `@Hector feedback: [headline] — [reason]`_\n"
        f"_Category feedback: `@Hector category: [story] — should be EVERGREEN not AUTHORITY`_"
    )
    try:
        app.client.chat_postMessage(channel="#hector-headlines", text=text)
    except Exception:
        logging.exception(
            "Could not post digest to #hector-headlines "
            "(frameworks are still cached, so suggestions keep working)."
        )


def _parse_feedback(text: str):
    """
    Parses: @Hector feedback: "Some Headline" — reason
    or:     @Hector feedback: Some Headline — reason
    Returns (headline, reason, positive) or None if not a feedback message.
    Positive = True unless reason contains negative keywords.
    """
    match = re.search(r'feedback:\s*"?(.+?)"?\s*[—\-–]\s*(.+)', text, re.IGNORECASE)
    if not match:
        return None
    headline = match.group(1).strip()
    reason = match.group(2).strip()
    negative_words = {"bad", "wrong", "not", "weak", "poor", "off", "avoid", "don't", "shouldn't"}
    positive = not any(w in reason.lower() for w in negative_words)
    return headline, reason, positive


@app.event("app_mention")
def handle_mention(event, say):
    text: str = event.get("text", "")
    user: str = event.get("user", "unknown")

    # Strip mention token
    clean = " ".join(w for w in text.split() if not w.startswith("<@")).strip()

    if not clean:
        say("Hey! Describe a story and I'll suggest headlines, or give feedback on a past headline.")
        return

    # Category correction branch
    cat_match = re.search(r'category:\s*(.+?)\s*[—\-–]\s*should be\s+(\w[\w\s]*?)\s+not\s+(\w[\w\s]*)', clean, re.IGNORECASE)
    if cat_match:
        story = cat_match.group(1).strip()
        correct = cat_match.group(2).strip()
        wrong = cat_match.group(3).strip()
        save_category_feedback(user=user, story=story, correct_category=correct, wrong_category=wrong)
        say(f":memo: Got it — noted that _{story}_ is *{correct.upper()}*, not {wrong.upper()}. I'll use this going forward.")
        return

    # Headline feedback branch
    parsed = _parse_feedback(clean)
    if parsed:
        headline, reason, positive = parsed
        save_feedback(user=user, headline=headline, reason=reason, positive=positive)
        sentiment = "Noted as a good pattern" if positive else "Noted — I'll avoid that pattern"
        say(f":memo: Feedback saved. {sentiment}: _{headline}_")
        return

    # Suggestion branch
    if not _current_frameworks:
        say(
            "I don't have today's frameworks loaded yet — "
            "try again after the 10am digest runs."
        )
        return

    say(f":thinking_face: Working on headline ideas for: _{clean}_")
    feedback_context = get_feedback_context()
    result = suggest_headlines(clean, _current_frameworks, feedback_context)
    say(result)


def start():
    _load_cached_frameworks()
    handler = SocketModeHandler(app, SLACK_APP_TOKEN)
    handler.start()
