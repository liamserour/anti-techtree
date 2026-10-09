"""Build and score the tree. Pure functions over JSON, no database."""
from __future__ import annotations
import hashlib, json, re
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

DATA = Path("data")
TREE = DATA / "tree.json"
SNAPSHOTS = DATA / "snapshots"
SECTORS = DATA / "sectors"

ALLIED = {"US","CA","GB","AU","NZ","FR","DE","IT","ES","NL","BE","DK","NO","SE","FI","PL","PT","CZ","GR","TR","RO","HU","SK","SI","HR","BG","EE","LV","LT","LU","IS","AL","ME","MK","IE","AT","CH","JP","KR","IL","TW","SG"}
STATUS_ORDER = {"solved": 0, "near": 1, "emerging": 2, "blocked": 3}
POSITION_W = {"first": 1.0, "last": 0.8, "middle": 0.4, None: 0.5}


def load_sector(sector_id: str) -> dict:
    return json.loads((SECTORS / f"{sector_id}.json").read_text())


def load_tree() -> dict:
    return json.loads(TREE.read_text())


def evidence_id(e: dict) -> str:
    key = re.sub(r"\W+", "", (e.get("title") or "").lower())[:80] + "|" + (e.get("source") or "")
    return hashlib.sha1(key.encode()).hexdigest()[:12]


def person_key(a: dict) -> str:
    if a.get("id"):
        return a["id"].rsplit("/", 1)[-1]
    return "n:" + re.sub(r"\W+", "", (a.get("name") or "").lower())


def recency_weight(d: str, today: date) -> float:
    if not d:
        return 0.2
    try:
        age = (today - date.fromisoformat(d[:10])).days
    except ValueError:
        return 0.2
    if age <= 90:
        return 1.0
    if age <= 365:
        return 0.6
    return 0.3


def assemble(sector: dict, raw: dict[str, list[dict]], today: date | None = None, counts: dict | None = None) -> dict:
    """raw maps node_id -> list of evidence from collectors; counts maps node_id -> {recent_90, prior_90}
    (true per-window counts from the index, independent of the sample size). Returns the tree document."""
    counts = counts or {}
    today = today or date.today()
    nodes_out, people = [], {}
    seen_titles: dict[str, str] = {}
    for n in sector["nodes"]:
        ev_map: dict[str, dict] = {}
        for e in raw.get(n["id"], []):
            eid = evidence_id(e)
            tkey = re.sub(r"\W+", "", (e.get("title") or "").lower())[:80]
            # prefer openalex over arxiv copy of the same paper (it carries institutions)
            if tkey in seen_titles and seen_titles[tkey] != eid and e["source"] == "arxiv":
                continue
            seen_titles[tkey] = eid
            e = {**e, "id": eid, "node": n["id"]}
            ev_map[eid] = e
        evidence = sorted(ev_map.values(), key=lambda x: x.get("date") or "", reverse=True)
        cutoff_recent = (today - timedelta(days=90)).isoformat()
        cutoff_prior = (today - timedelta(days=180)).isoformat()
        c = counts.get(n["id"])
        if c:
            recent, prior = c["recent_90"], c["prior_90"]
        else:  # fall back to counting the sample
            recent = sum(1 for e in evidence if (e.get("date") or "") >= cutoff_recent)
            prior = sum(1 for e in evidence if cutoff_prior <= (e.get("date") or "") < cutoff_recent)
        money = sum(float((e.get("extra") or {}).get("amount") or 0) for e in evidence)
        for e in evidence:
            for a in e.get("authors", []):
                if not a.get("name"):
                    continue
                k = person_key(a)
                p = people.setdefault(k, {"key": k, "name": a["name"], "institutions": [], "ids": {}, "nodes": [], "evidence": [], "score": 0.0, "latest": "", "first_author": 0, "country": a.get("country")})
                if a.get("institution") and a["institution"] not in p["institutions"]:
                    p["institutions"].append(a["institution"])
                if a.get("id"):
                    p["ids"]["openalex"] = a["id"]
                if a.get("orcid"):
                    p["ids"]["orcid"] = a["orcid"]
                if n["id"] not in p["nodes"]:
                    p["nodes"].append(n["id"])
                if e["id"] not in p["evidence"]:
                    p["evidence"].append(e["id"])
                    w = recency_weight(e.get("date", ""), today) * POSITION_W.get(a.get("position"), 0.5)
                    # work on blocked/near nodes is worth more than work on solved ones
                    w *= {"blocked": 1.3, "near": 1.0, "emerging": 1.1, "solved": 0.5}[n["status"]]
                    p["score"] += w
                    if a.get("position") == "first":
                        p["first_author"] += 1
                    p["latest"] = max(p["latest"], e.get("date") or "")
                if a.get("institution_type") == "education":
                    p["academic"] = True
                if a.get("country") and not p.get("country"):
                    p["country"] = a["country"]
        nodes_out.append({**n, "evidence": evidence, "momentum": {"recent_90": recent, "prior_90": prior, "delta": recent - prior, "funding_usd": round(money), "counted": bool(c)}})
    for p in people.values():
        p["score"] = round(p["score"], 2)
        p["allied"] = (p.get("country") or "") in ALLIED
        p["spinout_signal"] = bool(p.get("academic")) and p["first_author"] >= 1 and any(
            STATUS_ORDER[_status(sector, nid)] >= 1 for nid in p["nodes"])
    ranked = sorted(people.values(), key=lambda p: (-p["score"], p["name"]))
    return {
        "sector": {k: sector[k] for k in ("id", "name", "thesis", "root") } | {"roots": sector.get("roots", [sector["root"]])},
        "generated_at": today.isoformat(),
        "nodes": nodes_out,
        "people": ranked,
        "stats": {"nodes": len(nodes_out), "evidence": sum(len(n["evidence"]) for n in nodes_out), "people": len(ranked)},
    }


def _status(sector: dict, nid: str) -> str:
    return next(n["status"] for n in sector["nodes"] if n["id"] == nid)


def save_tree(tree: dict) -> None:
    TREE.write_text(json.dumps(tree, indent=1, ensure_ascii=False))
    SNAPSHOTS.mkdir(exist_ok=True)
    (SNAPSHOTS / f"{tree['generated_at']}.json").write_text(json.dumps(_snapshot(tree)))


def _snapshot(tree: dict) -> dict:
    return {"generated_at": tree["generated_at"],
            "nodes": {n["id"]: {"status": n["status"], "evidence": [e["id"] for e in n["evidence"]], "momentum": n["momentum"]} for n in tree["nodes"]},
            "people": {p["key"]: p["score"] for p in tree["people"]}}


def previous_snapshot(before: str) -> dict | None:
    if not SNAPSHOTS.exists():
        return None
    files = sorted(f for f in SNAPSHOTS.glob("*.json") if f.stem < before)
    return json.loads(files[-1].read_text()) if files else None
