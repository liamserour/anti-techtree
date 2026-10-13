---
name: techtree
description: A living technology tree for a frontier sector. Shows what became possible, what is one problem away, and who can solve it, from public sources (OpenAlex, arXiv, NSF, USAspending). Use when asked what moved in a sector, who is working on a blocked problem, or for facts to write a sourcing note about a researcher.
---

# techtree

A technology tree is a map of capabilities. Each node is something a product needs to be true. Edges say which capability gates which. Every node carries a hand-written judgment (status, why it matters) and machine-collected evidence (papers, grants, contracts, dated, with sources). People are derived from the evidence and ranked by recent first-author work on nodes that are not yet solved.

The judgment layer is in `data/sectors/<sector>.json`. The machine layer is `data/tree.json`. Snapshots in `data/snapshots/` make "what moved" a diff, not a feeling.

## Install (once)

Requires Python 3.11+ and [uv](https://docs.astral.sh/uv/). No API keys.

```bash
git clone <this repo> techtree && cd techtree
uv sync
```

## Commands

Run everything from the repo root.

| Task | Command |
|---|---|
| Open the tree in the browser (seed data included) | `uv run techtree serve` |
| Pull fresh evidence from all sources and rebuild | `uv run techtree update` |
| What moved since the previous snapshot (markdown) | `uv run techtree digest` |
| Nodes by status and momentum | `uv run techtree nodes` |
| Ranked people, US and allied institutions (default) | `uv run techtree people --top 40` |
| Ranked people, every country | `uv run techtree people --all` |
| Academics with first-author work on unsolved nodes | `uv run techtree people --spinout` |
| People on one node | `uv run techtree people --node gnss_denied_nav` |
| Facts for a 5-line note about a person | `uv run techtree note Mangelson` |

`update` takes about 4 minutes for 25 nodes because arXiv asks for 3 seconds between calls. Narrow it with `--nodes id1,id2` or `--sources openalex,nsf`. Partial updates merge into the existing tree. Responses are cached in `.cache/` for 12 hours.

## How an agent should use this

When the user asks what is happening in the sector, run `update` then `digest` and report the digest. Lead with blocked nodes whose momentum rose.

When the user asks who to talk to, run `people --spinout` and open the top names with `note <surname>`. Report the facts. Do not write the outreach note for the user: the note must be in their words and under 120 words. The tool is deliberately built so that step stays human.

When the user wants to change the judgment (a node's status, its reason, which nodes gate it, or its search terms), edit `data/sectors/<sector>.json` and run `update`. Statuses are `solved`, `near` (one problem away), `blocked`, `emerging`. Every node needs `id`, `label`, `cluster`, `status`, `why`, `unlocked_by` (list of node ids that gate it), `queries` (2 to 3 short searches, each with at most one quoted phrase; words are AND-ed).

To add a sector, copy `data/sectors/maritime_autonomy.json`, rewrite the nodes, and run `update --sector <id>`.

## What the numbers mean

- Momentum `recent_90` and `prior_90` are counts of works in OpenAlex matching the node's searches in the last 90 days and the 90 days before. They come from the index, not from the sample shown.
- Public money is the sum of NSF awards and federal contracts collected for the node in the look-back window. It is a floor, not a total.
- A person's score adds up their items on the tree, weighted by recency (last 90 days counts most), author position (first author counts most), and node status (blocked nodes count most, solved nodes least).
- Spinout signal: academic affiliation, at least one first-author item, on a node that is not solved.
- Country: taken from the first institution on record. `people` hides non-allied countries by default because most of the literature is from Chinese institutions (about 750 of 2,100 people on the maritime tree) and a US defense investor cannot act on those names. `--all` shows everyone.

## Sources

| Source | What | Auth |
|---|---|---|
| OpenAlex | papers with authors and institutions, plus window counts | none |
| arXiv | preprints from the last days, before OpenAlex indexes them | none, 3s between calls |
| NSF Awards | grants with PI and institution | none |
| USAspending | federal contracts by keyword | none |

SBIR.gov's API currently refuses unauthenticated calls, so SBIR awards are not collected yet. PatentsView (patents by inventor) is the next collector worth adding; it needs a free key.

## Limits to keep in mind

Everything here comes from public indexes with their own lag and noise. Treat a person on the tree as a lead to check, not a verified fact. The tool links every row to its source so the check takes one click.
