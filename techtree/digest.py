"""What moved on the tree since the last snapshot. Markdown out."""
from __future__ import annotations
from .model import load_tree, previous_snapshot


def build(tree: dict | None = None) -> str:
    tree = tree or load_tree()
    prev = previous_snapshot(tree["generated_at"])
    by_id = {n["id"]: n for n in tree["nodes"]}
    lines = [f"# Tech tree digest: {tree['sector']['name']}", f"_{tree['generated_at']}_", ""]
    if not prev:
        lines.append("First run, no previous snapshot. Everything below is new.")
    moved = []
    for n in tree["nodes"]:
        old = (prev or {}).get("nodes", {}).get(n["id"], {"evidence": [], "momentum": {"recent_90": 0}})
        new_ev = [e for e in n["evidence"] if e["id"] not in set(old["evidence"])]
        if new_ev:
            moved.append((len(new_ev), n, new_ev))
    moved.sort(key=lambda t: (-t[0], t[1]["label"]))
    lines.append(f"## What moved ({len(moved)} nodes)")
    if not moved:
        lines.append("Nothing new since last snapshot.")
    for count, n, new_ev in moved[:12]:
        lines.append(f"\n### {n['label']}  [{n['status']}]  +{count}")
        for e in new_ev[:3]:
            who = ", ".join(a["name"] for a in e.get("authors", [])[:3]) or (e.get("extra") or {}).get("recipient", "")
            amt = (e.get("extra") or {}).get("amount")
            tail = f"  (${amt:,.0f})" if amt else ""
            lines.append(f"- {e.get('date','')}: {e['title']}{tail}  \n  {who}  \n  {e['url']}")
    prev_people = (prev or {}).get("people", {})
    new_people = [p for p in tree["people"] if p["key"] not in prev_people and p["score"] >= 1.0][:10]
    lines.append(f"\n## New people worth a look ({len(new_people)})")
    for p in new_people:
        nodes = ", ".join(by_id[k]["label"] for k in p["nodes"][:2])
        inst = ", ".join(p["institutions"][:1]) or "no institution on record"
        flag = "  spinout-signal" if p.get("spinout_signal") else ""
        lines.append(f"- {p['name']} ({inst}) on {nodes}. Latest {p['latest']}. Score {p['score']}.{flag}")
    blocked = [n for n in tree["nodes"] if n["status"] == "blocked"]
    lines.append("\n## Blocked nodes, by momentum")
    for n in sorted(blocked, key=lambda n: -n["momentum"]["recent_90"]):
        m = n["momentum"]
        lines.append(f"- {n['label']}: {m['recent_90']} items in last 90d (prior 90d: {m['prior_90']})")
    return "\n".join(lines)
