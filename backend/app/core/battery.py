BATTERY_APPLICATIONS = {
    "cathode": {
        "description": "Positive electrode materials",
        "key_properties": ["high_voltage", "high_capacity", "rate_capability", "thermal_stability"],
        "target_band_gap": (0.5, 3.0),
        "target_formation_energy": (-4.0, -1.0),
        "known_families": ["layered_oxide", "spinel", "olivine", "polyanion"],
    },
    "anode": {
        "description": "Negative electrode materials",
        "key_properties": ["low_voltage", "high_capacity", "cycle_life", "low_expansion"],
        "target_band_gap": (0.0, 1.5),
        "target_formation_energy": (-3.0, -0.5),
        "known_families": ["graphite", "silicon", "lithium_titanate", "conversion"],
    },
    "solid_electrolyte": {
        "description": "Solid-state electrolyte materials",
        "key_properties": ["high_ionic_conductivity", "wide_band_gap", "electrochemical_stability"],
        "target_band_gap": (4.0, 8.0),
        "target_formation_energy": (-3.0, -0.5),
        "known_families": ["garnet", "perovskite", "NASICON", "sulfide"],
    },
}

BATTERY_ELEMENT_POOLS = {
    "cathode": ["Li", "Na", "Co", "Ni", "Mn", "Fe", "O", "P", "F"],
    "anode": ["Si", "Sn", "C", "Ti", "Li", "O"],
    "solid_electrolyte": ["Li", "Na", "La", "Zr", "Ta", "Ti", "P", "S", "O", "Cl", "Br"],
}


def assess_battery_suitability(formula: str, band_gap: float,
                                formation_energy: float,
                                composition: dict) -> dict:
    elements = list(composition.keys())
    results = {}

    for app, info in BATTERY_APPLICATIONS.items():
        bg_min, bg_max = info["target_band_gap"]
        fe_min, fe_max = info["target_formation_energy"]

        bg_score = max(0, 1 - abs(band_gap - (bg_min + bg_max) / 2) / ((bg_max - bg_min) / 2))
        bg_score = min(1, bg_score)

        fe_score = max(0, 1 - abs(formation_energy - (fe_min + fe_max) / 2) / ((fe_max - fe_min) / 2))
        fe_score = min(1, fe_score)

        pool = BATTERY_ELEMENT_POOLS.get(app, [])
        element_overlap = sum(1 for e in elements if e in pool) / max(len(elements), 1)
        elem_score = element_overlap

        overall = round(0.4 * bg_score + 0.3 * fe_score + 0.3 * elem_score, 3)

        if overall > 0.4:
            results[app] = {
                "score": overall,
                "band_gap_fit": round(bg_score, 2),
                "energy_fit": round(fe_score, 2),
                "element_fit": round(elem_score, 2),
                "assessment": "Excellent candidate" if overall > 0.7 else ("Promising" if overall > 0.5 else "Possible"),
            }

    return results
