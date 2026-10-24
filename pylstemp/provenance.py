"""Reproducible scene metadata; declared optical units are never inferred from values."""
import hashlib
import json
from pathlib import Path
import platform
import numpy as np


def _cards():
    return json.loads(Path(__file__).with_name("method_cards.json").read_text(encoding="utf8"))


def optical_contract(method, quantity):
    """Describe a declaration without claiming atmospheric or scene validation."""
    if quantity not in {None, "radiance", "reflectance", "toa_reflectance", "surface_reflectance"}:
        raise ValueError("optical_quantity must be radiance, reflectance/toa_reflectance or surface_reflectance.")
    quantity = "toa_reflectance" if quantity == "reflectance" else quantity
    card = next((c for c in _cards() if c["method"] == method), None)
    expected = {"gopinadh-2018": "radiance", "kerr-1992": "surface_reflectance"}.get(method)
    status = "quantity_undeclared" if quantity is None else (
        "source_quantity_unspecified" if expected is None else
        "declared_quantity_matches_source_interpretation" if quantity == expected else "optical_quantity_adaptation")
    return dict(method=method, declared_quantity=quantity, status=status,
                source_condition=None if card is None else card["optical_contract"],
                scene_threshold_validation="not established by declaring a radiometric quantity")


def _sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def scene_provenance(scene, *, emissivity_method, optical_quantity, mask=None, hash_inputs=False, pwv_method=None):
    """Record equations, actual MTL coefficients, grid and optional input content hashes.

    The package digest includes Python sources AND the reviewed coefficient cards.
    Without hash_inputs, size/mtime identify candidates, not file content identity.
    """
    package = Path(__file__).parent
    digest = hashlib.sha256()
    for path in sorted([*package.rglob("*.py"), package / "method_cards.json"]):
        digest.update(path.relative_to(package).as_posix().encode())
        digest.update(b"\0")
        digest.update(path.read_bytes())
    files = {}
    paths = dict(getattr(scene, "paths", {}))
    if getattr(scene, "mtl_path", None) is not None:
        paths["MTL"] = scene.mtl_path
    for token, path in paths.items():
        path = Path(path)
        stat = path.stat()
        files[token] = dict(name=path.name, size_bytes=stat.st_size, mtime_ns=stat.st_mtime_ns,
                            sha256=_sha(path) if hash_inputs or token == "MTL" else None)
    metadata = getattr(scene, "metadata", {})
    fields = {k: v for k, v in metadata.items() if k.startswith(("RADIANCE_", "REFLECTANCE_", "K1_CONSTANT_", "K2_CONSTANT_"))
              or k in {"SUN_ELEVATION", "SUN_AZIMUTH", "SPACECRAFT_ID", "PROCESSING_LEVEL", "LANDSAT_PRODUCT_ID"}}
    grid = dict(shape=list(scene.shape), backend=getattr(scene, "backend", "caller_scene"))
    src = getattr(scene, "sources", {}).get("B4")
    if src is not None and getattr(scene, "backend", None) == "rasterio":
        grid.update(crs=str(src.crs), transform=list(src.transform))
    elif src is not None and hasattr(src, "tag_v2"):
        grid["geotiff_tags"] = {str(k): src.tag_v2[k] for k in (33550,33922,34264,34735,34736,34737) if k in src.tag_v2}
    cards = {c["method"]: c for c in _cards()}
    chosen = {key: cards[key] for key in ("du-2015", emissivity_method, pwv_method) if key in cards}
    mask_digest = None if mask is None else hashlib.sha256(np.asarray(mask.shape,dtype="<i8").tobytes()+np.packbits(mask).tobytes()).hexdigest()
    return dict(provenance_schema=1, python_version=platform.python_version(), numpy_version=np.__version__,
                package_sha256=digest.hexdigest(), input_files=files,
                input_hash_policy="sha256_all_inputs" if hash_inputs else "MTL_sha256; imagery_size_and_mtime_only",
                calibration_mtl=fields, source_grid=grid, user_mask_sha256=mask_digest,
                optical_contract=optical_contract(emissivity_method, optical_quantity),
                solar_angle_source="SZA band (hundredths degree)" if "SZA" in paths else "scene MTL SUN_ELEVATION",
                qa_policy="QA_PIXEL fill/dilated/cirrus/cloud/shadow/snow; relevant QA_RADSAT; water excluded for PWV modes",
                source_method_cards=chosen,
                sensor_coefficient_status="native Landsat8 equations; field accuracy not established" if scene.sensor.lower() == "landsat_8" else "experimental sensor coefficient transfer; MTL calibration validity is separate")
