# Tech tree

A living technology tree for one frontier sector. It answers three questions, in the order a seed investor asks them:

1. What became possible in the last year?
2. What becomes possible if one more problem is solved?
3. Who is working on that problem right now?

The first sector is maritime autonomy: 25 capability nodes from "one operator, many hulls" down to the perception, navigation, coordination, platform and assurance problems that gate it.

```bash
uv sync
uv run techtree serve        # opens the tree with seed data, no network needed
uv run techtree update       # pulls fresh papers, grants and contracts (about 4 min)
uv run techtree digest       # what moved since the last snapshot
uv run techtree people --spinout
uv run techtree note <surname>
```

`SKILL.md` has the full command reference and is written so a coding agent can drive the tool.

## What is in the box

```
data/sectors/maritime_autonomy.json   the judgment: nodes, status, why, gates, search terms
data/tree.json                        the evidence: papers, grants, contracts, people (seed included)
data/snapshots/                       one file per update, so digest can diff
techtree/collectors/                  one file per public source
ui/index.html                         the browser view, one file, no build step
```

## Why a tree and not a market map

A market map lists companies that already exist, which means someone already funded them. A tree lists problems. Problems have people attached before they have companies attached. The tree moves when a paper, a grant or a contract lands on a node, and the people who made it move are ranked by how recently and how directly they did.

## Honest limits

Public indexes lag and carry noise. Every row links to its source so a claim takes one click to check. A person on the tree is a lead, not a verdict. The 5-line note is built from facts only and left for a human to write, on purpose.
