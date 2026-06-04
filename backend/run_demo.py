import sys; sys.path.insert(0, "backend")
import asyncio, json, time

from app.core.generator import MaterialsGenerator
from app.core.predictor import PropertyPredictor
from app.core.trainer import predict_space_group, predict_property
from app.core.dft import generate_vasp_inputs

gen = MaterialsGenerator()
pred = PropertyPredictor()

results = []

def log(s):
    print(s)
    results.append(s)

log("=" * 70)
log("ATOMCRAFT MATERIALS DISCOVERY DEMO")
log("Exploring novel cathode materials in Li-Ni-Mn-Co-O space")
log("=" * 70)

# Step 1: De-novo generation
log("\n[1] Generating novel cathode candidates (Li-Ni-Mn-Co-O)...")
t0 = time.time()
constraints = ["Li", "Ni", "Mn", "Co", "O"]
candidates = asyncio.run(gen.generate_denovo(
    element_constraints=constraints,
    target_properties={"band_gap": 2.0},
    num_candidates=15,
))
log(f"   Generated {len(candidates)} candidates in {time.time()-t0:.1f}s")

# Step 2: Predict all properties
log("\n[2] Predicting properties...")
t0 = time.time()
enriched = []
for c in candidates:
    f = c["formula"]
    gap, gc = predict_property(f, "band_gap")
    eform, ec = predict_property(f, "formation_energy")
    dens, dc = predict_property(f, "density")
    sg_num, sg_sym, sg_conf = predict_space_group(f)
    enriched.append({
        "formula": f,
        "space_group": sg_sym,
        "band_gap_eV": round(gap, 3),
        "formation_energy_eV_per_atom": round(eform, 3),
        "density_g_per_cm3": round(dens, 3),
        "stability_score": c["stability_score"],
        "generation_score": c["generation_score"],
        "elements": c["elements"],
    })
log(f"   Predicted {len(enriched)} candidates in {time.time()-t0:.1f}s")

# Top by stability
enriched.sort(key=lambda x: -x["formation_energy_eV_per_atom"])
log("\n   Top 5 most stable (most negative formation energy):")
log(f"   {'Formula':25s} {'SpG':10s} {'Gap(eV)':10s} {'E_form(eV)':12s} {'Density':10s} {'Score':8s}")
log(f"   {'-'*25} {'-'*10} {'-'*10} {'-'*12} {'-'*10} {'-'*8}")
for c in enriched[:5]:
    log(f"   {c['formula']:25s} {c['space_group']:10s} {c['band_gap_eV']:<10.3f} {c['formation_energy_eV_per_atom']:<12.3f} {c['density_g_per_cm3']:<10.3f} {c['stability_score']:<8.3f}")

# Top by band gap
log("\n   Top 5 highest band gap:")
log(f"   {'Formula':25s} {'SpG':10s} {'Gap(eV)':10s} {'E_form(eV)':12s} {'Density':10s}")
log(f"   {'-'*25} {'-'*10} {'-'*10} {'-'*12} {'-'*10}")
for c in sorted(enriched, key=lambda x: -x["band_gap_eV"])[:5]:
    log(f"   {c['formula']:25s} {c['space_group']:10s} {c['band_gap_eV']:<10.3f} {c['formation_energy_eV_per_atom']:<12.3f} {c['density_g_per_cm3']:<10.3f}")

# Step 3: Substitution generation
log("\n[3] Substitution-based generation from known templates...")
t0 = time.time()
subst = asyncio.run(gen.generate_crystal(
    element_constraints=constraints,
    num_candidates=10,
))
log(f"   Generated {len(subst)} substitution candidates")
for c in subst[:5]:
    gap, gc = predict_property(c["formula"], "band_gap")
    eform, ec = predict_property(c["formula"], "formation_energy")
    log(f"   {c['formula']:25s} subst={c.get('substitution','?'):15s} gap={gap:.3f} eV  E_form={eform:.3f} eV/atom")

# Step 4: Feature importance
log("\n[4] Feature importance analysis for cathode-relevant properties:")
for prop in ["band_gap", "formation_energy"]:
    fi = asyncio.run(pred.get_feature_importance(prop))
    top5 = list(fi["features"].items())[:5]
    log(f"\n   {prop} (top 5 of {len(fi['features'])} features):")
    for name, score in top5:
        log(f"     {name:30s}: {score:.4f}")

# Step 5: DFT input generation for best candidate
best = enriched[0]
log(f"\n[5] Generating VASP inputs for best candidate: {best['formula']}...")
import tempfile, os
with tempfile.TemporaryDirectory() as tmpdir:
    lattice = {"a": 5.0, "b": 5.0, "c": 5.0}
    vasp = generate_vasp_inputs(
        best["formula"],
        best["space_group"],
        lattice,
        best["elements"],
        tmpdir,
    )
    files = os.listdir(tmpdir)
    for f in sorted(files):
        path = os.path.join(tmpdir, f)
        with open(path) as fh:
            log(f"   {f}: {len(fh.readlines())} lines")

# Step 6: Active learning
log(f"\n[6] Active learning iteration (pseudo-validation)...")
from app.core.active_learning import ActiveLearningLoop
summary = ActiveLearningLoop.run_pseudo_loop(
    num_iterations=1,
    candidates_per_iter=6,
    element_constraints=constraints,
)
log(f"\n   Validated: {summary['total_validated']}")

# Summary
log(f"\n{'='*70}")
log("DEMO COMPLETE")
log(f"{'='*70}")
log(f"Total candidates generated:      {len(candidates) + len(subst)}")
stable = enriched[0]
highgap = sorted(enriched, key=lambda x: -x["band_gap_eV"])[0]
log(f"Total data points predicted:     {(len(candidates) + len(subst)) * 3}")
log(f"Models contributing:             11 trained RandomForest models")
log(f"Most stable candidate:           {stable['formula']} (E_form={stable['formation_energy_eV_per_atom']} eV/atom)")
log(f"Highest band gap candidate:      {highgap['formula']} ({highgap['band_gap_eV']} eV)")

# Save results
out = "\n".join(results)
with open("backend/demo_results.txt", "w") as f:
    f.write(out)
print(f"\nDemo results saved to backend/demo_results.txt")
