import json, sys
from pathlib import Path

def evaluate(pid: str) -> dict:
    persona = json.loads(Path(f"personas/persona_{pid}.json").read_text(encoding="utf-8"))
    script  = json.loads(Path(f"personas/activity_{pid}.json").read_text(encoding="utf-8"))

    keywords = set()
    for i in persona.get("interests", []):
        keywords.update(i.lower().split())
    keywords.update(persona.get("occupation","").lower().split())
    keywords -= {"and","the","or","in","a","an","of","for","to","with","who","is","at","on"}

    searches = [a["search_term"] for a in script if a.get("activity") == "google_search"]
    details  = []
    for term in searches:
        words   = set(term.lower().replace("?","").split())
        matched = sorted(words & keywords)
        details.append({"term": term, "matched": matched,
                        "score": round(len(matched)/max(len(words),1), 3)})

    avg = sum(d["score"] for d in details) / max(len(details), 1)
    report = {"persona": persona.get("name"), "total_searches": len(searches),
              "coherence_score_pct": round(avg*100, 1), "details": details}

    out = Path(f"results/coherence_{pid}.json")
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return report

def print_report(r):
    print(f"\n{'─'*56}\n{r['persona']}")
    print(f"Searches : {r['total_searches']}")
    print(f"Coherence: {r['coherence_score_pct']}%")
    for d in r["details"]:
        print(f"  {'✓' if d['matched'] else '✗'} {d['term'][:48]:48s} {d['matched']}")

if __name__ == "__main__":
    ids = sys.argv[1:] or ["khoa", "phuc"]
    reports = [evaluate(pid) for pid in ids]
    for r in reports: print_report(r)
    if len(reports) == 2:
        print(f"\n{'═'*56}\n{'So sánh':^56}\n{'═'*56}")
        for r in reports:
            print(f"  {r['persona'][:22]:22s} {r['coherence_score_pct']:5.1f}%  "
                  f"{'█'*int(r['coherence_score_pct']/4)}")