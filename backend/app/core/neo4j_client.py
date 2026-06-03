from typing import Optional, Any
from neo4j import AsyncGraphDatabase, AsyncDriver
from app.config import settings


class KnowledgeGraphClient:
    def __init__(self):
        self._driver: Optional[AsyncDriver] = None
        if settings.neo4j_uri and settings.neo4j_password != "password":
            self._driver = AsyncGraphDatabase.driver(
                settings.neo4j_uri,
                auth=(settings.neo4j_user, settings.neo4j_password),
            )

    async def _query(self, cypher: str, params: Optional[dict] = None) -> list[dict]:
        if not self._driver:
            return []
        async with self._driver.session() as session:
            result = await session.run(cypher, params or {})
            records = await result.data()
            return records

    async def search_materials_by_property(self, property_type: str,
                                            min_value: float,
                                            max_value: float) -> list[dict]:
        return await self._query(
            """MATCH (m:Material)-[:HAS_PROPERTY]->(p:Property {type: $type})
               WHERE p.value >= $min AND p.value <= $max
               RETURN m.formula AS formula, m.space_group AS space_group,
                      p.value AS property_value, p.unit AS unit
               LIMIT 50""",
            {"type": property_type, "min": min_value, "max": max_value},
        )

    async def find_related_materials(self, formula: str) -> list[dict]:
        return await self._query(
            """MATCH (m:Material {formula: $formula})-[:CONTAINS]->(e:Element)<-[:CONTAINS]-(related:Material)
               WHERE related.formula <> $formula
               RETURN related.formula AS formula,
                      COUNT(DISTINCT e) AS shared_elements
               ORDER BY shared_elements DESC
               LIMIT 20""",
            {"formula": formula},
        )

    async def get_synthesis_pathways(self, formula: str) -> list[dict]:
        return await self._query(
            """MATCH (m:Material {formula: $formula})<-[:PRODUCES]-(s:SynthesisMethod)
               RETURN s.name AS method, s.temperature AS temperature,
                      s.difficulty AS difficulty, s.success_rate AS success_rate
               ORDER BY s.success_rate DESC""",
            {"formula": formula},
        )

    async def get_element_statistics(self) -> list[dict]:
        return await self._query(
            """MATCH (e:Element)<-[:CONTAINS]-(m:Material)
               RETURN e.symbol AS element, COUNT(m) AS material_count,
                      AVG(m.formation_energy_per_atom) AS avg_formation_energy
               ORDER BY material_count DESC
               LIMIT 30"""
        )

    async def seed_material(self, formula: str, space_group: str,
                             band_gap: float = 0,
                             formation_energy: float = 0) -> None:
        await self._query(
            """MERGE (m:Material {formula: $formula})
               ON CREATE SET m.space_group = $space_group
               MERGE (bg:Property {type: 'band_gap', value: $band_gap, unit: 'eV'})
               MERGE (fe:Property {type: 'formation_energy', value: $formation_energy, unit: 'eV/atom'})
               MERGE (m)-[:HAS_PROPERTY]->(bg)
               MERGE (m)-[:HAS_PROPERTY]->(fe)""",
            {"formula": formula, "space_group": space_group,
             "band_gap": band_gap, "formation_energy": formation_energy},
        )

    async def close(self):
        if self._driver:
            await self._driver.close()


kg_client = KnowledgeGraphClient()
