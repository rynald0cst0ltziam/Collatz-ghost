# The Mathematics of Collatz Ghosts

## A Complete Guide to 2-adic Cycle Pattern Exclusion

---

## Table of Contents

1. [The Collatz Conjecture](#the-collatz-conjecture)
2. [What Are Collatz Ghosts?](#what-are-collatz-ghosts)
3. [The Odd-Iterate Formulation](#the-odd-iterate-formulation)
4. [Exponent Patterns and Cycles](#exponent-patterns-and-cycles)
5. [Type A Certificates: Rational Fixed-Point Exclusion](#type-a-certificates)
6. [Type B Certificates: 2-adic Valuation Constraints](#type-b-certificates)
7. [Why This Matters](#why-this-matters)
8. [What Finding a Ghost Means](#what-finding-a-ghost-means)
9. [The Novelty of This Approach](#the-novelty-of-this-approach)

---

## The Collatz Conjecture

The Collatz conjecture (also known as the 3n+1 problem) states:

> Starting from any positive integer n, repeatedly apply:
> - If n is even: n → n/2
> - If n is odd: n → 3n+1
> 
> Eventually, you will reach 1.

This has been verified for all integers up to approximately 2^68, yet remains unproven.

The conjecture is equivalent to proving that **no non-trivial cycles exist** — the only cycle is 1 → 4 → 2 → 1.

---

## What Are Collatz Ghosts?

A **Collatz ghost** is a mathematical phantom: a pattern that *looks like* it could be a cycle when examined through the lens of 2-adic arithmetic, but doesn't correspond to any actual integer cycle.

More precisely:

> A **ghost** is a residue class modulo 2^k that satisfies all the local 2-adic valuation constraints required for a cycle, but either:
> 1. Doesn't lift to a true integer solution, or
> 2. The integer it represents doesn't actually form a cycle

Think of it like this: if you're looking for a criminal and you have a partial fingerprint, many people might match that partial print. A ghost is someone who matches the partial evidence but isn't the actual criminal.

### The Ghost Metaphor

The name "ghost" captures the essence perfectly:
- **Ghosts appear real** when you look at them through a particular lens (modular arithmetic)
- **Ghosts vanish** when you try to grab them (lift to true integers)
- **Ghosts haunt specific regions** of the pattern space (SAT survivors at precision k)

---

## The Odd-Iterate Formulation

Instead of the standard Collatz map, we use the **odd-iterate** (or "shortcut") formulation:

For an odd integer x, define:
```
T(x) = (3x + 1) / 2^{v₂(3x+1)}
```

Where v₂(n) is the **2-adic valuation** of n — the largest power of 2 dividing n.

This map:
1. Takes an odd integer
2. Computes 3x+1 (always even)
3. Divides out ALL factors of 2
4. Returns the next odd integer

**Example:** T(7) = (3·7+1)/2^{v₂(22)} = 22/2 = 11

The exponent a = v₂(3x+1) tells us "how many times we divided by 2."

---

## Exponent Patterns and Cycles

A **cycle of length M** in the odd-iterate map is a sequence:
```
x₀ → x₁ → x₂ → ... → x_{M-1} → x₀
```

Each step has an associated exponent aᵢ = v₂(3xᵢ + 1).

The **exponent pattern** is the tuple [a₁, a₂, ..., aₘ].

### Key Insight

If a cycle exists with pattern [a₁, ..., aₘ], then:
1. The composed map F = T_{aₘ} ∘ ... ∘ T_{a₁} must satisfy F(x₀) = x₀
2. Each step must have **exactly** the specified 2-adic valuation

This gives us two independent constraint systems to check.

---

## Type A Certificates

### The Affine Map Structure

Each odd-step T_a(x) = (3x+1)/2^a is an affine map over rationals.

Composing M steps gives:
```
F(x) = (3^M · x + B) / 2^E
```

Where:
- E = a₁ + a₂ + ... + aₘ (sum of exponents)
- B is computed by the composition formula

### The Fixed-Point Equation

For F(x) = x:
```
x₀ = B / (2^E - 3^M)
```

This is the **unique rational fixed point** of the composed map.

### Type A Exclusion

A pattern is excluded by Type A if:
1. **D = 0**: Degenerate case (2^E = 3^M, which only happens for E=M=0)
2. **D ∤ B**: The fixed point is not an integer
3. **B/D ≤ 0**: The fixed point is non-positive

**Type A is exact arithmetic** — no approximation, no modular truncation.

### Example

Pattern [2,1,3,1]:
- Composed map: F(x) = (81x + 151) / 128
- Fixed point: x₀ = 151 / (128 - 81) = 151/47
- Since 47 ∤ 151, this is non-integer → **excluded**

---

## Type B Certificates

### When Type A Fails

Type A fails when the rational fixed point IS a positive integer. In this case, we need a second line of attack.

### 2-adic Valuation Constraints

The constraint v₂(3x+1) = a is **extremely restrictive**:

```
v₂(3x+1) = a  ⟺  3x+1 ≡ 2^a (mod 2^{a+1})
            ⟺  x ≡ (2^a - 1) · 3^{-1} (mod 2^{a+1})
```

This pins down x modulo 2^{a+1} **uniquely**.

### The DPLL-Style Proof Tree

Type B builds a binary search tree over residue classes:
1. Start with the residue class required by the first valuation constraint
2. Simulate the pattern with current precision
3. If contradiction found → leaf node (UNSAT)
4. If precision exhausted without contradiction → branch by adding one bit
5. Continue until reaching target precision k or all branches contradict

### UNSAT vs SAT

- **UNSAT**: All branches lead to contradictions → pattern excluded
- **SAT**: At least one branch survives → a "ghost" exists at precision 2^k

---

## Why This Matters

### The Cycle Exclusion Strategy

To prove no non-trivial cycles exist, one approach is:
1. Enumerate all possible exponent patterns
2. Prove each pattern cannot be a cycle
3. If all patterns are excluded, no cycles exist

This is the **pattern-space approach** to Collatz.

### What We're Actually Proving

Each certificate proves:
> "No positive integer Collatz cycle has exponent pattern [a₁, ..., aₘ]"

By clearing "boxes" of patterns (all patterns with M steps and exponents ≤ A), we systematically exclude large regions of the cycle-pattern space.

### The Trivial Cycle

The pattern [2] (and its repetitions [2,2], [2,2,2], etc.) corresponds to the trivial cycle:
```
1 → (3·1+1)/4 = 1
```

This is the ONLY known integer Collatz cycle, and our tool correctly identifies it as SAT.

---

## What Finding a Ghost Means

### Ghost ≠ Cycle

A ghost (Type B SAT at precision k) means:
> "There exists a residue class mod 2^k that satisfies all valuation constraints and closure"

This does NOT mean a cycle exists. The ghost might:
1. **Fail to lift**: No integer in that residue class actually works
2. **Lift to a non-cycle**: The integer exists but doesn't form a cycle
3. **Be the trivial cycle**: x=1 with pattern [2,2,...]

### Ghost Survivor Analysis

By running the same pattern at increasing k (precision ladder):
- k=16 → k=24 → k=32 → k=40

We can observe:
- Do ghosts persist or vanish at higher precision?
- Which patterns have "stable" ghosts?
- Is there structure to the ghost-feasible region?

### The Deep Question

If a ghost persists at arbitrarily high k, does it correspond to a true cycle?

This is related to the **2-adic lifting problem** and connects to deep questions in number theory.

---

## The Novelty of This Approach

### What's Known in the Literature

The 2-adic approach to Collatz is not new. Key prior work:
- **Lagarias (1985)**: Comprehensive survey of Collatz, mentions 2-adic analysis
- **Wirsching (1998)**: "The Dynamical System Generated by the 3n+1 Function"
- **Monks (2006)**: Sufficiency conditions for cycle non-existence

### What's Novel Here

1. **Certificate-Based Proofs**
   - Every exclusion comes with a verifiable certificate
   - Independent verifier doesn't trust the solver
   - Cryptographic hashing for integrity

2. **Systematic Atlas Enumeration**
   - Exhaustive clearing of pattern-space "boxes"
   - Reproducible, auditable runs
   - Merkle-style batch hashing

3. **DPLL-Style Proof Trees**
   - Explicit representation of the search space
   - Verifiable contradiction at each leaf
   - SAT/UNSAT determination at target precision

4. **Ghost Tracking Infrastructure**
   - Precision ladders for survivor analysis
   - Structured comparison across k values
   - Foundation for ghost stability research

---

## Appendix: Mathematical Details

### The Composition Formula

For T_a(x) = (3x+1)/2^a composed with map (Ax+B)/2^E:

```
T_a((Ax+B)/2^E) = (3(Ax+B)/2^E + 1) / 2^a
                = (3Ax + 3B + 2^E) / 2^{E+a}
```

So: A' = 3A, B' = 3B + 2^E, E' = E + a

### The Valuation Constraint Derivation

v₂(3x+1) = a means:
- 2^a | (3x+1)
- 2^{a+1} ∤ (3x+1)

This is equivalent to:
```
3x + 1 ≡ 2^a (mod 2^{a+1})
3x ≡ 2^a - 1 (mod 2^{a+1})
x ≡ (2^a - 1) · 3^{-1} (mod 2^{a+1})
```

Where 3^{-1} mod 2^{a+1} exists because gcd(3, 2^{a+1}) = 1.

### The Closure Condition

For a cycle, we need x_M = x_0 (mod 2^m) at sufficient precision m.

The simulation tracks x through the pattern, reducing precision as we divide by 2^{aᵢ} at each step. If the final x doesn't match the initial x at the available precision, we have a closure contradiction.

---
