import json, sys
from pathlib import Path

STOPWORDS = {
    "and","the","or","in","a","an","of","for","to","with","who","is","at","on",
    "how","what","why","when","where","which","do","does","can","could","should",
    "would","will","from","by","be","as","it","its","this","that","are","was",
    "were","been","have","has","had","not","but","if","so","also","about","up",
    "out","he","his","she","her","they","their","we","our","i","my","me","you",
    "your","its","into","than","more","most","some","all","use","using","used",
    "playing","visiting","watching","exploring","pursuing","enjoying","often",
    "frequently","engaging","participating","related","based","new","top","best",
    "latest","recent","popular","free","easy","simple","guide","tips","tricks",
    "ideas","list","ways","make","get","find","learn","start","improve","become",
    "2024","2025","2026","june","july","august","january","february","march",
    "april","may","october","november","december","ho","chi","minh","city",
    "vietnam","vietnamese",
}

def _normalize(word: str) -> str:
    """Strip common suffixes to handle plural/verb forms (e.g. museums->museum)."""
    for suffix in ("ing", "ies", "es", "s"):
        if word.endswith(suffix) and len(word) - len(suffix) >= 3:
            return word[: -len(suffix)]
    return word

def _extract_keywords(persona: dict) -> set:
    # Only use the most specific fields — broad paragraph fields (online_behavior,
    # information_needs) make every GPT-generated search match trivially.
    keywords = set()
    text_fields = [
        persona.get("occupation", ""),
        " ".join(persona.get("interests", [])),
        " ".join(persona.get("hobbies", [])),
    ]
    for text in text_fields:
        for word in text.lower().replace("-", " ").split():
            norm = _normalize(word)
            keywords.add(word)
            keywords.add(norm)
    return keywords - STOPWORDS

def evaluate(pid: str) -> dict:
    persona = json.loads(Path(f"personas/persona_{pid}.json").read_text(encoding="utf-8"))
    script  = json.loads(Path(f"personas/activity_{pid}.json").read_text(encoding="utf-8"))

    keywords = _extract_keywords(persona)

    searches   = [a["search_term"] for a in script if a.get("activity") == "google_search"]
    folders    = [a["folder_name"] for a in script if a.get("activity") == "create_folder"]
    documents  = [a["file_name"]   for a in script if a.get("activity") == "create_text_document"]
    downloads  = [(a["url"], a["file_name"]) for a in script if a.get("activity") == "download_file"]
    deletions  = [a["file_name"]   for a in script if a.get("activity") == "delete_file"]

    details = []
    for term in searches:
        raw_words = term.lower().replace("?","").split()
        matched = sorted({w for w in raw_words if {w, _normalize(w)} & keywords})
        details.append({"term": term, "matched": matched, "score": 1 if matched else 0})

    avg = sum(d["score"] for d in details) / max(len(details), 1)
    report = {
        "persona":             persona.get("name"),
        "total_searches":      len(searches),
        "coherence_score_pct": round(avg*100, 1),
        "details":             details,
        "folders_created":     folders,
        "documents_saved":     documents,
        "files_downloaded":    [{"url": u, "saved_as": f} for u, f in downloads],
        "files_deleted":       deletions,
    }

    out = Path(f"results/coherence_{pid}.json")
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return report

def print_report(r):
    print(f"\n{'-'*56}\n{r['persona']}")
    print(f"Searches : {r['total_searches']}  |  Coherence: {r['coherence_score_pct']}%")
    if r.get("folders_created"):
        print(f"Folders  : {', '.join(r['folders_created'])}")
    if r.get("documents_saved"):
        print(f"Docs     : {', '.join(r['documents_saved'])}")
    if r.get("files_downloaded"):
        for dl in r["files_downloaded"]:
            print(f"Download : {dl['saved_as']}  <- {dl['url'][:55]}")
    if r.get("files_deleted"):
        print(f"Deleted  : {', '.join(r['files_deleted'])}")
    print()
    for d in r["details"]:
        print(f"  {'[OK]' if d['matched'] else '[--]'} {d['term'][:48]:48s} {d['matched']}")

if __name__ == "__main__":
    ids = sys.argv[1:] or [
        p.stem.replace("persona_", "")
        for p in sorted(Path("personas").glob("persona_*.json"))
    ]
    if not ids:
        sys.exit("[ERROR] No persona_*.json found in personas/")
    reports = [evaluate(pid) for pid in ids]
    for r in reports: print_report(r)
    if len(reports) == 2:
        print(f"\n{'='*56}\n{'So sánh':^56}\n{'='*56}")
        for r in reports:
            print(f"  {r['persona'][:22]:22s} {r['coherence_score_pct']:5.1f}%  "
                  f"{'#'*int(r['coherence_score_pct']/4)}")