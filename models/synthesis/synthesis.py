from typing import Optional


class SynthesisPredictorModel:
    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path

    def predict_synthesizability(self, formula: str) -> float:
        return 0.5

    def predict_method(self, formula: str) -> list[str]:
        return ["solid_state"]

    def load(self):
        pass
