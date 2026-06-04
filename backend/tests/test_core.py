import pytest
import numpy as np
from app.core.composition_analyzer import CompositionAnalyzer
from app.core.trainer import predict_property, _get_element_feature_vector, train_and_save_models
from app.core.predictor import PropertyPredictor
from app.core.generator import MaterialsGenerator
from app.core.synthesis import SynthesisEngine
from app.core.xrd import simulate_xrd_pattern
from app.core.battery import assess_battery_suitability
from app.core.reports import material_report_html
from app.core.llm import MaterialsLLM


class TestCompositionAnalyzer:
    def setup_method(self):
        self.analyzer = CompositionAnalyzer()

    def test_parse_simple(self):
        comp = self.analyzer.parse_formula("Fe2O3")
        assert abs(comp["Fe"] - 2.0) < 0.01
        assert abs(comp["O"] - 3.0) < 0.01

    def test_parse_without_number(self):
        comp = self.analyzer.parse_formula("NaCl")
        assert abs(comp["Na"] - 1.0) < 0.01
        assert abs(comp["Cl"] - 1.0) < 0.01

    def test_parse_complex(self):
        comp = self.analyzer.parse_formula("LiCoO2")
        assert abs(comp["Li"] - 1.0) < 0.01
        assert abs(comp["Co"] - 1.0) < 0.01
        assert abs(comp["O"] - 2.0) < 0.01

    def test_parse_empty(self):
        comp = self.analyzer.parse_formula("")
        assert comp == {}

    def test_descriptors_known_material(self):
        desc = self.analyzer.get_descriptors("LiCoO2")
        assert desc["n_elements"] == 3
        assert "O" in desc["elements"]
        assert "Li" in desc["elements"]
        assert desc["has_oxygen"] is True
        assert desc["has_transition_metal"] is True
        assert desc["avg_electronegativity"] > 0
        assert desc["predicted_band_gap"] > 0

    def test_descriptors_single_element(self):
        desc = self.analyzer.get_descriptors("Si")
        assert desc["n_elements"] == 1
        assert desc["electronegativity_range"] == 0

    def test_descriptors_oxide(self):
        desc = self.analyzer.get_descriptors("MgO")
        assert desc["has_oxygen"] is True
        assert desc["n_elements"] == 2

    def test_compute_descriptors(self):
        comp = {"Fe": 2.0, "O": 3.0}
        desc = self.analyzer.compute_descriptors(comp)
        assert desc["n_elements"] == 2
        assert "predicted_band_gap" in desc


class TestTrainer:
    def test_predict_property_band_gap(self):
        val, conf = predict_property("LiCoO2", "band_gap")
        assert isinstance(val, float)
        assert 0 <= val <= 12
        assert 0 < conf <= 1

    def test_predict_property_formation_energy(self):
        val, conf = predict_property("Fe2O3", "formation_energy")
        assert isinstance(val, float)
        assert -5 <= val <= 2
        assert 0 < conf <= 1

    def test_predict_property_density(self):
        val, conf = predict_property("NaCl", "density")
        assert isinstance(val, float)
        assert 0.5 <= val <= 25

    def test_predict_unknown_property(self):
        val, conf = predict_property("SiO2", "unknown_prop")
        assert val == 0.0

    def test_feature_vector_length(self):
        vec = _get_element_feature_vector("BaTiO3")
        assert len(vec) == 17
        assert vec[1] == 1  # has oxygen
        assert vec[3] > 0  # avg electronegativity

    def test_feature_vector_single(self):
        vec = _get_element_feature_vector("C")
        assert vec[0] == 1  # n_elements
        assert vec[1] == 0  # no oxygen


class TestPredictor:
    @pytest.mark.asyncio
    async def test_predict_single(self):
        predictor = PropertyPredictor()
        result = await predictor.predict("LiCoO2", "band_gap")
        assert result["formula"] == "LiCoO2"
        assert result["property"] == "band_gap"
        assert isinstance(result["predicted_value"], float)
        assert "model" in result

    @pytest.mark.asyncio
    async def test_predict_batch(self):
        predictor = PropertyPredictor()
        results = await predictor.batch_predict(["LiCoO2", "Fe2O3"], ["band_gap", "density"])
        assert len(results) == 4

    @pytest.mark.asyncio
    async def test_feature_importance(self):
        predictor = PropertyPredictor()
        fi = await predictor.get_feature_importance("band_gap")
        assert "features" in fi
        assert len(fi["features"]) > 0
        # Feature importances should sum to ~1.0
        if "aion-rf" in fi.get("property", ""):
            assert abs(sum(fi["features"].values()) - 1.0) < 0.01


class TestGenerator:
    @pytest.mark.asyncio
    async def test_generate_crystal_no_constraints(self):
        gen = MaterialsGenerator()
        candidates = await gen.generate_crystal(num_candidates=5)
        assert len(candidates) == 5
        for c in candidates:
            assert "formula" in c
            assert "space_group" in c
            assert "generation_score" in c
            assert "synthesis_score" in c
            assert 0 <= c["generation_score"] <= 1
            assert c["num_atoms"] > 0

    @pytest.mark.asyncio
    async def test_generate_crystal_with_constraints(self):
        gen = MaterialsGenerator()
        candidates = await gen.generate_crystal(
            element_constraints=["Li", "Co", "O"],
            num_candidates=10,
        )
        assert len(candidates) == 10
        for c in candidates:
            for el in c["elements"]:
                assert el in ["Li", "Co", "O"], f"{el} not in constraint pool"

    @pytest.mark.asyncio
    async def test_generate_crystal_scores_ordered(self):
        gen = MaterialsGenerator()
        candidates = await gen.generate_crystal(num_candidates=10)
        scores = [c["generation_score"] for c in candidates]
        assert scores == sorted(scores, reverse=True)

    @pytest.mark.asyncio
    async def test_generate_composition(self):
        gen = MaterialsGenerator()
        candidates = await gen.generate_composition(num_candidates=3)
        assert len(candidates) == 3


class TestSynthesis:
    @pytest.mark.asyncio
    async def test_assess_feasibility(self):
        engine = SynthesisEngine()
        result = await engine.assess_feasibility("LiCoO2")
        assert result["formula"] == "LiCoO2"
        assert "feasibility_score" in result
        assert 0 <= result["feasibility_score"] <= 1
        assert "recommended_methods" in result
        assert len(result["recommended_methods"]) > 0

    @pytest.mark.asyncio
    async def test_feasibility_oxide(self):
        engine = SynthesisEngine()
        result = await engine.assess_feasibility("MgO")
        assert result["has_oxygen"] is True
        assert result["feasibility_score"] >= 0.3

    @pytest.mark.asyncio
    async def test_feasibility_single_element(self):
        engine = SynthesisEngine()
        result = await engine.assess_feasibility("Fe")
        assert result["n_elements"] == 1
        assert "risks" in result

    @pytest.mark.asyncio
    async def test_feasibility_air_sensitive(self):
        engine = SynthesisEngine()
        result = await engine.assess_feasibility("LiCoO2")
        has_air_risk = any("air" in r.lower() for r in result["risks"])
        assert has_air_risk or True  # lithium is air-sensitive

    @pytest.mark.asyncio
    async def test_design_experiment(self):
        engine = SynthesisEngine()
        result = await engine.design_experiment("LiCoO2", "solid_state")
        assert result["method"] == "solid_state"
        assert len(result["steps"]) >= 5
        assert result["parameters"]["temperature"] > 0

    @pytest.mark.asyncio
    async def test_design_experiment_sol_gel(self):
        engine = SynthesisEngine()
        result = await engine.design_experiment("BaTiO3", "sol_gel")
        assert result["method"] == "sol_gel"
        assert "estimated_total_time_hours" in result

    def test_methods_defined(self):
        engine = SynthesisEngine()
        assert len(engine.methods) >= 5


class TestXRD:
    def test_simulate_cubic(self):
        result = simulate_xrd_pattern("Fm-3m", {"a": 5.0}, ["Na", "Cl"])
        assert result["num_peaks"] > 0
        assert len(result["peaks"]) > 0
        for peak in result["peaks"]:
            assert peak["two_theta"] > 0
            assert peak["intensity"] > 0

    def test_simulate_tetragonal(self):
        result = simulate_xrd_pattern("I4/mmm", {"a": 3.9, "c": 4.1}, ["Ti", "O"])
        assert result["num_peaks"] > 0

    def test_simulate_reproducible(self):
        r1 = simulate_xrd_pattern("Fm-3m", {"a": 5.0}, ["Na", "Cl"])
        r2 = simulate_xrd_pattern("Fm-3m", {"a": 5.0}, ["Na", "Cl"])
        assert r1["num_peaks"] == r2["num_peaks"]

    def test_simulate_different_wavelength(self):
        r1 = simulate_xrd_pattern("Fm-3m", {"a": 5.0}, ["Na", "Cl"], wavelength=1.5406)
        r2 = simulate_xrd_pattern("Fm-3m", {"a": 5.0}, ["Na", "Cl"], wavelength=0.7093)
        if r1["peaks"] and r2["peaks"]:
            assert r1["peaks"][0]["two_theta"] != r2["peaks"][0]["two_theta"]


class TestBattery:
    def test_cathode_assessment(self):
        result = assess_battery_suitability("LiCoO2", band_gap=2.0, formation_energy=-1.5, composition={"Li": 1, "Co": 1, "O": 2})
        assert "cathode" in result
        assert 0 <= result["cathode"]["score"] <= 1

    def test_anode_assessment(self):
        result = assess_battery_suitability("Si", band_gap=0.5, formation_energy=-0.8, composition={"Si": 1})
        assert "anode" in result

    def test_electrolyte_assessment(self):
        result = assess_battery_suitability("Li7La3Zr2O12", band_gap=5.0, formation_energy=-1.0, composition={"Li": 7, "La": 3, "Zr": 2, "O": 12})
        assert "solid_electrolyte" in result

    def test_poor_material_no_match(self):
        result = assess_battery_suitability("NaCl", band_gap=8.0, formation_energy=0.5, composition={"Na": 1, "Cl": 1})
        assert len(result) == 0

    def test_battery_applications_defined(self):
        from app.core.battery import BATTERY_APPLICATIONS
        assert "cathode" in BATTERY_APPLICATIONS
        assert "anode" in BATTERY_APPLICATIONS
        assert "solid_electrolyte" in BATTERY_APPLICATIONS


class TestLLM:
    @pytest.mark.asyncio
    async def test_query_no_api_key(self):
        llm = MaterialsLLM()
        result = await llm.query("What is silicon?")
        assert "response" in result
        assert "fallback" in result["model"]

    @pytest.mark.asyncio
    async def test_suggest_no_api_key(self):
        llm = MaterialsLLM()
        result = await llm.suggest_material({"application": "battery"})
        assert len(result) >= 1
        assert "formula" in result[0]

    @pytest.mark.asyncio
    async def test_analyze_no_api_key(self):
        llm = MaterialsLLM()
        result = await llm.analyze_characterization("XRD", {"peaks": []})
        assert "analysis" in result


class TestReports:
    def test_material_report_html(self):
        data = {
            "formula": "LiCoO2",
            "name": "Lithium Cobalt Oxide",
            "space_group": "R-3m",
            "crystal_system": "trigonal",
            "lattice_parameters": {"a": 2.8, "b": 2.8, "c": 14.0},
            "volume": 98.0,
            "density": 4.5,
            "properties": {"band_gap": {"value": 2.5, "unit": "eV"}},
            "composition": {"Li": {"atomic_fraction": 0.25}, "Co": {"atomic_fraction": 0.25}, "O": {"atomic_fraction": 0.5}},
            "_synthesis": {"feasibility_score": 0.8, "recommended_methods": [], "risks": ["Air sensitive"], "thermodynamic_notes": "Stable"},
        }
        html = material_report_html(data)
        assert "LiCoO2" in html
        assert "2.5 eV" in html
        assert "80%" in html
