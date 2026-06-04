#!/usr/bin/env python3
"""Fetch additional MP properties with checkpoint-resume support."""
import sys, os, time, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

TARGET_PROPS = [
    "bulk_modulus", "shear_modulus", "universal_anisotropy",
    "homogeneous_poisson", "total_magnetization",
    "e_total", "e_ionic", "e_electronic",
    "energy_above_hull", "is_stable",
    "weighted_surface_energy", "weighted_work_function",
]
BATCH = 2000
CHECKPOINT = os.path.join(os.path.dirname(__file__), ".fetch_props_ckpt.json")


def fetch():
    api_key = os.getenv("MP_API_KEY", "")
    if not api_key:
        print("ERROR: Set MP_API_KEY"); return
    from mp_api.client import MPRester
    from app.database import SessionLocal
    from app.models.material import Material, Property
    from sqlalchemy import insert, text

    ckpt = {"offset": 0}
    if os.path.exists(CHECKPOINT):
        ckpt = json.load(open(CHECKPOINT))
        print(f"Resuming from offset {ckpt['offset']}")

    db = SessionLocal()
    all_mp_ids = [r[0] for r in db.query(Material.mp_id).filter(Material.mp_id.isnot(None)).all()]
    total = len(all_mp_ids)
    db.close()
    print(f"Materials in DB: {total}")

    client = MPRester(api_key)
    t0 = time.time()
    stored = 0
    # Process in chunks to avoid timeouts
    chunk_size = 500
    fields = ["material_id", "formula_pretty"] + TARGET_PROPS
    prop_unit_map = {
        "bulk_modulus": "GPa", "shear_modulus": "GPa",
        "universal_anisotropy": "", "homogeneous_poisson": "",
        "total_magnetization": "mu_B",
        "e_total": "", "e_ionic": "", "e_electronic": "",
        "energy_above_hull": "eV/atom", "is_stable": "",
        "weighted_surface_energy": "J/m^2", "weighted_work_function": "eV",
    }

    for offset in range(ckpt["offset"], total, chunk_size):
        batch_ids = all_mp_ids[offset:offset + chunk_size]
        try:
            docs = client.materials.summary.search(
                material_ids=batch_ids, fields=fields, num_chunks=1, chunk_size=chunk_size,
            )
        except Exception as e:
            print(f"Error at offset {offset}: {e}")
            json.dump({"offset": offset}, open(CHECKPOINT, "w"))
            continue

        db = SessionLocal()
        id_map = dict(db.query(Material.mp_id, Material.id).filter(
            Material.mp_id.in_([d.material_id for d in docs])
        ).all())
        new_props = []
        for doc in docs:
            mid = id_map.get(doc.material_id)
            if mid is None:
                continue
            for prop in TARGET_PROPS:
                val = getattr(doc, prop, None)
                if val is None:
                    continue
                if isinstance(val, (dict, list)):
                    continue
                scalar = float(val) if not isinstance(val, bool) else (1.0 if val else 0.0)
                new_props.append({
                    "material_id": mid,
                    "property_type": prop,
                    "value": scalar,
                    "unit": prop_unit_map.get(prop, ""),
                    "source": "Materials Project",
                    "confidence": 0.95,
                })
        if new_props:
            for i in range(0, len(new_props), 500):
                db.execute(insert(Property), new_props[i:i+500])
            db.commit()
            stored += len(new_props)
        db.close()
        json.dump({"offset": offset + chunk_size}, open(CHECKPOINT, "w"))
        elapsed = time.time() - t0
        print(f"  offset {offset+chunk_size}/{total} | {stored} props stored | {elapsed:.0f}s")

    client.close()
    if os.path.exists(CHECKPOINT):
        os.remove(CHECKPOINT)
    print(f"Done: {stored} properties in {time.time()-t0:.0f}s")


def count_props():
    from app.database import SessionLocal
    from app.models.material import Property
    from sqlalchemy import func
    db = SessionLocal()
    counts = db.query(Property.property_type, func.count(Property.id)).group_by(
        Property.property_type).order_by(func.count(Property.id).desc()).all()
    for pt, cnt in counts:
        print(f"  {pt}: {cnt}")
    db.close()


def retrain():
    from app.core.trainer import train_and_save_models
    train_and_save_models(force_retrain=True)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--retrain", action="store_true")
    parser.add_argument("--count", action="store_true")
    args = parser.parse_args()
    if args.count:
        count_props()
    elif args.retrain:
        retrain()
    else:
        fetch()
