"""Split-window temperature algorithms discovered from this folder."""

from ...registry import discover_algorithms
from ..base_temperature import BaseTemperatureAlgorithm
from .base import SplitWindowParentLST
from .jiminez_munoz import SplitWindowJiminezMunozLST
from .kerr import SplitWindowKerrLST
from .mc_millin import SplitWindowMcMillinLST
from .price import SplitWindowPriceLST
from .sobrino_1993 import SplitWindowSobrino1993LST

split_window_registry = discover_algorithms(__name__, "split_window")
default_algorithms = split_window_registry.as_mapping()
SplitWindowMcClainLST = SplitWindowMcMillinLST

__all__ = [
    "BaseTemperatureAlgorithm",
    "SplitWindowParentLST",
    "SplitWindowJiminezMunozLST",
    "SplitWindowKerrLST",
    "SplitWindowMcClainLST",
    "SplitWindowMcMillinLST",
    "SplitWindowPriceLST",
    "SplitWindowSobrino1993LST",
    "default_algorithms",
    "split_window_registry",
]
