import json
import re
from typing import List, Dict, Any
from langchain_core.messages import SystemMessage, HumanMessage

from app.core.llm_provider import get_llm


class IntentAnalyzer:
    """Analisa intenções do pedido usando OpenAI."""

    def analyze(self, message: str) -> List[Dict[str, Any]]:
        llm = get_llm()

        system_prompt = """
Você é um analisador de intenções para um assistente de culinária.
Extraia as intenções do usuário a partir da mensagem fornecida.

As intenções podem ser:
- "goal": objetivos (ex: "leve", "rápida", "barata", "saudável").
- "ingredient": ingredientes mencionados (ex: "tomate", "frango", "arroz").
- "restriction": restrições dietéticas (ex: "vegano", "sem glúten", "low carb", "sem lactose").

Retorne APENAS um JSON array de objetos com os campos "type" e "value".
Exemplo: [{"type": "goal", "value": "leve"}, {"type": "ingredient", "value": "tomate"}]
"""
        human_prompt = f"Mensagem do usuário: {message}"

        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt)
        ])

        content = response.content
        # Remove markdown code blocks (```json ... ```) se existir
        match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', content)
        if match:
            content = match.group(1)

        try:
            data = json.loads(content)
            if isinstance(data, list):
                return data
            return []
        except json.JSONDecodeError:
            print(f"Erro ao parsear JSON: {content}")
            return []
