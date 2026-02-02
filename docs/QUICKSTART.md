# Collatz-Ghost Quickstart Guide

## Installation

```bash
cd collatz_ghost
python3 -m pip install -e .
```

## Basic Commands

### Prove a Single Pattern
```bash
collatz-ghost prove --pattern 2,1,3,1 --k 32
```

### Prove a Family (Box)
```bash
collatz-ghost prove-family --M 10 --A 3 --k 28 --out results.jsonl
```

### Verify Certificates
```bash
collatz-ghost verify --cert results.jsonl
```

## Understanding Output

### Type A Certificate
```json
{
  "type": "A",
  "pattern": [2, 1, 3, 1],
  "B": "151",
  "D": "47",
  "reason": "non-integer rational fixed point (D does not divide B)"
}
```
**Meaning:** Pattern excluded — the rational fixed point is not an integer.

### Type B Certificate (UNSAT)
```json
{
  "type": "B",
  "pattern": [...],
  "k": 32,
  "reason": "UNSAT: no solution modulo 2^32 satisfying exact valuation constraints"
}
```
**Meaning:** Pattern excluded — no valid residue class exists at precision 2^k.

### Type B Certificate (SAT)
```json
{
  "type": "B",
  "pattern": [2, 2, 2],
  "k": 32,
  "reason": "valuation constraints SAT at target k (ghost/2-adic solution exists)"
}
```
**Meaning:** A "ghost" exists — a residue class satisfies constraints at this precision. This does NOT mean a cycle exists; it means this pattern cannot be excluded at precision k.

## Workflow

1. **Scout** a box with low k and limited patterns:
   ```bash
   collatz-ghost prove-family --M 12 --A 3 --k 16 --out scout.jsonl --max-patterns 1000
   ```

2. **Full run** if scout looks good:
   ```bash
   collatz-ghost prove-family --M 12 --A 3 --k 28 --out atlases/atlas_M12_A3_k28.jsonl
   ```

3. **Verify** the output:
   ```bash
   collatz-ghost verify --cert atlases/atlas_M12_A3_k28.jsonl
   ```

4. **Summarize** the results:
   ```bash
   python3 tools/summarize_atlas.py atlases/atlas_M12_A3_k28.jsonl
   ```

5. **Register** in `registry/RUNS.csv` and update `registry/BOXES.md`

## Key Parameters

| Parameter | Description |
|-----------|-------------|
| `--M` | Pattern length (number of odd steps) |
| `--A` | Maximum exponent value |
| `--amin` | Minimum exponent value (default: 1) |
| `--k` | Target precision (modulus 2^k) |
| `--max-patterns` | Limit for scouting runs |

## Box Size Formula

Number of patterns in box (M, A, amin):
```
(A - amin + 1)^M
```

Examples:
- M=12, A=3, amin=1: 3^12 = 531,441 patterns
- M=14, A=3, amin=1: 3^14 = 4,782,969 patterns
- M=24, A=2, amin=1: 2^24 = 16,777,216 patterns

