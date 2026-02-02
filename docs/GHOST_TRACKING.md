# Ghost Tracking System

## Overview

The ghost tracking system provides comprehensive storage, analysis, and monitoring of ghost patterns (Type B SAT survivors) across all atlas runs.

## What Gets Tracked

For each ghost found:
- **Pattern**: The exponent sequence `[a₁, a₂, ..., aₘ]`
- **Precision (k)**: The modulus 2^k at which SAT was observed
- **x₀ candidate**: The residue class mod 2^k that satisfies constraints
- **Source atlas**: Which atlas file the ghost came from
- **Timestamp**: When the ghost was first observed
- **Trivial flag**: Whether pattern is `[2,2,2,...]` (the known x=1 cycle)

## Files

| File | Purpose |
|------|---------|
| `registry/ghosts.jsonl` | Persistent ghost registry (append-only) |
| `registry/ghost_analysis.json` | Latest analysis summary |
| `tools/ghost_tracker.py` | Ghost tracking CLI tool |

## Commands

### Extract Ghosts from Atlas
```bash
python tools/ghost_tracker.py extract atlases/atlas_M12_A3_k28.jsonl
```

Extracts all SAT patterns from an atlas and adds new ones to the registry.

### List All Known Ghosts
```bash
python tools/ghost_tracker.py list
```

Shows all ghosts in the registry, grouped by pattern.

### Analyze Ghost Stability
```bash
python tools/ghost_tracker.py stability --pattern 2,2,2,2,2,2,2,2,2,2,2,2
```

Shows at which precision levels a specific pattern has been observed as SAT.

### Compare Precision Ladder
```bash
python tools/ghost_tracker.py ladder atlases/atlas_M12_A3_k24.jsonl atlases/atlas_M12_A3_k32.jsonl
```

Compares ghost sets between two atlases to find:
- **Stable ghosts**: SAT at both precision levels
- **Vanished ghosts**: SAT at lower k, UNSAT at higher k
- **New ghosts**: Only appeared at higher k (rare)

### Generate Full Report
```bash
python tools/ghost_tracker.py report
```

Produces a comprehensive ghost population report with:
- Total observations and unique patterns
- Trivial vs non-trivial breakdown
- Precision (k) distribution
- Pattern length (M) distribution
- Stable ghosts (observed at multiple k)
- Non-trivial ghost list

## Workflow Integration

### After Every Atlas Run

1. **Verify** the atlas:
   ```bash
   collatz-ghost verify --cert atlases/atlas_M12_A3_k28.jsonl
   ```
   The verify command now reports ghosts found and prompts for extraction.

2. **Extract** ghosts to registry:
   ```bash
   python tools/ghost_tracker.py extract atlases/atlas_M12_A3_k28.jsonl
   ```

3. **Update** the ghost report:
   ```bash
   python tools/ghost_tracker.py report
   ```

### Precision Ladder Analysis

When running the same box at multiple k values:

```bash
# Run at k=24
collatz-ghost prove-family --M 12 --A 3 --k 24 --out atlases/atlas_M12_A3_k24.jsonl

# Run at k=32
collatz-ghost prove-family --M 12 --A 3 --k 32 --out atlases/atlas_M12_A3_k32.jsonl

# Extract ghosts from both
python tools/ghost_tracker.py extract atlases/atlas_M12_A3_k24.jsonl
python tools/ghost_tracker.py extract atlases/atlas_M12_A3_k32.jsonl

# Compare ghost sets
python tools/ghost_tracker.py ladder atlases/atlas_M12_A3_k24.jsonl atlases/atlas_M12_A3_k32.jsonl
```

## Interpreting Results

### Trivial Ghosts
Pattern `[2,2,2,...]` (any length) is the **trivial cycle** x=1:
```
T_2(1) = (3·1+1)/4 = 1
```
This is expected and correct. The tool correctly identifies the known Collatz cycle.

### Non-Trivial Ghosts
If a non-trivial ghost is found:
1. **Don't panic** — it's probably just a ghost that will vanish at higher k
2. **Run at higher k** to see if it persists
3. **Document it** in the registry
4. **Investigate** if it persists at k > 40

### Ghost Attrition
The ladder comparison shows "ghost attrition rate" — what percentage of ghosts vanish when moving to higher precision. Typical patterns:
- Most ghosts vanish as k increases
- Trivial ghosts (`[2,2,...]`) never vanish (they're real)
- Persistent non-trivial ghosts would be extraordinary

## Example Output

```
============================================================
           COLLATZ-GHOST: GHOST POPULATION REPORT
============================================================

Generated: 2026-02-02T15:53:39.999877

--- Summary ---
Total ghost observations: 4
Unique ghost patterns: 3
  Trivial ([2,2,...] family): 3
  Non-trivial: 0

--- Precision (k) Distribution ---
  k=24: 1 observations
  k=28: 2 observations
  k=32: 1 observations

--- Pattern Length (M) Distribution ---
  M=8: 1 patterns
  M=12: 1 patterns
  M=14: 1 patterns

--- Stable Ghosts (observed at multiple k) ---
  [2,2,2,2,2,2,2,2,2,2,2,2] at k=[28, 32] [TRIVIAL]

--- Non-Trivial Ghosts ---
  None found! Only trivial ghosts exist.
  This is GOOD - it means all non-trivial patterns are excluded.

============================================================
```


## Registry Format

Each line in `registry/ghosts.jsonl`:
```json
{
  "pattern": [2, 2, 2, 2, 2, 2, 2, 2],
  "pattern_str": "2,2,2,2,2,2,2,2",
  "M": 8,
  "k": 24,
  "source_atlas": "atlases/atlas_M8_A3_amin1_k24.jsonl",
  "first_seen": "2026-02-02T15:52:11.733137",
  "x0_candidate": 1,
  "is_trivial": true,
  "notes": ""
}
```

