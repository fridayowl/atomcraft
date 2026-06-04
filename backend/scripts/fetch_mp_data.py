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

    all_binaries = [
        ["Li","O"],["Na","O"],["K","O"],["Rb","O"],["Cs","O"],["Be","O"],["Mg","O"],["Ca","O"],["Sr","O"],["Ba","O"],
        ["Al","O"],["Si","O"],["P","O"],["S","O"],["Ga","O"],["Ge","O"],["As","O"],["Sn","O"],["Pb","O"],["Bi","O"],
        ["Sc","O"],["Ti","O"],["V","O"],["Cr","O"],["Mn","O"],["Fe","O"],["Co","O"],["Ni","O"],["Cu","O"],["Zn","O"],
        ["Y","O"],["Zr","O"],["Nb","O"],["Mo","O"],["Tc","O"],["Ru","O"],["Rh","O"],["Pd","O"],["Ag","O"],["Cd","O"],
        ["Hf","O"],["Ta","O"],["W","O"],["Re","O"],["Os","O"],["Ir","O"],["Pt","O"],["Au","O"],
        ["La","O"],["Ce","O"],["Pr","O"],["Nd","O"],["Sm","O"],["Eu","O"],["Gd","O"],["Dy","O"],["Er","O"],["Yb","O"],
    ]
    all_nonoxides = [
        ["Si","N"],["Ga","N"],["Ga","As"],["Ga","P"],["Ga","Sb"],["In","N"],["In","P"],["In","As"],["In","Sb"],
        ["Zn","S"],["Zn","Se"],["Zn","Te"],["Cd","S"],["Cd","Se"],["Cd","Te"],["Hg","S"],["Hg","Se"],["Hg","Te"],
        ["Pb","S"],["Pb","Se"],["Pb","Te"],["Sn","S"],["Sn","Se"],["Sn","Te"],
        ["Fe","S"],["Co","S"],["Ni","S"],["Cu","S"],["Mo","S"],["Nb","S"],["Ta","S"],["W","S"],
        ["Ti","N"],["Zr","N"],["Hf","N"],["Nb","N"],["Ta","N"],["V","N"],["W","N"],["Mo","N"],
        ["Si","C"],["Ti","C"],["Zr","C"],["Hf","C"],["W","C"],["Nb","C"],["Ta","C"],["V","C"],
        ["Na","Cl"],["K","Cl"],["Rb","Cl"],["Cs","Cl"],["Mg","F"],["Ca","F"],["Sr","F"],["Ba","F"],["Li","F"],["Na","F"],
        ["Na","Br"],["K","Br"],["Li","I"],["Na","I"],["Cs","I"],
        ["Mg","Si"],["Mg","Ge"],["Mg","Sn"],["Al","Si"],["Ca","Si"],["Ca","Ge"],
        ["Fe","Si"],["Co","Si"],["Ni","Si"],["Mn","Si"],["Cr","Si"],
    ]
    all_ternary_oxides = [
        ["Li","Co","O"],["Li","Mn","O"],["Li","Fe","O"],["Li","Ni","O"],["Li","Cu","O"],["Li","Zn","O"],
        ["Na","Co","O"],["Na","Mn","O"],["Na","Fe","O"],["Na","Ni","O"],
        ["K","Mn","O"],["K","Co","O"],["K","Ni","O"],
        ["La","Fe","O"],["La","Co","O"],["La","Mn","O"],["La","Ni","O"],["La","Cu","O"],
        ["Sr","Ti","O"],["Ba","Ti","O"],["Pb","Ti","O"],["Ca","Ti","O"],["Mg","Ti","O"],
        ["Sr","Fe","O"],["Ba","Fe","O"],["Ca","Fe","O"],["Mg","Fe","O"],
        ["Sr","Co","O"],["Ba","Co","O"],["Ca","Co","O"],
        ["Sr","Mn","O"],["Ba","Mn","O"],["Ca","Mn","O"],
        ["Y","Fe","O"],["Y","Al","O"],["Y","Ba","O"],
        ["Mg","Al","O"],["Zn","Fe","O"],["Zn","Al","O"],["Ni","Fe","O"],["Co","Fe","O"],
        ["Li","Al","O"],["Li","Si","O"],["Li","Ti","O"],["Li","Zr","O"],
        ["Na","Al","O"],["Na","Si","O"],["Na","Ti","O"],["Na","Zr","O"],
        ["K","Al","O"],["K","Si","O"],["K","Ti","O"],
        ["Ce","Fe","O"],["Ce","Co","O"],["Ce","Mn","O"],["Ce","Zr","O"],
        ["Pr","Fe","O"],["Nd","Fe","O"],["Sm","Fe","O"],
        ["Bi","Fe","O"],["Bi","Mn","O"],["Bi","Ti","O"],
        ["Li","V","O"],["Li","Cr","O"],["Li","Mo","O"],["Li","W","O"],
        ["Na","V","O"],["Na","Mo","O"],["Na","W","O"],
        ["Pb","Zr","O"],["Pb","Hf","O"],["Ba","Zr","O"],["Sr","Zr","O"],
    ]
    all_ternary_nonoxides = [
        ["Cu","In","S"],["Cu","In","Se"],["Cu","Ga","S"],["Cu","Ga","Se"],
        ["Ag","In","S"],["Ag","In","Se"],["Ag","Ga","S"],["Ag","Ga","Se"],
        ["Li","Ti","S"],["Li","Ti","Se"],["Na","Ti","S"],
        ["Li","P","S"],["Na","P","S"],["Li","P","Se"],["Na","P","Se"],
        ["Cu","Zn","S"],["Cu","Sn","S"],["Cu","Sb","S"],
        ["Fe","Co","S"],["Fe","Ni","S"],["Co","Ni","S"],
    ]
    all_quaternaries = [
        ["Li","Ni","Mn","O"],["Li","Co","Mn","O"],["Li","Ni","Co","O"],
        ["Na","Ni","Mn","O"],["Na","Co","Mn","O"],
        ["Sr","Fe","Mo","O"],["Ba","Fe","Mo","O"],
        ["Li","Fe","Si","O"],["Li","Al","Si","O"],["Na","Al","Si","O"],
        ["Mg","Al","Si","O"],["Ca","Al","Si","O"],["K","Al","Si","O"],
        ["La","Sr","Mn","O"],["La","Ca","Mn","O"],["La","Sr","Fe","O"],
        ["Y","Ba","Cu","O"],["Bi","Sr","Ca","O"],
        ["Cu","Zn","Sn","S"],["Cu","Zn","In","S"],["Cu","Zn","Ga","S"],
    ]
    singles = [["C"],["Si"],["Ge"],["Sn"],["B"],["Se"],["Te"],["Bi"],["Sb"],["P"]]

    all_combos = all_binaries + all_nonoxides + all_ternary_oxides + all_ternary_nonoxides + all_quaternaries + singles

    for combo in all_combos:
        if len(data) >= num_materials:
            break
        chunk = await mp_client.search_materials(
            elements=combo,
            num_chunks=1,
            chunk_size=30,
        )
        data.extend(chunk)
        print(f"  {'-'.join(combo)}: {len(chunk)} materials")

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
