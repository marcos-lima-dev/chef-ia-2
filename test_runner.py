from app.workflow.runner import WorkflowRunner
import json

runner = WorkflowRunner()

# 1. Inicia o workflow
order_id = "ord_test_123"
result = runner.start(order_id, "session_1", "Quero uma salada leve com tomate")
print("Start result:", json.dumps(result, indent=2))

# 2. Verifica estado
state = runner.get_state(order_id)
print("State:", json.dumps(state, indent=2))

# 3. Simula confirmação dos chips
confirmed = [
    {"id": "intent_0", "label": "salada", "active": True},
    {"id": "intent_1", "label": "tomate", "active": True},
    {"id": "intent_2", "label": "receita leve", "active": True},
]
result2 = runner.resume(order_id, confirmed)
print("Resume result:", json.dumps(result2, indent=2))
