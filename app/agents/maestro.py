from typing import List, Dict, Any

class Maestro:
    """Coordena quais especialistas devem ser consultados."""

    def plan(self, intentions: List[Dict[str, Any]], proposal: str) -> List[str]:
        """Retorna uma lista de nomes de especialistas a serem executados."""
        specialists = []
        # Verifica se há objetivo de "leve" ou "saudável"
        for intent in intentions:
            if intent.get("type") == "goal":
                if intent.get("value") in ["leve", "saudável", "low-calorie"]:
                    specialists.append("nutritionist")
            if intent.get("type") == "restriction":
                if intent.get("value") in ["vegano", "vegetariano", "sem glúten", "low-carb"]:
                    specialists.append("diet")
        # Se não houver especialistas, retorna vazio
        return specialists