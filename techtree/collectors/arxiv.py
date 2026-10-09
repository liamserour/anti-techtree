"""arXiv Atom API. Keyless, asks for 3s between calls. https://info.arxiv.org/help/api"""
import re
import xml.etree.ElementTree as ET
from ._http import get

BASE = "https://export.arxiv.org/api/query"
NS = {"a": "http://www.w3.org/2005/Atom"}


def _to_arxiv_query(q: str) -> str:
    # keep quoted phrases, AND the rest
    phrases = re.findall(r'"([^"]+)"', q)
    rest = re.sub(r'"[^"]+"', " ", q).split()
    terms = [f'all:"{p}"' for p in phrases] + [f"all:{t}" for t in rest]
    return " AND ".join(terms)


def search(query: str, since: str, limit: int = 15) -> list[dict]:
    params = {"search_query": _to_arxiv_query(query), "start": 0, "max_results": limit,
              "sortBy": "submittedDate", "sortOrder": "descending"}
    xml = get(BASE, params, min_interval=3.0)
    root = ET.fromstring(xml)
    out = []
    for e in root.findall("a:entry", NS):
        date = (e.findtext("a:published", default="", namespaces=NS) or "")[:10]
        if date < since:
            continue
        out.append({
            "kind": "paper", "source": "arxiv",
            "title": " ".join((e.findtext("a:title", default="", namespaces=NS) or "").split()),
            "date": date,
            "url": e.findtext("a:id", default="", namespaces=NS),
            "authors": [{"name": a.findtext("a:name", default="", namespaces=NS)} for a in e.findall("a:author", NS)],
            "extra": {"summary": " ".join((e.findtext("a:summary", default="", namespaces=NS) or "").split())[:400]},
        })
    return out
