from typing import Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage


class MaterialsLLM:
    def __init__(self, api_key: str = "", model: str = "gpt-4o"):
        self.api_key = api_key
        self.model_name = model
        self._client: Optional[ChatOpenAI] = None
        if api_key:
            self._client = ChatOpenAI(api_key=api_key, model=model, temperature=0.3)

    async def query(self, prompt: str, system_prompt: Optional[str] = None) -> dict:
        if not system_prompt:
            system_prompt = """You are AION, an expert materials science AI assistant.
You help researchers discover, design, and understand materials.
You have deep knowledge of crystallography, thermodynamics, synthesis methods,
and computational materials science. Be precise, cite sources when possible,
and suggest concrete next steps."""

        if self._client:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=prompt),
            ]
            response = await self._client.ainvoke(messages)
            return {
                "response": response.content,
                "model": self.model_name,
                "sources": [],
            }

        return {
            "response": f"AION analysis for query: '{prompt}'\n\n"
                        f"Set OPENAI_API_KEY in your environment to enable "
                        f"real LLM responses via {self.model_name}.",
            "model": f"{self.model_name} (fallback)",
            "sources": [],
        }

    async def suggest_material(self, requirements: dict) -> list[dict]:
        if self._client:
            prompt = f"""Based on these requirements, suggest specific material candidates:
{requirements}

Return a JSON list of candidates, each with: formula, name, rationale, confidence (0-1), space_group.
Be specific and scientifically accurate."""
            messages = [
                SystemMessage(content="You are a materials discovery AI. Return only valid JSON."),
                HumanMessage(content=prompt),
            ]
            response = await self._client.ainvoke(messages)
            try:
                import json
                candidates = json.loads(response.content)
                if isinstance(candidates, list):
                    return candidates
            except (json.JSONDecodeError, TypeError):
                pass
            return []

        return [
            {
                "formula": "LiCoO2",
                "name": "Lithium Cobalt Oxide",
                "rationale": "Proven cathode material with high energy density",
                "confidence": 0.85,
                "space_group": "R-3m",
            }
        ]

    async def analyze_characterization(self, data_type: str, data: dict) -> dict:
        if self._client:
            prompt = f"Analyze this {data_type} characterization data:\n{data}"
            messages = [
                SystemMessage(content="You are an expert in materials characterization."),
                HumanMessage(content=prompt),
            ]
            response = await self._client.ainvoke(messages)
            return {"analysis": response.content, "model": self.model_name}

        return {"analysis": "Characterization analysis would be generated here."}
