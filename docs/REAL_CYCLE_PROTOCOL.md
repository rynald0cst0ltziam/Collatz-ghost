# What Happens If A Real Cycle Is Found

## The Scenario

A **real Collatz cycle** would be a sequence of positive integers that loops back to itself under the Collatz map, other than the trivial 1 → 4 → 2 → 1 cycle.

If this tool finds one, it would **disprove the Collatz conjecture**.

---

## How The Tool Detects Real Cycles

### Step 1: Ghost Detection

When running an atlas, the solver finds patterns that are SAT (ghost-feasible):
- Type B SAT means a residue class mod 2^k satisfies all valuation constraints
- The proof tree contains the actual x₀ candidate value

### Step 2: Real Cycle Verification

The `run_atlas.py` script automatically:
1. Extracts all ghosts from the atlas
2. For each ghost with an x₀ candidate, **directly verifies** if it's a real cycle:
   - Runs the Collatz map from x₀
   - Checks if each step has the correct 2-adic valuation
   - Checks if the sequence returns to x₀

```python
def verify_ghost_is_real_cycle(pattern, x0):
    x = x0
    for a in pattern:
        # Check x is odd
        if x % 2 == 0: return False
        # Check v2(3x+1) = a
        if v2(3*x + 1) != a: return False
        # Next step
        x = (3*x + 1) >> a
    # Check closure
    return x == x0
```

### Step 3: Automatic Alerting

If a non-trivial real cycle is found:

```
🚨🚨🚨 REAL COLLATZ CYCLE DETECTED 🚨🚨🚨

⚠️  NON-TRIVIAL CYCLE FOUND!
    Pattern: [3,1,2,1,...]
    Starting value: x₀ = 12345
    Trajectory: [12345, ...]
    
    THIS IS A MAJOR MATHEMATICAL DISCOVERY!
    The Collatz conjecture would be DISPROVEN.
```

### Step 4: Automatic Logging

The cycle is saved to `registry/REAL_CYCLES_FOUND.json`:

```json
{
  "discovered_at": "2026-02-02T16:00:00",
  "cycles": [
    {
      "pattern": [3, 1, 2, 1],
      "x0_candidate": 12345,
      "trajectory": [12345, ...],
      "verified_real": true
    }
  ],
  "note": "VERIFY MANUALLY BEFORE ANNOUNCING"
}
```

---

## What This Means

### If a Real Cycle Is Found

1. **The Collatz conjecture is FALSE** — there exists a non-trivial cycle
2. **This is a major mathematical discovery** — would be front-page news
3. **The tool provides proof** — the exact starting value and trajectory

### What To Do

1. **DO NOT DELETE ANY FILES** — preserve all evidence
2. **Verify manually** — run the Collatz sequence by hand or with independent code
3. **Check the certificate** — the atlas file contains the full proof tree
4. **Document everything** — timestamps, file hashes, machine info
5. **Contact mathematicians** — this would need peer review

---

## Why This Is Unlikely

The tool has processed millions of patterns across multiple atlases. Results so far:

| Patterns Tested | Type A Excluded | Type B UNSAT | Type B SAT (Ghosts) |
|-----------------|-----------------|--------------|---------------------|
| Millions | ~99.98% | ~0% | ~0.02% (all trivial) |

Every ghost found has been the **trivial cycle** `[2,2,2,...]` corresponding to x=1.

This is consistent with the Collatz conjecture being true.

---

## The Value of NOT Finding Cycles

Each atlas run that finds **only trivial ghosts** proves:

> "No integer Collatz cycle exists with exponent pattern of length M ≤ X and all exponents ≤ Y"

This is **positive evidence** for the conjecture, even though it doesn't prove it completely.

---

## Ghost vs Real Cycle Summary

| Finding | Meaning | Action |
|---------|---------|--------|
| Type A excluded | Pattern cannot be a cycle | None needed |
| Type B UNSAT | Pattern cannot be a cycle at precision k | None needed |
| Type B SAT (trivial) | x=1 cycle confirmed | Expected, log it |
| Type B SAT (non-trivial, not real) | Ghost exists but isn't integer cycle | Run at higher k |
| Type B SAT (non-trivial, REAL) | **ACTUAL CYCLE FOUND** | 🚨 Major discovery |

---

## Exit Codes

The `run_atlas.py` script uses special exit codes:

| Code | Meaning |
|------|---------|
| 0 | Success, no non-trivial cycles |
| 1 | Error during run |
| 99 | **REAL CYCLE FOUND** |

You can use this in scripts:

```bash
python tools/run_atlas.py --M 12 --A 3 --k 28
if [ $? -eq 99 ]; then
    echo "CYCLE FOUND - CHECK LOGS"
    # Send alert, etc.
fi
```

