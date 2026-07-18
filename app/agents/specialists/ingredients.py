import json
import re
from typing import Dict, Any
from langchain_core.messages import SystemMessage, HumanMessage
from app.core.llm_provider import get_llm
from app.agents.specialists.base import BaseSpecialist


class IngredientsSpecialist(BaseSpecialist):
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        recipe = context.get("proposal", "")
        if not recipe:
            return {"analysis": {}, "warnings": ["Receita vazia."], "suggestions": [], "events": []}

        llm = get_llm()
        system_prompt = """
Você é um especialista em ingredientes e combinações culinárias.

Analise a receita fornecida e responda APENAS um JSON com:
- "compatibility": booleano (os ingredientes combinam bem?)
- "substitutions": lista de sugestões de substituição (ex: "trocar creme de leite por iogurte")
- "conflicts": lista de conflitos (ex: "limão e leite podem talhar")
- "seasonality": string indicando se os ingredientes estão na estação
- "suggestions": lista de ingredientes adicionais que podem melhorar a receita
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
            data = {"compatibility": True, "substitutions": [], "conflicts": [], "suggestions": []}

        return {
            "analysis": {
                "compatibility": data.get("compatibility"),
                "substitutions": data.get("substitutions"),
                "conflicts": data.get("conflicts"),
                "seasonality": data.get("seasonality"),
            },
            "warnings": data.get("conflicts", []),
            "suggestions": data.get("suggestions", []),
            "events": [{"type": "INGREDIENT_ANALYSIS_COMPLETED"}]
        }
