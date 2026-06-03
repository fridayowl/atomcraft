from typing import Optional
from app.core.trainer import predict_property, load_prediction_model, _get_element_feature_vector
from app.core.composition_analyzer import CompositionAnalyzer


class PropertyPredictor:
    def __init__(self):
        self.models = {}
        for prop in ["band_gap", "formation_energy", "density"]:
            m = load_prediction_model(prop)
            if m:
                self.models[prop] = m

    async def predict(self, formula: str, property_type: str,
                       composition: Optional[dict] = None) -> dict:
        value, confidence = predict_property(formula, property_type)
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
            feature_names = [
                "n_elements", "has_oxygen", "has_transition_metal",
                "avg_electronegativity", "electronegativity_range",
                "avg_atomic_radius", "radius_range",
                "avg_atomic_mass", "avg_valence_electrons", "total_atoms",
            ]
            importances = model.feature_importances_
            features = {name: round(float(imp), 4)
                       for name, imp in sorted(
                           zip(feature_names, importances),
                           key=lambda x: x[1], reverse=True)}
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
