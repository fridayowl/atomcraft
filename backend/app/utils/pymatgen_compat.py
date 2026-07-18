"""Compatibility helpers for pymatgen / mp-api / emmet-core imports."""

from __future__ import annotations

import importlib
import sys


def _alias_module(alias: str, target: str) -> None:
    if alias in sys.modules:
        return
    sys.modules[alias] = importlib.import_module(target)


def ensure_pymatgen_compat() -> None:
    """Install module aliases expected by emmet-core on newer pymatgen layouts."""
    aliases = {
        "pymatgen.core.graphs": "pymatgen.analysis.graphs",
        "pymatgen.core.bond_valence": "pymatgen.analysis.bond_valence",
        "pymatgen.core.structure_matcher": "pymatgen.analysis.structure_matcher",
        "pymatgen.core.molecule_matcher": "pymatgen.analysis.molecule_matcher",
        "pymatgen.core.entries": "pymatgen.entries.computed_entries",
        "pymatgen.core.structure_analyzer": "pymatgen.analysis.structure_analyzer",
        "pymatgen.core.local_env": "pymatgen.analysis.local_env",
        "pymatgen.analysis.compatibility": "pymatgen.entries.compatibility",
    }

    for alias, target in aliases.items():
        _alias_module(alias, target)

    emmet_pmg = importlib.import_module("emmet.core.io.pymatgen")
    if not hasattr(emmet_pmg, "SymmetryUndeterminedError"):
        emmet_pmg.SymmetryUndeterminedError = importlib.import_module(
            "pymatgen.symmetry.analyzer"
        ).SymmetryUndetermined


def patch_mp_api_imports() -> None:
    """Public entry point for scripts before importing mp_api.client."""
    ensure_pymatgen_compat()
