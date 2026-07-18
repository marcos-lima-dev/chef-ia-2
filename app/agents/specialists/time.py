import json
import re
from typing import Dict, Any
from langchain_core.messages import SystemMessage, HumanMessage
from app.core.llm_provider import get_llm
from app.agents.specialists.base import BaseSpecialist


class TimeSpecialist(BaseSpecialist):
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        recipe = context.get("proposal", "")
        if not recipe:
            return {"analysis": {}, "warnings": ["Receita vazia."], "suggestions": [], "events": []}

        llm = get_llm()
        system_prompt = """
Você é um especialista em tempo de preparo de receitas.

Estime o tempo necessário para preparar a receita, considerando preparo, cozimento e montagem.
Responda APENAS um JSON com:
- "prep_time": número (minutos)
- "cook_time": número (minutos)
- "total_time": número (minutos)
- "complexity": "fácil", "médio" ou "difícil"
- "suggestions": lista de sugestões para otimizar o tempo
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
            data = {"prep_time": 0, "cook_time": 0, "total_time": 0, "complexity": "médio", "suggestions": []}

        return {
            "analysis": {
                "prep_time": data.get("prep_time"),
                "cook_time": data.get("cook_time"),
                "total_time": data.get("total_time"),
                "complexity": data.get("complexity"),
            },
            "warnings": [],
            "suggestions": data.get("suggestions", []),
            "events": [{"type": "TIME_ANALYSIS_COMPLETED"}]
        }
