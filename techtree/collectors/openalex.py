"""OpenAlex: papers with authors and institutions. Keyless. https://docs.openalex.org

search(): newest matching works, matched on title+abstract (tighter than full text).
count():  how many matching works were published in a date window. Used for momentum.
"""
import json
from datetime import date
from ._http import get

BASE = "https://api.openalex.org/works"
MAILTO = "techtree@users.noreply.github.com"


def _filter(query: str, since: str, until: str | None = None) -> str:
    until = until or date.today().isoformat()
    q = query.replace(",", " ")
    return f"title_and_abstract.search:{q},from_publication_date:{since},to_publication_date:{until}"


def search(query: str, since: str, limit: int = 15) -> list[dict]:
    params = {"filter": _filter(query, since), "sort": "publication_date:desc", "per-page": limit,
              "select": "id,title,publication_date,authorships,primary_location,doi,type", "mailto": MAILTO}
    data = json.loads(get(BASE, params, min_interval=0.5))
    out = []
    for w in data.get("results", []):
        if not w.get("title"):
            continue
        authors = []
        for a in w.get("authorships", []):
            inst = (a.get("institutions") or [{}])[0]
            authors.append({
                "name": a["author"]["display_name"], "id": a["author"]["id"], "orcid": a["author"].get("orcid"),
                "institution": inst.get("display_name"), "institution_type": inst.get("type"),
                "country": inst.get("country_code"), "position": a.get("author_position"),
            })
        loc = w.get("primary_location") or {}
        out.append({
            "kind": "paper", "source": "openalex",
            "title": w["title"], "date": w["publication_date"],
            "url": loc.get("landing_page_url") or w.get("doi") or w["id"],
            "authors": authors,
            "extra": {"venue": (loc.get("source") or {}).get("display_name"), "type": w.get("type")},
        })
    return out


def count(query: str, since: str, until: str) -> int:
    params = {"filter": _filter(query, since, until), "per-page": 1, "select": "id", "mailto": MAILTO}
    data = json.loads(get(BASE, params, min_interval=0.5))
    return int(data.get("meta", {}).get("count", 0))
