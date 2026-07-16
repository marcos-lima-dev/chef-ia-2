import uuid
from typing import Dict, Any, Optional, List

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from app.workflow.state import WorkflowState
from app.workflow.nodes import (
    intent_analyzer_node,
    chef_node,
    maestro_node,
    editor_node,
    should_continue,
)


def create_workflow():
    builder = StateGraph(WorkflowState)

    builder.add_node("intent_analyzer", intent_analyzer_node)
    builder.add_node("chef", chef_node)
    builder.add_node("maestro", maestro_node)
    builder.add_node("editor", editor_node)

    builder.add_conditional_edges(
        "intent_analyzer",
        should_continue,
        {"continue": "chef", "pause": END}
    )

    builder.add_edge("chef", "maestro")
    builder.add_edge("maestro", "editor")
    builder.add_edge("editor", END)
    builder.set_entry_point("intent_analyzer")

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
            "analyses": [],
            "final_response": None,
            "current_step": "start",
            "error": None,
        }

        result = self.graph.invoke(initial_state, config=config)
        print(f">>> [RUNNER] Resultado do start: {result}")

        if result.get("_interrupt", False):
            print(">>> [RUNNER] Interrupção detectada!")
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

    def resume(self, order_id: str, confirmed_chips: List[Dict[str, Any]]) -> Dict[str, Any]:
        thread_id = self._threads.get(order_id)
        if not thread_id:
            raise ValueError(f"Thread não encontrada para o pedido {order_id}")
        config = {"configurable": {"thread_id": thread_id}}

        state_snapshot = self.graph.get_state(config)
        if not state_snapshot:
            raise ValueError(f"Estado não encontrado para o pedido {order_id}")

        current_state = state_snapshot.values
        print(f">>> [RUNNER] Estado antes de atualizar: {current_state}")

        intentions = current_state.get("intentions", [])
        for chip in confirmed_chips:
            for intent in intentions:
                if intent.get("value") == chip.get("label"):
                    intent["confirmed"] = True

        updated_state = {
            **current_state,
            "intentions": intentions,
            "confirmed_chips": confirmed_chips,
            "_interrupt": False,
            "_skip_intent_analyzer": True,
        }
        print(f">>> [RUNNER] Estado atualizado: {updated_state}")

        self.graph.update_state(config, updated_state)

        result = self.graph.invoke(None, config=config)
        print(f">>> [RUNNER] Resultado da retomada: {result}")

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
