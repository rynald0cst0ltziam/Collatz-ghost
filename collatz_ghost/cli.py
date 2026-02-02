from __future__ import annotations
import argparse
import json
import os
from .util import parse_pattern
from .solver import ProverConfig, prove_pattern
from .family import FamilyJob, prove_family
from .verifier import verify_cert

GHOST_REGISTRY = "registry/ghosts.jsonl"

def cmd_prove(args: argparse.Namespace) -> int:
    pattern = parse_pattern(args.pattern)
    cfg = ProverConfig(k=args.k, max_nodes=args.max_nodes)
    cert = prove_pattern(pattern, cfg)
    print(json.dumps(cert, indent=2, sort_keys=True))
    return 0

def cmd_prove_family(args: argparse.Namespace) -> int:
    job = FamilyJob(M=args.M, A=args.A, k=args.k, amin=args.amin, out_path=args.out, max_patterns=args.max_patterns)
    summary = prove_family(job)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0

def cmd_verify(args: argparse.Namespace) -> int:
    ok_all = True
    count = 0
    ghosts_found = []
    
    with open(args.cert, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            cert = json.loads(line)
            ok, msg = verify_cert(cert)
            count += 1
            if not ok:
                ok_all = False
                print(f"[FAIL] #{count}: {msg}")
            else:
                if args.verbose:
                    print(f"[OK]   #{count}: {msg}")
            
            # Track ghosts (Type B SAT)
            if cert.get("type") == "B" and "SAT" in cert.get("reason", "") and "UNSAT" not in cert.get("reason", ""):
                ghosts_found.append(cert.get("pattern", []))
    
    if ok_all:
        print(f"All {count} certificate records verified.")
    else:
        print(f"Some certificates failed verification ({count} records processed).")
    
    # Report ghosts
    if ghosts_found:
        trivial = sum(1 for g in ghosts_found if all(x == 2 for x in g))
        nontrivial = len(ghosts_found) - trivial
        print(f"\nGhosts found: {len(ghosts_found)} ({trivial} trivial, {nontrivial} non-trivial)")
        if nontrivial > 0:
            print("⚠️  NON-TRIVIAL GHOSTS DETECTED:")
            for g in ghosts_found:
                if not all(x == 2 for x in g):
                    print(f"    [{','.join(map(str, g))}]")
        print(f"\nRun: python tools/ghost_tracker.py extract {args.cert}")
    
    return 0 if ok_all else 2

def main() -> None:
    p = argparse.ArgumentParser(prog="collatz-ghost", description="Certificate-based 2-adic Collatz pattern prover")
    sub = p.add_subparsers(dest="cmd", required=True)

    p1 = sub.add_parser("prove", help="Prove/exclude a single exponent pattern")
    p1.add_argument("--pattern", required=True, help="Comma-separated exponents, e.g. 2,1,3,1")
    p1.add_argument("--k", type=int, default=32, help="Target modulus exponent for type B: 2^k")
    p1.add_argument("--max-nodes", type=int, default=2_000_000, help="Max nodes in proof tree")
    p1.set_defaults(func=cmd_prove)

    p2 = sub.add_parser("prove-family", help="Enumerate and prove all patterns in a simple family")
    p2.add_argument("--M", type=int, required=True, help="Pattern length (number of odd steps)")
    p2.add_argument("--A", type=int, required=True, help="Max exponent value")
    p2.add_argument("--amin", type=int, default=1, help="Min exponent value")
    p2.add_argument("--k", type=int, default=28, help="Target modulus exponent for type B: 2^k")
    p2.add_argument("--out", default="results.jsonl", help="Output jsonl file path")
    p2.add_argument("--max-patterns", type=int, default=None, help="Optional cap for quick runs")
    p2.set_defaults(func=cmd_prove_family)

    p3 = sub.add_parser("verify", help="Verify certificates (jsonl)")
    p3.add_argument("--cert", required=True, help="Path to jsonl with certificates")
    p3.add_argument("--verbose", action="store_true", help="Verbose per-record output")
    p3.set_defaults(func=cmd_verify)

    args = p.parse_args()
    raise SystemExit(args.func(args))

if __name__ == "__main__":
    main()
