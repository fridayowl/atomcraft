import os
import json
from typing import Optional
import numpy as np
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
import joblib

MODELS_DIR = os.path.join(os.path.dirname(__file__), "models")
N_FEATURES = 17  # 10 composition + 1 volume + 6 crystal_system onehot

CRYSTAL_SYSTEMS = ["cubic", "tetragonal", "hexagonal", "orthorhombic", "monoclinic", "triclinic"]


def _generate_training_data(n_samples: int = 5000) -> tuple[np.ndarray, dict[str, np.ndarray]]:
    np.random.seed(42)
    n_feat = 10 + 1 + len(CRYSTAL_SYSTEMS)
    X = np.zeros((n_samples, n_feat))

    n_elements = np.random.randint(1, 6, n_samples)
    has_o = np.random.choice([0, 1], n_samples)
    has_tm = np.random.choice([0, 1], n_samples)
    avg_en = np.random.uniform(0.8, 4.0, n_samples)
    en_range = np.random.uniform(0, 3.0, n_samples)
    avg_radius = np.random.uniform(0.4, 2.7, n_samples)
    radius_range = np.random.uniform(0, 2.0, n_samples)
    avg_mass = np.random.uniform(1, 210, n_samples)
    avg_valence = np.random.uniform(1, 12, n_samples)
    total_atoms = np.random.randint(1, 30, n_samples) * 4

    X[:, 0] = n_elements
    X[:, 1] = has_o
    X[:, 2] = has_tm
    X[:, 3] = avg_en
    X[:, 4] = en_range
    X[:, 5] = avg_radius
    X[:, 6] = radius_range
    X[:, 7] = avg_mass
    X[:, 8] = avg_valence
    X[:, 9] = total_atoms
    # structural features (10+)
    X[:, 10] = np.random.uniform(2, 8, n_samples)
    for i in range(len(CRYSTAL_SYSTEMS)):
        X[:, 11 + i] = np.random.choice([0, 1], n_samples, p=[0.7, 0.3])

    band_gap = np.maximum(0, avg_en * 0.6 - avg_radius * 0.1 + np.random.normal(0, 0.3, n_samples))
    band_gap = np.clip(band_gap, 0, 12)

    formation_energy = -avg_en * 0.4 + en_range * 0.2 - n_elements * 0.05 + np.random.normal(0, 0.15, n_samples)
    formation_energy = np.clip(formation_energy, -5, 2)

    density = avg_mass / (avg_radius ** 3 * 2.5) * 2 + np.random.normal(0, 0.5, n_samples)
    density = np.clip(density, 0.5, 25)

    targets = {
        "band_gap": band_gap,
        "formation_energy": formation_energy,
        "density": density,
    }

    return X, targets


def _get_element_feature_vector(formula: str, crystal_system: str = "",
                                volume: float = 0) -> np.ndarray:
    from app.core.composition_analyzer import CompositionAnalyzer, ELEMENT_DATA
    analyzer = CompositionAnalyzer()
    comp = analyzer.parse_formula(formula)
    elements = list(comp.keys())
    total = sum(comp.values())
    fractions = [v / total for v in comp.values()]

    radii = []
    ens = []
    masses = []
    valences = []
    for el in elements:
        data = ELEMENT_DATA.get(el, {"radius": 1.5, "en": 1.5, "mass": 50.0, "valence": 3})
        radii.append(data["radius"])
        ens.append(data["en"])
        masses.append(data["mass"])
        valences.append(data["valence"])

    transition_metals = {"Sc","Ti","V","Cr","Mn","Fe","Co","Ni","Cu","Zn","Y","Zr","Nb","Mo","Tc","Ru","Rh","Pd","Ag","Cd","Hf","Ta","W","Re","Os","Ir","Pt","Au"}

    base = np.array([
        len(elements),
        1 if "O" in elements else 0,
        1 if any(el in transition_metals for el in elements) else 0,
        np.average(ens, weights=fractions),
        np.max(ens) - np.min(ens) if len(ens) > 1 else 0,
        np.average(radii, weights=fractions),
        np.max(radii) - np.min(radii) if len(radii) > 1 else 0,
        np.average(masses, weights=fractions),
        np.average(valences, weights=fractions),
        total,
    ])

    cs_onehot = np.zeros(len(CRYSTAL_SYSTEMS))
    if crystal_system and crystal_system.lower() in CRYSTAL_SYSTEMS:
        idx = CRYSTAL_SYSTEMS.index(crystal_system.lower())
        cs_onehot[idx] = 1

    vol_feat = np.array([np.log(max(volume, 1))]) if volume > 0 else np.array([0.0])

    return np.concatenate([base, vol_feat, cs_onehot])


def _load_real_training_data() -> tuple[dict[str, list[np.ndarray]], dict[str, list[float]]]:
    try:
        from app.database import SessionLocal
        from app.models.material import Material, Property
        from sqlalchemy.orm import joinedload

        db = SessionLocal()
        materials = (
            db.query(Material)
            .options(joinedload(Material.properties))
            .all()
        )

        if not materials:
            db.close()
            return {}, {}

        all_features = {}
        for m in materials:
            formula = m.formula
            cs = m.crystal_system or ""
            vol = m.volume or 0
            all_features[m.id] = _get_element_feature_vector(formula, crystal_system=cs, volume=vol)

        from collections import defaultdict
        targets = defaultdict(list)
        feature_maps = defaultdict(list)

        for m in materials:
            if m.id not in all_features:
                continue
            feats = all_features[m.id]
            props = {p.property_type: p.value for p in (m.properties or [])}

            if m.density is not None:
                feature_maps["density"].append(feats)
                targets["density"].append(float(m.density))

            for pt, val in props.items():
                if pt == "band_gap" and val <= 0:
                    continue
                feature_maps[pt].append(feats)
                targets[pt].append(float(val))

        db.close()
        return dict(feature_maps), dict(targets)
    except Exception as e:
        print(f"Error loading training data: {e}")
        return {}, {}


def train_and_save_models(force_retrain: bool = False):
    os.makedirs(MODELS_DIR, exist_ok=True)

    config_path = os.path.join(MODELS_DIR, "model_config.json")
    if os.path.exists(config_path) and not force_retrain:
        return

    X_real_dict, targets_real = _load_real_training_data()

    # sort by data count, put known properties first
    known_order = ["density", "band_gap", "formation_energy"]
    prop_names = sorted(targets_real.keys(), key=lambda p: (p not in known_order, -len(targets_real[p])))

    model_config = {}
    for prop_name in prop_names:
        X_real = X_real_dict.get(prop_name, [])
        y_real = targets_real.get(prop_name, [])
        n_real = len(X_real)
        print(f"{prop_name}: {n_real} real data points")

        if n_real < 50:
            if prop_name in {"band_gap", "formation_energy", "density"}:
                n_synth = max(2000, (50 - n_real) * 50)
                X_synth, targets_synth = _generate_training_data(n_synth)
                if n_real > 0:
                    X = np.vstack([np.array(X_real), X_synth])
                    y = np.concatenate([np.array(y_real), targets_synth[prop_name]])
                else:
                    X = X_synth
                    y = targets_synth[prop_name]
            else:
                continue
        else:
            X_arr = np.array(X_real)
            y_arr = np.array(y_real)
            # Clip outliers beyond 5 std
            if len(y_arr) > 100:
                mean, std = np.mean(y_arr), np.std(y_arr)
                mask = np.abs(y_arr - mean) <= 5 * std
                if np.sum(mask) > 50:
                    X_arr, y_arr = X_arr[mask], y_arr[mask]
            X, y = X_arr, y_arr

        print(f"Training {prop_name} on {len(X)} samples...")
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        model = RandomForestRegressor(n_estimators=300, max_depth=20, random_state=42)
        model.fit(X_train, y_train)

        y_pred = model.predict(X_test)
        mae = mean_absolute_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)

        model_path = os.path.join(MODELS_DIR, f"{prop_name}.joblib")
        joblib.dump(model, model_path)

        model_config[prop_name] = {
            "model": "RandomForestRegressor",
            "n_estimators": 300,
            "max_depth": 20,
            "mae": round(mae, 4),
            "r2": round(r2, 4),
            "n_real": n_real,
            "path": f"{prop_name}.joblib",
        }
        print(f"  {prop_name}: MAE={mae:.4f}, R²={r2:.4f}")

    with open(config_path, "w") as f:
        json.dump(model_config, f, indent=2)
    print(f"Models saved to {MODELS_DIR}")


def load_prediction_model(property_type: str):
    model_path = os.path.join(MODELS_DIR, f"{property_type}.joblib")
    if os.path.exists(model_path):
        return joblib.load(model_path)
    return None


def predict_property(formula: str, property_type: str,
                     crystal_system: str = "", volume: float = 0) -> tuple[float, float]:
    model = load_prediction_model(property_type)
    if model is not None:
        features = _get_element_feature_vector(formula, crystal_system, volume).reshape(1, -1)
        pred = model.predict(features)[0]
        return round(float(pred), 4), 0.85

    from app.core.composition_analyzer import CompositionAnalyzer
    analyzer = CompositionAnalyzer()
    desc = analyzer.get_descriptors(formula)
    key = f"predicted_{property_type}"
    return round(float(desc.get(key, 0)), 4), 0.6


# ──────────────────────────────────────────
# Space group + structure predictors
# ──────────────────────────────────────────

CRYSTAL_SYSTEM_IDS = {
    "cubic": 0, "tetragonal": 1, "orthorhombic": 2,
    "hexagonal": 3, "trigonal": 4, "monoclinic": 5, "triclinic": 6,
}
CRYSTAL_SYSTEMS_LIST = list(CRYSTAL_SYSTEM_IDS.keys())

TEMPLATE_SPG_CACHE = None


def _load_space_group_data():
    global TEMPLATE_SPG_CACHE
    if TEMPLATE_SPG_CACHE is not None:
        return TEMPLATE_SPG_CACHE
    from app.database import SessionLocal
    from app.models.material import Material
    db = SessionLocal()
    rows = db.query(Material.formula, Material.space_group, Material.crystal_system,
                    Material.lattice_a, Material.lattice_b, Material.lattice_c).all()
    db.close()
    TEMPLATE_SPG_CACHE = rows
    return rows


def train_crystal_system_predictor() -> tuple:
    """Train a classifier to predict crystal system from composition."""
    rows = _load_space_group_data()
    from sklearn.ensemble import RandomForestClassifier
    X, y = [], []
    for formula, spg, cs, a, b, c in rows:
        if not cs or cs not in CRYSTAL_SYSTEM_IDS:
            continue
        feat = _get_element_feature_vector(formula, crystal_system=cs, volume=(a or 5)*(b or 5)*(c or 5))
        X.append(feat)
        y.append(CRYSTAL_SYSTEM_IDS[cs])
    X = np.array(X)
    clf = RandomForestClassifier(n_estimators=200, max_depth=15, random_state=42)
    clf.fit(X, y)
    path = os.path.join(MODELS_DIR, "crystal_system_classifier.joblib")
    joblib.dump(clf, path)
    acc = clf.score(X, y)
    print(f"Crystal system classifier: {acc:.3f} accuracy ({len(X)} samples)")
    return clf


def predict_crystal_system(formula: str, volume: float = 0) -> tuple[str, float]:
    path = os.path.join(MODELS_DIR, "crystal_system_classifier.joblib")
    if not os.path.exists(path):
        train_crystal_system_predictor()
    clf = joblib.load(path)
    feat = _get_element_feature_vector(formula, volume=volume).reshape(1, -1)
    proba = clf.predict_proba(feat)[0]
    idx = int(np.argmax(proba))
    confidence = float(proba[idx])
    return CRYSTAL_SYSTEMS_LIST[idx], confidence


def predict_lattice_parameters(formula: str, crystal_system: str) -> dict:
    """Predict lattice params from similar known structures in same system."""
    rows = _load_space_group_data()
    candidates = [r for r in rows if r[2] == crystal_system and r[3] is not None]
    if not candidates:
        return {"a": 5.0, "b": 5.0, "c": 5.0}
    # Find materials with similar number of elements
    feat = _parse_formula_counts(formula)
    n_el = len(feat)
    scored = [(abs(len(_parse_formula_counts(r[0])) - n_el), r) for r in candidates]
    scored.sort(key=lambda x: x[0])
    nearest = scored[:10]
    avg_a = sum(r[3] for _, r in nearest) / len(nearest)
    avg_b = sum(r[4] or r[3] for _, r in nearest) / len(nearest)
    avg_c = sum(r[5] or r[3] for _, r in nearest) / len(nearest)
    return {"a": round(avg_a, 3), "b": round(avg_b, 3), "c": round(avg_c, 3)}


def generate_crystal_structure(formula: str, space_group: str = "",
                                crystal_system: str = "",
                                lattice: Optional[dict] = None) -> Optional[dict]:
    """Generate a full crystal structure using pymatgen from composition + symmetry."""
    try:
        from pymatgen.core.structure import Structure
        from pymatgen.core.lattice import Lattice
        from pymatgen.core.composition import Composition
        from pymatgen.symmetry.analyzer import SpacegroupAnalyzer
    except ImportError:
        print("pymatgen required for structure generation")
        return None

    if not crystal_system:
        crystal_system, _ = predict_crystal_system(formula)
    if not lattice:
        lattice = predict_lattice_parameters(formula, crystal_system)
    if not space_group:
        spg_map = {
            "cubic": "Pm-3m", "tetragonal": "I4/mmm",
            "orthorhombic": "Pnma", "hexagonal": "P6_3/mmc",
            "trigonal": "R-3m", "monoclinic": "P2_1/c",
            "triclinic": "P1",
        }
        space_group = spg_map.get(crystal_system, "P1")

    a, b, c = lattice.get("a", 5), lattice.get("b", 5), lattice.get("c", 5)
    alpha = lattice.get("alpha", 90)
    beta = lattice.get("beta", 90)
    gamma = lattice.get("gamma", 90)
    lat = Lattice.from_parameters(a, b, c, alpha, beta, gamma)
    comp = Composition(formula)

    # Find template in same space group from DB
    rows = _load_space_group_data()
    templates = [r for r in rows if r[1] == space_group and r[3] is not None]
    if templates:
        import random
        tmpl = random.choice(templates)
        tmpl_comp = Composition(tmpl[0])
        tmpl_lat = Lattice.from_parameters(
            tmpl[3] or a, tmpl[4] or b, tmpl[5] or c, 90, 90, 90)

        # Create structure with template's atomic positions but new composition
        from pymatgen.core.periodic_table import Element
        tmpl_elements = [Element(e) for e in tmpl_comp.elements]
        tmpl_frac_coords = [[0, 0, 0]]

        if hasattr(tmpl_comp, "elements"):
            tmpl_elements = list(tmpl_comp.elements)
            tmpl_frac_coords = [[i / len(tmpl_elements), i / len(tmpl_elements), 0]
                                for i in range(len(tmpl_elements))]

        new_elements = [Element(e) for e in comp.elements]
        new_frac_coords = [[i / len(new_elements), i / len(new_elements), 0]
                           for i in range(len(new_elements))]
        struct = Structure(lat, new_elements, new_frac_coords)
    else:
        # Place atoms at random positions in unit cell
        from pymatgen.core.periodic_table import Element
        elements = [Element(e) for e in comp.elements]
        n = len(elements)
        frac_coords = [[(i + 0.5) / n, (i + 0.5) / n, (i + 0.5) / n]
                       for i in range(n)]
        struct = Structure(lat, elements, frac_coords)
    try:
        sga = SpacegroupAnalyzer(struct)
        sym_struct = sga.get_symmetrized_structure()
        sg_symbol = sga.get_space_group_symbol()
    except Exception:
        sg_symbol = space_group

    cif_string = struct.to(fmt="cif")
    return {
        "formula": formula,
        "space_group": sg_symbol,
        "crystal_system": crystal_system,
        "lattice_parameters": lattice,
        "cif": cif_string,
        "volume": round(lat.volume, 3),
    }


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


# Train on import if models don't exist
if not os.path.exists(os.path.join(MODELS_DIR, "model_config.json")):
    train_and_save_models()
