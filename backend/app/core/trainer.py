import os
import json
import numpy as np
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
import joblib

MODELS_DIR = os.path.join(os.path.dirname(__file__), "models")


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


CRYSTAL_SYSTEMS = ["cubic", "tetragonal", "hexagonal", "orthorhombic", "monoclinic", "triclinic"]


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


def _load_real_training_data() -> tuple[list[np.ndarray], dict[str, list[float]]]:
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

        targets = {"band_gap": [], "formation_energy": [], "density": []}
        feature_maps = {"band_gap": [], "formation_energy": [], "density": []}

        for m in materials:
            if m.id not in all_features:
                continue
            feats = all_features[m.id]
            props = {p.property_type: p.value for p in (m.properties or [])}

            if m.density is not None:
                feature_maps["density"].append(feats)
                targets["density"].append(float(m.density))

            bg = props.get("band_gap")
            if bg is not None and bg > 0:
                feature_maps["band_gap"].append(feats)
                targets["band_gap"].append(float(bg))

            fe = props.get("formation_energy")
            if fe is not None:
                feature_maps["formation_energy"].append(feats)
                targets["formation_energy"].append(float(fe))

        db.close()
        return feature_maps, targets
    except Exception as e:
        print(f"Error loading training data: {e}")
        return {}, {}


def train_and_save_models(force_retrain: bool = False):
    os.makedirs(MODELS_DIR, exist_ok=True)

    config_path = os.path.join(MODELS_DIR, "model_config.json")
    if os.path.exists(config_path) and not force_retrain:
        return

    X_real_dict, targets_real = _load_real_training_data()

    model_config = {}
    for prop_name in ["band_gap", "formation_energy", "density"]:
        X_real = X_real_dict.get(prop_name, [])
        y_real = targets_real.get(prop_name, [])
        n_real = len(X_real)
        print(f"{prop_name}: {n_real} real data points")

        if n_real < 50:
            n_synth = max(2000, (50 - n_real) * 50)
            X_synth, targets_synth = _generate_training_data(n_synth)
            if n_real > 0:
                X = np.vstack([np.array(X_real), X_synth])
                y = np.concatenate([np.array(y_real), targets_synth[prop_name]])
            else:
                X = X_synth
                y = targets_synth[prop_name]
        else:
            X = np.array(X_real)
            y = np.array(y_real)

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
            "path": model_path,
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


# Train on import if models don't exist
if not os.path.exists(os.path.join(MODELS_DIR, "model_config.json")):
    train_and_save_models()
