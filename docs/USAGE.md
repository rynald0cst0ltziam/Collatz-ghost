# Collatz-Ghost Usage Guide

## Installation

```bash
cd collatz_ghost
python3 -m pip install -e .
```

Requires Python 3.10+. No external dependencies.

---

## CLI Commands

### `collatz-ghost prove`

Prove/exclude a single exponent pattern.

```bash
collatz-ghost prove --pattern 2,1,3,1 --k 32
```

**Options:**
| Option | Default | Description |
|--------|---------|-------------|
| `--pattern` | (required) | Comma-separated exponents, e.g., `2,1,3,1` |
| `--k` | 32 | Target precision (modulus 2^k) for Type B |
| `--max-nodes` | 2,000,000 | Max nodes in proof tree (safety cap) |

**Output:** JSON certificate (Type A or Type B)

---

### `collatz-ghost prove-family`

Enumerate and prove all patterns in a box.

```bash
collatz-ghost prove-family --M 12 --A 3 --k 28 --out atlases/atlas_M12_A3_k28.jsonl
```

**Options:**
| Option | Default | Description |
|--------|---------|-------------|
| `--M` | (required) | Pattern length (number of odd steps) |
| `--A` | (required) | Maximum exponent value |
| `--amin` | 1 | Minimum exponent value |
| `--k` | 28 | Target precision (modulus 2^k) |
| `--out` | `results.jsonl` | Output JSONL file path |
| `--max-patterns` | None | Optional cap for scouting runs |

**Output:** JSONL file with certificates + BATCH record

---

### `collatz-ghost verify`

Verify certificates in a JSONL file.

```bash
collatz-ghost verify --cert atlases/atlas_M12_A3_k28.jsonl
```

**Options:**
| Option | Default | Description |
|--------|---------|-------------|
| `--cert` | (required) | Path to JSONL certificate file |
| `--verbose` | false | Print status for each certificate |

**Output:** Verification summary + ghost report

---

## Ghost Tracker Commands

### `python tools/ghost_tracker.py extract`

Extract ghosts from atlas and add to registry.

```bash
python tools/ghost_tracker.py extract atlases/atlas_M12_A3_k28.jsonl
```

### `python tools/ghost_tracker.py list`

List all known ghosts in the registry.

```bash
python tools/ghost_tracker.py list
```

### `python tools/ghost_tracker.py stability`

Analyze ghost stability across k values.

```bash
python tools/ghost_tracker.py stability --pattern 2,2,2,2,2,2,2,2,2,2,2,2
```

### `python tools/ghost_tracker.py ladder`

Compare ghost sets between two atlases.

```bash
python tools/ghost_tracker.py ladder atlases/atlas_M12_A3_k24.jsonl atlases/atlas_M12_A3_k32.jsonl
```

### `python tools/ghost_tracker.py report`

Generate comprehensive ghost population report.

```bash
python tools/ghost_tracker.py report
```

---

## Atlas Summarizer

```bash
python tools/summarize_atlas.py atlases/atlas_M12_A3_k28.jsonl
```

**Options:**
| Option | Description |
|--------|-------------|
| `--compare <file>` | Compare SAT sets with another atlas |
| `--show-sat` | Print SAT patterns |
| `--top-sat N` | How many SAT patterns to print (default: 50) |
| `--json` | Emit machine-readable JSON summary |

---

## Configuration

### Solver Parameters

| Parameter | Meaning | Typical Values |
|-----------|---------|----------------|
| `k` | Precision (modulus 2^k) | 16 (scout), 24-28 (baseline), 32-40 (research) |
| `M` | Pattern length | 8-14 (laptop), 15-24 (PC) |
| `A` | Max exponent | 2-3 (deep), 4-5 (wide) |
| `amin` | Min exponent | 1 (default), 2 (no-1s), 3 (no-1s-or-2s) |
| `max_nodes` | Proof tree cap | 2M default, increase for complex patterns |

### Box Size Formula

```
patterns = (A - amin + 1)^M
```

Examples:
| Box | Patterns | Time Estimate |
|-----|----------|---------------|
| M=8, A=3 | 6,561 | ~seconds |
| M=10, A=3 | 59,049 | ~minutes |
| M=12, A=3 | 531,441 | ~10-30 min |
| M=14, A=3 | 4,782,969 | ~hours |
| M=24, A=2 | 16,777,216 | ~many hours |

### Precision Guidelines

| k | Use Case |
|---|----------|
| 16 | Quick scouting, feasibility check |
| 24 | Baseline runs, initial atlas |
| 28 | Standard research-grade |
| 32 | High precision, ghost refinement |
| 40+ | Deep ghost analysis (expensive) |

---

## Workflow

### Standard Box Clearing

```bash
# 1. Scout (optional)
collatz-ghost prove-family --M 12 --A 3 --k 16 --out scouts/scout_M12_A3_k16.jsonl --max-patterns 1000

# 2. Full run
collatz-ghost prove-family --M 12 --A 3 --k 28 --out atlases/atlas_M12_A3_amin1_k28.jsonl

# 3. Verify
collatz-ghost verify --cert atlases/atlas_M12_A3_amin1_k28.jsonl

# 4. Summarize
python tools/summarize_atlas.py atlases/atlas_M12_A3_amin1_k28.jsonl > summaries/summary_M12_A3_k28.txt

# 5. Extract ghosts
python tools/ghost_tracker.py extract atlases/atlas_M12_A3_amin1_k28.jsonl

# 6. Register (manual)
# - Add row to registry/RUNS.csv
# - Update registry/BOXES.md
# - Add checksum to registry/CHECKSUMS.txt
```

### Precision Ladder

```bash
# Run same box at increasing k
for k in 16 24 28 32; do
  collatz-ghost prove-family --M 12 --A 3 --k $k --out atlases/atlas_M12_A3_k${k}.jsonl
  python tools/ghost_tracker.py extract atlases/atlas_M12_A3_k${k}.jsonl
done

# Compare ghost sets
python tools/ghost_tracker.py ladder atlases/atlas_M12_A3_k24.jsonl atlases/atlas_M12_A3_k32.jsonl

# Generate report
python tools/ghost_tracker.py report
```

---

## File Naming Convention

### Atlas Files
```
atlas_M{M}_A{A}_amin{amin}_k{k}.jsonl
```

Examples:
- `atlas_M12_A3_amin1_k28.jsonl`
- `atlas_M24_A2_amin1_k32.jsonl`
- `atlas_M16_A3_amin2_k28.jsonl` (no 1s)

### Scout Files
```
scout_M{M}_A{A}_amin{amin}_k{k}_N{max_patterns}.jsonl
```

### Summary Files
```
summary_M{M}_A{A}_amin{amin}_k{k}.txt
```

---

## Directory Structure

```
collatz_ghost/
├── atlases/             # Completed atlas files
├── scouts/              # Scouting run outputs
├── summaries/           # Human-readable summaries
├── registry/
│   ├── RUNS.csv         # Machine-readable run log
│   ├── BOXES.md         # Human-readable box status
│   ├── CHECKSUMS.txt    # File integrity hashes
│   ├── ghosts.jsonl     # Ghost registry
│   └── ghost_analysis.json
├── docs/                # Documentation
├── tools/               # Analysis utilities
└── collatz_ghost/       # Python package
```

---

## Environment Variables

None required. All configuration is via CLI arguments.

---

## Performance Tips

1. **Start with scouts**: Use `--max-patterns 1000` to estimate time
2. **Use appropriate k**: Don't over-precision early runs
3. **Parallelize across boxes**: Run different (M,A) combinations simultaneously
4. **Monitor memory**: Large k values create big proof trees
5. **Verify immediately**: Catch issues before investing more compute

---

## Troubleshooting

### "max_nodes exceeded"

The proof tree hit the safety cap. Options:
- Increase `--max-nodes` (e.g., 5000000)
- Reduce `--k` for this pattern
- This pattern may have complex 2-adic structure

### Slow performance

- Reduce `--k` for initial runs
- Use `--max-patterns` to scout first
- Check if pattern has many SAT survivors (complex ghost landscape)

### Verification failures

- Re-run the atlas (possible corruption)
- Check disk space
- Report as bug if reproducible

