from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable, Iterator, Optional

@dataclass(frozen=True)
class PatternFamily:
    """Simple family: all sequences of length M with entries in [amin, amax]."""
    M: int
    amin: int = 1
    amax: int = 10

def enumerate_family(fam: PatternFamily) -> Iterator[list[int]]:
    from itertools import product
    for tup in product(range(fam.amin, fam.amax + 1), repeat=fam.M):
        yield list(tup)

def enumerate_bounded(M: int, A: int, amin: int = 1) -> Iterator[list[int]]:
    return enumerate_family(PatternFamily(M=M, amin=amin, amax=A))
