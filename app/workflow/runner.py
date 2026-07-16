import uuid
from typing import Dict, Any, Optional, List

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from app.workflow.state import WorkflowState
from app.workflow.nodes import intent_analyzer_node, chef_node, editor_node


def create_workflow():
    builder = StateGraph(WorkflowState)
    builder.add_node("intent_analyzer", intent_analyzer_node)
    builder.add_node("chef", chef_node)
    builder.add_node("editor", editor_node)
    builder.set_entry_point("intent_analyzer")
    builder.add_edge("intent_analyzer", "chef")
    builder.add_edge("chef", "editor")
    builder.add_edge("editor", END)
    checkpointer = MemorySaver()
    compiled = builder.compile(checkpointer=checkpointer)
    return compiled, checkpointer


class WorkflowRunner:
    def __init__(self):
        self.graph, self.checkpointer = create_workflow()
        self._threads: Dict[str, str] = {}

    def start(self, order_id: str, session_id: str, message: str) -> Dict[str, Any]:
        thread_id = f"thread_{uuid.uuid4().hex[:12]}"
        self._threads[order_id] = thread_id
        config = {"configurable": {"thread_id": thread_id}}

        initial_state: WorkflowState = {
            "order_id": order_id,
            "session_id": session_id,
            "original_message": message,
            "intentions": [],
            "confirmed_chips": [],
            "proposal": None,
            "proposal_version": 0,
            "final_response": None,
            "current_step": "start",
            "error": None,
        }

        print(">>> [RUNNER] Iniciando workflow...")
        result = self.graph.invoke(initial_state, config=config)
        print(">>> [RUNNER] Resultado do invoke:", result)

        # Verifica se o marcador de interrupção está presente
        if result.get("_interrupt", False):
            print(">>> [RUNNER] Detectado marcador de interrupção!")
            return {
                "status": "interrupted",
                "order_id": order_id,
                "intentions": result.get("intentions", []),
                "current_step": result.get("current_step", ""),
            }

        # Se não há interrupção, terminou
        return {
            "status": "completed",
            "order_id": order_id,
            "result": result.get("final_response", ""),
            "proposal": result.get("proposal", ""),
        }

    def resume(self, order_id: str, confirmed_chips: List[Dict[str, Any]]) -> Dict[str, Any]:
        thread_id = self._threads.get(order_id)
        if not thread_id:
            raise ValueError(f"Thread não encontrada para o pedido {order_id}")
        config = {"configurable": {"thread_id": thread_id}}

        # Obtém o estado atual via get_state
        state_snapshot = self.graph.get_state(config)
        if not state_snapshot:
            raise ValueError(f"Estado não encontrado para o pedido {order_id}")

        current_state = state_snapshot.values
        print(">>> [RUNNER] Estado antes de atualizar:", current_state)

        # Atualiza as intenções
        intentions = current_state.get("intentions", [])
        for chip in confirmed_chips:
            for intent in intentions:
                if intent.get("value") == chip.get("label"):
                    intent["confirmed"] = True

        # Prepara o novo estado: remove o marcador, adiciona flag de skip
        updated_state = {
            **current_state,
            "intentions": intentions,
            "confirmed_chips": confirmed_chips,
            "_interrupt": False,
            "_skip_intent_analyzer": True,
        }
        print(">>> [RUNNER] Estado atualizado:", updated_state)

        # Atualiza o estado no checkpointer
        self.graph.update_state(config, updated_state)

        # Invoca novamente para continuar
        print(">>> [RUNNER] Retomando workflow...")
        result = self.graph.invoke(None, config=config)
        print(">>> [RUNNER] Resultado da retomada:", result)

        # Verifica se há nova interrupção (não esperado)
        if result.get("_interrupt", False):
            return {
                "status": "interrupted",
                "order_id": order_id,
                "intentions": result.get("intentions", []),
                "current_step": result.get("current_step", ""),
            }

        return {
            "status": "completed",
            "order_id": order_id,
            "result": result.get("final_response", ""),
            "proposal": result.get("proposal", ""),
        }

    def get_state(self, order_id: str) -> Dict[str, Any]:
        thread_id = self._threads.get(order_id)
        if not thread_id:
            raise ValueError(f"Thread não encontrada para o pedido {order_id}")
        config = {"configurable": {"thread_id": thread_id}}
        state = self.graph.get_state(config)
        if not state:
            raise ValueError(f"Estado não encontrado para o pedido {order_id}")
        return state.values
