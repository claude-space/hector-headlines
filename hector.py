import logging
import threading
import time

import schedule

from config import DIGEST_HOUR
from bigquery_client import fetch_headlines
from analyzer import get_frameworks
from slack_bot import post_digest, start as start_slack, FRAMEWORKS_CACHE

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("hector")


def run_digest():
    """Fetch headlines -> derive frameworks -> cache + post to Slack.

    May raise. Callers that must not crash (startup, scheduler) use
    run_digest_safe() instead.
    """
    log.info("Running digest...")
    headlines = fetch_headlines()
    frameworks = get_frameworks(headlines)
    print(frameworks, flush=True)  # visible on `--now` and in the journal
    post_digest(frameworks)
    log.info("Digest complete.")


def run_digest_safe():
    """run_digest() that logs failures instead of propagating them, so a broken
    digest (BigQuery auth, Anthropic error, missing Slack channel) can never
    take the Slack bot down."""
    try:
        run_digest()
    except Exception:
        log.exception(
            "Digest failed - Slack bot stays up; frameworks unchanged until the next run."
        )


def scheduler_loop():
    schedule.every().day.at(f"{DIGEST_HOUR:02d}:00").do(run_digest_safe)
    log.info("Scheduler started - daily digest at %02d:00.", DIGEST_HOUR)
    while True:
        schedule.run_pending()
        time.sleep(30)


if __name__ == "__main__":
    import sys

    if "--now" in sys.argv:
        # Manual / test run: let exceptions surface so the real error is visible.
        run_digest()
    else:
        # The Slack bot is the critical path and must come up regardless of the
        # digest. Run the digest in the BACKGROUND (never blocking, never fatal);
        # frameworks can land a minute later. Until they do, mentions get the
        # graceful "frameworks not loaded yet" reply from slack_bot.handle_mention.
        if FRAMEWORKS_CACHE.exists():
            log.info("Cached frameworks present - bot will serve them immediately.")
        else:
            log.info("No cached frameworks - starting a background digest now.")
            threading.Thread(target=run_digest_safe, daemon=True).start()

        # Daily refresh, in the background.
        threading.Thread(target=scheduler_loop, daemon=True).start()

        # Connect to Slack. This blocks - and it is now the FIRST thing that
        # becomes responsive, independent of whether the digest succeeds.
        log.info("Starting Hector Slack bot...")
        start_slack()
