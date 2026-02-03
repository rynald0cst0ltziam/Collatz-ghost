<div align="center">

# 👻 Collatz-Ghost

**Certificate-Based 2-Adic Collatz Cycle Pattern Prover**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

*A rigorous, non-heuristic framework for systematic exclusion of Collatz cycle patterns with verifiable proofs*

</div>

---

## 🎯 What This Does

This tool proves that specific exponent patterns **cannot correspond to integer Collatz cycles**. Unlike testing individual integers, we enumerate the *pattern space* — proving structural impossibility.

| Method | Coverage | Description |
|--------|----------|-------------|
| **Type A** | ~99.98% | Exact rational fixed-point analysis |
| **Type B** | ~0.02% | 2-adic valuation constraint solving (DPLL-style) |

Patterns surviving both methods are **"ghosts"** — solutions in $\mathbb{Z}_2$ that may not be true integer cycles.

### Key Results

From millions of tested patterns:
- ✅ **All non-trivial patterns excluded**
- 👻 **Only trivial ghost survives**: `[2,2,2,...]` = the known cycle $x=1$
- 📜 **Every exclusion has a verifiable certificate**

---

## 🚀 Quick Start

```bash
# Install
git clone https://github.com/[your-repo]/collatz-ghost.git
cd collatz-ghost
python3 -m pip install -e .

# Run automated atlas (recommended)
python tools/run_atlas.py --M 10 --A 3 --k 28

# Or manual commands:
collatz-ghost prove --pattern 2,1,3,1 --k 32
collatz-ghost prove-family --M 10 --A 4 --k 28 --out results.jsonl
collatz-ghost verify --cert results.jsonl
```

## Documentation

| Document | Description |
|----------|-------------|
| [docs/WHAT_ARE_GHOSTS.md](docs/WHAT_ARE_GHOSTS.md) | **Start here** — What ghosts are and why they matter |
| [docs/USAGE.md](docs/USAGE.md) | Complete CLI reference and configuration guide |
| [docs/THEORY.md](docs/THEORY.md) | Mathematical foundations |
| [docs/QUICKSTART.md](docs/QUICKSTART.md) | Quick practical guide |
| [docs/GLOSSARY.md](docs/GLOSSARY.md) | Terminology reference |
| [docs/NOVELTY.md](docs/NOVELTY.md) | What makes this approach unique |
| [docs/GHOST_TRACKING.md](docs/GHOST_TRACKING.md) | Ghost tracking and analysis system |
| [docs/REAL_CYCLE_PROTOCOL.md](docs/REAL_CYCLE_PROTOCOL.md) | What happens if a real cycle is found |

## Certificate Types

### Type A (Rational Exclusion)
```json
{
  "type": "A",
  "pattern": [2, 1, 3, 1],
  "B": "151",
  "D": "47",
  "reason": "non-integer rational fixed point (D does not divide B)"
}
```

### Type B (2-adic Constraint Proof)
```json
{
  "type": "B",
  "pattern": [2, 2, 2],
  "k": 32,
  "reason": "valuation constraints SAT at target k (ghost/2-adic solution exists)"
}
```

## Project Structure

```
collatz_ghost/
├── collatz_ghost/       # Core Python package
│   ├── solver.py        # Main proving logic
│   ├── verifier.py      # Independent certificate verification
│   ├── affine.py        # Affine map composition
│   └── ...
├── docs/                # Comprehensive documentation
├── registry/            # Run tracking (RUNS.csv, BOXES.md)
├── atlases/             # Completed atlas files
├── scouts/              # Scouting run outputs
├── summaries/           # Human-readable summaries
└── tools/               # Analysis utilities
```
## Already Cleared (Updated 03022026)

| Box       | Total Patterns | Status        | Result                 |
|-----------|----------------|---------------|------------------------|
| M28, A2   | 268,435,456    | ✓ Verified    | 0 non-trivial cycles   |
| M24, A2   | 16,777,216     | ✓ Verified    | 0 non-trivial cycles   |
| M14, A3   | 4,782,969      | ✓ Verified    | 0 non-trivial cycles   |
| M12, A3   | 531,441        | ✓ Verified    | 0 non-trivial cycles   |


## Key Concepts

- **Pattern**: Sequence of 2-adic valuations [a₁, a₂, ..., aₘ] for a potential cycle
- **Box**: All patterns with length M and exponents in [amin, A]
- **Ghost**: A pattern that satisfies 2-adic constraints at precision 2^k
- **Atlas**: Complete certificate file for a box

## The Only Known Ghost

Pattern `[2, 2, 2, ...]` (any length) corresponds to the **trivial Collatz cycle** x=1:
```
T_2(1) = (3·1+1)/4 = 1
```

All other patterns tested so far are excluded.

## What Makes This Novel

1. **Certificate-based proofs** — every exclusion is independently verifiable
2. **Systematic enumeration** — exhaustive coverage of pattern-space regions
3. **Ghost tracking** — infrastructure for studying 2-adic survivors
4. **No heuristics** — exact arithmetic, no probabilistic arguments

See [docs/NOVELTY.md](docs/NOVELTY.md) for full discussion.

---

## 📊 The Mathematics

For a potential cycle of length $M$ with exponent pattern $(a_1, \ldots, a_M)$:

**Cycle Equation:**
$$x_0 = \frac{B}{2^E - 3^M}$$

where $E = \sum a_i$ and $B$ is computed from the pattern.

**Type A excludes** if $x_0 \notin \mathbb{N}^+$

**Type B explores** residue classes mod $2^k$ when Type A fails.

See [docs/PAPER.md](docs/PAPER.md) for complete mathematical treatment.

---

## 🔬 Theoretical Foundation

This framework implements insights from recent theoretical work:

- **Siegel (2024)**: Non-Archimedean spectral theory for Collatz
- **Dhiman & Pandey (2025)**: Ghost cycles in $\mathbb{Z}_2$ ([arXiv:2601.12772](https://arxiv.org/abs/2601.12772))

**What we add:**
- ✅ Exhaustive pattern enumeration
- ✅ Verifiable certificates
- ✅ Systematic atlas building
- ✅ Ghost tracking infrastructure

---

## 🤝 Contributing

Contributions welcome! Priority areas:
- Larger box coverage
- Performance optimization
- Formal verification (Lean/Coq)
- Ghost stability analysis

---

## 📄 Citation

If you use this work, please cite:

```bibtex
@software{collatz_ghost,
  author = {Stoltz, Rynaldo},
  title = {Collatz-Ghost: Certificate-Based 2-Adic Cycle Pattern Prover},
  year = {2026},
  url = {https://github.com/rynald0cst0ltziam/Collatz-ghost}
}
```

---

## 📜 License

MIT License - Copyright (c) 2026 Rynaldo Stoltz

See [LICENSE](LICENSE) for full details.

