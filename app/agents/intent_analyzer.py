from typing import List, Dict, Any


class IntentAnalyzer:
    """Analisa intenções do pedido (mock)."""

    def analyze(self, message: str) -> List[Dict[str, Any]]:
        # Simulação simples: extrai palavras-chave básicas
        intentions = []
        if "leve" in message.lower():
            intentions.append({"type": "goal", "value": "receita leve", "confirmed": False})
        if "tomate" in message.lower():
            intentions.append({"type": "ingredient", "value": "tomate", "confirmed": False})
        if "salada" in message.lower():
            intentions.append({"type": "ingredient", "value": "salada", "confirmed": False})
        if "vegano" in message.lower():
            intentions.append({"type": "diet", "value": "vegano", "confirmed": False})

        # Se não encontrou nada, coloca uma intenção genérica
        if not intentions:
            intentions.append({"type": "goal", "value": "receita", "confirmed": False})

        return intentions
