from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from .util import sha256_json

def cert_type_a(pattern: list[int], B: int, D: int, reason: str) -> dict:
    obj = {
        "type": "A",
        "pattern": pattern,
        "B": str(B),
        "D": str(D),
        "reason": reason,
    }
    obj["hash"] = sha256_json(obj)
    return obj

def cert_type_b(pattern: list[int], k: int, tree: dict, reason: str) -> dict:
    obj = {
        "type": "B",
        "pattern": pattern,
        "k": k,
        "tree": tree,
        "reason": reason,
    }
    obj["hash"] = sha256_json(obj)
    return obj

def batch_proof_header(family_desc: dict, cert_hashes: list[str]) -> dict:
    # Merkle-ish: hash of concatenated hashes
    import hashlib
    h = hashlib.sha256()
    for ch in cert_hashes:
        h.update(ch.encode("utf-8"))
    root = h.hexdigest()
    obj = {
        "type": "BATCH",
        "family": family_desc,
        "count": len(cert_hashes),
        "root": root,
    }
    obj["hash"] = sha256_json(obj)
    return obj
