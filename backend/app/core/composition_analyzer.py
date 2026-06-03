import re
import numpy as np
from typing import Optional

ELEMENT_DATA = {
    "H": {"radius": 0.53, "en": 2.20, "mass": 1.008, "valence": 1, "group": 1},
    "Li": {"radius": 1.67, "en": 0.98, "mass": 6.94, "valence": 1, "group": 1},
    "Be": {"radius": 1.12, "en": 1.57, "mass": 9.01, "valence": 2, "group": 2},
    "B": {"radius": 0.87, "en": 2.04, "mass": 10.81, "valence": 3, "group": 13},
    "C": {"radius": 0.67, "en": 2.55, "mass": 12.01, "valence": 4, "group": 14},
    "N": {"radius": 0.56, "en": 3.04, "mass": 14.01, "valence": 5, "group": 15},
    "O": {"radius": 0.48, "en": 3.44, "mass": 16.00, "valence": 6, "group": 16},
    "F": {"radius": 0.42, "en": 3.98, "mass": 19.00, "valence": 7, "group": 17},
    "Na": {"radius": 1.90, "en": 0.93, "mass": 22.99, "valence": 1, "group": 1},
    "Mg": {"radius": 1.45, "en": 1.31, "mass": 24.31, "valence": 2, "group": 2},
    "Al": {"radius": 1.18, "en": 1.61, "mass": 26.98, "valence": 3, "group": 13},
    "Si": {"radius": 1.11, "en": 1.90, "mass": 28.09, "valence": 4, "group": 14},
    "P": {"radius": 0.98, "en": 2.19, "mass": 30.97, "valence": 5, "group": 15},
    "S": {"radius": 0.88, "en": 2.58, "mass": 32.06, "valence": 6, "group": 16},
    "Cl": {"radius": 0.79, "en": 3.16, "mass": 35.45, "valence": 7, "group": 17},
    "K": {"radius": 2.43, "en": 0.82, "mass": 39.10, "valence": 1, "group": 1},
    "Ca": {"radius": 1.94, "en": 1.00, "mass": 40.08, "valence": 2, "group": 2},
    "Sc": {"radius": 1.84, "en": 1.36, "mass": 44.96, "valence": 3, "group": 3},
    "Ti": {"radius": 1.76, "en": 1.54, "mass": 47.87, "valence": 4, "group": 4},
    "V": {"radius": 1.71, "en": 1.63, "mass": 50.94, "valence": 5, "group": 5},
    "Cr": {"radius": 1.66, "en": 1.66, "mass": 52.00, "valence": 6, "group": 6},
    "Mn": {"radius": 1.61, "en": 1.55, "mass": 54.94, "valence": 7, "group": 7},
    "Fe": {"radius": 1.56, "en": 1.83, "mass": 55.85, "valence": 8, "group": 8},
    "Co": {"radius": 1.52, "en": 1.88, "mass": 58.93, "valence": 9, "group": 9},
    "Ni": {"radius": 1.49, "en": 1.91, "mass": 58.69, "valence": 10, "group": 10},
    "Cu": {"radius": 1.45, "en": 1.90, "mass": 63.55, "valence": 11, "group": 11},
    "Zn": {"radius": 1.42, "en": 1.65, "mass": 65.38, "valence": 12, "group": 12},
    "Zr": {"radius": 2.06, "en": 1.33, "mass": 91.22, "valence": 4, "group": 4},
    "Nb": {"radius": 1.98, "en": 1.60, "mass": 92.91, "valence": 5, "group": 5},
    "Mo": {"radius": 1.90, "en": 2.16, "mass": 95.95, "valence": 6, "group": 6},
    "Sn": {"radius": 1.40, "en": 1.96, "mass": 118.71, "valence": 4, "group": 14},
    "Sb": {"radius": 1.33, "en": 2.05, "mass": 121.76, "valence": 5, "group": 15},
    "Te": {"radius": 1.23, "en": 2.10, "mass": 127.60, "valence": 6, "group": 16},
    "Ba": {"radius": 2.68, "en": 0.89, "mass": 137.33, "valence": 2, "group": 2},
    "Ta": {"radius": 2.00, "en": 1.50, "mass": 180.95, "valence": 5, "group": 5},
    "W": {"radius": 1.93, "en": 2.36, "mass": 183.84, "valence": 6, "group": 6},
    "Pt": {"radius": 1.77, "en": 2.28, "mass": 195.08, "valence": 10, "group": 10},
    "Au": {"radius": 1.74, "en": 2.54, "mass": 196.97, "valence": 11, "group": 11},
    "Pb": {"radius": 1.54, "en": 2.33, "mass": 207.20, "valence": 14, "group": 14},
    "Bi": {"radius": 1.43, "en": 2.02, "mass": 208.98, "valence": 15, "group": 15},
    "La": {"radius": 2.50, "en": 1.10, "mass": 138.91, "valence": 3, "group": 3},
    "Ce": {"radius": 2.48, "en": 1.12, "mass": 140.12, "valence": 4, "group": 3},
    "Nd": {"radius": 2.45, "en": 1.14, "mass": 144.24, "valence": 3, "group": 3},
    "Gd": {"radius": 2.38, "en": 1.20, "mass": 157.25, "valence": 3, "group": 3},
    "Er": {"radius": 2.34, "en": 1.24, "mass": 167.26, "valence": 3, "group": 3},
    "Ga": {"radius": 1.24, "en": 1.81, "mass": 69.72, "valence": 3, "group": 13},
    "Ge": {"radius": 1.21, "en": 2.01, "mass": 72.63, "valence": 4, "group": 14},
    "As": {"radius": 1.14, "en": 2.18, "mass": 74.92, "valence": 5, "group": 15},
    "Se": {"radius": 1.03, "en": 2.55, "mass": 78.97, "valence": 6, "group": 16},
    "Br": {"radius": 0.94, "en": 2.96, "mass": 79.90, "valence": 7, "group": 17},
    "I": {"radius": 1.15, "en": 2.66, "mass": 126.90, "valence": 7, "group": 17},
    "Ru": {"radius": 1.78, "en": 2.20, "mass": 101.07, "valence": 8, "group": 8},
    "Rh": {"radius": 1.73, "en": 2.28, "mass": 102.91, "valence": 9, "group": 9},
    "Pd": {"radius": 1.69, "en": 2.20, "mass": 106.42, "valence": 10, "group": 10},
    "Ag": {"radius": 1.65, "en": 1.93, "mass": 107.87, "valence": 11, "group": 11},
    "Cd": {"radius": 1.61, "en": 1.69, "mass": 112.41, "valence": 12, "group": 12},
    "In": {"radius": 1.44, "en": 1.78, "mass": 114.82, "valence": 3, "group": 13},
    "Hf": {"radius": 2.16, "en": 1.30, "mass": 178.49, "valence": 4, "group": 4},
    "Re": {"radius": 1.88, "en": 1.90, "mass": 186.21, "valence": 7, "group": 7},
    "Os": {"radius": 1.85, "en": 2.20, "mass": 190.23, "valence": 8, "group": 8},
    "Ir": {"radius": 1.80, "en": 2.20, "mass": 192.22, "valence": 9, "group": 9},
}


class CompositionAnalyzer:
    def parse_formula(self, formula: str) -> dict[str, float]:
        try:
            from pymatgen.core import Composition as PMGComposition
            comp = PMGComposition(formula)
            return {str(el): float(amt) for el, amt in comp.as_dict().items() if float(amt) > 0}
        except Exception:
            pass

        pattern = r'([A-Z][a-z]*)(\d*\.?\d*)'
        matches = re.findall(pattern, formula)
        composition = {}
        for element, count in matches:
            if element:
                count = float(count) if count else 1.0
                composition[element] = composition.get(element, 0) + count
        return composition

    def get_descriptors(self, formula: str,
                        composition: Optional[dict] = None) -> dict:
        if composition is None:
            composition = self.parse_formula(formula)

        if not composition:
            return {"formula": formula, "elements": [], "n_elements": 0}

        elements = list(composition.keys())
        amounts = list(composition.values())
        total = sum(amounts)
        fractions = [a / total for a in amounts]

        radii = []
        ens = []
        masses = []
        valences = []
        groups = []
        missing = 0
        for el in elements:
            data = ELEMENT_DATA.get(el)
            if data:
                radii.append(data["radius"])
                ens.append(data["en"])
                masses.append(data["mass"])
                valences.append(data["valence"])
                groups.append(data["group"])
            else:
                missing += 1
                radii.append(1.5)
                ens.append(1.5)
                masses.append(50.0)
                valences.append(3)
                groups.append(10)

        avg_radius = float(np.average(radii, weights=fractions))
        avg_en = float(np.average(ens, weights=fractions))
        avg_mass = float(np.average(masses, weights=fractions))
        avg_valence = float(np.average(valences, weights=fractions))
        en_diff = float(np.max(ens) - np.min(ens)) if len(ens) > 1 else 0
        radius_diff = float(np.max(radii) - np.min(radii)) if len(radii) > 1 else 0

        transition_metals = {"Sc","Ti","V","Cr","Mn","Fe","Co","Ni","Cu","Zn","Y","Zr","Nb","Mo","Tc","Ru","Rh","Pd","Ag","Cd","Hf","Ta","W","Re","Os","Ir","Pt","Au"}
        has_tm = any(el in transition_metals for el in elements)

        from app.core.trainer import predict_property
        formula_for_pred = formula if formula else "-".join(sorted(elements))
        _band_gap, _ = predict_property(formula_for_pred, "band_gap")
        _formation_energy, _ = predict_property(formula_for_pred, "formation_energy")
        _density, _ = predict_property(formula_for_pred, "density")

        return {
            "formula": formula,
            "elements": elements,
            "n_elements": len(elements),
            "has_oxygen": "O" in elements,
            "has_transition_metal": has_tm,
            "avg_atomic_radius": round(avg_radius, 3),
            "avg_electronegativity": round(avg_en, 3),
            "avg_atomic_mass": round(avg_mass, 3),
            "avg_valence_electrons": round(avg_valence, 3),
            "electronegativity_range": round(en_diff, 3),
            "radius_range": round(radius_diff, 3),
            "total_atoms": round(total),
            "predicted_band_gap": _band_gap,
            "predicted_formation_energy": _formation_energy,
            "predicted_density": _density,
        }

    def compute_descriptors(self, composition: dict) -> dict:
        return self.get_descriptors("", composition)
