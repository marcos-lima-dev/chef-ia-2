import json
import re
from typing import Dict, Any
from langchain_core.messages import SystemMessage, HumanMessage
from app.core.llm_provider import get_llm
from app.agents.specialists.base import BaseSpecialist


class DietSpecialist(BaseSpecialist):
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        recipe = context.get("proposal", "")
        restrictions = context.get("restrictions", [])
        if not recipe:
            return {"analysis": {}, "warnings": ["Receita vazia."], "suggestions": [], "events": []}

        llm = get_llm()
        system_prompt = """
Você é um especialista em dietas e restrições alimentares.

Avalie se a receita atende a cada uma das restrições fornecidas.
Responda APENAS um JSON com:
- "diet_compliance": dict com chave = restrição, valor = booleano
- "warnings": lista de alertas
- "suggestions": lista de sugestões para adequar a receita
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
            data = {"diet_compliance": {}, "warnings": [], "suggestions": []}

        return {
            "analysis": data.get("diet_compliance", {}),
            "warnings": data.get("warnings", []),
            "suggestions": data.get("suggestions", []),
            "events": [{"type": "DIET_ANALYSIS_COMPLETED"}]
        }
