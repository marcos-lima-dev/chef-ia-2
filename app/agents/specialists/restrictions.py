import json
import re
from typing import Dict, Any
from langchain_core.messages import SystemMessage, HumanMessage
from app.core.llm_provider import get_llm
from app.agents.specialists.base import BaseSpecialist


class RestrictionsSpecialist(BaseSpecialist):
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        recipe = context.get("proposal", "")
        restrictions = context.get("restrictions", [])
        if not recipe:
            return {"analysis": {}, "warnings": ["Receita vazia."], "suggestions": [], "events": []}

        llm = get_llm()
        system_prompt = """
Você é um especialista em segurança alimentar e alergias.

Analise a receita e verifique se há ingredientes que podem causar reações alérgicas ou são proibidos.
Responda APENAS um JSON com:
- "contains_allergens": lista de alergênicos encontrados
- "risk_level": "alto", "médio" ou "baixo"
- "warnings": lista de alertas específicos
- "suggestions": lista de substituições seguras
"""
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Restrições: {restrictions}\nReceita:\n{recipe}")
        ])

        content = response.content
        match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', content)
        if match:
            content = match.group(1)

        try:
            data = json.loads(content)
        except:
            data = {"contains_allergens": [], "risk_level": "baixo", "warnings": [], "suggestions": []}

        return {
            "analysis": {
                "contains_allergens": data.get("contains_allergens"),
                "risk_level": data.get("risk_level"),
            },
            "warnings": data.get("warnings", []),
            "suggestions": data.get("suggestions", []),
            "events": [{"type": "RESTRICTION_ANALYSIS_COMPLETED"}]
        }
