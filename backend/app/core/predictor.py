from typing import Optional
from app.core.trainer import predict_property, load_prediction_model, _get_element_feature_vector
from app.core.composition_analyzer import CompositionAnalyzer

FEATURE_NAMES_56 = [
    "n_elements", "has_oxygen", "has_transition_metal", "total_atoms",
    "avg_group", "group_range", "avg_row", "row_range",
    "avg_atomic_radius", "radius_range", "radius_std",
    "avg_electronegativity", "electronegativity_range", "electronegativity_std",
    "avg_atomic_mass", "mass_range", "mass_std",
    "avg_ionization_energy", "ionization_energy_range",
    "s_electrons", "p_electrons", "d_electrons", "f_electrons",
    "n_metal", "n_nonmetal", "n_metalloid",
    "n_alkali", "n_alkaline", "n_halogen", "n_noble_gas",
    "log_volume",
    "crystal_cubic", "crystal_tetragonal", "crystal_hexagonal",
    "crystal_orthorhombic", "crystal_monoclinic", "crystal_triclinic",
] + [f"reserved_{i}" for i in range(37, 56)]


class PropertyPredictor:
    def __init__(self):
        self.models = {}
        import json, os
        config_path = os.path.join(os.path.dirname(__file__), "models", "model_config.json")
        if os.path.exists(config_path):
            with open(config_path) as f:
                cfg = json.load(f)
            for prop in cfg:
                m = load_prediction_model(prop)
                if m:
                    self.models[prop] = m

    async def predict(self, formula: str, property_type: str,
                       composition: Optional[dict] = None,
                       crystal_system: str = "", volume: float = 0) -> dict:
        value, confidence = predict_property(formula, property_type, crystal_system, volume)
        return {
            "formula": formula,
            "property": property_type,
            "predicted_value": value,
            "confidence": confidence,
            "model": "aion-rf-v2" if property_type in self.models else "aion-heuristic-v1",
        }

    async def batch_predict(self, formulas: list[str],
                             properties: list[str]) -> list[dict]:
        results = []
        for formula in formulas:
            for prop in properties:
                pred = await self.predict(formula, prop)
                results.append(pred)
        return results

    async def get_feature_importance(self, property_type: str) -> dict:
        model = self.models.get(property_type)
        if model and hasattr(model, "feature_importances_"):
            importances = model.feature_importances_
            # Map only the 37 actual features (indices 0-36)
            names = FEATURE_NAMES_56[:37]
            imps = importances[:37] if len(importances) >= 37 else importances
            fnames = names[:len(imps)]
            features = {name: round(float(imp), 4)
                       for name, imp in sorted(zip(fnames, imps),
                                                key=lambda x: -x[1])
                       if imp > 0.001}
            return {"property": property_type, "features": features}

        return {
            "property": property_type,
            "features": {
                "avg_electronegativity": 0.25,
                "electronegativity_range": 0.20,
                "avg_atomic_radius": 0.18,
                "n_elements": 0.15,
                "avg_atomic_mass": 0.12,
                "radius_range": 0.10,
            }
        }
