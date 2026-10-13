"""techtree CLI. Run `techtree --help`."""
from __future__ import annotations
import argparse, json, sys, time
from datetime import date, timedelta
from . import model, digest, note, serve
from .collectors import REGISTRY, openalex


def cmd_update(args):
    sector = model.load_sector(args.sector)
    since = (date.today() - timedelta(days=args.days)).isoformat()
    sources = args.sources.split(",") if args.sources else list(REGISTRY)
    only = set(args.nodes.split(",")) if args.nodes else None
    raw: dict[str, list] = {}
    counts: dict[str, dict] = {}
    today = date.today()
    w_recent = ((today - timedelta(days=90)).isoformat(), today.isoformat())
    w_prior = ((today - timedelta(days=180)).isoformat(), (today - timedelta(days=91)).isoformat())
    t0 = time.time()
    for n in sector["nodes"]:
        if only and n["id"] not in only:
            continue
        rows = []
        for s in sources:
            qs = n.get("contract_queries", n["queries"]) if s == "usaspending" else n["queries"]
            for q in qs:
                try:
                    got = REGISTRY[s](q, since)
                    rows += got
                    print(f"  {n['id']:<34} {s:<11} {len(got):>3}  {q[:50]}", file=sys.stderr)
                except Exception as ex:  # keep going; one dead source should not kill the run
                    print(f"  {n['id']:<34} {s:<11} ERR {type(ex).__name__}: {str(ex)[:80]}", file=sys.stderr)
        raw[n["id"]] = rows
        if "openalex" in sources:
            try:
                counts[n["id"]] = {"recent_90": sum(openalex.count(q, *w_recent) for q in n["queries"]),
                                   "prior_90": sum(openalex.count(q, *w_prior) for q in n["queries"])}
            except Exception as ex:
                print(f"  {n['id']:<34} count       ERR {type(ex).__name__}", file=sys.stderr)
    # keep evidence from (node, source) pairs this run did not refresh
    try:
        old = model.load_tree()
        for n in old["nodes"]:
            keep = [e for e in n["evidence"] if (only and n["id"] not in only) or e["source"] not in sources]
            raw.setdefault(n["id"], [])
            raw[n["id"]] += [{k: v for k, v in e.items() if k not in ("id", "node")} for e in keep]
        for nid, n in ((n["id"], n) for n in old["nodes"]):
            if nid not in counts and n["momentum"].get("counted"):
                counts[nid] = {"recent_90": n["momentum"]["recent_90"], "prior_90": n["momentum"]["prior_90"]}
    except FileNotFoundError:
        pass
    tree = model.assemble(sector, raw, counts=counts)
    model.save_tree(tree)
    s = tree["stats"]
    print(f"techtree: {s['nodes']} nodes, {s['evidence']} evidence rows, {s['people']} people, {time.time()-t0:.0f}s -> data/tree.json")


def cmd_rebuild(args):
    """Re-apply the sector judgment (status, gates, why) to the evidence already collected. No network."""
    sector = model.load_sector(args.sector)
    old = model.load_tree()
    raw = {n["id"]: [{k: v for k, v in e.items() if k not in ("id", "node")} for e in n["evidence"]] for n in old["nodes"]}
    counts = {n["id"]: {"recent_90": n["momentum"]["recent_90"], "prior_90": n["momentum"]["prior_90"]} for n in old["nodes"] if n["momentum"].get("counted")}
    tree = model.assemble(sector, raw, counts=counts)
    model.save_tree(tree)
    print(f"techtree: rebuilt from {tree['stats']['evidence']} rows -> data/tree.json")


def cmd_digest(args):
    print(digest.build())


def cmd_people(args):
    tree = model.load_tree()
    by_id = {n["id"]: n["label"] for n in tree["nodes"]}
    rows = tree["people"]
    if args.spinout:
        rows = [p for p in rows if p.get("spinout_signal")]
    if args.node:
        rows = [p for p in rows if args.node in p["nodes"]]
    if not args.all:
        rows = [p for p in rows if p.get("allied")]
    if args.country:
        rows = [p for p in rows if (p.get("country") or "") == args.country.upper()]
    for p in rows[: args.top]:
        inst = (p["institutions"][:1] or ["-"])[0]
        print(f"{p['score']:>5}  {p['name']:<28} {(p.get('country') or '--'):<3} {inst[:32]:<32} {p['latest']:<10} {by_id[p['nodes'][0]][:36]}")


def cmd_nodes(args):
    tree = model.load_tree()
    for n in sorted(tree["nodes"], key=lambda n: (model.STATUS_ORDER[n["status"]], -n["momentum"]["recent_90"])):
        m = n["momentum"]
        print(f"[{n['status']:<8}] {n['label']:<48} 90d:{m['recent_90']:>3}  prior:{m['prior_90']:>3}  ${m['funding_usd']:,}")


def cmd_note(args):
    print(note.facts(" ".join(args.person)))


def cmd_serve(args):
    serve.run(args.port, open_browser=not args.no_open)


def main(argv=None):
    p = argparse.ArgumentParser(prog="techtree", description="A living technology tree: what became possible, what is one problem away, who can solve it.")
    sub = p.add_subparsers(dest="cmd", required=True)
    u = sub.add_parser("update", help="pull fresh evidence from public sources and rebuild data/tree.json")
    u.add_argument("--sector", default="maritime_autonomy")
    u.add_argument("--days", type=int, default=365, help="look-back window")
    u.add_argument("--sources", default="", help="comma list: openalex,arxiv,nsf,usaspending (default all)")
    u.add_argument("--nodes", default="", help="comma list of node ids to refresh (default all)")
    u.set_defaults(fn=cmd_update)
    rb = sub.add_parser("rebuild", help="re-apply sector judgment to collected evidence, no network")
    rb.add_argument("--sector", default="maritime_autonomy")
    rb.set_defaults(fn=cmd_rebuild)
    d = sub.add_parser("digest", help="what moved since the previous snapshot (markdown)")
    d.set_defaults(fn=cmd_digest)
    pe = sub.add_parser("people", help="ranked people on the tree")
    pe.add_argument("--top", type=int, default=25)
    pe.add_argument("--spinout", action="store_true", help="academics with first-author work on near/blocked nodes")
    pe.add_argument("--node", default="", help="filter to one node id")
    pe.add_argument("--all", action="store_true", help="include every country (default: US and allied institutions only)")
    pe.add_argument("--allied", action="store_true", help=argparse.SUPPRESS)
    pe.add_argument("--country", default="", help="ISO country code, e.g. US")
    pe.set_defaults(fn=cmd_people)
    no = sub.add_parser("nodes", help="nodes by status and momentum")
    no.set_defaults(fn=cmd_nodes)
    nt = sub.add_parser("note", help="facts for a 5-line note about a person (you write the note)")
    nt.add_argument("person", nargs="+")
    nt.set_defaults(fn=cmd_note)
    sv = sub.add_parser("serve", help="open the tree in a browser")
    sv.add_argument("--port", type=int, default=8787)
    sv.add_argument("--no-open", action="store_true")
    sv.set_defaults(fn=cmd_serve)
    args = p.parse_args(argv)
    args.fn(args)


if __name__ == "__main__":
    main()
