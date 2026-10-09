"""Facts for the 5-line note. Deliberately not prose: the human writes the note."""
from __future__ import annotations
from .model import load_tree


def facts(query: str, tree: dict | None = None) -> str:
    tree = tree or load_tree()
    q = query.lower()
    hits = [p for p in tree["people"] if q in p["name"].lower()]
    if not hits:
        return f"No person matching '{query}'. Try `techtree people` to list candidates."
    p = hits[0]
    by_id = {n["id"]: n for n in tree["nodes"]}
    ev = {e["id"]: e for n in tree["nodes"] for e in n["evidence"]}
    out = [f"FACTS FOR A NOTE ABOUT: {p['name']}", ""]
    out.append("1. Who:   " + p["name"] + (f", {', '.join(p['institutions'])}" if p["institutions"] else "") + (f"  orcid {p['ids']['orcid']}" if p["ids"].get("orcid") else ""))
    works = [ev[i] for i in p["evidence"] if i in ev]
    works.sort(key=lambda e: e.get("date", ""), reverse=True)
    out.append("2. Why they matter (their recent work):")
    for e in works[:4]:
        out.append(f"      {e.get('date','')}  {e['title']}  {e['url']}")
    out.append("3. Why now:  latest item " + (p["latest"] or "unknown") + "; " + ("first author on " + str(p["first_author"]) + " of these" if p["first_author"] else "co-author"))
    out.append("4. Why Anti Fund should care (the node they are pushing on):")
    for nid in p["nodes"][:2]:
        n = by_id[nid]
        out.append(f"      [{n['status']}] {n['label']}: {n['why']}")
    out.append("5. Your relationship to the opportunity:  <you write this; the tool cannot>")
    out.append("")
    out.append("Write the note yourself, in your own words, under 120 words. Do not paste this output.")
    return "\n".join(out)
