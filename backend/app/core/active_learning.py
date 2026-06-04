"""Active learning loop: generate → predict → validate → retrain → repeat."""
import asyncio, json, os, time, random
from typing import Optional

from app.core.generator import MaterialsGenerator
from app.core.predictor import PropertyPredictor


class ActiveLearningLoop:
    """Active learning loop with optional DFT validation or pseudo-validation.

    Modes:
      - dft_mode=True:  requires DFTOrchestrator + DFT software installed
      - dft_mode=False: uses pseudo-validation (predictor confidence as proxy),
                        stores candidates in DB, and retrains — no DFT needed.
    """

    def __init__(self, dft_mode: bool = False):
        self.generator = MaterialsGenerator()
        self.predictor = PropertyPredictor()
        self.dft = None
        if dft_mode:
            from app.core.dft import DFTOrchestrator
            self.dft = DFTOrchestrator()
        self.iteration = 0
        self.history = []

    async def run_iteration(self, element_constraints: Optional[list] = None,
                             target_properties: Optional[dict] = None,
                             num_candidates: int = 20,
                             dft_engine: str = "vasp",
                             use_denovo: bool = True,
                             max_validate: int = 5) -> dict:
        self.iteration += 1
        t0 = time.time()
        print(f"\n{'='*60}")
        print(f"Active Learning Iteration {self.iteration}")
        if self.dft:
            print(f"  Mode: DFT ({dft_engine})")
        else:
            print("  Mode: pseudo-validation (no DFT)")
        print(f"{'='*60}")

        # Step 1: Generate candidates
        print("\n[1/5] Generating candidates...")
        candidates = []
        if use_denovo:
            denovo = await self.generator.generate_denovo(
                element_constraints=element_constraints,
                target_properties=target_properties,
                num_candidates=num_candidates // 2,
            )
            candidates.extend(denovo)
        subst = await self.generator.generate_crystal(
            element_constraints=element_constraints,
            target_properties=target_properties,
            num_candidates=num_candidates // 2,
        )
        candidates.extend(subst)
        print(f"  Generated {len(candidates)} candidates")

        # Step 2: Predict all properties
        print("\n[2/5] Predicting properties...")
        for c in candidates:
            formula = c["formula"]
            for prop in ["band_gap", "formation_energy", "density"]:
                pred = await self.predictor.predict(
                    formula, prop,
                    crystal_system=c.get("crystal_system", ""),
                    volume=c.get("lattice_parameters", {}).get("a", 5) ** 3,
                )
                c.setdefault("predictions", {})[prop] = pred

        # Step 3: Select candidates for validation
        print("\n[3/5] Selecting candidates for validation...")
        scored = []
        for c in candidates:
            eform = abs(c.get("predicted_formation_energy", 0))
            uncertainty = 1.0 / (eform + 0.1)
            scored.append((uncertainty, c))
        scored.sort(key=lambda x: -x[0])
        val_candidates = scored[:min(max_validate, len(scored))]
        print(f"  Selected {len(val_candidates)} for validation")

        # Step 4: Validate candidates
        print("\n[4/5] Validating candidates...")
        validated = []
        if self.dft:
            dft_results = self.dft.batch_validate(
                [c for _, c in val_candidates], engine=dft_engine
            )
            for c, dr in zip([c for _, c in val_candidates], dft_results):
                validated.append({
                    "formula": c["formula"],
                    "method": "dft",
                    "result": dr,
                    "energy": dr.get("energy") or dr.get("final_energy"),
                    "band_gap": dr.get("band_gap"),
                    "predicted_gap": c.get("predicted_band_gap"),
                    "predicted_eform": c.get("predicted_formation_energy"),
                })
        else:
            # Pseudo-validation: use predictor's own confidence
            for _, c in val_candidates:
                validated.append({
                    "formula": c["formula"],
                    "method": "pseudo",
                    "result": c.get("predictions", {}),
                    "energy": c.get("predicted_formation_energy", 0) * -5,
                    "band_gap": c.get("predicted_band_gap", 0),
                    "predicted_gap": c.get("predicted_band_gap"),
                    "predicted_eform": c.get("predicted_formation_energy"),
                })

        # Step 5: Store results and retrain
        print("\n[5/5] Storing results and retraining...")
        validated_count = 0
        for v in validated:
            if v["energy"] is not None:
                self._store_validation_result(v["formula"], v)
                validated_count += 1

        if validated_count > 0:
            self._retrain_models()

        iteration_result = {
            "iteration": self.iteration,
            "candidates_generated": len(candidates),
            "candidates_validated": len(val_candidates),
            "validation_success": validated_count,
            "elapsed_seconds": round(time.time() - t0, 1),
            "validated": [
                {
                    "formula": v["formula"],
                    "method": v["method"],
                    "dft_energy": v.get("energy"),
                    "dft_band_gap": v.get("band_gap"),
                    "predicted_gap": v.get("predicted_gap"),
                    "predicted_eform": v.get("predicted_eform"),
                }
                for v in validated
            ],
        }
        self.history.append(iteration_result)

        print(f"\n  Done in {iteration_result['elapsed_seconds']:.0f}s")
        print(f"  Validated: {validated_count}/{len(val_candidates)}")
        return iteration_result

    def _store_validation_result(self, formula: str, result: dict):
        from app.database import SessionLocal
        from app.models.material import Material, Property
        from sqlalchemy import insert

        db = SessionLocal()
        material = db.query(Material).filter(Material.formula == formula).first()
        if material is None:
            material = Material(
                formula=formula, name=formula,
                space_group="P1", crystal_system="unknown",
            )
            db.add(material)
            db.flush()

        energy = result.get("energy")
        band_gap = result.get("band_gap")
        source = "DFT_VASP" if result.get("method") == "dft" else "AL_PSEUDO"
        conf = 0.98 if result.get("method") == "dft" else 0.70

        if energy is not None:
            from app.core.composition_analyzer import CompositionAnalyzer
            analyzer = CompositionAnalyzer()
            comp = analyzer.parse_formula(formula)
            n_atoms = sum(comp.values()) if comp else 1
            eform = energy / n_atoms
            db.execute(insert(Property), [{
                "material_id": material.id,
                "property_type": "formation_energy",
                "value": float(eform),
                "unit": "eV/atom",
                "source": source,
                "confidence": conf,
            }])
        if band_gap is not None:
            db.execute(insert(Property), [{
                "material_id": material.id,
                "property_type": "band_gap",
                "value": float(band_gap),
                "unit": "eV",
                "source": source,
                "confidence": conf,
            }])
        db.commit()
        db.close()

    def _retrain_models(self):
        from app.core.trainer import train_and_save_models
        print("  Retraining models with new data...")
        train_and_save_models(force_retrain=True)

    def get_summary(self) -> dict:
        return {
            "total_iterations": self.iteration,
            "history": self.history,
            "total_validated": sum(h["validation_success"] for h in self.history),
        }

    @staticmethod
    def run_pseudo_loop(num_iterations: int = 3, candidates_per_iter: int = 10,
                        element_constraints: Optional[list] = None):
        """Convenient synchronous entry point for pseudo-validation loop."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        al = ActiveLearningLoop(dft_mode=False)

        async def _run():
            for i in range(num_iterations):
                result = await al.run_iteration(
                    element_constraints=element_constraints,
                    num_candidates=candidates_per_iter,
                    max_validate=3,
                )
                print(f"  Iteration {i+1}: {result['validation_success']} validated")
            summary = al.get_summary()
            print(f"\n{'='*60}")
            print(f"Active Learning Complete: {summary['total_validated']} total validated")
            print(f"{'='*60}")
            return summary

        return loop.run_until_complete(_run())
