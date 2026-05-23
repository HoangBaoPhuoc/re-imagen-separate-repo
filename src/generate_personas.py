"""
Tạo persona + activity script qua GPT-4o.
Chạy rồi nhập thông tin từng người khi được hỏi.
Output lưu vào personas/
"""
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from openai import OpenAI

sys.path.insert(0, str(Path(__file__).parent.parent))
import config

client = OpenAI(api_key=config.OPENAI_API_KEY)

# -- Prompts ------------------------------------------------------------------------

PERSONA_PROMPT = """Create a computer-user persona from this seed:
{seed}

Output ONLY valid JSON (no markdown fences) with these fields exactly:
- full_name
- name (first name or short name)
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
- information_needs (array of short phrases)
- it_proficiency (one of: none, basic, intermediate, advanced)
- devices (array)
- unique_attributes (array)
- summary

Be creative but realistic. Return only the JSON object, no extra text.
"""

ACTIVITY_PROMPT = """Generate a detailed Activity Description Script for the persona below.
Schedule: {schedule}

Persona: {persona}

Rules (strict):
- Output ONLY a valid JSON array (no markdown fences). Each element MUST be an object
  with at least "time" (ISO8601 with UTC offset) and "activity".
- First element: `computer_on` at schedule start. Last element: `computer_off` at schedule end.
- Times MUST include minutes and seconds (e.g. 2025-06-14T20:03:17+07:00).

Supported activity types:
  - computer_on / computer_off        - no extra fields
  - google_search                     - field: search_term (realistic Google query)
  - create_folder                     - field: folder_name (short, underscores instead of spaces)
  - create_text_document              - fields: file_name (with .txt), content (use \\n for newlines),
                                        folder (must match a previously created folder_name)
  - delete_file                       - field: file_name ("file.txt" on Desktop,
                                        or "FolderName/file.txt" if inside a subfolder)

Quotas:
- 8-10 google_search entries. Terms MUST clearly relate to the persona's interests, occupation, or hobbies.
- Exactly 1 create_folder early in the session (organises the documents the persona saves).
- Exactly {doc_count} create_text_document entries, each with "folder" pointing to the created folder.
- Exactly 1 delete_file to delete one of the created text documents after the persona finishes using it.
- Include multi-step browsing runs (several searches in a row on one topic).
- Keep time gaps realistic (1-20 min). Avoid round-number times.

Example elements:
  {{"time": "2025-06-14T20:05:00+07:00", "activity": "create_folder", "folder_name": "Cyber_Notes"}}
  {{"time": "2025-06-14T20:30:00+07:00", "activity": "create_text_document", "file_name": "cert_plan.txt", "folder": "Cyber_Notes", "content": "1. Study CEH\\n2. Do CTF"}}
  {{"time": "2025-06-14T21:45:00+07:00", "activity": "delete_file", "file_name": "Cyber_Notes/cert_plan.txt"}}

Return ONLY the JSON array. No explanatory text.
"""

# -- Input helpers ------------------------------------------------------------------

def ask(prompt: str, default: str = "") -> str:
    """Hỏi người dùng, cho phép bỏ qua bằng Enter nếu có default."""
    hint = f" [{default}]" if default else ""
    val = input(f"  {prompt}{hint}: ").strip()
    return val if val else default


def ask_int(prompt: str, default: int) -> int:
    while True:
        raw = ask(prompt, str(default))
        try:
            return int(raw)
        except ValueError:
            print("  -> Vui lòng nhập số nguyên.")


def collect_seed() -> dict:
    """Thu thập thông tin một persona từ bàn phím."""
    print()
    pid       = ask("ID ngắn (dùng cho tên file, không dấu, không khoảng trắng)").lower()
    while not pid.isidentifier():
        print("  -> ID chỉ gồm chữ cái, chữ số và dấu gạch dưới.")
        pid = ask("ID ngắn").lower()

    name      = ask("Họ và tên đầy đủ")
    age       = ask_int("Tuổi", 22)
    location  = ask("Địa điểm (thành phố, quốc gia)", "Ho Chi Minh City, Vietnam")
    occupation= ask("Nghề nghiệp / chuyên ngành")
    institution= ask("Trường / tổ chức (bỏ qua nếu không có)", "")
    language  = ask("Ngôn ngữ và mức độ (ví dụ: Vietnamese native, English intermediate)",
                    "Vietnamese (native), English (intermediate)")
    schedule  = ask("Lịch sử dụng máy (ví dụ: Saturday June 14 2025, 20:00-23:00 UTC+7)")
    doc_count = ask_int("Số file text cần tạo trong session", 1)
    dl_url    = ask("URL file cần download (Enter để bỏ qua)", "")
    dl_name   = ask("Tên file lưu (ví dụ: paper.pdf)", "file.pdf") if dl_url else ""

    seed = {
        "name":        name,
        "age":         age,
        "location":    location,
        "occupation":  occupation,
        "language":    language,
    }
    if institution:
        seed["institution"] = institution

    return {"id": pid, "seed": seed, "schedule": schedule, "doc_count": doc_count,
            "dl_url": dl_url, "dl_name": dl_name}


# -- Download injection -------------------------------------------------------------

def inject_download(script: list, url: str, filename: str) -> list:
    """Chèn download_file + delete_file vào trước computer_off."""
    off_idx = next(
        (i for i, e in enumerate(script) if e.get("activity") == "computer_off"),
        len(script),
    )
    base_t = datetime.fromisoformat(script[off_idx - 1]["time"]) if off_idx > 0 else datetime.now().astimezone()
    dl_t  = (base_t + timedelta(minutes=5)).isoformat()
    del_t = (base_t + timedelta(minutes=20)).isoformat()

    script.insert(off_idx, {"time": del_t, "activity": "delete_file",   "file_name": filename})
    script.insert(off_idx, {"time": dl_t,  "activity": "download_file", "url": url, "file_name": filename})
    return script


# -- GPT call -----------------------------------------------------------------------

def call(prompt: str) -> str:
    r = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.8,
    )
    text = r.choices[0].message.content.strip()
    if text.startswith("```"):
        text = "\n".join(text.split("\n")[1:])
    if text.endswith("```"):
        text = "\n".join(text.split("\n")[:-1])
    return text.strip()


# -- Core generate -----------------------------------------------------------------

def generate(s: dict):
    pid = s["id"]
    out = Path("personas")
    out.mkdir(exist_ok=True)

    print(f"\n[{pid}] Đang tạo persona profile...")
    persona = json.loads(call(PERSONA_PROMPT.format(
        seed=json.dumps(s["seed"], ensure_ascii=False)
    )))
    (out / f"persona_{pid}.json").write_text(
        json.dumps(persona, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"[{pid}]  -> personas/persona_{pid}.json")

    print(f"[{pid}] Đang tạo activity script...")
    script = json.loads(call(ACTIVITY_PROMPT.format(
        schedule=s["schedule"],
        persona=json.dumps(persona, ensure_ascii=False),
        doc_count=s["doc_count"],
    )))
    if s.get("dl_url"):
        script = inject_download(script, s["dl_url"], s["dl_name"])
        print(f"[{pid}]  + download_file injected: {s['dl_name']}")
    (out / f"activity_{pid}.json").write_text(
        json.dumps(script, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"[{pid}]  -> personas/activity_{pid}.json  ({len(script)} entries)")


# -- Main --------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 56)
    print(" Re-Imagen - Tạo Persona & Activity Script")
    print("=" * 56)
    print("Nhập thông tin cho từng người dùng cần mô phỏng.")
    print("Gõ Enter để dùng giá trị mặc định [trong ngoặc].\n")

    n = ask_int("Số lượng persona cần tạo", 1)
    seeds = []
    for i in range(1, n + 1):
        print(f"\n-- Persona {i}/{n} " + "-" * 38)
        seeds.append(collect_seed())

    print("\n" + "=" * 56)
    print(f"Bắt đầu gọi GPT-4o cho {len(seeds)} persona...")
    print("=" * 56)

    for s in seeds:
        generate(s)

    print(f"\n[OK] Xong. Kiểm tra thư mục personas/")
    print("Bước tiếp theo: python src/translation.py")
