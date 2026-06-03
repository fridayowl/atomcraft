from typing import Optional
from app.config import settings


MP_API_KEY_ENV = "MP_API_KEY"


def get_mp_api_key() -> Optional[str]:
    import os
    return os.getenv(MP_API_KEY_ENV) or None


class MaterialsProjectClient:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or get_mp_api_key()
        self._mprester = None
        if self.api_key:
            try:
                from mp_api.client import MPRester
                self._mprester = MPRester(api_key=self.api_key)
            except ImportError:
                self._mprester = None

    def _get_rester(self):
        if not self._mprester and self.api_key:
            try:
                from mp_api.client import MPRester
                self._mprester = MPRester(api_key=self.api_key)
            except ImportError:
                pass
        return self._mprester

    async def search_materials(
        self,
        formula: Optional[str] = None,
        elements: Optional[list[str]] = None,
        property_max: Optional[dict[str, float]] = None,
        property_min: Optional[dict[str, float]] = None,
        num_chunks: int = 1,
        chunk_size: int = 100,
    ) -> list[dict]:
        rester = self._get_rester()
        if not rester:
            return []

        criteria = {}
        if formula:
            criteria["formula"] = formula
        if elements:
            criteria["elements"] = elements
            criteria.setdefault("num_sites", (1, 50))
        if not formula and not elements:
            return []
        if property_max:
            for k, v in property_max.items():
                criteria[f"{k}_max"] = v
        if property_min:
            for k, v in property_min.items():
                criteria[f"{k}_min"] = v

        all_results = []
        try:
            results = rester.materials.summary.search(
                **criteria,
                num_chunks=num_chunks,
                chunk_size=chunk_size,
                fields=["material_id", "formula_pretty", "symmetry",
                        "band_gap", "formation_energy_per_atom", "volume", "density",
                        "nsites"],
            )
            for r in results:
                sym = getattr(r, "symmetry", None) or {}
                if hasattr(sym, "model_dump"):
                    sym = sym.model_dump()
                entry = {
                    "material_id": getattr(r, "material_id", None),
                    "formula_pretty": getattr(r, "formula_pretty", None),
                    "symmetry": sym,
                    "band_gap": getattr(r, "band_gap", None),
                    "formation_energy_per_atom": getattr(r, "formation_energy_per_atom", None),
                    "volume": getattr(r, "volume", None),
                    "density": getattr(r, "density", None),
                    "nsites": getattr(r, "nsites", None),
                }
                all_results.append(entry)
        except Exception as e:
            print(f"MP search error: {e}")

        return all_results

    async def is_available(self) -> bool:
        rester = self._get_rester()
        if not rester:
            return False
        try:
            results = rester.materials.summary.search(chunk_size=1, fields=["material_id"])
            return len(results) > 0
        except Exception:
            return False

    async def close(self):
        if self._mprester:
            try:
                self._mprester.client.close()
            except Exception:
                pass


mp_client = MaterialsProjectClient()
