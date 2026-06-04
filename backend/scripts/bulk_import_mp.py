#!/usr/bin/env python3
"""Download ALL MP materials, batch-insert into DB, retrain models."""

import os, sys, time, argparse
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--retrain", action="store_true")
    args = parser.parse_args()

    api_key = os.getenv("MP_API_KEY", "")
    if not api_key:
        print("ERROR: Set MP_API_KEY")
        sys.exit(1)

    from mp_api.client import MPRester
    from app.database import SessionLocal
    from app.models.material import Material, Property
    from sqlalchemy import insert

    client = MPRester(api_key=api_key)
    total = client.materials.summary.count()
    num_chunks = (total // 1000) + 1
    print(f"MP: {total} materials ({num_chunks} chunks of 1000)")

    fields = [
        "material_id", "formula_pretty", "symmetry",
        "band_gap", "formation_energy_per_atom", "volume", "density",
    ]

    t0 = time.time()
    results = client.materials.summary.search(
        chunk_size=1000, num_chunks=num_chunks, fields=fields,
    )
    print(f"Downloaded {len(results)} in {time.time()-t0:.0f}s")

    db = SessionLocal()
    existing = set(row[0] for row in db.query(Material.formula).all())
    print(f"DB has {len(existing)} materials")

    BATCH = 5000
    stored_total = 0
    all_new = []

    for r in results:
        formula = getattr(r, "formula_pretty", None) or getattr(r, "material_id", "")
        if formula in existing:
            continue
        existing.add(formula)

        sym = getattr(r, "symmetry", None)
        if hasattr(sym, "model_dump"):
            sym = sym.model_dump()
        elif not isinstance(sym, dict):
            sym = {}

        all_new.append((formula, r, sym))

    print(f"New: {len(all_new)}")

    for i in range(0, len(all_new), BATCH):
        batch = all_new[i:i+BATCH]
        mats = []
        result_map = {}

        for formula, r, sym in batch:
            mats.append({
                "formula": formula, "name": formula,
                "space_group": sym.get("symbol"),
                "crystal_system": sym.get("crystal_system"),
                "mp_id": getattr(r, "material_id", None),
                "volume": getattr(r, "volume", None),
                "density": getattr(r, "density", None),
            })
            result_map[formula] = r

        # INSERT + RETURNING to get IDs in one shot
        stmt = insert(Material).returning(Material.id, Material.formula)
        inserted = db.execute(stmt, mats).all()
        id_map = dict(inserted)  # (id, formula) -> {id: formula}

        props = []
        for mid, formula in id_map.items():
            r = result_map.get(formula)
            if r is None:
                continue
            bg = getattr(r, "band_gap", None)
            if bg is not None:
                props.append({"material_id": mid, "property_type": "band_gap",
                              "value": bg, "unit": "eV", "source": "Materials Project", "confidence": 0.9})
            fe = getattr(r, "formation_energy_per_atom", None)
            if fe is not None:
                props.append({"material_id": mid, "property_type": "formation_energy",
                              "value": fe, "unit": "eV/atom", "source": "Materials Project", "confidence": 0.9})

        if props:
            db.execute(insert(Property), props)

        db.commit()
        stored_total += len(mats)
        elapsed = time.time() - t0
        print(f"  batch {i//BATCH+1}/{(len(all_new)-1)//BATCH+1} | "
              f"+{len(mats)} | {stored_total} total | {elapsed:.0f}s", flush=True)

    db.close()
    print(f"\nDone: {stored_total} stored in {time.time()-t0:.0f}s")

    if args.retrain and stored_total > 0:
        from app.core.trainer import train_and_save_models
        print("Retraining...")
        train_and_save_models(force_retrain=True)


if __name__ == "__main__":
    main()
