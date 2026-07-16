from typing import Dict, Any

from app.workflow.state import WorkflowState
from app.agents.intent_analyzer import IntentAnalyzer
from app.agents.chef import Chef
from app.agents.editor import Editor


def intent_analyzer_node(state: WorkflowState) -> Dict[str, Any]:
    """Extrai intenções e retorna marcador de interrupção."""
    print(">>> [NODE] intent_analyzer_node executando")
    
    # Se já passamos pela análise (retomada), apenas continua
    if state.get("_skip_intent_analyzer", False):
        print(">>> [NODE] Pulando análise (retomada)")
        return {}

    message = state.get("original_message", "")
    order_id = state.get("order_id", "unknown")
    analyzer = IntentAnalyzer()
    intentions = analyzer.analyze(message)
    print(f">>> [NODE] Intenções extraídas: {intentions}")

    # Retorna o estado com o marcador de interrupção
    return {
        "intentions": intentions,
        "current_step": "intent_analyzer",
        "_interrupt": True,  # <-- Marcador de interrupção
    }


def chef_node(state: WorkflowState) -> Dict[str, Any]:
    """Cria a proposta."""
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


def editor_node(state: WorkflowState) -> Dict[str, Any]:
    """Formata a resposta final."""
    print(">>> [NODE] editor_node executando")
    proposal = state.get("proposal", "")
    editor = Editor()
    final_response = editor.format_response(proposal)
    return {"final_response": final_response, "current_step": "editor"}


def should_continue(state: WorkflowState) -> str:
    """Decide se deve continuar ou pausar."""
    if state.get("_interrupt", False):
        print(">>> [NODE] Interrupção detectada, pausando workflow")
        return "pause"
    return "continue"
