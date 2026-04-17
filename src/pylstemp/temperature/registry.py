"""Registry definitions for LST algorithms."""

from __future__ import annotations

from collections import namedtuple

from ..core import AlgorithmRegistry
from ..references import TEMPERATURE_REFERENCES
from .mono_window import MonoWindowLST
from .split_window.jiminez_munoz import SplitWindowJiminezMunozLST
from .split_window.kerr import SplitWindowKerrLST
from .split_window.mc_millin import SplitWindowMcMillinLST
from .split_window.price import SplitWindowPriceLST
from .split_window.sobrino_1993 import SplitWindowSobrino1993LST

single_window_registry = AlgorithmRegistry("temperature.single_window")
single_window_registry.register(
    "mono-window",
    MonoWindowLST,
    name=TEMPERATURE_REFERENCES["mono-window"]["name"],
    reference=TEMPERATURE_REFERENCES["mono-window"]["reference"],
    citation=TEMPERATURE_REFERENCES["mono-window"]["citation"],
)

split_window_registry = AlgorithmRegistry("temperature.split_window")
split_window_registry.register(
    "jiminez-munoz",
    SplitWindowJiminezMunozLST,
    name=TEMPERATURE_REFERENCES["jiminez-munoz"]["name"],
    reference=TEMPERATURE_REFERENCES["jiminez-munoz"]["reference"],
    citation=TEMPERATURE_REFERENCES["jiminez-munoz"]["citation"],
)
split_window_registry.register(
    "kerr",
    SplitWindowKerrLST,
    name=TEMPERATURE_REFERENCES["kerr"]["name"],
    reference=TEMPERATURE_REFERENCES["kerr"]["reference"],
    citation=TEMPERATURE_REFERENCES["kerr"]["citation"],
)
split_window_registry.register(
    "mc-millin",
    SplitWindowMcMillinLST,
    name=TEMPERATURE_REFERENCES["mc-millin"]["name"],
    reference=TEMPERATURE_REFERENCES["mc-millin"]["reference"],
    citation=TEMPERATURE_REFERENCES["mc-millin"]["citation"],
    aliases=("mc-clain",),
)
split_window_registry.register(
    "price",
    SplitWindowPriceLST,
    name=TEMPERATURE_REFERENCES["price"]["name"],
    reference=TEMPERATURE_REFERENCES["price"]["reference"],
    citation=TEMPERATURE_REFERENCES["price"]["citation"],
)
split_window_registry.register(
    "sobrino-1993",
    SplitWindowSobrino1993LST,
    name=TEMPERATURE_REFERENCES["sobrino-1993"]["name"],
    reference=TEMPERATURE_REFERENCES["sobrino-1993"]["reference"],
    citation=TEMPERATURE_REFERENCES["sobrino-1993"]["citation"],
)

Algorithms = namedtuple("Algorithms", ("single_window", "split_window"))
default_algorithms = Algorithms(
    single_window_registry.as_mapping(),
    split_window_registry.as_mapping(),
)

