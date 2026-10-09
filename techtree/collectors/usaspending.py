"""USAspending.gov: federal contracts and grants by keyword. Keyless. https://api.usaspending.gov"""
import json
from datetime import date
from ._http import get

BASE = "https://api.usaspending.gov/api/v2/search/spending_by_award/"


def search(query: str, since: str, limit: int = 10) -> list[dict]:
    body = {
        "filters": {
            "keywords": [query.replace('"', "")],
            "time_period": [{"start_date": since, "end_date": date.today().isoformat()}],
            "award_type_codes": ["A", "B", "C", "D"],  # contracts only; grants are a different code group
        },
        "fields": ["Award ID", "Recipient Name", "Award Amount", "Start Date", "Description", "Awarding Agency", "Awarding Sub Agency"],
        "limit": limit, "page": 1, "sort": "Start Date", "order": "desc",
    }
    data = json.loads(get(BASE, method="POST", json_body=body, min_interval=0.3))
    out = []
    for r in data.get("results", []):
        desc = (r.get("Description") or "").split("!")[-1].strip()
        out.append({
            "kind": "contract", "source": "usaspending",
            "title": f"{r.get('Recipient Name','').title()}: {desc[:140]}",
            "date": r.get("Start Date") or "",
            "url": f"https://www.usaspending.gov/award/{r.get('generated_internal_id')}",
            "authors": [],
            "extra": {"amount": r.get("Award Amount"), "recipient": r.get("Recipient Name"),
                      "agency": r.get("Awarding Sub Agency") or r.get("Awarding Agency")},
        })
    return out
