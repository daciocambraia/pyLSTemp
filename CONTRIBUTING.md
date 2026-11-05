# Contributing

## Development

Create a virtual environment outside the source folder, then install the extras:

```bash
python -m pip install -e ".[dev]"
python -m pytest tests -q
python -m build --outdir ../dist-pylstemp
python -m twine check ../dist-pylstemp/*
```

CI installs the wheel and executes
`python -I -m pytest --import-mode=importlib tests -q` in Windows and Linux.
The dev extra includes pytest, Rasterio, Pillow, build and Twine. Tests use
independent synthetic numeric references and aligned small GeoTIFF/MTL/QA
fixtures; notebook execution does not require user images or research data.

## Change review

- Preserve source equations and coefficients unless an independently justified correction is requested.
- Keep family + method identities, units, domains and optical assumptions explicit.
- Test behavior and independent numeric outcomes, including masks and rejection reasons.
- Preserve screened defaults when extending diagnostic information.
- Update signatures, examples, migration notes and the README together.
- Inspect wheel/sdist contents and avoid packaging environments, caches or generated output.
- Keep research data, manuscripts and research-specific scenarios outside this project.
- Preserve the original pylandtemp credit and bibliographic references.

See [contracts](docs/result-contracts.md), [verification](docs/validation.md)
and [architecture](docs/architecture.md).
