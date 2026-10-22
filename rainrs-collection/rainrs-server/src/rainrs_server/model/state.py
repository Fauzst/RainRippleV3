"""The state of the Runge–Kutta integration as a data model.

The derivation stage integrates a system of ordinary differential
equations. Two kinds of values flow through the integrator:

* the **state vector** — the position and the velocity of every
  oscillator — and the *parameters* that describe the system;
* the **parameters** of the coupled oscillator pair, derived from the
  geometry of a ripple.

Both are part of the data model, because the derivation stage, the
database layer and the documentation all describe them with the same
names and types.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

__all__ = [
    "Derivative",
    "RippleWaveParameters",
    "Trajectory",
    "Vector",
]

#: The state of the oscillator pair: ``(x1, x2, y1, y2)``.
Vector = tuple[float, ...]

#: The right-hand side of the differential equation system.
Derivative = Callable[[float, Vector], Vector]

#: A sampled trajectory of the integration.
Trajectory = list[Vector]


@dataclass(frozen=True, slots=True)
class RippleWaveParameters:
    """Parameters of the coupled oscillator system.

    Attributes:
        mu: Nonlinearity (van der Pol damping) of both oscillators.
        coupling: Coupling strength between the two oscillators.
        forcing: Amplitude of the periodic forcing term.
        phase: Phase of the forcing term in radians.
    """

    mu: float
    coupling: float
    forcing: float
    phase: float

    def to_dict(self) -> dict[str, float]:
        """Return the parameters as a plain dictionary."""
        return {
            "mu": self.mu,
            "coupling": self.coupling,
            "forcing": self.forcing,
            "phase": self.phase,
        }
