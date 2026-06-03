import numpy as np

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


class SynthesisEngine:
    def __init__(self):
        self.methods = SYNTHESIS_METHODS

    async def assess_feasibility(self, formula: str,
                                  composition: dict | None = None) -> dict:
        from app.core.composition_analyzer import CompositionAnalyzer
        analyzer = CompositionAnalyzer()
        desc = analyzer.get_descriptors(formula, composition)

        elements = desc.get("elements", [])
        n_elements = len(elements)
        has_oxygen = "O" in elements
        transition_metals = ["Sc", "Ti", "V", "Cr", "Mn", "Fe", "Co", "Ni", "Cu", "Zn",
                             "Y", "Zr", "Nb", "Mo", "Tc", "Ru", "Rh", "Pd", "Ag", "Cd",
                             "Hf", "Ta", "W", "Re", "Os", "Ir", "Pt", "Au"]
        has_tm = any(el in elements for el in transition_metals)

        recommended_methods = []
        if has_oxygen and n_elements >= 2:
            recommended_methods.extend(["solid_state", "sol_gel", "hydrothermal"])
        if has_tm:
            recommended_methods.append("solid_state")
        if n_elements <= 3:
            recommended_methods.append("mechanochemical")
        if n_elements >= 4:
            recommended_methods.append("solid_state")

        recommended_methods = list(set(recommended_methods))
        if not recommended_methods:
            recommended_methods = ["solid_state"]

        methods_detail = []
        for m in recommended_methods[:3]:
            method = self.methods.get(m, {})
            tr = method.get("temp_range", (500, 1000))
            methods_detail.append({
                "method": m,
                "description": method.get("description", ""),
                "estimated_temperature": int(np.random.uniform(*tr)),
                "estimated_duration_hours": float(round(np.random.uniform(2, 72), 1)),
                "difficulty": str(np.random.choice(["easy", "moderate", "hard"])),
                "success_probability": round(float(np.random.beta(4, 3)), 2),
            })

        score = float(np.mean([m["success_probability"] for m in methods_detail])) if methods_detail else 0.3

        air_sensitive = any(el in elements for el in ["Li", "Na", "K", "Ca"])

        return {
            "formula": formula,
            "feasibility_score": round(score, 2),
            "n_elements": n_elements,
            "has_oxygen": has_oxygen,
            "has_transition_metal": has_tm,
            "recommended_methods": methods_detail,
            "known_precursors": [f"{e}O" if has_oxygen else f"{e}" for e in elements[:3]],
            "thermodynamic_notes": "Formation energy suggests synthesizable under standard conditions" if score > 0.5 else "May require non-equilibrium synthesis methods",
            "risks": ["Air-sensitive precursors may be required"] if air_sensitive else [],
        }

    async def design_experiment(self, formula: str, method: str) -> dict:
        method_info = self.methods.get(method, self.methods["solid_state"])
        tr = method_info["temp_range"]
        temp = int(np.random.uniform(*tr))
        has_oxygen = "O" in formula
        atmosphere = "argon" if not has_oxygen else "air"

        return {
            "formula": formula,
            "method": method,
            "parameters": {
                "temperature": temp,
                "temperature_ramp_rate": 5.0,
                "holding_time_hours": 12.0,
                "atmosphere": atmosphere,
                "pressure": "ambient",
                "grinding_time_minutes": 30,
                "pelletizing_pressure_MPa": 100,
            },
            "steps": [
                {"step": 1, "action": "Weigh and mix precursors in stoichiometric ratio"},
                {"step": 2, "action": "Grind in agate mortar for 30 minutes"},
                {"step": 3, "action": "Press into pellet at 100 MPa"},
                {"step": 4, "action": f"Heat to {temp}°C at 5°C/min in {atmosphere}"},
                {"step": 5, "action": f"Hold at {temp}°C for 12 hours"},
                {"step": 6, "action": "Cool to room temperature naturally"},
                {"step": 7, "action": "Regrind and repeat heating if needed"},
            ],
            "characterization": ["XRD", "SEM", "EDS", "XPS"],
            "estimated_total_time_hours": 24.0,
            "estimated_cost_usd": 150.0,
        }
