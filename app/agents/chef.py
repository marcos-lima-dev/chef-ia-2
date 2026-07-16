from typing import List, Dict, Any
from langchain_core.messages import SystemMessage, HumanMessage

from app.core.llm_provider import get_llm


class Chef:
    """Cria receitas reais usando OpenAI."""

    def create_proposal(self, intentions: List[Dict[str, Any]]) -> str:
        if not intentions:
            return "Não foram fornecidas intenções suficientes para criar uma receita."

        llm = get_llm()

        system_prompt = """
Você é um Chef especialista em criar receitas deliciosas e bem estruturadas.

Com base nas intenções confirmadas pelo usuário, crie uma receita completa.
A receita deve ter:
1. Um título atrativo.
2. Uma lista de ingredientes com quantidades (use medidas comuns: gramas, xícaras, colheres, etc.).
3. Modo de preparo detalhado, passo a passo.

Seja claro, organizado e objetivo. Use uma linguagem acolhedora e inspiradora.
"""
        human_prompt = f"Intenções confirmadas pelo usuário: {intentions}"

        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt)
        ])

        return response.content
