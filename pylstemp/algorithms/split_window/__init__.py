"""Split-window temperature algorithms discovered from this folder."""

from ...registry import discover_algorithms
from ..base_temperature import BaseTemperatureAlgorithm
from .base import SplitWindowParentLST
from .du_2015 import SplitWindowDu2015LST
from .kerr_1992 import SplitWindowKerr1992LST
from .price_1984 import SplitWindowPrice1984LST
from .sobrino_1993 import SplitWindowSobrino1993LST

split_window_registry = discover_algorithms(__name__, "split_window")
default_algorithms = split_window_registry.as_mapping()

__all__ = [
    "BaseTemperatureAlgorithm",
    "SplitWindowDu2015LST",
    "SplitWindowParentLST",
    "SplitWindowKerr1992LST",
    "SplitWindowPrice1984LST",
    "SplitWindowSobrino1993LST",
    "default_algorithms",
    "split_window_registry",
]
