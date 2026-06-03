import httpx
from typing import Optional, Any
from app.config import settings


MP_API_BASE = "https://api.materialsproject.org"
MP_API_KEY_ENV = "MP_API_KEY"


def get_mp_api_key() -> Optional[str]:
    import os
    return os.getenv(MP_API_KEY_ENV) or settings.openai_api_key or None


class MaterialsProjectClient:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or get_mp_api_key()
        self._client: Optional[httpx.AsyncClient] = None
        if self.api_key:
            self._client = httpx.AsyncClient(
                base_url=MP_API_BASE,
                headers={"X-API-KEY": self.api_key},
                timeout=30.0,
            )

    async def _get(self, path: str, params: Optional[dict] = None) -> Optional[dict]:
        if not self._client:
            return None
        try:
            resp = await self._client.get(path, params=params)
            resp.raise_for_status()
            return resp.json()
        except Exception:
            return None

    async def search_materials(
        self,
        formula: Optional[str] = None,
        elements: Optional[list[str]] = None,
        property_max: Optional[dict[str, float]] = None,
        property_min: Optional[dict[str, float]] = None,
        num_chunks: int = 1,
        chunk_size: int = 100,
    ) -> list[dict]:
        criteria: dict[str, Any] = {}
        if formula:
            criteria["formula"] = formula
        if elements:
            criteria["elements"] = elements
        if property_max:
            for k, v in property_max.items():
                criteria[f"{k}_max"] = v
        if property_min:
            for k, v in property_min.items():
                criteria[f"{k}_min"] = v

        all_results = []
        for chunk in range(num_chunks):
            params = {
                "criteria": str(criteria) if criteria else None,
                "chunk": str(chunk),
                "_chunk_size": str(chunk_size),
                "_fields": "material_id,formula_pretty,symmetry,crystal_system,band_gap,formation_energy_per_atom,volume,density,nsites,spacegroup",
            }
            data = await self._get("/v2/materials/core", params)
            if data and "data" in data:
                all_results.extend(data["data"])
        return all_results

    async def get_structure(self, material_id: str) -> Optional[dict]:
        data = await self._get(f"/v2/materials/{material_id}/structure")
        return data

    async def get_thermo_data(self, material_id: str) -> Optional[dict]:
        data = await self._get(f"/v2/materials/{material_id}/thermo")
        return data

    async def get_xrd_pattern(self, material_id: str) -> Optional[dict]:
        data = await self._get(f"/v2/materials/{material_id}/xrd")
        return data

    async def is_available(self) -> bool:
        if not self._client:
            return False
        try:
            resp = await self._client.get("/v2/materials/core", params={"_fields": "material_id", "_chunk_size": "1"})
            return resp.status_code < 500
        except Exception:
            return False

    async def close(self):
        if self._client:
            await self._client.aclose()


mp_client = MaterialsProjectClient()
