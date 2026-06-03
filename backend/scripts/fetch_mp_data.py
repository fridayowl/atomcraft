#!/usr/bin/env python3
"""
Fetch real material data from Materials Project API and retrain ML models.

Usage:
    export MP_API_KEY="your_key_here"
    python scripts/fetch_mp_data.py --num 100 --retrain

Requires MP_API_KEY from https://materialsproject.org/api
"""

import os
import sys
import argparse
import json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.core.materials_project import mp_client
from app.database import SessionLocal
from app.models.material import Material, Composition, Property
from app.core.trainer import train_and_save_models


async def fetch_and_store(num_materials: int = 100, retrain: bool = False):
    if not mp_client.api_key:
        print("ERROR: No MP_API_KEY found.")
        print("Get one at https://materialsproject.org/api")
        print("Then: export MP_API_KEY='your_key'")
        return

    print(f"Fetching up to {num_materials} materials from Materials Project...")

    data = []
    element_pairs = [
        ["Si", "O"], ["Fe", "O"], ["Mg", "O"], ["Al", "O"], ["Ti", "O"],
        ["Na", "O"], ["Ca", "O"], ["Li", "O"], ["Cu", "O"], ["Zn", "O"],
        ["Si", "N"], ["Ga", "As"], ["In", "P"], ["Cd", "Te"],
        ["La", "O"], ["Zr", "O"], ["Ce", "O"], ["Ba", "O"],
        ["C"], ["Si"], ["Ge"],
    ]

    for pair in element_pairs:
        if len(data) >= num_materials:
            break
        chunk = await mp_client.search_materials(
            elements=pair,
            num_chunks=1,
            chunk_size=min(100, num_materials - len(data)),
        )
        data.extend(chunk)
        print(f"  {'-'.join(pair)}: {len(chunk)} materials")

    if not data:
        print("WARNING: No materials returned from API. Nothing to store or retrain.")
        return

    print(f"Got {len(data)} materials. Storing in database...")
    db = SessionLocal()

    stored = 0
    for entry in data:
        formula = entry.get("formula_pretty", entry.get("material_id", ""))
        existing = db.query(Material).filter(Material.formula == formula).first()
        if existing:
            continue

        sym = entry.get("symmetry", {}) or {}
        if hasattr(sym, "get"):
            sg = sym.get("symbol")
            crystal = sym.get("crystal_system")
        else:
            sg = None
            crystal = None

        material = Material(
            formula=formula,
            name=formula,
            space_group=sg,
            crystal_system=crystal,
            mp_id=entry.get("material_id"),
            volume=entry.get("volume"),
            density=entry.get("density"),
            lattice_a=entry.get("structure", {}).get("lattice", {}).get("a"),
            lattice_b=entry.get("structure", {}).get("lattice", {}).get("b"),
            lattice_c=entry.get("structure", {}).get("lattice", {}).get("c"),
        )
        db.add(material)
        db.flush()

        if entry.get("band_gap") is not None:
            db.add(Property(
                material_id=material.id,
                property_type="band_gap",
                value=entry["band_gap"],
                unit="eV",
                source="Materials Project",
                confidence=0.9,
            ))
        if entry.get("formation_energy_per_atom") is not None:
            db.add(Property(
                material_id=material.id,
                property_type="formation_energy",
                value=entry["formation_energy_per_atom"],
                unit="eV/atom",
                source="Materials Project",
                confidence=0.9,
            ))
        if entry.get("density") is not None:
            db.add(Property(
                material_id=material.id,
                property_type="density",
                value=entry["density"],
                unit="g/cm³",
                source="Materials Project",
                confidence=0.9,
            ))

        stored += 1

    db.commit()
    db.close()
    print(f"Stored {stored} new materials (skipped {len(data) - stored} duplicates).")

    if retrain and stored > 0:
        print("Retraining models with real data...")
        train_and_save_models(force_retrain=True)

    await mp_client.close()


def main():
    parser = argparse.ArgumentParser(description="Fetch data from Materials Project")
    parser.add_argument("--num", type=int, default=100, help="Number of materials to fetch")
    parser.add_argument("--retrain", action="store_true", help="Retrain ML models after fetching")
    args = parser.parse_args()

    import asyncio
    asyncio.run(fetch_and_store(args.num, args.retrain))


if __name__ == "__main__":
    main()
