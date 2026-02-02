from __future__ import annotations
import hashlib
import json
from dataclasses import dataclass
from typing import Any, Dict

def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def sha256_json(obj: Any) -> str:
    data = json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256_bytes(data)

def pow2(k: int) -> int:
    return 1 << k

def inv_mod_odd(a: int, mod: int) -> int:
    # Inverse of odd a modulo 2^k
    # Python pow supports modular inverse for gcd(a, mod)=1
    return pow(a, -1, mod)

def v2_of_int(n: int) -> int:
    # 2-adic valuation on integers: v2(0)=inf not used here
    if n == 0:
        raise ValueError("v2(0) not supported here")
    return (n & -n).bit_length() - 1

def parse_pattern(s: str) -> list[int]:
    s = s.strip()
    if not s:
        return []
    return [int(x.strip()) for x in s.split(",") if x.strip()]

def format_pattern(p: list[int]) -> str:
    return ",".join(str(x) for x in p)

def canonical_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))
