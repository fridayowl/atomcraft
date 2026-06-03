import numpy as np
from typing import Optional


class PropertyPredictorModel:
    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path
        self.loaded = False

    def load(self):
        self.loaded = True

    def predict(self, descriptors: np.ndarray) -> dict:
        return {"prediction": 0.0, "confidence": 0.0, "model": "property_predictor_v1"}
