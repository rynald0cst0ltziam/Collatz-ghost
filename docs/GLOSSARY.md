# Collatz-Ghost Glossary

## Core Concepts

### 2-adic Valuation (v₂)
The largest power of 2 dividing an integer. For example:
- v₂(12) = 2 (since 12 = 4 × 3 = 2² × 3)
- v₂(8) = 3 (since 8 = 2³)
- v₂(7) = 0 (7 is odd)

### Affine Map
A function of the form f(x) = (Ax + B) / 2^E. The Collatz odd-step is an affine map.

### Atlas
A complete JSONL file containing certificates for all patterns in a box. Named like `atlas_M12_A3_k28.jsonl`.

### Batch Root
A Merkle-style hash of all certificate hashes in an atlas. Provides integrity verification for the entire batch.

### Box
A Cartesian product of exponent choices: all patterns of length M with exponents in [amin, A]. Written as (M, A, amin, k).

### Certificate
A verifiable proof that a pattern is excluded (Type A or Type B UNSAT) or that a ghost exists (Type B SAT).

### Closure
The requirement that a cycle returns to its starting point: x_M = x_0.

### Exponent Pattern
The sequence [a₁, a₂, ..., aₘ] of 2-adic valuations for each step in a potential cycle.

---

## Ghost-Related Terms

### Ghost
A residue class mod 2^k that satisfies all valuation constraints and closure, but may not correspond to a true integer cycle. Ghosts "haunt" the pattern space.

### Ghost Survivor
A pattern that remains SAT (ghost-feasible) at a given precision k. Survivors at high k are of particular interest.

### Ghost Stability
The phenomenon of ghosts persisting (or vanishing) as precision k increases. Stable ghosts are patterns that remain SAT at all tested k values.

### Ghost-Feasible Region
The set of patterns that have ghosts at a given precision. This region typically shrinks as k increases.

### Precision Ladder
Running the same box at increasing k values (e.g., k=16→24→32→40) to study ghost stability.

---

## Certificate Types

### Type A Certificate
Exclusion based on the rational fixed-point formula. The pattern is excluded if x₀ = B/D is:
- Non-integer (D ∤ B)
- Non-positive (B/D ≤ 0)
- Degenerate (D = 0)

### Type B Certificate
Exclusion (or ghost detection) based on 2-adic valuation constraints. Uses a DPLL-style proof tree.

### Type B UNSAT
All branches of the proof tree lead to contradictions. The pattern is excluded.

### Type B SAT
At least one branch survives to precision k. A ghost exists; the pattern cannot be excluded at this precision.

---

## Proof Tree Terms

### DPLL
Davis-Putnam-Logemann-Loveland algorithm. A backtracking search algorithm for SAT solving. Our proof tree uses a similar structure.

### Leaf Node
A terminal node in the proof tree. Either a contradiction (UNSAT) or a surviving residue class (SAT).

### Branching
Splitting the search by adding one bit of precision. Each node has two children: bit=0 and bit=1.

### Contradiction
A local failure in the proof tree:
- Valuation mismatch: v₂(3x+1) ≠ expected exponent
- Closure mismatch: x_M ≢ x_0 at available precision
- Parity violation: x is even when it should be odd

---

## Operational Terms

### Scout Run
A quick, limited run to test feasibility before committing to a full atlas. Uses `--max-patterns`.

### Clearing a Box
Completing a full atlas run with verification for a given (M, A, amin, k).

### Registry
The tracking system for completed runs: `RUNS.csv`, `BOXES.md`, `CHECKSUMS.txt`.

### Verification
Running `collatz-ghost verify` to independently check all certificates in an atlas.

---

## Mathematical Notation

| Symbol | Meaning |
|--------|---------|
| M | Pattern length (number of odd steps) |
| A | Maximum exponent value |
| amin | Minimum exponent value |
| k | Target precision (modulus 2^k) |
| v₂(n) | 2-adic valuation of n |
| T_a(x) | Odd-step map: (3x+1)/2^a |
| F(x) | Composed map for full pattern |
| B, D | Numerator and denominator of rational fixed point |
| E | Sum of exponents in pattern |

