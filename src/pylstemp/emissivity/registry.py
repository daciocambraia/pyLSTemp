"""Registry definitions for emissivity algorithms."""

from __future__ import annotations

from ..core import AlgorithmRegistry
from ..references import EMISSIVITY_REFERENCES
from .avdan import ComputeMonoWindowEmissivity
from .gopinadh import ComputeEmissivityGopinadh
from .xiaolei import ComputeEmissivityNBEM

emissivity_registry = AlgorithmRegistry("emissivity")
emissivity_registry.register(
    "avdan",
    ComputeMonoWindowEmissivity,
    name=EMISSIVITY_REFERENCES["avdan"]["name"],
    reference=EMISSIVITY_REFERENCES["avdan"]["reference"],
    citation=EMISSIVITY_REFERENCES["avdan"]["citation"],
)
emissivity_registry.register(
    "xiaolei",
    ComputeEmissivityNBEM,
    name=EMISSIVITY_REFERENCES["xiaolei"]["name"],
    reference=EMISSIVITY_REFERENCES["xiaolei"]["reference"],
    citation=EMISSIVITY_REFERENCES["xiaolei"]["citation"],
)
emissivity_registry.register(
    "gopinadh",
    ComputeEmissivityGopinadh,
    name=EMISSIVITY_REFERENCES["gopinadh"]["name"],
    reference=EMISSIVITY_REFERENCES["gopinadh"]["reference"],
    citation=EMISSIVITY_REFERENCES["gopinadh"]["citation"],
)

default_algorithms = emissivity_registry.as_mapping()

