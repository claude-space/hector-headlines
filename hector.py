import threading
import schedule
import time
from config import DIGEST_HOUR
from bigquery_client import fetch_headlines
from analyzer import get_frameworks
from slack_bot import post_digest, start as start_slack, FRAMEWORKS_CACHE


def run_digest():
    print("Running daily digest...")
    headlines = fetch_headlines()
    frameworks = get_frameworks(headlines)
    print("\n" + "=" * 60)
    print(frameworks)
    print("=" * 60)
    post_digest(frameworks)
    print("Digest posted to Slack.")


def scheduler_loop():
    schedule.every().day.at(f"{DIGEST_HOUR:02d}:00").do(run_digest)
    print(f"Scheduler started — digest will run daily at {DIGEST_HOUR:02d}:00.")
    while True:
        schedule.run_pending()
        time.sleep(30)


if __name__ == "__main__":
    import sys

    if "--now" in sys.argv:
        # Run the digest immediately (useful for testing)
        run_digest()
    else:
        if not FRAMEWORKS_CACHE.exists():
            print("No cached frameworks — running digest now...")
            threading.Thread(target=run_digest, daemon=True).start()
        else:
            print("Cached frameworks loaded — skipping startup digest.")

        # Start scheduler in background
        threading.Thread(target=scheduler_loop, daemon=True).start()

        # Start Slack bot (blocking)
        print("Starting Hector Slack bot...")
        start_slack()
