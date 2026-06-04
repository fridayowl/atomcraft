#!/usr/bin/env python3
"""Download ALL ~165k materials from MP, store in DB, retrain models."""

import os
import sys
import time
import argparse
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from mp_api.client import MPRester


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--retrain", action="store_true")
    args = parser.parse_args()

    api_key = os.getenv("MP_API_KEY", "")
    if not api_key:
        print("ERROR: Set MP_API_KEY environment variable")
        sys.exit(1)

    from app.database import SessionLocal
    from app.models.material import Material, Property

    client = MPRester(api_key=api_key)
    total = client.materials.summary.count()
    num_chunks = (total // 1000) + 1
    print(f"Total in MP: {total} materials ({num_chunks} chunks of 1000)")

    fields = [
        "material_id", "formula_pretty", "symmetry",
        "band_gap", "formation_energy_per_atom", "volume", "density",
        "nelements", "elements",
    ]

    t0 = time.time()
    results = client.materials.summary.search(
        chunk_size=1000,
        num_chunks=num_chunks,
        fields=fields,
    )
    elapsed = time.time() - t0
    print(f"Downloaded {len(results)} materials in {elapsed:.0f}s ({len(results)/elapsed:.0f}/s)")

    # Store in DB
    os.makedirs("data", exist_ok=True)
    db = SessionLocal()
    existing = set(row[0] for row in db.query(Material.formula).all())
    stored = 0
    skipped = 0

    for r in results:
        formula = getattr(r, "formula_pretty", None) or getattr(r, "material_id", "")
        if formula in existing:
            skipped += 1
            continue

        sym = getattr(r, "symmetry", None)
        if hasattr(sym, "model_dump"):
            sym = sym.model_dump()
        elif not isinstance(sym, dict):
            sym = {}

        material = Material(
            formula=formula,
            name=formula,
            space_group=sym.get("symbol"),
            crystal_system=sym.get("crystal_system"),
            mp_id=getattr(r, "material_id", None),
            volume=getattr(r, "volume", None),
            density=getattr(r, "density", None),
        )
        db.add(material)
        db.flush()

        bg = getattr(r, "band_gap", None)
        if bg is not None:
            db.add(Property(material_id=material.id, property_type="band_gap",
                           value=bg, unit="eV", source="Materials Project", confidence=0.9))
        fe = getattr(r, "formation_energy_per_atom", None)
        if fe is not None:
            db.add(Property(material_id=material.id, property_type="formation_energy",
                           value=fe, unit="eV/atom", source="Materials Project", confidence=0.9))

        stored += 1
        existing.add(formula)

        if stored % 1000 == 0:
            db.commit()
            print(f"  DB: {stored} stored, {skipped} skipped, {stored/(time.time()-t0):.0f}/s", flush=True)

    db.commit()
    db.close()
    t1 = time.time()
    print(f"DB: {stored} stored, {skipped} skipped in {t1-t0:.0f}s total")

    if args.retrain and stored > 0:
        from app.core.trainer import train_and_save_models
        print("Retraining models on all MP data...")
        train_and_save_models(force_retrain=True)

    print("Done!")


if __name__ == "__main__":
    main()
