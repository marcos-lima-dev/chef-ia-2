from typing import Dict, Any

from app.workflow.state import WorkflowState
from app.agents.intent_analyzer import IntentAnalyzer
from app.agents.chef import Chef
from app.agents.maestro import Maestro
from app.agents.specialists import Nutritionist
from app.agents.editor import Editor


def intent_analyzer_node(state: WorkflowState) -> Dict[str, Any]:
    print(">>> [NODE] intent_analyzer_node executando")
    if state.get("_skip_intent_analyzer", False):
        print(">>> [NODE] Pulando análise (retomada)")
        return {}

    message = state.get("original_message", "")
    order_id = state.get("order_id", "unknown")
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


def maestro_node(state: WorkflowState) -> Dict[str, Any]:
    print(">>> [NODE] maestro_node executando")
    intentions = state.get("intentions", [])
    proposal = state.get("proposal", "")
    goals = [i["value"] for i in intentions if i["type"] == "goal"]

    maestro = Maestro()
    specialist_names = maestro.plan(intentions, proposal)

    analyses = []
    if "nutritionist" in specialist_names:
        nutritionist = Nutritionist()
        result = nutritionist.execute({"proposal": proposal, "goals": goals})
        analyses.append({
            "specialist": "nutritionist",
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
    if state.get("_interrupt", False):
        print(">>> [NODE] Interrupção detectada, pausando workflow")
        return "pause"
    return "continue"
