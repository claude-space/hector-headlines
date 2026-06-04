import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_APP_TOKEN = os.getenv("SLACK_APP_TOKEN")

BQ_PROJECT = "data-science-458422"
BQ_DATASET = "pubinsights_consum_data"

BRANDS = {
    "CL":  f"`{BQ_PROJECT}.{BQ_DATASET}.screen_CL_new_article_analysis`",
    "CBR": f"`{BQ_PROJECT}.{BQ_DATASET}.screen_CBR_new_article_analysis`",
    "MW":  f"`{BQ_PROJECT}.{BQ_DATASET}.screen_MW_new_article_analysis`",
    "SR":  f"`{BQ_PROJECT}.{BQ_DATASET}.screen_SR_new_article_analysis`",
}

MIN_SESSIONS = 10000
LOOKBACK_DAYS = 7

DIGEST_HOUR = 10   # 10am daily digest
