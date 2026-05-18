import csv, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
import config

def translate(pid: str):
    src = Path(f"personas/activity_{pid}.json")
    dst = Path(f"vm_scripts/vm_script_{pid}.csv")
    dst.parent.mkdir(exist_ok=True)

    items = json.loads(src.read_text(encoding="utf-8"))
    rows  = [["timestamp", "command", "arg1", "arg2"]]
    browser_open = False

    for item in items:
        t, act = item["time"], item["activity"]

        if act == "computer_on":
            rows.append([t, "start_computer",   "",                 ""])
            rows.append([t, "login_user",        config.GUEST_PASS, ""])
            browser_open = False

        elif act == "computer_off":
            rows.append([t, "shutdown_computer", "", ""])
            browser_open = False

        elif act == "google_search":
            cmd = "firefox_first_search" if not browser_open else "firefox_new_search"
            rows.append([t, cmd, item["search_term"], ""])
            browser_open = True

        elif act == "create_text_document":
            rows.append([t, "create_text_file",
                         item["file_name"],
                         item.get("content", "").replace("\n", "\\n")])

    with dst.open("w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows(rows)
    print(f"[OK] {len(rows)-1} commands → {dst}")

if __name__ == "__main__":
    translate("khoa")
    translate("phuc")