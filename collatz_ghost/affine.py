from __future__ import annotations
from dataclasses import dataclass
from typing import Tuple

@dataclass(frozen=True)
class AffineMap:
    """Represents an affine map x -> (A*x + B) / 2^E over rationals (exact integers).
    A,B,E are integers with A>=0, E>=0.
    """
    A: int
    B: int
    E: int

def compose_step(a: int, amap: AffineMap) -> AffineMap:
    """Compose current map with one odd-step T_a(x) = (3x+1)/2^a on the LEFT:
        new(x) = T_a(amap(x)).
    If amap(x) = (A x + B)/2^E, then
        T_a(amap(x)) = (3(Ax+B)/2^E + 1)/2^a = (3A x + 3B + 2^E)/2^{E+a}.
    """
    A2 = 3 * amap.A
    B2 = 3 * amap.B + (1 << amap.E)
    E2 = amap.E + a
    return AffineMap(A2, B2, E2)

def compose_pattern(pattern: list[int]) -> AffineMap:
    """Return the M-fold composition F = T_{a_M}∘...∘T_{a_1} as AffineMap."""
    amap = AffineMap(1, 0, 0)  # identity
    for a in pattern:
        amap = compose_step(a, amap)
    return amap

def rational_cycle_candidate(pattern: list[int]) -> Tuple[int, int]:
    """Compute exact rational candidate x0 = B/(2^E - A) for fixed point F(x)=x,
    where F(x) = (A x + B)/2^E.
    Returns (num, den) reduced not guaranteed; den may be negative.
    """
    F = compose_pattern(pattern)
    num = F.B
    den = (1 << F.E) - F.A
    return (num, den)
