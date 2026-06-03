import random
import numpy as np
from typing import Optional

PROTOTYPE_STRUCTURES = [
    {"sg": "Fm-3m", "system": "cubic", "a": 4.0, "example": "NaCl"},
    {"sg": "Pm-3m", "system": "cubic", "a": 3.8, "example": "CsCl"},
    {"sg": "Fd-3m", "system": "cubic", "a": 8.0, "example": "MgAl2O4"},
    {"sg": "R-3m", "system": "trigonal", "a": 2.8, "c": 14.0, "example": "LiCoO2"},
    {"sg": "P6_3/mmc", "system": "hexagonal", "a": 3.2, "c": 5.2, "example": "Graphite"},
    {"sg": "I4/mmm", "system": "tetragonal", "a": 3.9, "c": 4.1, "example": "TiO2"},
    {"sg": "P2_1/c", "system": "monoclinic", "a": 4.8, "b": 8.5, "c": 5.5, "beta": 106.0, "example": "Zeolite"},
    {"sg": "Pnma", "system": "orthorhombic", "a": 6.0, "b": 7.5, "c": 5.5, "example": "Perovskite"},
    {"sg": "C2/c", "system": "monoclinic", "a": 7.0, "b": 5.0, "c": 7.0, "beta": 115.0, "example": "Spodumene"},
    {"sg": "Pbca", "system": "orthorhombic", "a": 8.0, "b": 6.0, "c": 7.0, "example": "Olivine"},
]


def _assign_elements(n_elements: int, constraints: Optional[list[str]] = None) -> tuple[list[str], list[int], str]:
    pool = constraints or ["Li", "Na", "K", "Mg", "Ca", "Fe", "Co", "Ni", "Mn", "Ti",
                           "Zr", "Zn", "Al", "Si", "O", "S", "F", "Cl", "C", "N"]
    if len(pool) < n_elements:
        n_elements = len(pool)

    selected = random.sample(pool, n_elements)
    oxide = "O" in selected

    if oxide and n_elements == 2:
        other = [e for e in selected if e != "O"][0]
        if other in ["Li", "Na", "K"]:
            stoich = [2, 1] if random.random() > 0.5 else [1, 1]
        elif other in ["Mg", "Ca", "Zn"]:
            stoich = [1, 1]
        elif other in ["Fe", "Co", "Ni", "Mn"]:
            stoich = [1, 1]
        else:
            stoich = [1, 2] if random.random() > 0.5 else [1, 1]
        formula_parts = []
        for i, el in enumerate(selected):
            if i == 0 and stoich[i] > 1:
                formula_parts.append(f"{el}{stoich[i]}")
            elif i == 0:
                formula_parts.append(el)
            else:
                formula_parts.append(f"{el}{stoich[i]}" if stoich[i] > 1 else el)
    elif n_elements >= 3:
        stoich = [random.randint(1, 4) for _ in range(n_elements)]
        formula_parts = [f"{el}{s}" if s > 1 else el for el, s in zip(selected, stoich)]
    else:
        stoich = [1 for _ in range(n_elements)]
        formula_parts = list(selected)

    formula = "".join(formula_parts)
    return selected, stoich, formula


class MaterialsGenerator:
    def __init__(self):
        self.models = {}

    async def generate_crystal(self, target_properties: Optional[dict] = None,
                                element_constraints: Optional[list] = None,
                                num_candidates: int = 10) -> list[dict]:
        candidates = []
        for i in range(num_candidates):
            n_elements = random.choices([2, 3, 4, 5], weights=[4, 3, 2, 1])[0]
            elements, stoich, formula = _assign_elements(n_elements, element_constraints)
            proto = random.choice(PROTOTYPE_STRUCTURES)
            sg = proto["sg"]
            sys = proto["system"]

            a = round(proto.get("a", 5.0) * random.uniform(0.8, 1.4), 3)
            b = round(proto.get("b", proto.get("a", 5.0)) * random.uniform(0.8, 1.4), 3)
            c = round(proto.get("c", proto.get("a", 5.0)) * random.uniform(0.8, 1.4), 3)

            lattice = {"a": a, "b": b, "c": c}
            if "beta" in proto:
                lattice["beta"] = proto["beta"]

            from app.core.trainer import predict_property
            gap, _ = predict_property(formula, "band_gap")
            eform, _ = predict_property(formula, "formation_energy")

            gen_score = round(float(1.0 - abs(eform) / 3.0 * 0.5 + (1.0 - gap / 8.0) * 0.3 + random.uniform(0, 0.2)), 3)
            gen_score = max(0.1, min(0.99, gen_score))
            syn_score = round(float(0.3 + 0.4 * (1.0 - n_elements / 5.0) + random.uniform(0, 0.3)), 3)
            syn_score = max(0.1, min(0.99, syn_score))

            candidates.append({
                "id": f"gen_{i}_{abs(hash(formula)) % 10000:04d}",
                "formula": formula,
                "space_group": sg,
                "crystal_system": sys,
                "lattice_parameters": lattice,
                "num_atoms": sum(stoich),
                "elements": elements,
                "stoichiometry": stoich,
                "generation_score": gen_score,
                "synthesis_score": syn_score,
                "predicted_band_gap": gap,
                "predicted_formation_energy": eform,
            })

        candidates.sort(key=lambda x: x["generation_score"], reverse=True)
        return candidates

    async def generate_composition(self, target_properties: Optional[dict] = None,
                                    num_candidates: int = 5) -> list[dict]:
        return await self.generate_crystal(target_properties, num_candidates=num_candidates)
