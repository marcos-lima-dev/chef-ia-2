from typing import Dict, Tuple
from app.domain.enums import OrderState, EventType


class InvalidTransitionError(Exception):
    pass


# Mapeamento de transições válidas (baseado no documento 08-state-machine.md)
TRANSITIONS: Dict[Tuple[OrderState, EventType], OrderState] = {
    (OrderState.RECEBIDO, EventType.ORDER_CREATED): OrderState.INTERPRETADO,
    (OrderState.INTERPRETADO, EventType.INTENTIONS_EXTRACTED): OrderState.AGUARDANDO_CONFIRMACAO,
    (OrderState.AGUARDANDO_CONFIRMACAO, EventType.INTENTIONS_CONFIRMED): OrderState.EM_ELABORACAO,
    (OrderState.EM_ELABORACAO, EventType.PROPOSAL_CREATED): OrderState.EM_ANALISE,
    (OrderState.EM_ANALISE, EventType.ANALYSIS_COMPLETED): OrderState.DECISAO,
    (OrderState.DECISAO, EventType.CONFLICT_FOUND): OrderState.AGUARDANDO_DECISAO,
    (OrderState.DECISAO, EventType.NO_CONFLICT): OrderState.FINALIZANDO,
    (OrderState.AGUARDANDO_DECISAO, EventType.CUSTOMER_DECISION_RECEIVED): OrderState.EM_REVISAO,
    (OrderState.EM_REVISAO, EventType.REVISION_COMPLETED): OrderState.EM_ANALISE,
    (OrderState.FINALIZANDO, EventType.FINAL_RESPONSE_CREATED): OrderState.FINALIZADO,
}


class StateMachine:
    @staticmethod
    def can_transition(from_state: OrderState, event: EventType) -> bool:
        return (from_state, event) in TRANSITIONS

    @staticmethod
    def transition(from_state: OrderState, event: EventType) -> OrderState:
        if not StateMachine.can_transition(from_state, event):
            raise InvalidTransitionError(
                f"Transição inválida de '{from_state.value}' com evento '{event.value}'"
            )
        return TRANSITIONS[(from_state, event)]

    @staticmethod
    def is_terminal(state: OrderState) -> bool:
        return state == OrderState.FINALIZADO

    @staticmethod
    def is_waiting_for_client(state: OrderState) -> bool:
        return state in [
            OrderState.AGUARDANDO_CONFIRMACAO,
            OrderState.AGUARDANDO_DECISAO,
        ]