"""The experimental research artifacts derived from the ripple geometry.

Two levels are derived for every capture:

* a **master key**, derived from the *averaged* attributes of the image
  (mean centre position, mean radius and the number of ripples);
* one **slave key** per detected ripple, derived from the *individual*
  attributes of that ripple and bound to the master key.

The material is a research artifact of 32 or 64 bits — it is **not** a
production cryptographic key. See the repository-root ``AGENTS.md``,
section "Security Boundaries".
"""

from __future__ import annotations

from dataclasses import dataclass

__all__ = ["MasterKey", "SlaveKey"]


@dataclass(frozen=True, slots=True)
class MasterKey:
    """A master research key derived from the averaged ripple attributes.

    Attributes:
        image_id: Identifier of the source image in the database.
        key: Hex-encoded key material (experimental research artifact).
        bits: Key size in bits (32 or 64).
        algorithm: Identifier of the derivation procedure.
        parameters: The averaged attributes and ODE parameters that were
            used, kept for reproducibility of the research experiment.
        derived_at: ISO 8601 UTC timestamp.
    """

    image_id: int
    key: str
    bits: int
    algorithm: str
    parameters: dict[str, float]
    derived_at: str

    def with_image_id(self, image_id: int) -> MasterKey:
        """Return a copy of the key that belongs to ``image_id``.

        The dataclass is frozen; the identifier of the capture is only
        known once the row was written, so it is set through a copy.
        """
        return MasterKey(
            image_id=image_id,
            key=self.key,
            bits=self.bits,
            algorithm=self.algorithm,
            parameters=self.parameters,
            derived_at=self.derived_at,
        )


@dataclass(frozen=True, slots=True)
class SlaveKey:
    """A slave research key bound to exactly one master key.

    Attributes:
        master_key_id: Identifier of the master key this slave key
            belongs to.
        image_id: Identifier of the source image in the database.
        ripple_index: Index of the ripple the key was derived from.
        key: Hex-encoded key material (experimental research artifact).
        bits: Key size in bits (32 or 64).
        algorithm: Identifier of the derivation procedure, including the
            binding that was applied.
        derived_at: ISO 8601 UTC timestamp.
    """

    master_key_id: int
    image_id: int
    ripple_index: int
    key: str
    bits: int
    algorithm: str
    derived_at: str

    def with_master_key_id(self, master_key_id: int) -> SlaveKey:
        """Return a copy of the key that belongs to ``master_key_id``.

        The dataclass is frozen; the identifier of the master key is
        only known once the row was written, so it is set through a
        copy.
        """
        return SlaveKey(
            master_key_id=master_key_id,
            image_id=self.image_id,
            ripple_index=self.ripple_index,
            key=self.key,
            bits=self.bits,
            algorithm=self.algorithm,
            derived_at=self.derived_at,
        )
