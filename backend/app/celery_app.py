from celery import Celery
from app.config import settings

celery_app = Celery(
    "aion",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)


@celery_app.task(bind=True, max_retries=3)
def run_property_prediction(self, formula: str, properties: list[str]) -> dict:
    from app.core.predictor import PropertyPredictor
    from app.core.composition_analyzer import CompositionAnalyzer

    analyzer = CompositionAnalyzer()
    predictor = PropertyPredictor()

    composition = analyzer.parse_formula(formula)
    features = analyzer.compute_descriptors(composition)
    results = {}
    for prop in properties:
        try:
            value, confidence = predictor.predict(composition, prop)
            results[prop] = {"value": value, "confidence": confidence}
        except Exception as e:
            results[prop] = {"error": str(e)}
    return {"formula": formula, "results": results}


@celery_app.task(bind=True, max_retries=2)
def run_simulation_job(self, material_id: int, sim_type: str) -> dict:
    from app.core.simulation import SimulationOrchestrator

    orchestrator = SimulationOrchestrator()
    if sim_type == "dft":
        return orchestrator.run_dft_calculation(material_id)
    elif sim_type == "md":
        return orchestrator.run_molecular_dynamics(material_id)
    return {"error": f"Unknown simulation type: {sim_type}"}
