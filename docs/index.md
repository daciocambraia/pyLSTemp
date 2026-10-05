# Documentation

This folder contains the user-facing documentation for the current modular `pyLSTemp` codebase.

## Suggested reading order

1. [installation.md](installation.md)
2. [usage.md](usage.md)
3. [api-reference.md](api-reference.md)
4. [architecture.md](architecture.md)
5. [extending.md](extending.md)
6. [references.md](references.md)

## Main ideas

- the public API stays small and stable
- calibration supplies TOA radiance, optional TOA reflectance and TOA brightness temperature; NDVI is the sole spectral index
- sensor-specific thermal constants live in `pylstemp/sensors/`
- the real implementations live in `pylstemp/algorithms/`
- new algorithms are discovered automatically from their family folder
- new families can also be discovered automatically when they expose a family registry

- [Scientific methods, migration and validation limits](scientific-methods.md)

- [Index corrections, one NDVI, reflectance and actionable errors](CORRECOES_INDICES_REFLECTANCIA_v1.11.md)

- [Current Level-1 scope and Xiaolei removal](ESCOPO_LEVEL1_v1.11.md)

- [Current radiance workflow and EVI removal](FLUXO_RADIANCIA_v1.11.md)
