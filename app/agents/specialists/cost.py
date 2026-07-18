import json
import re
from typing import Dict, Any
from langchain_core.messages import SystemMessage, HumanMessage
from app.core.llm_provider import get_llm
from app.agents.specialists.base import BaseSpecialist


class CostSpecialist(BaseSpecialist):
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        recipe = context.get("proposal", "")
        if not recipe:
            return {"analysis": {}, "warnings": ["Receita vazia."], "suggestions": [], "events": []}

        llm = get_llm()
        system_prompt = """
Você é um especialista em custos de receitas.

Estime o custo total da receita com base nos ingredientes (preços médios de mercado).
Responda APENAS um JSON com:
- "total_cost": número (em R$)
- "cost_per_serving": número (R$ por porção)
- "cost_level": "baixo", "médio" ou "alto"
- "suggestions": lista de sugestões para reduzir custo
"""
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Receita:\n{recipe}")
        ])

        content = response.content
        match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', content)
        if match:
            content = match.group(1)

        try:
            data = json.loads(content)
        except:
            data = {"total_cost": 0, "cost_per_serving": 0, "cost_level": "médio", "suggestions": []}

        return {
            "analysis": {
                "total_cost": data.get("total_cost"),
                "cost_per_serving": data.get("cost_per_serving"),
                "cost_level": data.get("cost_level"),
            },
            "warnings": [],
            "suggestions": data.get("suggestions", []),
            "events": [{"type": "COST_ANALYSIS_COMPLETED"}]
        }
