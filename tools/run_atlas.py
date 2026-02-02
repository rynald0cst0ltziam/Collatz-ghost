#!/usr/bin/env python3
"""
run_atlas.py

Automated atlas run with full post-processing:
1. Run prove-family
2. Verify all certificates
3. Extract ghosts to registry
4. Check for real cycles (non-trivial ghosts with integer x0)
5. Generate summary
6. Update registry files
7. Compute checksum

Usage:
  python tools/run_atlas.py --M 12 --A 3 --k 28
  python tools/run_atlas.py --M 12 --A 3 --k 28 --amin 2
  python tools/run_atlas.py --M 10 --A 4 --k 24 --scout 1000

This is the recommended way to run atlases - it handles everything automatically.
"""

import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Paths
ATLASES_DIR = "atlases"
SCOUTS_DIR = "scouts"
SUMMARIES_DIR = "summaries"
REGISTRY_DIR = "registry"
RUNS_CSV = f"{REGISTRY_DIR}/RUNS.csv"
GHOSTS_JSONL = f"{REGISTRY_DIR}/ghosts.jsonl"
CHECKSUMS_TXT = f"{REGISTRY_DIR}/CHECKSUMS.txt"
REAL_CYCLES_FILE = f"{REGISTRY_DIR}/REAL_CYCLES_FOUND.json"


def run_command(cmd: List[str], capture: bool = True) -> Tuple[int, str]:
    """Run a command and return (exit_code, output)."""
    print(f"  Running: {' '.join(cmd)}")
    if capture:
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode, result.stdout + result.stderr
    else:
        result = subprocess.run(cmd)
        return result.returncode, ""


def sha256_file(path: str) -> str:
    """Compute SHA256 of a file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def is_trivial_pattern(pat: List[int]) -> bool:
    """Check if pattern is [2,2,2,...] (the trivial cycle x=1)."""
    return all(x == 2 for x in pat)


def verify_ghost_is_real_cycle(pattern: List[int], x0: int) -> Tuple[bool, List[int]]:
    """
    Verify if a ghost with given x0 is actually a real Collatz cycle.
    Returns (is_real, trajectory).
    """
    if x0 <= 0:
        return False, []
    
    trajectory = [x0]
    x = x0
    
    for i, a in enumerate(pattern):
        # Check: x must be odd
        if x % 2 == 0:
            return False, trajectory
        
        # Compute 3x+1
        next_val = 3 * x + 1
        
        # Check: v2(3x+1) must equal a
        v2 = (next_val & -next_val).bit_length() - 1
        if v2 != a:
            return False, trajectory
        
        # Compute next x
        x = next_val >> a
        trajectory.append(x)
    
    # Check closure: must return to x0
    if x == x0:
        return True, trajectory
    
    return False, trajectory


def extract_ghosts_and_check_real(atlas_path: str) -> Tuple[List[Dict], List[Dict]]:
    """
    Extract ghosts from atlas and check if any are real cycles.
    Returns (all_ghosts, real_cycles).
    """
    ghosts = []
    real_cycles = []
    
    with open(atlas_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            
            if rec.get("type") != "B":
                continue
            
            reason = rec.get("reason", "")
            if "UNSAT" in reason or "SAT" not in reason:
                continue
            
            # This is a ghost (Type B SAT)
            pattern = rec.get("pattern", [])
            tree = rec.get("tree", {})
            k = rec.get("k", 0)
            
            # Extract x0 from tree
            x0 = extract_x0_from_tree(tree)
            
            ghost = {
                "pattern": pattern,
                "pattern_str": ",".join(map(str, pattern)),
                "M": len(pattern),
                "k": k,
                "x0_candidate": x0,
                "is_trivial": is_trivial_pattern(pattern),
                "source_atlas": atlas_path,
                "found_at": datetime.now().isoformat(),
            }
            ghosts.append(ghost)
            
            # Check if this ghost is a REAL cycle
            if x0 is not None and x0 > 0:
                is_real, trajectory = verify_ghost_is_real_cycle(pattern, x0)
                if is_real:
                    real_cycle = {
                        **ghost,
                        "verified_real": True,
                        "trajectory": trajectory,
                    }
                    real_cycles.append(real_cycle)
    
    return ghosts, real_cycles


def extract_x0_from_tree(tree: dict) -> Optional[int]:
    """Extract x0 from SAT leaf in proof tree."""
    if tree.get("sat") is True:
        return tree.get("x0_mod_2^m")
    for child in tree.get("children", []):
        result = extract_x0_from_tree(child)
        if result is not None:
            return result
    return None


def save_ghosts_to_registry(ghosts: List[Dict], registry_path: str = GHOSTS_JSONL):
    """Append ghosts to registry, avoiding duplicates."""
    # Load existing
    existing = set()
    if os.path.exists(registry_path):
        with open(registry_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    rec = json.loads(line)
                    existing.add((rec.get("pattern_str"), rec.get("k")))
    
    # Append new
    new_count = 0
    with open(registry_path, "a", encoding="utf-8") as f:
        for ghost in ghosts:
            key = (ghost["pattern_str"], ghost["k"])
            if key not in existing:
                f.write(json.dumps(ghost, sort_keys=True) + "\n")
                existing.add(key)
                new_count += 1
    
    return new_count


def handle_real_cycle_found(real_cycles: List[Dict]):
    """
    CRITICAL: Handle discovery of a real Collatz cycle.
    This would be a historic mathematical discovery.
    """
    print("\n" + "=" * 70)
    print("🚨🚨🚨 REAL COLLATZ CYCLE DETECTED 🚨🚨🚨")
    print("=" * 70)
    
    for cycle in real_cycles:
        if cycle.get("is_trivial"):
            print(f"\n✓ Trivial cycle confirmed: x=1 with pattern {cycle['pattern_str']}")
            continue
        
        print(f"\n⚠️  NON-TRIVIAL CYCLE FOUND!")
        print(f"    Pattern: [{cycle['pattern_str']}]")
        print(f"    Starting value: x₀ = {cycle['x0_candidate']}")
        print(f"    Trajectory: {cycle.get('trajectory', [])}")
        print(f"    Source: {cycle['source_atlas']}")
        print()
        print("    THIS IS A MAJOR MATHEMATICAL DISCOVERY!")
        print("    The Collatz conjecture would be DISPROVEN.")
        print()
        print("    IMMEDIATE ACTIONS:")
        print("    1. DO NOT DELETE ANY FILES")
        print("    2. Verify manually: run the Collatz sequence from x₀")
        print("    3. Document everything")
        print("    4. Contact mathematicians")
    
    # Save to special file
    os.makedirs(REGISTRY_DIR, exist_ok=True)
    with open(REAL_CYCLES_FILE, "w", encoding="utf-8") as f:
        json.dump({
            "discovered_at": datetime.now().isoformat(),
            "cycles": real_cycles,
            "note": "VERIFY MANUALLY BEFORE ANNOUNCING",
        }, f, indent=2)
    
    print(f"\n    Saved to: {REAL_CYCLES_FILE}")
    print("=" * 70)


def update_runs_csv(M: int, A: int, amin: int, k: int, count: int, 
                    outfile: str, batch_root: str, batch_hash: str,
                    verify_ok: bool, wall_time: float, notes: str):
    """Append a row to RUNS.csv."""
    os.makedirs(REGISTRY_DIR, exist_ok=True)
    
    # Create header if file doesn't exist
    if not os.path.exists(RUNS_CSV):
        with open(RUNS_CSV, "w", encoding="utf-8") as f:
            f.write("date,machine,git_commit,M,A,amin,k,count,outfile,batch_root,batch_hash,verify_ok,wall_time_s,notes\n")
    
    # Get machine name
    import socket
    machine = socket.gethostname()[:10]
    
    # Append row
    with open(RUNS_CSV, "a", encoding="utf-8") as f:
        row = [
            datetime.now().strftime("%Y-%m-%d"),
            machine,
            "-",  # git commit
            str(M),
            str(A),
            str(amin),
            str(k),
            str(count),
            outfile,
            batch_root[:16] + "...",
            batch_hash[:16] + "...",
            "YES" if verify_ok else "NO",
            f"{wall_time:.1f}" if wall_time else "-",
            notes.replace(",", ";"),
        ]
        f.write(",".join(row) + "\n")


def update_checksums(outfile: str, checksum: str):
    """Append checksum to CHECKSUMS.txt."""
    os.makedirs(REGISTRY_DIR, exist_ok=True)
    
    if not os.path.exists(CHECKSUMS_TXT):
        with open(CHECKSUMS_TXT, "w", encoding="utf-8") as f:
            f.write("# Collatz-Ghost Atlas Checksums\n")
            f.write("# Format: SHA256  filename\n\n")
    
    with open(CHECKSUMS_TXT, "a", encoding="utf-8") as f:
        f.write(f"{checksum}  {outfile}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Automated atlas run with full post-processing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument("--M", type=int, required=True, help="Pattern length")
    parser.add_argument("--A", type=int, required=True, help="Max exponent")
    parser.add_argument("--amin", type=int, default=1, help="Min exponent")
    parser.add_argument("--k", type=int, default=28, help="Precision (2^k)")
    parser.add_argument("--scout", type=int, default=None, help="Scout mode: limit patterns")
    parser.add_argument("--out", type=str, default=None, help="Override output path")
    
    args = parser.parse_args()
    
    # Determine output path
    if args.out:
        outfile = args.out
    elif args.scout:
        os.makedirs(SCOUTS_DIR, exist_ok=True)
        outfile = f"{SCOUTS_DIR}/scout_M{args.M}_A{args.A}_amin{args.amin}_k{args.k}_N{args.scout}.jsonl"
    else:
        os.makedirs(ATLASES_DIR, exist_ok=True)
        outfile = f"{ATLASES_DIR}/atlas_M{args.M}_A{args.A}_amin{args.amin}_k{args.k}.jsonl"
    
    print("\n" + "=" * 60)
    print("         COLLATZ-GHOST AUTOMATED ATLAS RUN")
    print("=" * 60)
    print(f"\nParameters: M={args.M}, A={args.A}, amin={args.amin}, k={args.k}")
    if args.scout:
        print(f"Mode: SCOUT (max {args.scout} patterns)")
    else:
        print(f"Mode: FULL ATLAS")
    print(f"Output: {outfile}")
    print()
    
    start_time = datetime.now()
    
    # =========================================================================
    # STEP 1: Run prove-family
    # =========================================================================
    print("=" * 60)
    print("STEP 1: Running prove-family")
    print("=" * 60)
    
    cmd = [
        "collatz-ghost", "prove-family",
        "--M", str(args.M),
        "--A", str(args.A),
        "--amin", str(args.amin),
        "--k", str(args.k),
        "--out", outfile,
    ]
    if args.scout:
        cmd.extend(["--max-patterns", str(args.scout)])
    
    code, output = run_command(cmd)
    if code != 0:
        print(f"ERROR: prove-family failed with code {code}")
        print(output)
        return 1
    
    # Parse output for batch info
    count = 0
    batch_root = ""
    batch_hash = ""
    try:
        # The output is JSON, find the JSON object
        for line in output.strip().split("\n"):
            line = line.strip()
            if line.startswith("{") and "count" in line:
                result = json.loads(line)
                count = result.get("count", 0)
                batch_root = result.get("root", "")
                batch_hash = result.get("batch_hash", "")
                break
    except:
        pass
    
    # If count still 0, count lines in file
    if count == 0 and os.path.exists(outfile):
        with open(outfile, "r") as f:
            count = sum(1 for line in f if line.strip() and '"type": "A"' in line or '"type": "B"' in line)
    
    print(f"  Completed: {count} patterns processed")
    
    # =========================================================================
    # STEP 2: Verify certificates
    # =========================================================================
    print("\n" + "=" * 60)
    print("STEP 2: Verifying certificates")
    print("=" * 60)
    
    cmd = ["collatz-ghost", "verify", "--cert", outfile]
    code, output = run_command(cmd)
    
    verify_ok = (code == 0)
    if verify_ok:
        print("  ✓ All certificates verified")
    else:
        print("  ✗ VERIFICATION FAILED")
        print(output)
    
    # =========================================================================
    # STEP 3: Extract ghosts and check for real cycles
    # =========================================================================
    print("\n" + "=" * 60)
    print("STEP 3: Extracting ghosts and checking for real cycles")
    print("=" * 60)
    
    ghosts, real_cycles = extract_ghosts_and_check_real(outfile)
    
    trivial_ghosts = [g for g in ghosts if g.get("is_trivial")]
    nontrivial_ghosts = [g for g in ghosts if not g.get("is_trivial")]
    
    print(f"  Ghosts found: {len(ghosts)}")
    print(f"    Trivial (x=1 cycle): {len(trivial_ghosts)}")
    print(f"    Non-trivial: {len(nontrivial_ghosts)}")
    
    # Save to registry
    new_ghosts = save_ghosts_to_registry(ghosts)
    print(f"  New ghosts added to registry: {new_ghosts}")
    
    # Check for real cycles
    nontrivial_real = [c for c in real_cycles if not c.get("is_trivial")]
    if nontrivial_real:
        handle_real_cycle_found(nontrivial_real)
        # This is historic - stop everything
        return 99  # Special exit code for "cycle found"
    
    if nontrivial_ghosts:
        print("\n  ⚠️  NON-TRIVIAL GHOSTS (not verified as real cycles):")
        for g in nontrivial_ghosts[:10]:
            print(f"      [{g['pattern_str']}] x0={g.get('x0_candidate')}")
        if len(nontrivial_ghosts) > 10:
            print(f"      ... and {len(nontrivial_ghosts) - 10} more")
        print("\n  These patterns could not be excluded at k={args.k}.")
        print("  Consider running at higher k to see if they vanish.")
    
    # =========================================================================
    # STEP 4: Generate summary
    # =========================================================================
    print("\n" + "=" * 60)
    print("STEP 4: Generating summary")
    print("=" * 60)
    
    os.makedirs(SUMMARIES_DIR, exist_ok=True)
    summary_file = f"{SUMMARIES_DIR}/summary_M{args.M}_A{args.A}_amin{args.amin}_k{args.k}.txt"
    
    cmd = ["python3", "tools/summarize_atlas.py", outfile]
    code, output = run_command(cmd)
    
    with open(summary_file, "w", encoding="utf-8") as f:
        f.write(output)
    
    print(f"  Summary saved to: {summary_file}")
    
    # =========================================================================
    # STEP 5: Update registry
    # =========================================================================
    print("\n" + "=" * 60)
    print("STEP 5: Updating registry")
    print("=" * 60)
    
    end_time = datetime.now()
    wall_time = (end_time - start_time).total_seconds()
    
    # Compute checksum
    checksum = sha256_file(outfile)
    
    # Notes
    notes = f"{len(trivial_ghosts)} trivial + {len(nontrivial_ghosts)} non-trivial ghosts"
    if args.scout:
        notes = f"SCOUT: {notes}"
    
    # Update RUNS.csv
    update_runs_csv(
        M=args.M, A=args.A, amin=args.amin, k=args.k,
        count=count, outfile=outfile,
        batch_root=batch_root, batch_hash=batch_hash,
        verify_ok=verify_ok, wall_time=wall_time, notes=notes
    )
    print(f"  Updated: {RUNS_CSV}")
    
    # Update CHECKSUMS.txt
    update_checksums(outfile, checksum)
    print(f"  Updated: {CHECKSUMS_TXT}")
    
    # =========================================================================
    # FINAL REPORT
    # =========================================================================
    print("\n" + "=" * 60)
    print("                    RUN COMPLETE")
    print("=" * 60)
    print(f"""
  Atlas: {outfile}
  Patterns: {count}
  Verified: {'✓ YES' if verify_ok else '✗ NO'}
  Ghosts: {len(ghosts)} ({len(trivial_ghosts)} trivial, {len(nontrivial_ghosts)} non-trivial)
  Time: {wall_time:.1f}s
  Checksum: {checksum[:16]}...
  
  Files updated:
    - {outfile}
    - {summary_file}
    - {RUNS_CSV}
    - {CHECKSUMS_TXT}
    - {GHOSTS_JSONL}
""")
    
    if nontrivial_ghosts:
        print("  ⚠️  Non-trivial ghosts found - consider running at higher k")
    else:
        print("  ✓ All patterns excluded (except trivial cycle)")
    
    print("=" * 60 + "\n")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
