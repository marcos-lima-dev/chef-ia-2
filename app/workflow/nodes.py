from typing import Dict, Any

from app.workflow.state import WorkflowState
from app.agents.intent_analyzer import IntentAnalyzer
from app.agents.chef import Chef
from app.agents.editor import Editor


def intent_analyzer_node(state: WorkflowState) -> Dict[str, Any]:
    # Se já passamos pela análise (resumo), pulamos
    if state.get("_skip_intent_analyzer", False):
        print(">>> [NODE] Pulando intent_analyzer (retomada)")
        return {}

    print(">>> [NODE] intent_analyzer_node executando")
    message = state.get("original_message", "")
    analyzer = IntentAnalyzer()
    intentions = analyzer.analyze(message)
    print(">>> [NODE] Intenções extraídas:", intentions)

    # Retorna o estado com marcador de pausa
    return {
        "intentions": intentions,
        "current_step": "intent_analyzer",
        "_interrupt": True,  # Indica que precisa de confirmação
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


def editor_node(state: WorkflowState) -> Dict[str, Any]:
    print(">>> [NODE] editor_node executando")
    proposal = state.get("proposal", "")
    editor = Editor()
    final_response = editor.format_response(proposal)
    return {"final_response": final_response, "current_step": "editor"}
