"""Collectors turn a search query into Evidence rows. Each one hits a public, keyless API.

A collector returns a list of dicts shaped like:
  {kind, title, date (YYYY-MM-DD), url, source, authors: [{name, institution, id}], extra: {...}}
"""
from . import arxiv, openalex, nsf, usaspending

REGISTRY = {
    "openalex": openalex.search,
    "arxiv": arxiv.search,
    "nsf": nsf.search,
    "usaspending": usaspending.search,
}
