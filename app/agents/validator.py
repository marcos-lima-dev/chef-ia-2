class Validator:
    def validate(self, ingredients: list[str]) -> dict:
        # 1. Lista básica de ingredientes comuns (exemplo pequeno)
        valid = {
            "tomate", "alface", "batata", "cebola", "alho", "frango", "carne", "arroz",
            "feijão", "ervilha", "milho", "cenoura", "abóbora", "pepino", "pimentão",
            "óleo", "azeite", "manteiga", "sal", "pimenta", "vinagre", "limão", "iogurte",
            "queijo", "leite", "creme de leite", "farinha", "ovo", "açúcar", "mel",
            "linguiça", "bacon", "calabresa", "ervilhas", "couve", "brócolis", "espinafre"
        }
        
        invalid = [i for i in ingredients if i.lower() not in valid]
        
        # 2. Se houver itens inválidos, usar LLM como fallback (opcional)
        #    (Aqui você pode chamar o LLM para perguntar se é comestível)
        
        return {
            "valid": not bool(invalid),
            "invalid": invalid,
            "suggestions": []  # Pode incluir sugestões de substituição
        }