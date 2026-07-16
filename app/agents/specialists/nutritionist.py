import json
import re
from typing import Dict, Any, List
from langchain_core.messages import SystemMessage, HumanMessage
from app.core.llm_provider import get_llm
from app.agents.specialists.base import BaseSpecialist

class Nutritionist(BaseSpecialist):
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        recipe = context.get("proposal", "")
        goals = context.get("goals", [])

        if not recipe:
            return {
                "analysis": {},
                "warnings": ["Receita vazia, não é possível analisar."],
                "suggestions": [],
                "events": []
            }

        llm = get_llm()
        system_prompt = """
Você é um nutricionista especializado em análise de receitas.
Dada a receita abaixo, extraia as informações nutricionais aproximadas e avalie se ela atende aos objetivos do usuário.

Responda APENAS um JSON com os campos:
- "calories": número (kcal)
- "protein": número (gramas)
- "carbs": número (gramas)
- "fat": número (gramas)
- "fiber": número (gramas, opcional)
- "warnings": lista de strings (alertas, ex: "Alto teor de sódio")
- "suggestions": lista de strings (sugestões, ex: "Substituir creme de leite por iogurte")
- "meets_goals": booleano (se atende aos objetivos)
- "goal_analysis": string (explicação sobre como atende ou não os objetivos)
"""
        human_prompt = f"Receita:\n{recipe}\n\nObjetivos do usuário: {goals}"

        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt)
        ])

        content = response.content
        # Extrair JSON
        match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', content)
        if match:
            content = match.group(1)

        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            # Fallback
            data = {
                "calories": 0,
                "protein": 0,
                "carbs": 0,
                "fat": 0,
                "warnings": ["Erro ao analisar a receita."],
                "suggestions": [],
                "meets_goals": False,
                "goal_analysis": "Não foi possível analisar."
            }

        return {
            "analysis": {
                "calories": data.get("calories"),
                "protein": data.get("protein"),
                "carbs": data.get("carbs"),
                "fat": data.get("fat"),
                "fiber": data.get("fiber"),
                "meets_goals": data.get("meets_goals"),
                "goal_analysis": data.get("goal_analysis"),
            },
            "warnings": data.get("warnings", []),
            "suggestions": data.get("suggestions", []),
            "events": [{"type": "NUTRITION_ANALYSIS_COMPLETED"}]
        }