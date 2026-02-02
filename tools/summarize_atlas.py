#!/usr/bin/env python3
"""
summarize_atlas.py

Translate collatz-ghost JSONL outputs into:
- counts of Type A / Type B UNSAT / Type B SAT
- list of SAT patterns
- basic motif stats (frequency of exponent values, run lengths)
- (optional) compare two atlas files and compute SAT overlap

Usage:
  python tools/summarize_atlas.py path/to/atlas.jsonl
  python tools/summarize_atlas.py path/to/atlas_k24.jsonl --compare path/to/atlas_k32.jsonl
  python tools/summarize_atlas.py atlas.jsonl --top-sat 50 --show-sat

Notes:
- Treats each JSON line as one record (cert or BATCH header).
- For Type B, it uses the "reason" field to decide UNSAT vs SAT.
"""

import argparse
import json
from collections import Counter, defaultdict
from typing import Dict, Any, List, Tuple, Optional


def parse_jsonl(path: str) -> List[Dict[str, Any]]:
    recs = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            recs.append(json.loads(line))
    return recs


def is_type_b_sat(rec: Dict[str, Any]) -> bool:
    # Solver emits reason containing "SAT" when a sat leaf exists; UNSAT contains "UNSAT"
    reason = rec.get("reason", "")
    if "UNSAT" in reason:
        return False
    if "SAT" in reason:
        return True
    # If ambiguous, treat as not SAT
    return False


def pattern_to_str(pat: List[int]) -> str:
    return ",".join(map(str, pat))


def run_lengths(pat: List[int]) -> Counter:
    c = Counter()
    if not pat:
        return c
    cur = pat[0]
    ln = 1
    for x in pat[1:]:
        if x == cur:
            ln += 1
        else:
            c[(cur, ln)] += 1
            cur = x
            ln = 1
    c[(cur, ln)] += 1
    return c


def summarize(path: str) -> Dict[str, Any]:
    recs = parse_jsonl(path)

    counts = Counter()
    sat_patterns: List[List[int]] = []
    unsat_patterns: List[List[int]] = []
    type_a_patterns: List[List[int]] = []
    batch = None

    value_hist = Counter()
    run_hist = Counter()

    for rec in recs:
        t = rec.get("type")
        if t == "BATCH":
            batch = rec
            continue

        pat = rec.get("pattern")
        if not isinstance(pat, list):
            continue

        # motif stats
        value_hist.update(pat)
        run_hist.update(run_lengths(pat))

        if t == "A":
            counts["A"] += 1
            type_a_patterns.append(pat)
        elif t == "B":
            if is_type_b_sat(rec):
                counts["B_SAT"] += 1
                sat_patterns.append(pat)
            else:
                counts["B_UNSAT"] += 1
                unsat_patterns.append(pat)
        else:
            counts["OTHER"] += 1

    total = counts["A"] + counts["B_SAT"] + counts["B_UNSAT"]

    out = {
        "file": path,
        "total_patterns": total,
        "counts": dict(counts),
        "batch": batch,
        "sat_patterns": sat_patterns,
        "unsat_patterns": unsat_patterns,
        "type_a_patterns": type_a_patterns,
        "value_hist": dict(value_hist),
        "run_hist_top20": [
            {"value": v, "run_len": l, "count": run_hist[(v, l)]}
            for (v, l) in run_hist.most_common(20)
        ],
    }
    return out


def compare_sat(a: Dict[str, Any], b: Dict[str, Any]) -> Dict[str, Any]:
    sat_a = {pattern_to_str(p) for p in a["sat_patterns"]}
    sat_b = {pattern_to_str(p) for p in b["sat_patterns"]}

    inter = sat_a & sat_b
    only_a = sat_a - sat_b
    only_b = sat_b - sat_a

    return {
        "sat_count_a": len(sat_a),
        "sat_count_b": len(sat_b),
        "intersection": len(inter),
        "only_a": len(only_a),
        "only_b": len(only_b),
        "intersection_patterns": sorted(list(inter))[:200],  # cap to avoid huge output
        "only_a_patterns": sorted(list(only_a))[:200],
        "only_b_patterns": sorted(list(only_b))[:200],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("atlas", help="Path to atlas JSONL output")
    ap.add_argument("--compare", help="Optional: second atlas JSONL to compare SAT sets")
    ap.add_argument("--show-sat", action="store_true", help="Print SAT patterns")
    ap.add_argument("--top-sat", type=int, default=50, help="How many SAT patterns to print")
    ap.add_argument("--json", action="store_true", help="Emit machine-readable JSON summary")
    args = ap.parse_args()

    s1 = summarize(args.atlas)

    if args.compare:
        s2 = summarize(args.compare)
        comp = compare_sat(s1, s2)
    else:
        s2 = None
        comp = None

    if args.json:
        out = {"summary": s1}
        if s2:
            out["summary_compare"] = s2
        if comp:
            out["sat_compare"] = comp
        print(json.dumps(out, indent=2, sort_keys=True))
        return

    # Human-readable report
    print("\n=== Atlas summary ===")
    print(f"File: {s1['file']}")
    if s1["batch"]:
        fam = s1["batch"].get("family", {})
        print(f"Family: {fam} | batch root: {s1['batch'].get('root')}")
    print(f"Total patterns: {s1['total_patterns']}")
    print("Counts:", s1["counts"])

    total = s1["total_patterns"] or 1
    a = s1["counts"].get("A", 0)
    bu = s1["counts"].get("B_UNSAT", 0)
    bs = s1["counts"].get("B_SAT", 0)
    print(f"Fractions: A={a/total:.4f}, B_UNSAT={bu/total:.4f}, B_SAT={bs/total:.4f}")

    print("\nValue histogram (exponent frequencies):")
    for k in sorted(s1["value_hist"].keys()):
        print(f"  {k}: {s1['value_hist'][k]}")

    print("\nTop run-length motifs (value, run_len -> count):")
    for item in s1["run_hist_top20"]:
        print(f"  ({item['value']}, {item['run_len']}): {item['count']}")

    if args.show_sat:
        print(f"\nSAT patterns (showing up to {args.top_sat}):")
        for p in s1["sat_patterns"][: args.top_sat]:
            print(" ", pattern_to_str(p))

    if comp:
        print("\n=== SAT set comparison ===")
        print(f"A: {args.atlas}")
        print(f"B: {args.compare}")
        print(json.dumps(comp, indent=2))

        if args.show_sat:
            print("\nIntersection SAT patterns (first 200):")
            for p in comp["intersection_patterns"]:
                print(" ", p)


if __name__ == "__main__":
    main()
