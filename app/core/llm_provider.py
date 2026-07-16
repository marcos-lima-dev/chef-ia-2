from langchain_openai import ChatOpenAI
from app.core.config import settings

_llm = None

def get_llm():
    """Retorna uma instância singleton do ChatOpenAI."""
    global _llm
    if _llm is None:
        if not settings.openai_api_key:
            raise ValueError(
                "OPENAI_API_KEY não configurada. Adicione no arquivo .env"
            )
        _llm = ChatOpenAI(
            model=settings.llm_model,
            api_key=settings.openai_api_key,
            temperature=0.7,
        )
    return _llm
