from dataclasses import dataclass


@dataclass(frozen=True)
class AlgorithmMetadata:
    """Small immutable record used to document registered algorithms."""

    key: str
    name: str
    family: str
    reference: str
    citation: str
    aliases: tuple[str, ...] = ()

