"""NSF Award Search API. Keyless. https://www.research.gov/common/webapi/awardapisearch-v1.htm

The keyword search is loose, so we search the quoted phrase (or the first three words) and then
require the title or abstract to contain most of the query's content words.
"""
import json, re
from ._http import get

BASE = "https://api.nsf.gov/services/v1/awards.json"
STOP = {"a", "an", "the", "and", "or", "of", "for", "in", "on", "at", "to", "with", "based", "using", "short-term", "onboard"}


def _terms(q: str) -> list[str]:
    return [t.lower() for t in re.findall(r"[A-Za-z][A-Za-z\-]+", q) if t.lower() not in STOP and len(t) > 2]


def search(query: str, since: str, limit: int = 10) -> list[dict]:
    phrases = re.findall(r'"([^"]+)"', query)
    kw = f'"{phrases[0]}"' if phrases else " ".join(query.split()[:3])
    params = {"keyword": kw, "rpp": 25, "dateStart": _mdy(since),
              "printFields": "id,title,date,piFirstName,piLastName,awardeeName,startDate,fundsObligatedAmt,abstractText"}
    data = json.loads(get(BASE, params, min_interval=0.5))
    terms = _terms(query)
    need = max(2, len(terms) - 1)
    out = []
    for a in data.get("response", {}).get("award", []):
        text = f"{a.get('title','')} {a.get('abstractText','')}".lower()
        if sum(1 for t in terms if t in text) < need:
            continue
        date = _iso(a.get("date") or a.get("startDate") or "")
        if date and date < since:
            continue
        out.append({
            "kind": "grant", "source": "nsf",
            "title": a.get("title", ""), "date": date,
            "url": f"https://www.nsf.gov/awardsearch/showAward?AWD_ID={a.get('id')}",
            "authors": [{"name": f"{a.get('piFirstName','')} {a.get('piLastName','')}".strip(),
                         "institution": a.get("awardeeName"), "institution_type": "education", "position": "first"}],
            "extra": {"amount": float(a.get("fundsObligatedAmt") or 0), "recipient": a.get("awardeeName"),
                      "summary": (a.get("abstractText") or "")[:400]},
        })
        if len(out) >= limit:
            break
    return out


def _mdy(iso: str) -> str:
    y, m, d = iso.split("-")
    return f"{m}/{d}/{y}"


def _iso(mdy: str) -> str:
    return f"{mdy[6:10]}-{mdy[0:2]}-{mdy[3:5]}" if len(mdy) == 10 else ""
