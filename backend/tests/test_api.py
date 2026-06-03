def test_health(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"


def test_root(client):
    res = client.get("/")
    assert res.status_code == 200
    data = res.json()
    assert data["name"] == "AION Materials Discovery Platform"
    assert "endpoints" in data


class TestAuth:
    def test_signup(self, client):
        res = client.post("/api/auth/signup", json={
            "email": "new@aion.ai",
            "username": "newuser",
            "password": "secure123",
        })
        assert res.status_code == 201
        data = res.json()
        assert data["email"] == "new@aion.ai"
        assert data["username"] == "newuser"
        assert "password" not in data

    def test_signup_duplicate_email(self, client, auth_headers):
        res = client.post("/api/auth/signup", json={
            "email": "test@aion.ai",
            "username": "another",
            "password": "secure123",
        })
        assert res.status_code == 400

    def test_login(self, client):
        client.post("/api/auth/signup", json={
            "email": "login@aion.ai",
            "username": "loginuser",
            "password": "pass123",
        })
        res = client.post("/api/auth/login", data={
            "username": "login@aion.ai",
            "password": "pass123",
        })
        assert res.status_code == 200
        data = res.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_invalid(self, client):
        res = client.post("/api/auth/login", data={
            "username": "nonexist@aion.ai",
            "password": "wrong",
        })
        assert res.status_code == 401

    def test_me_authenticated(self, client, auth_headers):
        res = client.get("/api/auth/me", headers=auth_headers)
        assert res.status_code == 200
        assert res.json()["email"] == "test@aion.ai"

    def test_me_unauthenticated(self, client):
        res = client.get("/api/auth/me")
        assert res.status_code == 200
        assert res.json() is None


class TestMaterials:
    def test_list_materials(self, client):
        res = client.get("/api/materials/")
        assert res.status_code == 200
        data = res.json()
        assert "data" in data
        assert "total" in data

    def test_create_material(self, client):
        res = client.post("/api/materials/", json={
            "formula": "LiCoO2",
            "space_group": "R-3m",
        })
        assert res.status_code == 200
        data = res.json()
        assert data["formula"] == "LiCoO2"
        assert data["id"] > 0

    def test_get_material(self, client):
        create = client.post("/api/materials/", json={"formula": "Fe2O3"}).json()
        res = client.get(f"/api/materials/{create['id']}")
        assert res.status_code == 200
        data = res.json()
        assert data["formula"] == "Fe2O3"
        assert "composition" in data
        assert "Fe" in data["composition"]

    def test_search_material(self, client):
        client.post("/api/materials/", json={"formula": "BaTiO3"})
        res = client.get("/api/materials/?search=BaTiO3")
        assert res.status_code == 200
        assert len(res.json()["data"]) >= 1

    def test_delete_material(self, client):
        create = client.post("/api/materials/", json={"formula": "SiO2"}).json()
        res = client.delete(f"/api/materials/{create['id']}")
        assert res.status_code == 200
        res = client.get(f"/api/materials/{create['id']}")
        assert res.status_code == 404


class TestChat:
    def test_chat_query(self, client):
        res = client.post("/api/chat/query", json={
            "message": "What is a good cathode material?",
        })
        assert res.status_code == 200
        assert "response" in res.json()

    def test_suggest_materials(self, client):
        res = client.post("/api/chat/suggest", json={
            "requirements": {"application": "battery cathode", "elements": ["Li", "Co", "O"]},
        })
        assert res.status_code == 200
        assert "suggestions" in res.json()


class TestExperiments:
    def test_create_experiment(self, client):
        mat = client.post("/api/materials/", json={"formula": "LiFePO4"}).json()
        res = client.post("/api/experiments/", json={
            "material_id": mat["id"],
            "name": "Test Synthesis",
            "experiment_type": "solid_state",
        })
        assert res.status_code == 200
        assert res.json()["message"] == "Experiment created"

    def test_list_experiments(self, client):
        res = client.get("/api/experiments/")
        assert res.status_code == 200
        assert "data" in res.json()


class TestPrediction:
    def test_single_prediction(self, client):
        res = client.post("/api/predict/", json={
            "formula": "LiCoO2",
            "properties": ["band_gap", "formation_energy"],
        })
        assert res.status_code == 200
        assert "predictions" in res.json()

    def test_batch_prediction(self, client):
        res = client.post("/api/predict/batch", json={
            "formulas": ["LiCoO2", "Fe2O3"],
            "properties": ["band_gap"],
        })
        assert res.status_code == 200
        assert len(res.json()["results"]) == 2


class TestCIF:
    def test_import_cif_no_file(self, client):
        res = client.post("/api/materials/import-cif")
        assert res.status_code == 422

    def test_export_cif_not_found(self, client):
        res = client.get("/api/materials/99999/cif")
        assert res.status_code == 404

    def test_cif_roundtrip(self, client):
        create = client.post("/api/materials/", json={"formula": "NaCl", "space_group": "Fm-3m"}).json()
        res = client.get(f"/api/materials/{create['id']}/cif")
        assert res.status_code == 200
        assert "_chemical_formula_sum" in res.text or "Na" in res.text


class TestSynthesis:
    def test_feasibility(self, client):
        res = client.post("/api/synthesis/feasibility", json={"formula": "Na3Zr2Si2PO12"})
        assert res.status_code == 200
        assert "feasibility_score" in res.json()

    def test_design_experiment(self, client):
        res = client.post("/api/synthesis/design-experiment", json={
            "formula": "LiCoO2",
            "method": "solid_state",
        })
        assert res.status_code == 200
        assert "steps" in res.json()

    def test_methods(self, client):
        res = client.get("/api/synthesis/methods")
        assert res.status_code == 200
        assert "methods" in res.json()
        assert isinstance(res.json()["methods"], list)
