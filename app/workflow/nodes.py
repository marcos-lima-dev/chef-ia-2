from typing import Dict, Any

from app.services.ingredient_specialist import IngredientSpecialist
from app.infrastructure.database.base import get_db
from app.workflow.state import WorkflowState
from app.agents.intent_analyzer import IntentAnalyzer
from app.agents.chef import Chef
from app.agents.validator import Validator
from app.agents.maestro import Maestro
from app.agents.specialists import (
    Nutritionist,
    IngredientsSpecialist,
    DietSpecialist,
    RestrictionsSpecialist,
    CostSpecialist,
    TimeSpecialist,
)
from app.agents.editor import Editor


def ingredient_specialist_node(state: WorkflowState) -> Dict[str, Any]:
    """
    Nó que resolve entidades culinárias usando o IngredientSpecialist.
    Retorna:
        - Se todas as intenções forem resolvidas (continue) → atualiza intenções com entidades.
        - Se houver itens que precisam de confirmação (needs_confirmation) → interrompe com erro.
        - Se houver itens bloqueados (block) → interrompe com erro.
    """
    print(">>> [NODE] ingredient_specialist_node executando")
    
    intentions = state.get("intentions", [])
    terms = [i["value"] for i in intentions if i.get("type") == "ingredient"]
    
    if not terms:
        return {"current_step": "ingredient_specialist"}
    
    # Obtém sessão do banco
    db = next(get_db())
    specialist = IngredientSpecialist(db)
    resolutions = specialist.resolve(terms)
    
    # Separa por ação
    continue_items = []
    needs_confirmation = []
    blocked = []
    
    for r in resolutions:
        if r.action == "continue":
            continue_items.append(r)
        elif r.action == "needs_confirmation":
            needs_confirmation.append(r)
        else:  # block
            blocked.append(r)
    
    # Se houver bloqueio, interrompe o workflow
    if blocked:
        messages = []
        for r in blocked:
            messages.append(f"❌ {r.original_input} não é um ingrediente válido.")
        return {
            "error": "\n".join(messages),
            "current_step": "ingredient_specialist",
            "_interrupt": True,
        }
    
    # Se houver itens que precisam de confirmação, interrompe e envia para o frontend
    if needs_confirmation:
        messages = []
        pending = []
        for r in needs_confirmation:
            if r.suggestions:
                messages.append(f"❓ {r.original_input} → Você quis dizer '{r.suggestions[0]}'?")
            else:
                messages.append(f"❓ Não conheço '{r.original_input}'. Você confirma que é um alimento?")
            # Guarda a resolução para o frontend processar a confirmação
            pending.append(r.dict())
        
        return {
            "error": "\n".join(messages),
            "current_step": "ingredient_specialist",
            "_interrupt": True,
            "_pending_resolutions": pending,  # <-- frontend usará para pedir confirmação
        }
    
    # Todos aceitos: atualiza intenções
    new_intentions = []
    for r in continue_items:
        if r.entity:
            new_intentions.append({
                "type": "ingredient",
                "value": r.entity.canonical_name,
                "confirmed": False,
                "entity": r.entity.dict(),
            })
    
    return {
        "intentions": new_intentions,
        "current_step": "ingredient_specialist",
    }


def intent_analyzer_node(state: WorkflowState) -> Dict[str, Any]:
    print(">>> [NODE] intent_analyzer_node executando")
    if state.get("_skip_intent_analyzer", False):
        print(">>> [NODE] Pulando análise (retomada)")
        return {}

    message = state.get("original_message", "")
    analyzer = IntentAnalyzer()
    intentions = analyzer.analyze(message)
    print(f">>> [NODE] Intenções extraídas: {intentions}")

    return {
        "intentions": intentions,
        "current_step": "intent_analyzer",
        "_interrupt": True,
    }


def chef_node(state: WorkflowState) -> Dict[str, Any]:
    print(">>> [NODE] chef_node executando")
    intentions = state.get("intentions", [])
    confirmed = [i for i in intentions if i.get("confirmed", False)]
    chef = Chef()
    proposal = chef.create_proposal(confirmed)
    return {
        "proposal": proposal,
        "proposal_version": state.get("proposal_version", 0) + 1,
        "current_step": "chef",
    }


def validator_node(state: WorkflowState) -> Dict[str, Any]:
    """
    (Opcional) Valida se os ingredientes são plausíveis usando lista estática.
    Este nó pode ser removido ou mantido como fallback, já que o IngredientSpecialist
    faz a validação completa. Mantido por compatibilidade.
    """
    print(">>> [NODE] validator_node executando (fallback)")
    
    intentions = state.get("intentions", [])
    ingredients = [i["value"] for i in intentions if i.get("type") == "ingredient"]
    
    validator = Validator()
    result = validator.validate(ingredients)
    
    if not result["valid"]:
        error_msg = f"Ingredientes não reconhecidos: {', '.join(result['invalid'])}"
        print(f">>> [NODE] ⚠️ {error_msg}")
        return {
            "error": error_msg,
            "current_step": "validator",
            "_interrupt": True,
        }
    
    print(">>> [NODE] ✅ Ingredientes validados com sucesso (fallback)")
    return {"current_step": "validator"}


def maestro_node(state: WorkflowState) -> Dict[str, Any]:
    print(">>> [NODE] maestro_node executando")
    intentions = state.get("intentions", [])
    proposal = state.get("proposal", "")

    maestro = Maestro()
    specialist_names = maestro.plan(intentions, proposal)

    goals = [i["value"] for i in intentions if i["type"] == "goal"]
    restrictions = [i["value"] for i in intentions if i["type"] == "restriction"]

    analyses = []
    specialist_map = {
        "nutritionist": Nutritionist(),
        "ingredients": IngredientsSpecialist(),
        "diet": DietSpecialist(),
        "restrictions": RestrictionsSpecialist(),
        "cost": CostSpecialist(),
        "time": TimeSpecialist(),
    }

    for name in specialist_names:
        if name in specialist_map:
            print(f">>> [NODE] Executando especialista: {name}")
            context = {"proposal": proposal, "goals": goals, "restrictions": restrictions}
            result = specialist_map[name].execute(context)
            analyses.append({
                "specialist": name,
                "analysis": result["analysis"],
                "warnings": result["warnings"],
                "suggestions": result["suggestions"],
                "events": result["events"],
            })

    return {
        "analyses": analyses,
        "current_step": "maestro",
    }


def editor_node(state: WorkflowState) -> Dict[str, Any]:
    print(">>> [NODE] editor_node executando")
    proposal = state.get("proposal", "")
    analyses = state.get("analyses", [])
    editor = Editor()
    final_response = editor.format_response(proposal, analyses)
    return {"final_response": final_response, "current_step": "editor"}


def should_continue(state: WorkflowState) -> str:
    """Decide se o workflow deve continuar ou pausar."""
    if state.get("_interrupt", False):
        print(">>> [NODE] Interrupção detectada, pausando workflow")
        return "pause"
    return "continue"