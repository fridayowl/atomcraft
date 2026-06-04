"""Active learning loop: generate → predict → validate → retrain → repeat."""
import asyncio, json, os, time, random
from typing import Optional

from app.core.generator import MaterialsGenerator
from app.core.predictor import PropertyPredictor
from app.core.dft import DFTOrchestrator


class ActiveLearningLoop:
    def __init__(self):
        self.generator = MaterialsGenerator()
        self.predictor = PropertyPredictor()
        self.dft = DFTOrchestrator()
        self.iteration = 0
        self.history = []

    async def run_iteration(self, element_constraints: Optional[list] = None,
                             target_properties: Optional[dict] = None,
                             num_candidates: int = 20,
                             dft_engine: str = "vasp",
                             use_denovo: bool = True) -> dict:
        self.iteration += 1
        t0 = time.time()
        print(f"\n{'='*60}")
        print(f"Active Learning Iteration {self.iteration}")
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

        # Step 3: Select most uncertain candidates for DFT
        print("\n[3/5] Selecting candidates for DFT validation...")
        # Use formation energy proximity to 0 as uncertainty proxy
        scored = []
        for c in candidates:
            eform = abs(c.get("predicted_formation_energy", 0))
            uncertainty = 1.0 / (eform + 0.1)
            scored.append((uncertainty, c))
        scored.sort(key=lambda x: -x[0])
        dft_candidates = scored[:max(3, len(candidates) // 5)]
        print(f"  Selected {len(dft_candidates)} for DFT validation")

        # Step 4: Run DFT validation
        print("\n[4/5] Running DFT validation...")
        dft_results = self.dft.batch_validate(
            [c for _, c in dft_candidates], engine=dft_engine
        )
        validated = []
        for c, dr in zip([c for _, c in dft_candidates], dft_results):
            validated.append({
                "formula": c["formula"],
                "dft_job": dr,
                "predicted_gap": c.get("predicted_band_gap"),
                "predicted_eform": c.get("predicted_formation_energy"),
            })

        # Step 5: Store results and retrain
        print("\n[5/5] Storing DFT results and retraining...")
        validated_count = 0
        for v in validated:
            dr = v.get("dft_job", {})
            energy = dr.get("energy") or dr.get("final_energy")
            if energy is not None:
                self._store_dft_result(v["formula"], dr)
                validated_count += 1

        if validated_count > 0:
            self._retrain_models()

        iteration_result = {
            "iteration": self.iteration,
            "candidates_generated": len(candidates),
            "dft_submitted": len(dft_candidates),
            "dft_converged": validated_count,
            "elapsed_seconds": round(time.time() - t0, 1),
            "validated": validated,
        }
        self.history.append(iteration_result)

        print(f"\n  Done in {iteration_result['elapsed_seconds']:.0f}s")
        return iteration_result

    def _store_dft_result(self, formula: str, dft_result: dict):
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

        energy = dft_result.get("energy") or dft_result.get("final_energy")
        band_gap = dft_result.get("band_gap")
        if energy is not None:
            from app.core.composition_analyzer import CompositionAnalyzer
            analyzer = CompositionAnalyzer()
            comp = analyzer.parse_formula(formula)
            n_atoms = sum(comp.values()) if comp else 1
            eform = energy / n_atoms
            db.execute(insert(Property), [{
                "material_id": material.id,
                "property_type": "dft_energy",
                "value": float(energy),
                "unit": "eV",
                "source": "DFT_VASP",
                "confidence": 0.98,
            }])
        if band_gap is not None:
            db.execute(insert(Property), [{
                "material_id": material.id,
                "property_type": "dft_band_gap",
                "value": float(band_gap),
                "unit": "eV",
                "source": "DFT_VASP",
                "confidence": 0.98,
            }])
        db.commit()
        db.close()

    def _retrain_models(self):
        from app.core.trainer import train_and_save_models
        print("  Retraining models with DFT-validated data...")
        train_and_save_models(force_retrain=True)

    def get_summary(self) -> dict:
        return {
            "total_iterations": self.iteration,
            "history": self.history,
            "total_dft_submitted": sum(h["dft_submitted"] for h in self.history),
            "total_dft_converged": sum(h["dft_converged"] for h in self.history),
        }
