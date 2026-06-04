import math
from app.core.composition_analyzer import CompositionAnalyzer

SYNTHESIS_METHODS = {
    "solid_state": {
        "description": "High-temperature solid-state reaction",
        "temp_range": (600, 1500),
        "suitable_for": ["oxides", "sulfides", "intermetallics"],
    },
    "sol_gel": {
        "description": "Solution-based synthesis via sol-gel process",
        "temp_range": (300, 1000),
        "suitable_for": ["oxides", "nanomaterials", "thin_films"],
    },
    "hydrothermal": {
        "description": "Aqueous synthesis at elevated temperature and pressure",
        "temp_range": (100, 500),
        "suitable_for": ["zeolites", "oxides", "hydroxides"],
    },
    "cvd": {
        "description": "Chemical vapor deposition",
        "temp_range": (400, 1200),
        "suitable_for": ["thin_films", "2d_materials", "coatings"],
    },
    "mechanochemical": {
        "description": "Ball milling / mechanical alloying",
        "temp_range": (25, 200),
        "suitable_for": ["alloys", "metastable_phases", "nanocrystalline"],
    },
}


def _compute_feasibility_score(desc: dict) -> tuple[float, dict]:
    elements = desc.get("elements", [])
    n_elements = desc["n_elements"]
    has_o = desc.get("has_oxygen", False)
    has_tm = desc.get("has_transition_metal", False)
    avg_en = desc.get("avg_electronegativity", 1.5)
    en_range = desc.get("electronegativity_range", 0)
    eform = abs(desc.get("predicted_formation_energy", 0))

    score = 0.5
    reasons = []

    if n_elements <= 2:
        score += 0.2
        reasons.append("simple composition")
    elif n_elements >= 5:
        score -= 0.2
        reasons.append("complex composition")

    if has_o:
        score += 0.1
        reasons.append("oxide chemistry well-studied")

    if has_tm and has_o:
        score += 0.1
        reasons.append("transition metal oxide — extensive literature")

    if en_range > 1.5:
        score += 0.05
        reasons.append("ionic bonding favorable")
    elif en_range < 0.3 and n_elements > 2:
        score -= 0.05
        reasons.append("low electronegativity difference")

    if eform > 3.0:
        score -= 0.15
        reasons.append("high predicted formation energy")
    elif eform < 1.0:
        score += 0.1
        reasons.append("low predicted formation energy")

    air_sensitive = any(el in elements for el in ["Li", "Na", "K", "Ca"])
    if air_sensitive:
        score -= 0.05
        reasons.append("air-sensitive precursors")

    toxic = any(el in elements for el in ["Be", "As", "Cd", "Hg", "Pb"])
    if toxic:
        score -= 0.05
        reasons.append("toxic elements require special handling")

    score = max(0.05, min(0.98, score))
    return round(score, 2), {
        "score": score,
        "n_elements_factor": 0.2 if n_elements <= 2 else (-0.2 if n_elements >= 5 else 0),
        "oxide_factor": 0.1 if has_o else 0,
        "tm_oxide_factor": 0.1 if (has_tm and has_o) else 0,
        "en_factor": 0.05 if en_range > 1.5 else (-0.05 if en_range < 0.3 and n_elements > 2 else 0),
        "eform_factor": -0.15 if eform > 3.0 else (0.1 if eform < 1.0 else 0),
    }


class SynthesisEngine:
    def __init__(self):
        self.methods = SYNTHESIS_METHODS
        self.analyzer = CompositionAnalyzer()

    async def assess_feasibility(self, formula: str,
                                  composition: dict | None = None) -> dict:
        desc = self.analyzer.get_descriptors(formula, composition)
        elements = desc.get("elements", [])
        n_elements = desc["n_elements"]
        has_o = desc.get("has_oxygen", False)
        has_tm = desc.get("has_transition_metal", False)
        eform = desc.get("predicted_formation_energy", 0)

        score, breakdown = _compute_feasibility_score(desc)

        recommended = []
        if has_o and n_elements >= 2:
            recommended.append("solid_state")
            if n_elements <= 4:
                recommended.append("sol_gel")
            if n_elements <= 3:
                recommended.append("hydrothermal")
        if has_tm:
            if "solid_state" not in recommended:
                recommended.append("solid_state")
        if n_elements <= 3:
            recommended.append("mechanochemical")
        if n_elements >= 4 and "solid_state" not in recommended:
            recommended.append("solid_state")
        if not recommended:
            recommended = ["solid_state"]

        recommended = list(dict.fromkeys(recommended))[:3]

        from app.core.trainer import predict_property
        gap, _ = predict_property(formula, "band_gap", "")

        methods_detail = []
        for m in recommended:
            method = self.methods.get(m, {})
            tr = method.get("temp_range", (500, 1000))
            temp = tr[0] + int((tr[1] - tr[0]) * (1.0 - score))
            temp = max(tr[0], min(tr[1], temp))

            duration = 48.0 if m == "solid_state" else (24.0 if m == "sol_gel" else (12.0 if m == "hydrothermal" else (6.0 if m == "cvd" else 4.0)))
            difficulty = "easy" if score > 0.7 else ("moderate" if score > 0.4 else "hard")
            success_prob = round(score * (0.9 if n_elements <= 3 else (0.8 if n_elements <= 4 else 0.6)), 2)

            methods_detail.append({
                "method": m,
                "description": method.get("description", ""),
                "estimated_temperature": temp,
                "estimated_duration_hours": duration,
                "difficulty": difficulty,
                "success_probability": max(0.1, min(0.99, success_prob)),
            })

        precursors = []
        for el in elements[:4]:
            if has_o and el != "O":
                precursors.append(f"{el}O")
            elif el != "O":
                precursors.append(el)
            if len(precursors) >= 3:
                break

        thermo_notes = (
            f"Formation energy: {eform:.2f} eV/atom. "
            f"{'Thermodynamically stable under standard conditions.' if eform < 0 else 'May require careful synthesis conditions to stabilize.'}"
        )

        risks = []
        if any(el in elements for el in ["Li", "Na", "K", "Ca"]):
            risks.append("Air-sensitive precursors may require glovebox handling")
        if any(el in elements for el in ["Be", "As", "Cd", "Hg", "Pb"]):
            risks.append("Toxic elements require special handling and disposal")
        if n_elements >= 4:
            risks.append("Multi-element system may form competing phases")
        if eform > 0:
            risks.append("Positive formation energy — metastable phase possible")
        if gap > 3.0:
            risks.append("Wide band gap — may require high processing temperatures")

        return {
            "formula": formula,
            "feasibility_score": score,
            "n_elements": n_elements,
            "has_oxygen": has_o,
            "has_transition_metal": has_tm,
            "recommended_methods": methods_detail,
            "known_precursors": precursors,
            "thermodynamic_notes": thermo_notes,
            "risks": risks,
        }

    async def design_experiment(self, formula: str, method: str) -> dict:
        method_info = self.methods.get(method, self.methods["solid_state"])
        tr = method_info["temp_range"]

        desc = self.analyzer.get_descriptors(formula)
        score, _ = _compute_feasibility_score(desc)
        temp = tr[0] + int((tr[1] - tr[0]) * (1.0 - score))
        temp = max(tr[0], min(tr[1], temp))

        has_oxygen = "O" in desc.get("elements", [])
        has_tm = desc.get("has_transition_metal", False)
        atmosphere = "argon" if any(el in desc.get("elements", []) for el in ["Li","Na","K","Ca"]) else ("air" if has_oxygen else "argon")
        holding_time = 24.0 if method == "solid_state" else (12.0 if method == "sol_gel" else 6.0)
        ramp_rate = 5.0 if has_oxygen else 10.0

        return {
            "formula": formula,
            "method": method,
            "parameters": {
                "temperature": temp,
                "temperature_ramp_rate": ramp_rate,
                "holding_time_hours": holding_time,
                "atmosphere": atmosphere,
                "pressure": "ambient",
                "grinding_time_minutes": 30,
                "pelletizing_pressure_MPa": 100,
            },
            "steps": [
                {"step": 1, "action": f"Weigh and mix precursors in stoichiometric ratio for {formula}"},
                {"step": 2, "action": "Grind in agate mortar for 30 minutes"},
                {"step": 3, "action": "Press into pellet at 100 MPa"},
                {"step": 4, "action": f"Heat to {temp}°C at {ramp_rate}°C/min in {atmosphere}"},
                {"step": 5, "action": f"Hold at {temp}°C for {holding_time} hours"},
                {"step": 6, "action": "Cool to room temperature naturally"},
                {"step": 7, "action": "Characterize by XRD, SEM, and EDS"},
            ],
            "characterization": ["XRD", "SEM", "EDS"] + (["XPS", "TGA"] if has_oxygen else []),
            "estimated_total_time_hours": holding_time + 6,
            "estimated_cost_usd": round(50 + holding_time * 2.5 + (50 if has_tm else 0), 2),
        }
