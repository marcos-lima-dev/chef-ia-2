from typing import List, Dict, Any


class Maestro:
    def plan(self, intentions: List[Dict[str, Any]], proposal: str) -> List[str]:
        specialists = []
        for intent in intentions:
            intent_type = intent.get("type")
            value = intent.get("value", "").lower()

            if intent_type == "goal":
                if value in ["leve", "saudável", "low-calorie"]:
                    specialists.append("nutritionist")
                if value in ["barato", "econômico", "low-cost"]:
                    specialists.append("cost")
                if value in ["rápido", "rápida"]:
                    specialists.append("time")

            if intent_type == "ingredient":
                specialists.append("ingredients")

            if intent_type == "restriction":
                if value in ["vegano", "vegetariano", "sem glúten", "low-carb", "cetogênica"]:
                    specialists.append("diet")
                # Sempre executa restrições para verificar alergias
                specialists.append("restrictions")

        return list(set(specialists))
