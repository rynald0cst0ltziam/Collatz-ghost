from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Tuple, Dict, Any, List
from .affine import rational_cycle_candidate
from .util import pow2, v2_of_int, inv_mod_odd

def _required_residue_exact_v2(a: int) -> Tuple[int, int]:
    """Return (r, m) meaning: exact constraint v2(3x+1)=a implies
    x ≡ r (mod 2^{a+1}), uniquely.
    Reason: v2(3x+1)=a  <=> 3x+1 ≡ 2^a (mod 2^{a+1}).
    So x ≡ (2^a - 1) * 3^{-1} (mod 2^{a+1}).
    """
    m = a + 1
    mod = 1 << m
    r = ((1 << a) - 1) * inv_mod_odd(3, mod) % mod
    return r, m

def _simulate_prefix_mod(pattern: list[int], x0: int, m: int) -> Tuple[int, int, Optional[Tuple[int,str]]]:
    """Simulate as far as possible with current precision m (mod 2^m for x0).
    Returns (xM_mod, m_out, contradiction) where contradiction=(step_index, reason) or None.
    We stop when we lack enough precision to check the next valuation constraint exactly.
    """
    mod = 1 << m
    x = x0 % mod
    # x should be odd in the odd-iterate model
    if x % 2 == 0:
        return (x, m, (0, "x0 even; odd-iterate required"))
    for i, a in enumerate(pattern):
        # Need to check v2(3x+1)=a using only x mod 2^{a+1}
        need = a + 1
        if m < need:
            # can't decide this step yet
            return (x, m, None)
        tmod = 1 << need
        val = (3 * (x % tmod) + 1) % tmod
        # exact valuation means 3x+1 ≡ 2^a (mod 2^{a+1})
        if val != (1 << a) % tmod:
            return (x, m, (i+1, f"valuation mismatch: (3x+1) mod 2^{a+1} != 2^a"))
        # compute x_next = (3x+1)/2^a mod 2^{m-a}
        # we know numerator divisible by 2^a under constraint
        num = (3 * x + 1)
        # reduce to integer by exact division (safe because constraint enforced mod 2^{a+1}, but
        # for true integer we only know mod; still, in modular arithmetic this is well-defined for quotient mod 2^{m-a})
        # We take num modulo 2^m before division to avoid huge ints
        num_mod = num % (1 << m)
        q = (num_mod >> a)  # division by 2^a in Z/2^m works by shifting
        m = m - a
        if m <= 0:
            m = 1
        x = q % (1 << m)
        # x should be odd (since exact valuation makes q odd)
        if x % 2 == 0:
            return (x, m, (i+1, "quotient even; should be odd under exact valuation"))
    return (x, m, None)

def _closure_contradiction(x_end: int, m_end: int, x0: int, m0: int, target_m: int) -> Optional[str]:
    """Check closure consistency at common precision target_m.
    x_end known mod 2^{m_end}; x0 known mod 2^{m0}.
    We can only compare at min(m_end, m0, target_m).
    """
    m = min(m_end, m0, target_m)
    mod = 1 << m
    if (x_end % mod) != (x0 % mod):
        return f"closure mismatch modulo 2^{m}"
    return None

@dataclass
class ProverConfig:
    k: int = 32           # target modulus 2^k for certificate B
    max_nodes: int = 2_000_000  # safety cap for proof tree size
    min_start_m: int = 8  # starting precision bits for lifting
    require_exact_first_step: bool = True

def prove_pattern(pattern: list[int], cfg: ProverConfig) -> dict:
    """Return either a type A or type B certificate dict.

    Non-heuristic outputs:
      - Type A: exact rational fixed-point integrality/sign exclusion
      - Type B: DPLL-style UNSAT proof tree for exact valuation constraints mod 2^k
    """
    # --- Type A: exact rational candidate for cycle closure ---
    B0, D0 = rational_cycle_candidate(pattern)
    if D0 == 0:
        from .certs import cert_type_a
        return cert_type_a(pattern, B0, D0, "D=0 (degenerate); no integer cycle")

    # Normalize a working copy for arithmetic checks, but KEEP originals for the certificate.
    B, D = B0, D0
    if D < 0:
        B, D = -B, -D

    from math import gcd
    g = gcd(abs(B), D)
    Bred, Dred = B // g, D // g

    if Dred != 1:
        from .certs import cert_type_a
        return cert_type_a(pattern, B0, D0, "non-integer rational fixed point (D does not divide B)")
    if Bred <= 0:
        from .certs import cert_type_a
        return cert_type_a(pattern, B0, D0, "non-positive integer fixed point")

    # --- Type B: exact 2-adic valuation constraints modulo 2^k ---
    tree, reason = _prove_unsat_valuation(pattern, cfg)
    from .certs import cert_type_b
    return cert_type_b(pattern, cfg.k, tree, reason)


def _prove_unsat_valuation(pattern: list[int], cfg: ProverConfig) -> Tuple[dict, str]:
    """Build a DPLL-style proof tree showing no x0 modulo 2^k works."""
    k = cfg.k
    # initial constraint from first step valuation can pin x0 mod 2^{a1+1}
    if not pattern:
        return {"leaf": True, "contradiction": "empty pattern not supported"}, "empty pattern"
    a1 = pattern[0]
    r0, m0 = _required_residue_exact_v2(a1)
    if cfg.require_exact_first_step and k < m0:
        return {"leaf": True, "contradiction": "k < a1+1; increase k"}, "insufficient k for first-step valuation"
    # start at precision m_start = max(min_start_m, m0, min(k, something))
    m_start = max(cfg.min_start_m, m0)
    if m_start > k:
        m_start = k
    # Ensure residue at m_start consistent with r0 mod 2^{m0}
    x0_base = r0 % (1 << m0)
    # choose representative modulo 2^{m_start} that matches base
    x0_rep = x0_base  # lower bits
    # proof tree over residues mod 2^m, branching one bit at a time until k
    nodes = 0

    def recurse(m: int, x0: int) -> dict:
        nonlocal nodes
        nodes += 1
        if nodes > cfg.max_nodes:
            return {"leaf": True, "contradiction": "max_nodes exceeded (increase cap or reduce k)"}
        # Enforce base congruence mod 2^{m0}
        if (x0 % (1 << m0)) != x0_base:
            return {"leaf": True, "contradiction": f"violates base residue mod 2^{m0}"}
        # Must be odd
        if x0 % 2 == 0:
            return {"leaf": True, "contradiction": "x0 even"}
        # simulate with precision m
        x_end, m_end, contra = _simulate_prefix_mod(pattern, x0, m)
        if contra is not None:
            step, msg = contra
            return {"leaf": True, "contradiction": msg, "at_step": step, "m": m}
        # if we completed all steps, check closure at precision m (or k?)
        # Note: _simulate_prefix_mod returns x in modulus 2^{m_end} after full loop if no early stop.
        # But if m_end < 1 shouldn't happen.
        # We consider closure at min(m_end, m, k)
        if len(pattern) > 0 and m_end <= m and m_end > 0:
            # We only know x_end mod 2^{m_end}, x0 mod 2^m. Compare at min(m_end,m)
            cl = _closure_contradiction(x_end, m_end, x0, m, m)
            if cl is not None:
                return {"leaf": True, "contradiction": cl, "m": m, "m_end": m_end}
        # If m == k and still no contradiction detected, then SAT at this leaf
        if m >= k:
            return {"leaf": True, "sat": True, "m": m, "x0_mod_2^m": int(x0)}
        # Otherwise, branch by adding next bit
        # To preserve base residue, if m < m0 then branching must match, but we already start m>=m0.
        child0 = recurse(m + 1, x0)              # bit 0
        child1 = recurse(m + 1, x0 + (1 << m))   # set new bit to 1
        # UNSAT if both children unsat (no 'sat':True)
        return {"m": m, "x0_mod_2^m": int(x0), "children": [child0, child1]}

    tree = recurse(m_start, x0_rep)
    # Determine satisfiable?
    def has_sat(t: dict) -> bool:
        if t.get("sat") is True:
            return True
        for c in t.get("children", []):
            if has_sat(c):
                return True
        return False
    if has_sat(tree):
        return tree, "valuation constraints SAT at target k (ghost/2-adic solution exists); Type B cannot exclude"
    return tree, f"UNSAT: no solution modulo 2^{k} satisfying exact valuation constraints and closure"

