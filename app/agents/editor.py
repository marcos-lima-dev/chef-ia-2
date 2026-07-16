from typing import List, Dict, Any
from langchain_core.messages import SystemMessage, HumanMessage
from app.core.llm_provider import get_llm


class Editor:
    def format_response(self, proposal: str, analyses: List[Dict[str, Any]] = None) -> str:
        if not proposal:
            return "Desculpe, não consegui gerar uma proposta válida."

        llm = get_llm()

        # Monta o contexto das análises
        analysis_text = ""
        if analyses:
            for a in analyses:
                specialist = a.get("specialist")
                analysis = a.get("analysis", {})
                warnings = a.get("warnings", [])
                suggestions = a.get("suggestions", [])
                analysis_text += f"\nAnálise do {specialist}:\n"
                if analysis:
                    for key, value in analysis.items():
                        analysis_text += f"- {key}: {value}\n"
                if warnings:
                    analysis_text += f"- ⚠️ Avisos: {', '.join(warnings)}\n"
                if suggestions:
                    analysis_text += f"- 💡 Sugestões: {', '.join(suggestions)}\n"

        system_prompt = f"""
Você é um Editor de respostas para um assistente de culinária.

Sua tarefa é formatar a receita fornecida pelo Chef, incluindo as análises nutricionais e sugestões.

Instruções:
- Mantenha toda a receita original.
- Adicione uma seção "Análise Nutricional" com as informações fornecidas pelos especialistas.
- Inclua avisos e sugestões de forma amigável.
- Use emojis apropriados (🍽️, 👨‍🍳, ✅, ⏱️, 📊, 💡, ⚠️) para tornar a leitura mais agradável.
- Se houver sugestões, coloque-as como dicas úteis no final.
- Não invente informações novas.
"""
        human_prompt = f"""
Proposta do Chef:
{proposal}

Análises dos especialistas:
{analysis_text if analysis_text else "Nenhuma análise disponível."}
"""
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt)
        ])
        return response.content
