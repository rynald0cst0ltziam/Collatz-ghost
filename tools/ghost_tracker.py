#!/usr/bin/env python3
"""
ghost_tracker.py

Comprehensive ghost tracking, storage, and analysis system.

Features:
- Extract ghosts from atlas files
- Store in a persistent ghost registry (JSONL)
- Track ghost stability across precision levels (k-ladder)
- Analyze ghost properties and patterns
- Generate reports on ghost populations

Usage:
  # Extract ghosts from an atlas and add to registry
  python tools/ghost_tracker.py extract atlases/atlas_M12_A3_k28.jsonl

  # Show all known ghosts
  python tools/ghost_tracker.py list

  # Analyze ghost stability across k values
  python tools/ghost_tracker.py stability --pattern 2,2,2,2,2,2,2,2

  # Compare ghosts across two atlases (precision ladder)
  python tools/ghost_tracker.py ladder atlases/atlas_M12_A3_k24.jsonl atlases/atlas_M12_A3_k32.jsonl

  # Generate full ghost report
  python tools/ghost_tracker.py report
"""

import argparse
import json
import os
from collections import defaultdict
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Set, Tuple

# Default paths
GHOST_REGISTRY = "registry/ghosts.jsonl"
GHOST_ANALYSIS = "registry/ghost_analysis.json"


@dataclass
class GhostRecord:
    """A single ghost observation."""
    pattern: List[int]
    pattern_str: str
    M: int  # pattern length
    k: int  # precision at which SAT was observed
    source_atlas: str
    first_seen: str  # ISO timestamp
    x0_candidate: Optional[int]  # if extractable from tree
    is_trivial: bool  # True if pattern is [2,2,2,...]
    notes: str = ""


def pattern_to_str(pat: List[int]) -> str:
    return ",".join(map(str, pat))


def str_to_pattern(s: str) -> List[int]:
    return [int(x.strip()) for x in s.split(",") if x.strip()]


def is_trivial_pattern(pat: List[int]) -> bool:
    """Check if pattern is [2,2,2,...] (the trivial cycle x=1)."""
    return all(x == 2 for x in pat)


def extract_x0_from_tree(tree: dict) -> Optional[int]:
    """Try to extract the SAT x0 value from a proof tree."""
    if tree.get("sat") is True:
        return tree.get("x0_mod_2^m")
    for child in tree.get("children", []):
        result = extract_x0_from_tree(child)
        if result is not None:
            return result
    return None


def is_type_b_sat(rec: Dict[str, Any]) -> bool:
    reason = rec.get("reason", "")
    if "UNSAT" in reason:
        return False
    if "SAT" in reason:
        return True
    return False


def extract_ghosts_from_atlas(atlas_path: str) -> List[GhostRecord]:
    """Extract all ghost (SAT) patterns from an atlas file."""
    ghosts = []
    batch_info = None
    
    with open(atlas_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            
            if rec.get("type") == "BATCH":
                batch_info = rec
                continue
            
            if rec.get("type") == "B" and is_type_b_sat(rec):
                pat = rec.get("pattern", [])
                k = rec.get("k", 0)
                tree = rec.get("tree", {})
                x0 = extract_x0_from_tree(tree)
                
                ghost = GhostRecord(
                    pattern=pat,
                    pattern_str=pattern_to_str(pat),
                    M=len(pat),
                    k=k,
                    source_atlas=atlas_path,
                    first_seen=datetime.now().isoformat(),
                    x0_candidate=x0,
                    is_trivial=is_trivial_pattern(pat),
                )
                ghosts.append(ghost)
    
    return ghosts


def load_ghost_registry(path: str = GHOST_REGISTRY) -> List[Dict[str, Any]]:
    """Load existing ghost registry."""
    if not os.path.exists(path):
        return []
    
    records = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            records.append(json.loads(line))
    return records


def save_ghost_to_registry(ghost: GhostRecord, path: str = GHOST_REGISTRY):
    """Append a ghost record to the registry."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(asdict(ghost), sort_keys=True) + "\n")


def get_known_ghost_keys(path: str = GHOST_REGISTRY) -> Set[Tuple[str, int]]:
    """Get set of (pattern_str, k) pairs already in registry."""
    records = load_ghost_registry(path)
    return {(r["pattern_str"], r["k"]) for r in records}


# ============================================================================
# Commands
# ============================================================================

def cmd_extract(args):
    """Extract ghosts from atlas and add to registry."""
    atlas_path = args.atlas
    
    if not os.path.exists(atlas_path):
        print(f"Error: Atlas file not found: {atlas_path}")
        return 1
    
    print(f"Extracting ghosts from: {atlas_path}")
    ghosts = extract_ghosts_from_atlas(atlas_path)
    
    if not ghosts:
        print("No ghosts (SAT patterns) found in this atlas.")
        return 0
    
    # Check for duplicates
    known = get_known_ghost_keys()
    new_ghosts = [g for g in ghosts if (g.pattern_str, g.k) not in known]
    
    print(f"Found {len(ghosts)} ghost(s), {len(new_ghosts)} new")
    
    for ghost in new_ghosts:
        save_ghost_to_registry(ghost)
        trivial_tag = " [TRIVIAL]" if ghost.is_trivial else ""
        print(f"  + [{ghost.pattern_str}] k={ghost.k} x0={ghost.x0_candidate}{trivial_tag}")
    
    if len(ghosts) > len(new_ghosts):
        print(f"  ({len(ghosts) - len(new_ghosts)} already in registry)")
    
    return 0


def cmd_list(args):
    """List all known ghosts."""
    records = load_ghost_registry()
    
    if not records:
        print("No ghosts in registry yet.")
        print("Run: python tools/ghost_tracker.py extract <atlas.jsonl>")
        return 0
    
    # Group by pattern
    by_pattern = defaultdict(list)
    for r in records:
        by_pattern[r["pattern_str"]].append(r)
    
    print(f"\n=== Ghost Registry ({len(records)} observations, {len(by_pattern)} unique patterns) ===\n")
    
    # Sort by pattern length, then pattern string
    for pat_str in sorted(by_pattern.keys(), key=lambda s: (len(s.split(",")), s)):
        observations = by_pattern[pat_str]
        k_values = sorted(set(r["k"] for r in observations))
        is_trivial = observations[0].get("is_trivial", False)
        trivial_tag = " [TRIVIAL - x=1 cycle]" if is_trivial else ""
        
        print(f"Pattern: [{pat_str}]{trivial_tag}")
        print(f"  Length: M={len(pat_str.split(','))}")
        print(f"  Observed at k: {k_values}")
        print(f"  First seen: {observations[0].get('first_seen', 'unknown')}")
        if observations[0].get("x0_candidate"):
            print(f"  x0 candidate (mod 2^k): {observations[0]['x0_candidate']}")
        print()
    
    return 0


def cmd_stability(args):
    """Analyze stability of a specific pattern across k values."""
    pattern_str = args.pattern
    records = load_ghost_registry()
    
    # Find all observations of this pattern
    observations = [r for r in records if r["pattern_str"] == pattern_str]
    
    if not observations:
        print(f"Pattern [{pattern_str}] not found in ghost registry.")
        print("It may have been excluded by Type A or Type B UNSAT.")
        return 0
    
    k_values = sorted(set(r["k"] for r in observations))
    
    print(f"\n=== Ghost Stability Analysis: [{pattern_str}] ===\n")
    print(f"Pattern length: M={len(pattern_str.split(','))}")
    print(f"Is trivial (x=1 cycle): {observations[0].get('is_trivial', False)}")
    print(f"\nObserved as SAT at precision levels:")
    
    for k in k_values:
        obs = [r for r in observations if r["k"] == k]
        x0 = obs[0].get("x0_candidate")
        source = obs[0].get("source_atlas", "unknown")
        print(f"  k={k:3d}: SAT (x0 mod 2^{k} = {x0}) from {os.path.basename(source)}")
    
    if len(k_values) >= 2:
        print(f"\nStability: Ghost persists across {len(k_values)} precision levels")
        print(f"  k range: {min(k_values)} → {max(k_values)}")
    
    return 0


def cmd_ladder(args):
    """Compare ghost sets between two atlases (precision ladder analysis)."""
    atlas_a = args.atlas_a
    atlas_b = args.atlas_b
    
    ghosts_a = extract_ghosts_from_atlas(atlas_a)
    ghosts_b = extract_ghosts_from_atlas(atlas_b)
    
    set_a = {g.pattern_str for g in ghosts_a}
    set_b = {g.pattern_str for g in ghosts_b}
    
    k_a = ghosts_a[0].k if ghosts_a else "?"
    k_b = ghosts_b[0].k if ghosts_b else "?"
    
    intersection = set_a & set_b
    only_a = set_a - set_b
    only_b = set_b - set_a
    
    print(f"\n=== Ghost Ladder Comparison ===\n")
    print(f"Atlas A: {atlas_a} (k={k_a})")
    print(f"  Ghosts: {len(set_a)}")
    print(f"Atlas B: {atlas_b} (k={k_b})")
    print(f"  Ghosts: {len(set_b)}")
    print()
    print(f"Intersection (stable ghosts): {len(intersection)}")
    print(f"Only in A (vanished at higher k): {len(only_a)}")
    print(f"Only in B (appeared at higher k): {len(only_b)}")
    
    if intersection:
        print(f"\nStable ghosts (persist across both k):")
        for p in sorted(intersection):
            trivial = " [TRIVIAL]" if is_trivial_pattern(str_to_pattern(p)) else ""
            print(f"  [{p}]{trivial}")
    
    if only_a:
        print(f"\nVanished ghosts (SAT at k={k_a}, UNSAT at k={k_b}):")
        for p in sorted(only_a)[:20]:
            print(f"  [{p}]")
        if len(only_a) > 20:
            print(f"  ... and {len(only_a) - 20} more")
    
    if only_b:
        print(f"\nNew ghosts (only at k={k_b}):")
        for p in sorted(only_b)[:20]:
            print(f"  [{p}]")
        if len(only_b) > 20:
            print(f"  ... and {len(only_b) - 20} more")
    
    # Calculate attrition rate
    if set_a:
        attrition = len(only_a) / len(set_a) * 100
        print(f"\nGhost attrition rate: {attrition:.1f}% vanished from k={k_a} to k={k_b}")
    
    return 0


def cmd_report(args):
    """Generate comprehensive ghost report."""
    records = load_ghost_registry()
    
    if not records:
        print("No ghosts in registry. Run extract first.")
        return 0
    
    # Group by pattern
    by_pattern = defaultdict(list)
    for r in records:
        by_pattern[r["pattern_str"]].append(r)
    
    # Analyze
    trivial_count = sum(1 for p, obs in by_pattern.items() if obs[0].get("is_trivial"))
    nontrivial_count = len(by_pattern) - trivial_count
    
    # k-value distribution
    all_k = [r["k"] for r in records]
    k_counts = defaultdict(int)
    for k in all_k:
        k_counts[k] += 1
    
    # Length distribution
    m_counts = defaultdict(int)
    for p in by_pattern.keys():
        m = len(p.split(","))
        m_counts[m] += 1
    
    # Multi-k patterns (stable ghosts)
    multi_k_patterns = [(p, obs) for p, obs in by_pattern.items() 
                        if len(set(o["k"] for o in obs)) > 1]
    
    print("\n" + "="*60)
    print("           COLLATZ-GHOST: GHOST POPULATION REPORT")
    print("="*60)
    print(f"\nGenerated: {datetime.now().isoformat()}")
    print(f"\n--- Summary ---")
    print(f"Total ghost observations: {len(records)}")
    print(f"Unique ghost patterns: {len(by_pattern)}")
    print(f"  Trivial ([2,2,...] family): {trivial_count}")
    print(f"  Non-trivial: {nontrivial_count}")
    
    print(f"\n--- Precision (k) Distribution ---")
    for k in sorted(k_counts.keys()):
        print(f"  k={k}: {k_counts[k]} observations")
    
    print(f"\n--- Pattern Length (M) Distribution ---")
    for m in sorted(m_counts.keys()):
        print(f"  M={m}: {m_counts[m]} patterns")
    
    if multi_k_patterns:
        print(f"\n--- Stable Ghosts (observed at multiple k) ---")
        for p, obs in sorted(multi_k_patterns, key=lambda x: x[0]):
            k_vals = sorted(set(o["k"] for o in obs))
            trivial = " [TRIVIAL]" if obs[0].get("is_trivial") else ""
            print(f"  [{p}] at k={k_vals}{trivial}")
    
    print(f"\n--- Non-Trivial Ghosts ---")
    nontrivial = [(p, obs) for p, obs in by_pattern.items() 
                  if not obs[0].get("is_trivial")]
    if nontrivial:
        for p, obs in sorted(nontrivial, key=lambda x: (len(x[0].split(",")), x[0])):
            k_vals = sorted(set(o["k"] for o in obs))
            print(f"  [{p}] at k={k_vals}")
    else:
        print("  None found! Only trivial ghosts exist.")
        print("  This is GOOD - it means all non-trivial patterns are excluded.")
    
    print("\n" + "="*60)
    
    # Save analysis to JSON
    analysis = {
        "generated": datetime.now().isoformat(),
        "total_observations": len(records),
        "unique_patterns": len(by_pattern),
        "trivial_count": trivial_count,
        "nontrivial_count": nontrivial_count,
        "k_distribution": dict(k_counts),
        "m_distribution": dict(m_counts),
        "stable_ghosts": [p for p, _ in multi_k_patterns],
        "nontrivial_ghosts": [p for p, obs in nontrivial],
    }
    
    os.makedirs(os.path.dirname(GHOST_ANALYSIS), exist_ok=True)
    with open(GHOST_ANALYSIS, "w", encoding="utf-8") as f:
        json.dump(analysis, f, indent=2, sort_keys=True)
    print(f"\nAnalysis saved to: {GHOST_ANALYSIS}")
    
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Collatz-Ghost: Ghost Tracking and Analysis System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # extract
    p_extract = subparsers.add_parser("extract", help="Extract ghosts from atlas")
    p_extract.add_argument("atlas", help="Path to atlas JSONL file")
    p_extract.set_defaults(func=cmd_extract)
    
    # list
    p_list = subparsers.add_parser("list", help="List all known ghosts")
    p_list.set_defaults(func=cmd_list)
    
    # stability
    p_stab = subparsers.add_parser("stability", help="Analyze ghost stability")
    p_stab.add_argument("--pattern", required=True, help="Pattern string (e.g., 2,2,2,2)")
    p_stab.set_defaults(func=cmd_stability)
    
    # ladder
    p_ladder = subparsers.add_parser("ladder", help="Compare ghosts across precision levels")
    p_ladder.add_argument("atlas_a", help="First atlas (lower k)")
    p_ladder.add_argument("atlas_b", help="Second atlas (higher k)")
    p_ladder.set_defaults(func=cmd_ladder)
    
    # report
    p_report = subparsers.add_parser("report", help="Generate comprehensive ghost report")
    p_report.set_defaults(func=cmd_report)
    
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
