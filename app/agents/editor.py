from langchain_core.messages import SystemMessage, HumanMessage

from app.core.llm_provider import get_llm


class Editor:
    """Formata a resposta final com OpenAI."""

    def format_response(self, proposal: str) -> str:
        if not proposal:
            return "Desculpe, não consegui gerar uma proposta válida."

        llm = get_llm()

        system_prompt = """
Você é um Editor de respostas para um assistente de culinária.

Sua tarefa é formatar a receita fornecida pelo Chef para ser apresentada ao usuário final.
Mantenha todo o conteúdo, mas organize com:
- Uma saudação inicial calorosa.
- Emojis apropriados (🍽️, 👨‍🍳, ✅, ⏱️, etc.) para tornar a leitura mais agradável.
- Estrutura clara (título, ingredientes, modo de preparo).
- Uma despedida motivacional.

Não invente informações novas. Apenas melhore a apresentação e legibilidade.
"""
        human_prompt = f"Proposta do Chef:\n{proposal}"

        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt)
        ])

        return response.content
