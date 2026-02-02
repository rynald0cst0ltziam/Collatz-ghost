from __future__ import annotations
from dataclasses import dataclass
from typing import Iterator, Optional, TextIO
import json
from .pattern import enumerate_bounded
from .solver import ProverConfig, prove_pattern
from .certs import batch_proof_header
from .util import sha256_json

@dataclass
class FamilyJob:
    M: int
    A: int
    k: int = 28
    amin: int = 1
    out_path: str = "results.jsonl"
    max_patterns: Optional[int] = None

def prove_family(job: FamilyJob) -> dict:
    cfg = ProverConfig(k=job.k)
    cert_hashes = []
    family_desc = {"M": job.M, "A": job.A, "amin": job.amin, "k": job.k}
    count = 0
    with open(job.out_path, "w", encoding="utf-8") as f:
        for pat in enumerate_bounded(job.M, job.A, amin=job.amin):
            cert = prove_pattern(pat, cfg)
            f.write(json.dumps(cert, sort_keys=True) + "\n")
            cert_hashes.append(cert["hash"])
            count += 1
            if job.max_patterns is not None and count >= job.max_patterns:
                break
        header = batch_proof_header(family_desc, cert_hashes)
        f.write(json.dumps(header, sort_keys=True) + "\n")
    return {"out": job.out_path, "count": count, "batch_hash": sha256_json(header), "root": header["root"]}
