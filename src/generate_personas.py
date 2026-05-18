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
            "occupation": "3rd-year IT student, CTF competitions, cybersecurity",
            "language": "Vietnamese (native), English (intermediate)",
        },
        "schedule": "Saturday June 14 2025, 20:00–23:00 (UTC+7)",
        "doc_count": 1,
    },
    {
        "id": "phuc",
        "seed": {
            "name": "Chau Hoang Phuc",
            "age": 35,
            "location": "Hanoi, Vietnam",
            "occupation": "High school history teacher, Vietnamese history, travel photography",
            "language": "Vietnamese (native), English (basic)",
        },
        "schedule": "Sunday June 15 2025, 19:30–22:30 (UTC+7)",
        "doc_count": 2,
    },
]

PERSONA_PROMPT = """Create a computer-user persona from this seed:
{seed}

Output ONLY valid JSON (no markdown fences) with fields:
name, age, gender, location, language, occupation, interests (array), tech_proficiency, summary."""

ACTIVITY_PROMPT = """Generate a computer Activity Description Script for the persona below.
Schedule: {schedule}

Persona: {persona}

Rules:
- First entry computer_on at schedule start; last entry computer_off at schedule end
- Exactly 9 google_search entries; search terms must clearly match persona interests
- Exactly {doc_count} create_text_document entries with persona-relevant content
- Realistic gaps between activities (5–20 min)

Output ONLY a valid JSON array (no markdown fences). Each element:
  {{"time": "ISO8601+07:00", "activity": "..."}}
google_search adds "search_term". create_text_document adds "file_name" and "content"."""


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