from google.cloud import bigquery
from config import BQ_PROJECT, BRANDS, MIN_SESSIONS, LOOKBACK_DAYS

MIN_SESSIONS_MUSIC_REVIEWS = 7000

client = bigquery.Client(project=BQ_PROJECT)

def _union_all():
    parts = []
    for brand, table in BRANDS.items():
        parts.append(
            f'SELECT ArticleTitle, "{brand}" as Brand, ActSess, PubDatetime, ContentType '
            f'FROM {table}'
        )
    return "\n  UNION ALL\n  ".join(parts)

def _base_query(content_type_filter: str, min_sessions: int = MIN_SESSIONS) -> str:
    return f"""
SELECT ArticleTitle, Brand, ActSess
FROM (
  {_union_all()}
) t
WHERE ActSess >= {min_sessions}
AND PubDatetime >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {LOOKBACK_DAYS} DAY)
AND {content_type_filter}
ORDER BY ActSess DESC
"""

LIST_FILTER = "ContentType IN ('List', 'Long List')"
INTERVIEW_FILTER = "ContentType = 'Interview'"
REVIEW_FILTER = "ContentType = 'Review'"
OTHER_FILTER = "ContentType NOT IN ('List', 'Long List', 'Interview', 'Review', 'Video', 'Video Feature', 'List Video', 'Video News')"


def _run(query: str) -> str:
    rows = client.query(query).result()
    return "\n".join([f"{r.ArticleTitle},{r.Brand},{r.ActSess}" for r in rows])


def fetch_headlines() -> dict:
    print("Fetching LIST headlines...")
    lists = _run(_base_query(LIST_FILTER))
    print("Fetching INTERVIEW headlines...")
    interviews = _run(_base_query(INTERVIEW_FILTER))
    print("Fetching REVIEW headlines...")
    reviews = _run(_base_query(REVIEW_FILTER, min_sessions=MIN_SESSIONS_MUSIC_REVIEWS))
    print("Fetching OTHER headlines...")
    others = _run(_base_query(OTHER_FILTER))

    print(
        f"List: {len(lists.splitlines())} | "
        f"Interview: {len(interviews.splitlines())} | "
        f"Review: {len(reviews.splitlines())} | "
        f"Other: {len(others.splitlines())}"
    )
    return {"list": lists, "interview": interviews, "review": reviews, "other": others}
