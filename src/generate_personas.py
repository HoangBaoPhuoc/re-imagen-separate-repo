"""
Gọi GPT-4o API để tự động tạo persona + activity script cho Khoa và Phúc.
Chạy một lần. Output lưu vào personas/
"""
import json, sys
from pathlib import Path
from openai import OpenAI
sys.path.insert(0, str(Path(__file__).parent.parent))
import config

client = OpenAI(api_key=config.OPENAI_API_KEY)

SEEDS = [
    {
        "id": "khoa",
        "seed": {
            "name": "Huynh Dang Khoa",
            "age": 22,
            "location": "Ho Chi Minh City, Vietnam",
            "occupation": "Undergraduate student, Computer Science (UIT)",
            "institution": "University of Information Technology (UIT)",
            "language": "Vietnamese (native), English (intermediate)",
        },
        "schedule": "Saturday June 14 2025, 20:00–23:00 (UTC+7)",
        "doc_count": 1,
    },
    {
        "id": "phuc",
        "seed": {
            "name": "Chau Hoang Phuc",
            "age": 23,
            "location": "Ho Chi Minh City, Vietnam",
            "occupation": "Undergraduate student, History (UIT)",
            "institution": "University of Information Technology (UIT)",
            "language": "Vietnamese (native), English (basic)",
        },
        "schedule": "Sunday June 15 2025, 19:30–22:30 (UTC+7)",
        "doc_count": 2,
    },
]

PERSONA_PROMPT = """Create a computer-user persona from this seed:
{seed}

Output ONLY valid JSON (no markdown fences) with these fields exactly:
- full_name
- name
- age
- gender
- location
- language
- occupation
- institution
- interests (array of short phrases)
- hobbies (array)
- education
- online_behavior (short paragraph)
- information_needs (short list or sentence)
- it_proficiency (one of: none, basic, intermediate, advanced)
- devices (array)
- unique_attributes (array)
- summary

Be creative but realistic. Return only JSON object text with those fields.
"""

ACTIVITY_PROMPT = """Generate a detailed Activity Description Script for the persona below.
Schedule: {schedule}

Persona: {persona}

Rules (strict):
- Output ONLY a valid JSON array (no markdown fences). Each element MUST be an object with at least "time" (ISO8601 with offset) and "activity".
- The first element MUST be a `computer_on` entry at the schedule start time; the last element MUST be a `computer_off` entry at the schedule end time.
- Times MUST include minutes and seconds (e.g. 2025-06-14T20:03:17+07:00).
- Use these activity types and fields:
    - `computer_on` / `computer_off` (no extra fields)
    - `google_search` with field `search_term` (string)
    - `create_text_document` with fields `file_name` and `content` (content may include newlines)
- Exactly 9 `google_search` entries total. Search terms MUST be realistic Google queries and MUST clearly relate to the persona's interests, occupation, or education. Consider the persona's language proficiency when choosing phrasing.
- Exactly {doc_count} `create_text_document` entries with persona-relevant filenames and contents.
- Include occasional multi-step browsing sessions: you may place several `google_search` entries in a row on the same topic to represent a longer session.
- Keep gaps between activities realistic (typically 1–20 minutes). Do not use round-only times.

Return ONLY the JSON array. Example element:
    {{"time": "2025-06-14T20:03:17+07:00", "activity": "google_search", "search_term": "how to set up local webserver windows 10"}}

Remember: no explanatory text, only the JSON array.
"""


def call(prompt: str) -> str:
    r = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.8,
    )
    text = r.choices[0].message.content.strip()
    # strip markdown fences if present
    if text.startswith("```"):
        text = "\n".join(text.split("\n")[1:])
    if text.endswith("```"):
        text = "\n".join(text.split("\n")[:-1])
    return text.strip()


def generate(s: dict):
    pid = s["id"]
    out = Path("personas"); out.mkdir(exist_ok=True)

    print(f"[{pid}] Generating persona...")
    persona = json.loads(call(PERSONA_PROMPT.format(seed=json.dumps(s["seed"], ensure_ascii=False))))
    (out / f"persona_{pid}.json").write_text(
        json.dumps(persona, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[{pid}]  → persona_{pid}.json")

    print(f"[{pid}] Generating activity script...")
    script = json.loads(call(ACTIVITY_PROMPT.format(
        schedule=s["schedule"],
        persona=json.dumps(persona, ensure_ascii=False),
        doc_count=s["doc_count"],
    )))
    (out / f"activity_{pid}.json").write_text(
        json.dumps(script, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[{pid}]  → activity_{pid}.json  ({len(script)} entries)\n")


if __name__ == "__main__":
    for s in SEEDS:
        generate(s)
    print("Done. Check personas/ directory.")