from typing import List, Dict, Any


class Chef:
    """Cria propostas culinárias (mock)."""

    def create_proposal(self, intentions: List[Dict[str, Any]]) -> str:
        # Constrói uma receita simples baseada nas intenções
        ingredients = [i["value"] for i in intentions if i["type"] == "ingredient"]
        goals = [i["value"] for i in intentions if i["type"] == "goal"]

        if not ingredients:
            ingredients = ["ingredientes básicos"]

        receita = f"Receita com {', '.join(ingredients)}.\n"
        receita += "Modo de preparo: Misture todos os ingredientes e sirva.\n"
        if goals:
            receita += f"Objetivo: {', '.join(goals)}.\n"

        return receita
