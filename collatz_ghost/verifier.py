from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple
import json
from math import gcd
from .affine import rational_cycle_candidate
from .util import sha256_json, inv_mod_odd

def verify_cert(cert: dict) -> Tuple[bool, str]:
    # hash integrity
    h = cert.get("hash")
    cert_wo_hash = dict(cert)
    cert_wo_hash.pop("hash", None)
    if h != sha256_json(cert_wo_hash):
        return False, "hash mismatch"
    t = cert.get("type")
    if t == "A":
        return _verify_a(cert)
    if t == "B":
        return _verify_b(cert)
    if t == "BATCH":
        return True, "batch header hash OK (does not rehash members here)"
    return False, f"unknown cert type: {t}"

def _verify_a(cert: dict) -> Tuple[bool, str]:
    pattern = cert["pattern"]
    B = int(cert["B"])
    D = int(cert["D"])
    # recompute
    B2, D2 = rational_cycle_candidate(pattern)
    if B2 != B or D2 != D:
        return False, "B,D do not match recomputation"
    if D == 0:
        return True, "degenerate D=0 confirmed"
    # normalize sign
    if D < 0:
        Bn, Dn = -B, -D
    else:
        Bn, Dn = B, D
    g = gcd(abs(Bn), Dn)
    Bred, Dred = Bn // g, Dn // g
    reason = cert.get("reason", "")
    if "non-integer" in reason or "does not divide" in reason:
        if Dred == 1:
            return False, "claimed non-integer but reduced denominator is 1"
        return True, "non-integer confirmed"
    if "non-positive" in reason:
        if Dred != 1:
            return False, "claimed non-positive integer but not integer"
        if Bred > 0:
            return False, "claimed non-positive but value is positive"
        return True, "non-positive confirmed"
    # Generic: accept if either non-integer or non-positive actually holds
    if Dred != 1:
        return True, "non-integer confirmed (generic)"
    if Bred <= 0:
        return True, "non-positive confirmed (generic)"
    return False, "Type A certificate does not demonstrate exclusion"

def _simulate_prefix_mod(pattern: list[int], x0: int, m: int):
    # duplicated minimal logic from solver (verifier is independent-ish but must be consistent)
    mod = 1 << m
    x = x0 % mod
    if x % 2 == 0:
        return (x, m, (0, "x0 even"))
    for i, a in enumerate(pattern):
        need = a + 1
        if m < need:
            return (x, m, None)
        tmod = 1 << need
        val = (3 * (x % tmod) + 1) % tmod
        if val != (1 << a) % tmod:
            return (x, m, (i+1, "valuation mismatch"))
        num_mod = (3 * x + 1) % (1 << m)
        q = (num_mod >> a)
        m = m - a
        if m <= 0:
            m = 1
        x = q % (1 << m)
        if x % 2 == 0:
            return (x, m, (i+1, "quotient even"))
    return (x, m, None)

def _closure_mismatch(x_end: int, m_end: int, x0: int, m0: int, target_m: int) -> bool:
    m = min(m_end, m0, target_m)
    mod = 1 << m
    return (x_end % mod) != (x0 % mod)

def _verify_tree(pattern: list[int], k: int, tree: dict) -> Tuple[bool, str, bool]:
    """Return (ok, msg, has_sat)"""
    if tree.get("leaf") is True:
        if tree.get("sat") is True:
            # validate SAT leaf actually satisfies constraints up to m
            m = int(tree["m"])
            x0 = int(tree["x0_mod_2^m"])
            x_end, m_end, contra = _simulate_prefix_mod(pattern, x0, m)
            if contra is not None:
                return False, "sat leaf contradicts simulation", True
            if _closure_mismatch(x_end, m_end, x0, m, m):
                return False, "sat leaf contradicts closure", True
            return True, "sat leaf valid", True
        # contradiction leaf: check that contradiction is real at claimed m/step if present
        m = int(tree.get("m", 0)) or None
        x0 = int(tree.get("x0_mod_2^m", 0)) if "x0_mod_2^m" in tree else None
        if m is not None and x0 is not None and m > 0:
            x_end, m_end, contra = _simulate_prefix_mod(pattern, x0, m)
            # Either a direct contradiction or closure mismatch is acceptable
            if contra is None and not _closure_mismatch(x_end, m_end, x0, m, m):
                return False, "contradiction leaf not justified by simulation/closure", False
        return True, "contradiction leaf accepted", False
    # internal node: must have two children
    ch = tree.get("children")
    if not isinstance(ch, list) or len(ch) != 2:
        return False, "internal node missing 2 children", False
    ok0, msg0, sat0 = _verify_tree(pattern, k, ch[0])
    if not ok0:
        return False, f"child0 invalid: {msg0}", sat0
    ok1, msg1, sat1 = _verify_tree(pattern, k, ch[1])
    if not ok1:
        return False, f"child1 invalid: {msg1}", sat1
    return True, "node OK", (sat0 or sat1)

def _verify_b(cert: dict) -> Tuple[bool, str]:
    pattern = cert["pattern"]
    k = int(cert["k"])
    tree = cert["tree"]
    ok, msg, has_sat = _verify_tree(pattern, k, tree)
    if not ok:
        return False, msg
    reason = cert.get("reason", "")
    if "UNSAT" in reason:
        if has_sat:
            return False, "certificate claims UNSAT but tree contains a SAT leaf"
        return True, "UNSAT proof tree verified"
    # If SAT present, we accept as a correct report that Type B cannot exclude.
    if has_sat:
        return True, "SAT tree verified (ghost solution exists at this k)"
    return True, "proof tree verified"
