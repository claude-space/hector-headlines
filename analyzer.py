import anthropic
from config import ANTHROPIC_API_KEY

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

FRAMEWORK_PROMPT = """You are analyzing Valnet article headlines that achieved 10,000+ sessions in the last 7 days.
Extract reusable headline FRAMEWORKS grouped by category. Use placeholders like (Streamer), (Show), (Actor), (Genre), (Number), (Franchise), (Type of Content), (Adjective).

The headlines are split into three groups:

--- LIST HEADLINES (ContentType = List or Long List) ---
{list_headlines}

--- INTERVIEW HEADLINES (ContentType = Interview) ---
{interview_headlines}

--- REVIEW HEADLINES (ContentType = Review) ---
{review_headlines}

--- ALL OTHER HEADLINES (no list, no interview, no review, no video) ---
{other_headlines}

Categories and their rules:
1. LIST — use ONLY LIST HEADLINES. Listicles, countdowns, rankings.
2. EVERGREEN PERFORMANCE — use ONLY OTHER HEADLINES. Articles championing a specific show or movie with NO current news hook. The article exists purely because the content is good/notable. Includes streaming recommendations, "X years later this is perfect for fans", evergreen quality praise, and writer-led opinions about a show/movie's greatness. IMPORTANT: only include a headline here if the writer — not the actor/director — is making the claim. Extract 6-7 frameworks if there are enough qualifying headlines.
3. BREAKING — use ONLY OTHER HEADLINES. Headlines driven by a current news event: casting announcements, first looks, season renewals/cancellations, spinoff confirmations, official studio/network reveals. Must have a real-world trigger event.
4. CHARTS — use ONLY OTHER HEADLINES. Strictly about numbers and platform movement: box office figures, streaming chart positions, shows/movies arriving on or leaving a platform, subscriber/service changes, comeback surges driven by data. Do NOT include decisions, announcements, cancellations or renewals — those belong in BREAKING even if they reference numbers.
5. AUTHORITY — use ONLY INTERVIEW HEADLINES plus OTHER HEADLINES where the actor or director themselves is the direct source — they said, confirmed, revealed, or regretted something. The journalist is reporting words that came out of the talent's mouth. Do NOT include headlines where the writer is making a claim about talent (e.g. "X proved they play one of franchise's greatest characters" — that is the writer's opinion, not the talent speaking).
6. MUSIC — use ONLY OTHER HEADLINES from the CL brand that are clearly about music: albums, songs, tours, artists, chart positions, music streaming, or music-related news. Extract 1-3 frameworks only if qualifying CL music headlines exist — skip this category entirely if there are none.
7. REVIEWS — use ONLY REVIEW HEADLINES. Critical assessments of films, shows, or albums. Extract 1-2 frameworks only if qualifying headlines exist — skip this category entirely if there are none.

Rules:
- Extract 5 frameworks per category (6-7 for LIST and EVERGREEN PERFORMANCE if data supports it), 1-3 for MUSIC, 1-2 for REVIEWS — only if qualifying headlines exist
- No overlap: a headline can only appear in one category
- Frameworks only — no actual titles, no session numbers
- Use (Type of Content) as a placeholder for movies/series/shows/anime etc.
- Every framework must be under 100 characters including placeholders
- Follow AP headline style: capitalize the first word and all major words; lowercase articles (a, an, the), coordinating conjunctions (and, but, or, nor, for, so, yet), and prepositions of 3 letters or fewer (at, by, for, in, of, on, to, up) unless they start the headline; use present tense for recent events; no periods at the end
- Never use em dashes (—) in any framework; use a comma instead

Format exactly like this (bold category names, dash-prefixed frameworks, nothing else):

*LIST*
- (Number) (Adjective) (Genre) (Type of Content) That No One Remembers Today
- (Number) (Superlative) (Franchise) Characters, Ranked

*EVERGREEN PERFORMANCE*
- ...

*BREAKING*
- ...

*CHARTS*
- ...

*AUTHORITY*
- ...

*MUSIC* (only if qualifying headlines exist — omit section entirely if none)
- ...

*REVIEWS* (only if qualifying headlines exist — omit section entirely if none)
- ...
"""

SUGGEST_PROMPT = """You are Hector, a headline strategy assistant for Valnet editorial teams.

An editor has described a story. Your job is to:
1. Identify which headline category it belongs to (LIST, EVERGREEN PERFORMANCE, BREAKING, CHARTS, or AUTHORITY)
2. Explain briefly why it fits that category
3. Suggest 5 specific headline options for their story using proven frameworks

Category definitions:
- LIST: Listicles, countdowns, rankings
- EVERGREEN PERFORMANCE: Writer-led opinion piece about a show/movie's quality — no current news hook
- BREAKING: Current news event: casting, renewals, cancellations, first looks, official reveals
- CHARTS: Pure numbers/platform movement: box office, streaming positions, arrivals/departures from platforms
- AUTHORITY: Talent is the direct source — actor/director said, confirmed, revealed, or regretted something
- MUSIC: Music-focused story — albums, artists, tours, chart positions, music news
- REVIEWS: Critical assessment of a film, show, or album

AP headline style rules (apply to every headline you write):
- Capitalize the first word and all major words
- Lowercase: articles (a, an, the), coordinating conjunctions (and, but, or, nor, for, so, yet), prepositions of 3 letters or fewer (at, by, in, of, on, to, up) — unless they start the headline
- Use present tense for recent past actions
- No periods at the end
- Never use em dashes (—); use a comma instead
- Every headline must be under 100 characters

Today's top-performing headline frameworks (for reference):
{frameworks}

{feedback_section}

Editor's story:
{story}

Respond in this format:

*Category:* [CATEGORY NAME]
*Why:* [1-2 sentence explanation]

*Headline suggestions:*
1. [headline]
2. [headline]
3. [headline]
4. [headline]
5. [headline]
"""


def get_frameworks(headlines: dict) -> str:
    prompt = FRAMEWORK_PROMPT.format(
        list_headlines=headlines["list"],
        interview_headlines=headlines["interview"],
        review_headlines=headlines["review"],
        other_headlines=headlines["other"],
    )
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text.replace("—", ",")


def suggest_headlines(story: str, frameworks: str, feedback_context: str = "") -> str:
    if feedback_context:
        feedback_section = (
            "Editor feedback on past headlines (use this to improve your suggestions):\n"
            + feedback_context
        )
    else:
        feedback_section = ""

    prompt = SUGGEST_PROMPT.format(
        frameworks=frameworks,
        story=story,
        feedback_section=feedback_section,
    )
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text.replace("—", ",")
