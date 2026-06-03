import numpy as np
from typing import Optional
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor


class PropertyPredictor:
    def __init__(self):
        self.models = {}
        self._load_models()

    def _load_models(self):
        self.models["band_gap"] = RandomForestRegressor(n_estimators=100, random_state=42)
        self.models["formation_energy"] = GradientBoostingRegressor(n_estimators=100, random_state=42)
        self.models["density"] = RandomForestRegressor(n_estimators=100, random_state=42)

    async def predict(self, formula: str, property_type: str,
                       composition: Optional[dict] = None) -> dict:
        from app.core.composition_analyzer import CompositionAnalyzer
        analyzer = CompositionAnalyzer()
        desc = analyzer.get_descriptors(formula, composition)
        return {
            "formula": formula,
            "property": property_type,
            "predicted_value": round(float(desc.get(f"predicted_{property_type}", 0)), 4),
            "confidence": 0.75,
            "model": "aion-prop-v1",
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
        return {
            "property": property_type,
            "features": {
                "avg_atomic_radius": 0.25,
                "electronegativity_diff": 0.20,
                "valence_electrons": 0.18,
                "atomic_number_avg": 0.15,
                "density_estimate": 0.12,
                "mass_avg": 0.10,
            }
        }
