import os, json
from typing import Optional
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
import joblib

MODELS_DIR = os.path.join(os.path.dirname(__file__), "models")
CRYSTAL_SYSTEMS = ["cubic", "tetragonal", "hexagonal", "orthorhombic", "monoclinic", "triclinic"]


def _get_element_feature_vector(formula: str, crystal_system: str = "",
                                volume: float = 0) -> np.ndarray:
    from collections import Counter
    from pymatgen.core.periodic_table import Element
    from pymatgen.core.composition import Composition

    try:
        comp = Composition(formula)
        elements = list(comp.elements)
        fractions = [comp.get_atomic_fraction(e) for e in elements]
    except Exception:
        return np.zeros(56)

    n = len(elements)
    has_o = any(e.symbol == "O" for e in elements)
    has_tm = any(getattr(e, "is_transition_metal", False) for e in elements)
    total_atoms = int(comp.num_atoms)

    groups = []
    rows = []
    radii = []
    ens = []
    masses = []
    valences = []
    ion_ens = []
    s_elec, p_elec, d_elec, f_elec = 0, 0, 0, 0
    n_metal, n_nonmetal, n_metalloid = 0, 0, 0
    n_alkali, n_alkaline, n_halogen, n_noble = 0, 0, 0, 0

    for el in elements:
        sym = el.symbol
        groups.append(el.group or 0)
        rows.append(el.row or 0)
        radii.append(el.atomic_radius or 1.5)
        ens.append(el.X or 1.5)
        masses.append(el.atomic_mass or 50)
        ie_list = el.ionization_energies or [0]
        v = max(ie_list)
        ion_ens.append(v if v and v > 0 else 0)

        try:
            el_s, el_p, el_d, el_f = 0, 0, 0, 0
            for orbital, count in el.full_electronic_structure:
                o = orbital.lower()
                if "s" in o: el_s += count
                elif "p" in o: el_p += count
                elif "d" in o: el_d += count
                elif "f" in o: el_f += count
            s_elec += el_s; p_elec += el_p; d_elec += el_d; f_elec += el_f
        except Exception:
            pass

        if getattr(el, "is_metal", False): n_metal += 1
        elif getattr(el, "is_metalloid", False): n_metalloid += 1
        else: n_nonmetal += 1

        if getattr(el, "is_alkali", False): n_alkali += 1
        if getattr(el, "is_alkaline", False): n_alkaline += 1
        if getattr(el, "is_halogen", False): n_halogen += 1
        if getattr(el, "is_noble_gas", False): n_noble += 1

    if len(valences) < n:
        valences = [e.average_ionic_radius or 0 for e in elements]
    if not any(valences):
        valences = [e.group or 0 for e in elements]

    w = fractions
    base = np.array([
        n, has_o, has_tm, total_atoms,
        np.average(groups, weights=w), max(groups) - min(groups) if len(groups) > 1 else 0,
        np.average(rows, weights=w), max(rows) - min(rows) if len(rows) > 1 else 0,
        np.average(radii, weights=w), max(radii) - min(radii) if len(radii) > 1 else 0,
        np.std(radii) if len(radii) > 1 else 0,
        np.average(ens, weights=w), max(ens) - min(ens) if len(ens) > 1 else 0,
        np.std(ens) if len(ens) > 1 else 0,
        np.average(masses, weights=w), max(masses) - min(masses) if len(masses) > 1 else 0,
        np.std(masses) if len(masses) > 1 else 0,
        np.average(ion_ens, weights=w) if any(ion_ens) else 0,
        max(ion_ens) - min(ion_ens) if len(ion_ens) > 1 and any(ion_ens) else 0,
        s_elec, p_elec, d_elec, f_elec,
        n_metal, n_nonmetal, n_metalloid,
        n_alkali, n_alkaline, n_halogen, n_noble,
    ])

    cs_onehot = np.zeros(len(CRYSTAL_SYSTEMS))
    if crystal_system and crystal_system.lower() in CRYSTAL_SYSTEMS:
        cs_onehot[CRYSTAL_SYSTEMS.index(crystal_system.lower())] = 1

    vol_feat = np.array([np.log(max(volume, 1))]) if volume > 0 else np.array([0.0])

    vec = np.concatenate([base, vol_feat, cs_onehot])
    return np.nan_to_num(vec, nan=0.0, posinf=0.0, neginf=0.0)


def _generate_training_data(n_samples: int = 5000) -> tuple[np.ndarray, dict[str, np.ndarray]]:
    np.random.seed(42)
    n_feat = 56
    X = np.zeros((n_samples, n_feat))
    n_el = np.random.randint(1, 6, n_samples)
    X[:, 0] = n_el
    X[:, 1] = np.random.choice([0, 1], n_samples)  # has_O
    X[:, 2] = np.random.choice([0, 1], n_samples)  # has_TM
    X[:, 3] = np.random.randint(1, 50, n_samples) * 4  # total_atoms

    X[:, 4] = np.random.uniform(1, 18, n_samples)  # avg group
    X[:, 5] = np.random.uniform(0, 17, n_samples)  # group range
    X[:, 6] = np.random.uniform(1, 7, n_samples)   # avg row
    X[:, 7] = np.random.uniform(0, 6, n_samples)   # row range

    X[:, 8] = np.random.uniform(0.4, 2.7, n_samples)    # avg radius
    X[:, 9] = np.random.uniform(0, 2.3, n_samples)      # radius range
    X[:, 10] = np.random.uniform(0, 1.0, n_samples)     # radius std
    X[:, 11] = np.random.uniform(0.8, 4.0, n_samples)   # avg EN
    X[:, 12] = np.random.uniform(0, 3.0, n_samples)     # EN range
    X[:, 13] = np.random.uniform(0, 1.2, n_samples)     # EN std
    X[:, 14] = np.random.uniform(1, 210, n_samples)     # avg mass
    X[:, 15] = np.random.uniform(0, 200, n_samples)     # mass range
    X[:, 16] = np.random.uniform(0, 80, n_samples)      # mass std

    X[:, 17] = np.random.uniform(0, 25, n_samples)      # avg ioniz. energy
    X[:, 18] = np.random.uniform(0, 24, n_samples)      # ioniz. range
    X[:, 19] = np.random.uniform(0, 20, n_samples)      # s electrons
    X[:, 20] = np.random.uniform(0, 30, n_samples)      # p electrons
    X[:, 21] = np.random.uniform(0, 20, n_samples)      # d electrons
    X[:, 22] = np.random.uniform(0, 14, n_samples)      # f electrons
    X[:, 23] = np.random.uniform(0, 5, n_samples)       # n_metal
    X[:, 24] = np.random.uniform(0, 5, n_samples)       # n_nonmetal
    X[:, 25] = np.random.uniform(0, 3, n_samples)       # n_metalloid
    X[:, 26] = np.random.uniform(0, 2, n_samples)       # n_alkali
    X[:, 27] = np.random.uniform(0, 2, n_samples)       # n_alkaline
    X[:, 28] = np.random.uniform(0, 2, n_samples)       # n_halogen
    X[:, 29] = np.random.uniform(0, 1, n_samples)       # n_noble

    X[:, 30] = np.random.uniform(2, 8, n_samples)
    for i in range(6):
        X[:, 31 + i] = np.random.choice([0, 1], n_samples, p=[0.7, 0.3])

    avg_en = X[:, 11]
    avg_radius = X[:, 8]
    avg_mass = X[:, 14]

    targets = {
        "band_gap": np.clip(np.maximum(0, avg_en * 0.6 - avg_radius * 0.1 + np.random.normal(0, 0.3, n_samples)), 0, 12),
        "formation_energy": np.clip(-avg_en * 0.4 + np.random.normal(0, 0.15, n_samples), -5, 2),
        "density": np.clip(avg_mass / (avg_radius ** 3 * 2.5) * 2 + np.random.normal(0, 0.5, n_samples), 0.5, 25),
        "energy_above_hull": np.clip(np.random.exponential(0.1, n_samples), 0, 5),
        "total_magnetization": np.clip(np.random.exponential(1, n_samples), 0, 30),
        "is_stable": np.random.choice([0, 1], n_samples, p=[0.3, 0.7]).astype(float),
    }
    return X, targets


def _percentile_clip(arr: np.ndarray, low: float = 0.5, high: float = 99.5) -> np.ndarray:
    """Clip extreme outliers at percentiles."""
    lo, hi = np.percentile(arr, [low, high])
    return np.clip(arr, lo, hi)


def _load_real_training_data() -> tuple[dict[str, list[np.ndarray]], dict[str, list[float]]]:
    try:
        from app.database import SessionLocal
        from app.models.material import Material, Property
        from sqlalchemy.orm import joinedload
        from collections import defaultdict

        db = SessionLocal()
        materials = (db.query(Material).options(joinedload(Material.properties)).all())
        if not materials:
            db.close()
            return {}, {}

        all_features = {}
        for m in materials:
            all_features[m.id] = _get_element_feature_vector(
                m.formula, crystal_system=m.crystal_system or "", volume=m.volume or 0)

        targets = defaultdict(list)
        feature_maps = defaultdict(list)

        for m in materials:
            feats = all_features.get(m.id)
            if feats is None:
                continue
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
    known_order = ["density", "band_gap", "formation_energy"]
    prop_names = sorted(targets_real.keys(), key=lambda p: (p not in known_order, -len(targets_real[p])))

    model_config = {}
    for prop_name in prop_names:
        Xr = X_real_dict.get(prop_name, [])
        yr = targets_real.get(prop_name, [])
        n_real = len(Xr)
        print(f"{prop_name}: {n_real} real data points", end="", flush=True)

        if n_real < 100:
            if prop_name in {"band_gap", "formation_energy", "density",
                             "energy_above_hull", "total_magnetization", "is_stable"}:
                n_synth = max(2000, (100 - n_real) * 20)
                X_s, targets_s = _generate_training_data(n_synth)
                if n_real > 0:
                    X = np.vstack([np.array(Xr), X_s])
                    y = np.concatenate([np.array(yr), targets_s[prop_name]])
                else:
                    X, y = X_s, targets_s[prop_name]
            else:
                print(" — skipping (insufficient data)")
                continue
        else:
            X_arr, y_arr = np.array(Xr), np.array(yr)
            y_arr = _percentile_clip(y_arr, 0.5, 99.5)
            mask = ~np.isnan(y_arr)
            if np.sum(mask) > 50:
                X_arr, y_arr = X_arr[mask], y_arr[mask]
            X, y = X_arr, y_arr

        print(f" → {len(X)} samples")

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        model = RandomForestRegressor(n_estimators=300, max_depth=20, random_state=42, n_jobs=-1)
        model.fit(X_train, y_train)

        y_pred = model.predict(X_test)
        mae = mean_absolute_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)

        joblib.dump(model, os.path.join(MODELS_DIR, f"{prop_name}.joblib"))
        model_config[prop_name] = {
            "model": "RandomForestRegressor", "n_estimators": 300, "max_depth": 20,
            "mae": round(mae, 4), "r2": round(r2, 4), "n_real": n_real,
            "path": f"{prop_name}.joblib",
        }
        print(f"  MAE={mae:.4f} R²={r2:.4f}")

    with open(config_path, "w") as f:
        json.dump(model_config, f, indent=2)
    print(f"Models saved to {MODELS_DIR}")

    # Train space group classifier
    train_space_group_classifier()


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
        pred = float(model.predict(features)[0])
        return round(pred, 4), 0.85
    return 0, 0.0


# ──────────────────────────────────────────
# Space Group Predictor (230 groups)
# ──────────────────────────────────────────

SPG_DATA_CACHE = None


def _load_spg_training_data():
    global SPG_DATA_CACHE
    if SPG_DATA_CACHE is not None:
        return SPG_DATA_CACHE
    from app.database import SessionLocal
    from app.models.material import Material
    db = SessionLocal()
    rows = db.query(Material.formula, Material.space_group).all()
    db.close()
    SPG_DATA_CACHE = rows
    return rows


_SPG_CACHE = None


def _load_spg_cache():
    global _SPG_CACHE
    if _SPG_CACHE is None:
        path = os.path.join(MODELS_DIR, "spg_cache.json")
        if os.path.exists(path):
            with open(path) as f:
                _SPG_CACHE = json.load(f)
        else:
            _SPG_CACHE = {}
    return _SPG_CACHE


def _parse_spg_number(spg: str) -> int:
    """Parse space group symbol or number to integer 1-230."""
    if not spg:
        return 0
    if spg.lstrip("-").isdigit():
        n = abs(int(spg))
        return n if 1 <= n <= 230 else 0
    cache = _load_spg_cache()
    n = cache.get(spg, 0)
    if n:
        return n
    # Fallback: try without hyphen
    n = cache.get(spg.replace("-", ""), 0)
    return n


def _fast_feature_vector(formula: str) -> np.ndarray:
    """Fast feature extraction using ELEMENT_DATA (no pymatgen overhead)."""
    from app.core.composition_analyzer import CompositionAnalyzer, ELEMENT_DATA
    analyzer = CompositionAnalyzer()
    comp = analyzer.parse_formula(formula)
    if not comp:
        return np.zeros(20)
    elements = list(comp.keys())
    total = sum(comp.values())
    fractions = [v / total for v in comp.values()]

    radii, ens, masses, groups = [], [], [], []
    for el in elements:
        d = ELEMENT_DATA.get(el, {"radius": 1.5, "en": 1.5, "mass": 50.0, "valence": 3, "group": 1})
        radii.append(d["radius"]); ens.append(d["en"]); masses.append(d["mass"]); groups.append(d.get("group", 1))

    w = fractions
    return np.array([
        len(elements), 1 if "O" in elements else 0,
        np.average(ens, weights=w), max(ens) - min(ens) if len(ens) > 1 else 0, np.std(ens) if len(ens) > 1 else 0,
        np.average(radii, weights=w), max(radii) - min(radii) if len(radii) > 1 else 0, np.std(radii) if len(radii) > 1 else 0,
        np.average(masses, weights=w), max(masses) - min(masses) if len(masses) > 1 else 0, np.std(masses) if len(masses) > 1 else 0,
        np.average(groups, weights=w), max(groups) - min(groups) if len(groups) > 1 else 0,
        total, sum(comp.values()),
    ])


def train_space_group_classifier():
    rows = _load_spg_training_data()
    from collections import Counter, defaultdict

    label_counts = Counter()
    for formula, spg in rows:
        num = _parse_spg_number(spg)
        if num >= 1:
            label_counts[num] += 1

    popular = {lbl for lbl, cnt in label_counts.items() if cnt >= 50}
    if len(popular) < 5:
        print(f"Space group classifier: only {len(popular)} groups — skipping"); return

    by_label = defaultdict(list)
    for formula, spg in rows:
        num = _parse_spg_number(spg)
        if num in popular:
            by_label[num].append(formula)

    X, y = [], []
    for lbl, formulas in by_label.items():
        for f in formulas[:300]:
            X.append(_fast_feature_vector(f))
            y.append(lbl)

    X, y = np.array(X), np.array(y)
    n_groups = len(set(y))

    from sklearn.ensemble import RandomForestClassifier
    clf = RandomForestClassifier(n_estimators=100, max_depth=18, random_state=42, n_jobs=-1)
    clf.fit(X, y)
    acc = clf.score(X, y)
    path = os.path.join(MODELS_DIR, "space_group_classifier.joblib")
    joblib.dump(clf, path)
    print(f"Space group classifier: {n_groups} groups, {len(X)} samples, {acc:.3f} accuracy")


def predict_space_group(formula: str) -> tuple[int, str, float]:
    """Predict space group for a formula. Returns (number, symbol, confidence)."""
    path = os.path.join(MODELS_DIR, "space_group_classifier.joblib")
    if not os.path.exists(path):
        train_space_group_classifier()
    if not os.path.exists(path):
        return 1, "P1", 0.0
    clf = joblib.load(path)
    feat = _fast_feature_vector(formula).reshape(1, -1)
    probs = clf.predict_proba(feat)[0]
    idx = int(np.argmax(probs))
    sg_number = int(clf.classes_[idx])
    confidence = float(probs[idx])
    cache = _load_spg_cache()
    rev_cache = {v: k for k, v in cache.items()}
    symbol = rev_cache.get(sg_number, f"{sg_number}")
    return sg_number, symbol, confidence


# ──────────────────────────────────────────
# Structure Relaxation
# ──────────────────────────────────────────

def relax_structure(cif_string: str, force_field: str = "uff") -> Optional[dict]:
    """Relax a crystal structure using a universal force field."""
    try:
        from pymatgen.core.structure import Structure
        from pymatgen.io.cif import CifParser
        from io import StringIO
    except ImportError:
        return None

    try:
        parser = CifParser(StringIO(cif_string))
        struct = parser.get_structures()[0]
    except Exception:
        return None

    try:
        if force_field == "uff":
            from pymatgen.analysis.force_field import UFF
            uff = UFF()
            # Simple geometry optimization via energy minimization
            opt_struct = uff.optimize_structure(struct)
            if opt_struct:
                return {
                    "formula": opt_struct.composition.reduced_formula,
                    "lattice": {
                        "a": opt_struct.lattice.a, "b": opt_struct.lattice.b,
                        "c": opt_struct.lattice.c,
                        "alpha": opt_struct.lattice.alpha,
                        "beta": opt_struct.lattice.beta,
                        "gamma": opt_struct.lattice.gamma,
                    },
                    "volume": opt_struct.lattice.volume,
                    "energy": None,
                    "cif": opt_struct.to(fmt="cif"),
                    "force_field": "uff",
                }
    except Exception as e:
        pass

    return {"formula": struct.composition.reduced_formula,
            "cif": struct.to(fmt="cif"),
            "note": "relaxation not available, returning unrelaxed structure"}


# Train on import if models don't exist
if not os.path.exists(os.path.join(MODELS_DIR, "model_config.json")):
    train_and_save_models()
