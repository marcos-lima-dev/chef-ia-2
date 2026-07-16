import pytest
from app.services.workflow_manager import WorkflowManager
from app.services.event_publisher import EventPublisher
from app.domain.enums import OrderState, EventType
from app.core.exceptions import InvalidStateError


@pytest.fixture
def manager():
    pub = EventPublisher()
    return WorkflowManager(pub)


def test_create_order(manager):
    order = manager.create_order("session_123", "Quero uma salada leve")
    assert order.id.startswith("ord_")
    assert order.current_state == OrderState.INTERPRETADO
    assert order.original_message == "Quero uma salada leve"

    # Deve ter criado um workflow
    assert order.id in manager._workflows
    assert manager._workflows[order.id].status == OrderState.INTERPRETADO


def test_get_chips(manager):
    order = manager.create_order("session_123", "Quero uma salada leve")
    chips = manager.get_chips(order.id)
    # Deve ter chip de estado e de progresso
    assert len(chips) >= 1
    assert any(c.label == "Interpretando seu pedido..." for c in chips)


def test_confirm_intentions_invalid_state(manager):
    order = manager.create_order("session_123", "Teste")
    with pytest.raises(InvalidStateError):
        manager.confirm_intentions(order.id, [])


def test_full_flow(manager):
    # 1. Cria pedido
    order = manager.create_order("session_123", "Quero uma salada leve com tomate")
    assert order.current_state == OrderState.INTERPRETADO

    # Simula extração de intenções (normalmente feito pelo analista)
    event = manager.event_publisher.create_event(
        order_id=order.id,
        event_type=EventType.INTENTIONS_EXTRACTED.value,
        source="intent_analyzer",
        payload={
            "intentions": [
                {"type": "goal", "value": "receita leve", "confirmed": False},
                {"type": "ingredient", "value": "tomate", "confirmed": False}
            ]
        }
    )
    manager.event_publisher.publish(event)

    # Transição para AGUARDANDO_CONFIRMACAO
    manager._transition(order.id, EventType.INTENTIONS_EXTRACTED)
    assert manager.get_order(order.id).current_state == OrderState.AGUARDANDO_CONFIRMACAO

    # 2. Confirma intenções
    confirmed = manager.confirm_intentions(order.id, [
        {"id": "intent_0_tomate", "active": True},
        {"id": "intent_1_receita_leve", "active": True}
    ])
    assert confirmed.current_state == OrderState.EM_ELABORACAO

    # 3. Define proposta
    proposal = manager.set_proposal(order.id, "Receita de salada com tomate...")
    assert proposal.content == "Receita de salada com tomate..."
    assert manager.get_order(order.id).current_state == OrderState.EM_ANALISE

    # 4. Simula conclusão da análise (vai para DECISAO)
    manager._transition(order.id, EventType.ANALYSIS_COMPLETED)
    assert manager.get_order(order.id).current_state == OrderState.DECISAO

    # 5. Simula conflito (via request_decision)
    decision = manager.request_decision(
        order.id,
        "A receita ficou mais calórica do que o esperado. Deseja adaptar?",
        ["adaptar", "manter"]
    )
    assert decision.id.startswith("dec_")
    assert manager.get_order(order.id).current_state == OrderState.AGUARDANDO_DECISAO

    # 6. Cliente responde
    manager.submit_decision(order.id, decision.id, "adaptar")
    assert manager.get_order(order.id).current_state == OrderState.EM_REVISAO

    # 7. Conclui (simula revisão concluída e depois finaliza)
    manager._transition(order.id, EventType.REVISION_COMPLETED)
    assert manager.get_order(order.id).current_state == OrderState.EM_ANALISE

    # Simula nova análise concluída sem conflito
    manager._transition(order.id, EventType.ANALYSIS_COMPLETED)
    assert manager.get_order(order.id).current_state == OrderState.DECISAO

    # Sem conflito, vai para FINALIZANDO
    manager._transition(order.id, EventType.NO_CONFLICT)
    assert manager.get_order(order.id).current_state == OrderState.FINALIZANDO

    # Finaliza
    manager.finalize_order(order.id, {"result": "receita adaptada"})
    assert manager.get_order(order.id).current_state == OrderState.FINALIZADO