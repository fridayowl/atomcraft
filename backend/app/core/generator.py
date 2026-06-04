import random
import numpy as np
from typing import Optional

SUBSTITUTION_GROUPS = [
    {"Li", "Na", "K", "Rb", "Cs"},
    {"Be", "Mg", "Ca", "Sr", "Ba"},
    {"Sc", "Y", "La", "Ce", "Pr", "Nd", "Sm", "Eu", "Gd", "Tb", "Dy", "Ho", "Er", "Tm", "Yb", "Lu"},
    {"Ti", "Zr", "Hf"},
    {"V", "Nb", "Ta"},
    {"Cr", "Mo", "W"},
    {"Mn", "Tc", "Re"},
    {"Fe", "Ru", "Os"},
    {"Co", "Rh", "Ir"},
    {"Ni", "Pd", "Pt"},
    {"Cu", "Ag", "Au"},
    {"Zn", "Cd", "Hg"},
    {"B", "Al", "Ga", "In", "Tl"},
    {"C", "Si", "Ge", "Sn", "Pb"},
    {"N", "P", "As", "Sb", "Bi"},
    {"O", "S", "Se", "Te"},
    {"F", "Cl", "Br", "I"},
]

SUBSTITUTION_MAP = {}
for group in SUBSTITUTION_GROUPS:
    for el in group:
        SUBSTITUTION_MAP[el] = [e for e in group if e != el]


def _get_substitutes(element: str) -> list[str]:
    return SUBSTITUTION_MAP.get(element, [])


def _parse_formula_counts(formula: str) -> dict[str, int]:
    counts = {}
    i = 0
    while i < len(formula):
        el = formula[i]
        i += 1
        while i < len(formula) and formula[i].islower():
            el += formula[i]
            i += 1
        n = 0
        while i < len(formula) and formula[i].isdigit():
            n = n * 10 + int(formula[i])
            i += 1
        counts[el] = counts.get(el, 0) + (n if n else 1)
    return counts


def _formula_from_counts(counts: dict[str, int]) -> str:
    parts = []
    for el, n in counts.items():
        parts.append(f"{el}{n}" if n > 1 else el)
    return "".join(parts)


def _load_templates(element_constraints: Optional[list[str]] = None, max_templates: int = 500) -> list[dict]:
    from app.database import SessionLocal
    from app.models.material import Material
    from sqlalchemy import func

    db = SessionLocal()
    try:
        query = db.query(
            Material.formula, Material.space_group, Material.crystal_system,
            Material.lattice_a, Material.lattice_b, Material.lattice_c,
            Material.lattice_alpha, Material.lattice_beta, Material.lattice_gamma,
            Material.volume,
        )

        if element_constraints:
            filters = []
            for el in element_constraints:
                filters.append(Material.formula.contains(el))
            from sqlalchemy import or_
            query = query.filter(or_(*filters))

        templates = query.limit(max_templates).all()
        result = []
        for t in templates:
            formula_els = list(_parse_formula_counts(t.formula).keys())
            if len(formula_els) < 2:
                continue
            result.append({
                "formula": t.formula,
                "space_group": t.space_group,
                "crystal_system": t.crystal_system,
                "lattice_a": t.lattice_a,
                "lattice_b": t.lattice_b,
                "lattice_c": t.lattice_c,
                "lattice_alpha": t.lattice_alpha,
                "lattice_beta": t.lattice_beta,
                "lattice_gamma": t.lattice_gamma,
                "volume": t.volume,
                "elements": formula_els,
            })
        return result
    finally:
        db.close()


def _apply_substitution(template: dict, element_constraints: Optional[list[str]] = None
                        ) -> Optional[dict]:
    formula = template["formula"]
    counts = _parse_formula_counts(formula)
    elements = list(counts.keys())

    candidates = []
    for target_el in elements:
        subs = _get_substitutes(target_el)
        if not subs:
            continue
        for sub in random.sample(subs, min(2, len(subs))):
            if sub == target_el:
                continue

            new_counts = dict(counts)
            new_counts[sub] = new_counts.pop(target_el)
            new_formula = _formula_from_counts(new_counts)
            subst = f"{target_el}->{sub}"

            candidates.append({
                "formula": new_formula,
                "substitution": subst,
                "template_formula": formula,
            })

            if len(candidates) >= 3:
                break
        if len(candidates) >= 3:
            break

    return random.choice(candidates) if candidates else None


RANDOM_POOL = ["Li","Na","K","Mg","Ca","Fe","Co","Ni","Mn","Ti",
                "Zr","Zn","Al","Si","O","S","F","Cl","C","N",
                "V","Cr","Cu","Ga","Ge","Se","Br","Rb","Sr","Y",
                "Nb","Mo","Ru","Rh","Pd","Ag","Cd","In","Sn","Sb",
                "Te","I","Cs","Ba","La","Ce","Pr","Nd","Sm","Eu",
                "Gd","Tb","Dy","Ho","Er","Tm","Yb","Lu","Hf","Ta",
                "W","Re","Os","Ir","Pt","Au","Pb","Bi"]


def _random_composition_dict(n_elements: int) -> dict[str, int]:
    elements = random.sample(RANDOM_POOL, min(n_elements, len(RANDOM_POOL)))
    counts = {}
    for el in elements:
        counts[el] = random.randint(1, 4)
    return counts


def _formula_from_counts(counts: dict[str, int]) -> str:
    parts = []
    for el, n in counts.items():
        parts.append(f"{el}{n}" if n > 1 else el)
    return "".join(parts)


class MaterialsGenerator:
    def __init__(self):
        self.models = {}
        self._template_cache = None

    async def generate_crystal(self, target_properties: Optional[dict] = None,
                                element_constraints: Optional[list] = None,
                                num_candidates: int = 10) -> list[dict]:
        from app.core.trainer import predict_property

        templates = _load_templates(element_constraints, max_templates=min(num_candidates * 10, 1000))

        if not templates:
            return []

        candidates = []
        seen_formulas = set()
        attempts = 0
        max_attempts = num_candidates * 20

        while len(candidates) < num_candidates and attempts < max_attempts:
            attempts += 1
            template = random.choice(templates)
            result = _apply_substitution(template, element_constraints)
            if result is None:
                continue

            formula = result["formula"]
            if formula in seen_formulas:
                continue
            seen_formulas.add(formula)

            formula_els = list(_parse_formula_counts(formula).keys())
            if element_constraints:
                if not any(el in element_constraints for el in formula_els):
                    continue
                constraint_non_o = [e for e in element_constraints if e != "O"]
                if constraint_non_o and not any(el in constraint_non_o for el in formula_els):
                    continue

            sg = template["space_group"]
            sys = template["crystal_system"]
            a = template["lattice_a"] or 5.0
            b = template["lattice_b"] or a
            c = template["lattice_c"] or a
            alpha = template["lattice_alpha"] or 90
            beta = template["lattice_beta"] or 90
            gamma = template["lattice_gamma"] or 90
            vol = a * b * c

            lattice = {"a": a, "b": b, "c": c}
            if beta and beta != 90:
                lattice["beta"] = beta
            if alpha and alpha != 90:
                lattice["alpha"] = alpha
            if gamma and gamma != 90:
                lattice["gamma"] = gamma

            gap, _ = predict_property(formula, "band_gap", crystal_system=sys, volume=vol)
            eform, _ = predict_property(formula, "formation_energy", crystal_system=sys, volume=vol)

            if eform > 0:
                continue

            stability = round(float(max(0, min(1, 1.0 - abs(eform) / 5.0))), 3)

            target_score = 0.5
            if target_properties:
                target_gap = target_properties.get("band_gap")
                if target_gap is not None:
                    target_score = 1.0 - min(abs(gap - target_gap) / 5.0, 1.0)

            gen_score = round(float(stability * 0.6 + target_score * 0.4), 3)

            formula_els = list(_parse_formula_counts(formula).keys())
            candidates.append({
                "id": f"gen_{len(candidates)}_{abs(hash(formula)) % 10000:04d}",
                "formula": formula,
                "space_group": sg,
                "crystal_system": sys,
                "lattice_parameters": lattice,
                "elements": formula_els,
                "generation_score": gen_score,
                "synthesis_score": round(float(0.5 + 0.3 * (1.0 - len(formula_els) / 6.0)), 3),
                "predicted_band_gap": gap,
                "predicted_formation_energy": eform,
                "substitution": result["substitution"],
                "template": result["template_formula"],
                "stability_score": stability,
            })

        candidates.sort(key=lambda x: x["generation_score"], reverse=True)
        return candidates[:num_candidates]

    async def generate_denovo(self, target_properties: Optional[dict] = None,
                               element_constraints: Optional[list] = None,
                               num_candidates: int = 10) -> list[dict]:
        from app.core.trainer import (
            predict_property, predict_crystal_system, predict_lattice_parameters,
            generate_crystal_structure, _parse_formula_counts, train_crystal_system_predictor,
        )

        # Train crystal system predictor on first call
        try:
            train_crystal_system_predictor()
        except Exception:
            pass

        candidates = []
        seen_formulas = set()
        attempts = 0
        max_attempts = num_candidates * 30

        while len(candidates) < num_candidates and attempts < max_attempts:
            attempts += 1
            n_elements = random.choices([2, 3, 4, 5], weights=[3, 3, 2, 1])[0]
            pool = element_constraints or RANDOM_POOL
            if element_constraints:
                # Generate from user's elements
                selected = random.sample(pool, min(n_elements, len(pool)))
                if "O" not in selected and random.random() > 0.5:
                    selected.append("O")
            else:
                selected = random.sample(pool, min(n_elements, len(pool)))

            counts = {}
            for el in selected:
                counts[el] = random.randint(1, 4)
            formula = _formula_from_counts(counts)

            if formula in seen_formulas:
                continue
            seen_formulas.add(formula)

            formula_els = list(counts.keys())

            try:
                crystal_system, cs_conf = predict_crystal_system(formula)
                lattice = predict_lattice_parameters(formula, crystal_system)
            except Exception:
                crystal_system = random.choice(["cubic", "tetragonal", "orthorhombic", "monoclinic", "triclinic", "hexagonal", "trigonal"])
                lattice = {"a": 5.0, "b": 5.0, "c": 5.0}

            vol = lattice["a"] * lattice["b"] * lattice["c"]

            gap, _ = predict_property(formula, "band_gap", crystal_system=crystal_system, volume=vol)
            eform, _ = predict_property(formula, "formation_energy", crystal_system=crystal_system, volume=vol)

            if eform > 0:
                continue

            stability = round(float(max(0, min(1, 1.0 - abs(eform) / 5.0))), 3)

            # Generate crystal structure via pymatgen
            struct_info = None
            try:
                struct_info = generate_crystal_structure(
                    formula, crystal_system=crystal_system, lattice=lattice)
            except Exception:
                pass

            target_score = 0.5
            if target_properties:
                tg = target_properties.get("band_gap")
                if tg is not None:
                    target_score = 1.0 - min(abs(gap - tg) / 5.0, 1.0)

            gen_score = round(float(stability * 0.6 + target_score * 0.4), 3)

            cand = {
                "id": f"denovo_{len(candidates)}_{abs(hash(formula)) % 10000:04d}",
                "formula": formula,
                "space_group": (struct_info or {}).get("space_group", "P1"),
                "crystal_system": crystal_system,
                "lattice_parameters": lattice,
                "elements": formula_els,
                "generation_score": gen_score,
                "synthesis_score": round(float(0.5 + 0.3 * (1.0 - len(formula_els) / 6.0)), 3),
                "predicted_band_gap": gap,
                "predicted_formation_energy": eform,
                "stability_score": stability,
                "generation_method": "denovo",
                "cif": (struct_info or {}).get("cif", ""),
            }
            candidates.append(cand)

        candidates.sort(key=lambda x: x["generation_score"], reverse=True)
        return candidates[:num_candidates]

    async def generate_composition(self, target_properties: Optional[dict] = None,
                                    num_candidates: int = 5) -> list[dict]:
        return await self.generate_crystal(target_properties, num_candidates=num_candidates)
