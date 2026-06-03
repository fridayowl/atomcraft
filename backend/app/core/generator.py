import numpy as np
from typing import Optional


class MaterialsGenerator:
    def __init__(self):
        self.models = {}

    async def generate_crystal(self, target_properties: dict,
                                element_constraints: Optional[list] = None,
                                num_candidates: int = 10) -> list[dict]:
        candidates = []
        for i in range(num_candidates):
            n_elements = int(np.random.choice([2, 3, 4, 5]))
            elements = np.random.choice(
                element_constraints or ["Li", "Na", "K", "Mg", "Ca", "Fe", "Co", "Ni", "Mn", "Ti",
                                        "Zr", "O", "S", "F", "Cl"],
                size=n_elements, replace=False
            )
            stoichiometry = np.random.dirichlet(np.ones(n_elements)) * 10
            stoichiometry = np.round(stoichiometry / np.min(stoichiometry)).astype(int)

            formula_parts = []
            for el, amt in zip(elements, stoichiometry):
                if amt > 0:
                    formula_parts.append(f"{el}{'' if amt == 1 else amt}")
            formula = "".join(formula_parts)

            space_groups = ["Fm-3m", "Pm-3m", "R-3m", "P6_3/mmc", "I4/mmm",
                            "Fd-3m", "P2_1/c", "C2/c", "Pbca", "Pnma"]
            sg = str(np.random.choice(space_groups))
            a = float(np.random.uniform(3.5, 12.0))
            b = float(np.random.uniform(3.5, 12.0))
            c = float(np.random.uniform(3.5, 12.0))

            candidates.append({
                "id": f"gen_{i}_{hash(formula) % 10000:04d}",
                "formula": formula,
                "space_group": sg,
                "lattice_parameters": {"a": round(a, 3), "b": round(b, 3), "c": round(c, 3)},
                "num_atoms": int(np.sum(stoichiometry)),
                "elements": elements.tolist(),
                "stoichiometry": stoichiometry.tolist(),
                "generation_score": round(float(np.random.beta(2, 5)), 3),
                "synthesis_score": round(float(np.random.beta(3, 3)), 3),
            })

        candidates.sort(key=lambda x: x["generation_score"], reverse=True)
        return candidates

    async def generate_composition(self, target_properties: dict,
                                    num_candidates: int = 5) -> list[dict]:
        return await self.generate_crystal(target_properties, num_candidates=num_candidates)
