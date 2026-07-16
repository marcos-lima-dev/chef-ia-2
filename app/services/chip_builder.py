from typing import List
from app.domain.models.chip import Chip
from app.domain.models.event import Event
from app.domain.models.order import Order
from app.domain.enums import EventType, ChipState, ChipCategory, OrderState


class ChipBuilder:
    """Constrói chips para exibição ao cliente baseado no estado e eventos."""

    @staticmethod
    def build_from_order(order: Order, events: List[Event]) -> List[Chip]:
        """Gera a lista de chips atuais."""
        chips = []

        # Chips baseados no estado
        state_chips = ChipBuilder._build_state_chips(order.current_state)
        chips.extend(state_chips)

        # Chips baseados em eventos recentes
        event_chips = ChipBuilder._build_event_chips(events)
        chips.extend(event_chips)

        # Chips de intenções (se houver)
        intention_chips = ChipBuilder._build_intention_chips(events)
        chips.extend(intention_chips)

        return chips

    @staticmethod
    def _build_state_chips(state: OrderState) -> List[Chip]:
        chips = []
        state_messages = {
            OrderState.RECEBIDO: "Pedido recebido",
            OrderState.INTERPRETADO: "Interpretando seu pedido...",
            OrderState.AGUARDANDO_CONFIRMACAO: "Confirme as informações abaixo",
            OrderState.EM_ELABORACAO: "Chef está criando sua receita",
            OrderState.EM_ANALISE: "Especialistas estão analisando",
            OrderState.AGUARDANDO_DECISAO: "Aguardando sua decisão",
            OrderState.EM_REVISAO: "Chef está revisando",
            OrderState.FINALIZANDO: "Preparando resposta final",
            OrderState.FINALIZADO: "Pedido concluído",
        }
        if state in state_messages:
            chips.append(Chip(
                id=f"state_{state.value}",
                label=state_messages[state],
                category=ChipCategory.PROGRESS,
                state=ChipState.ACTIVE if state != OrderState.FINALIZADO else ChipState.COMPLETED
            ))
        return chips

    @staticmethod
    def _build_event_chips(events: List[Event]) -> List[Chip]:
        chips = []
        for event in events:
            label = None
            if event.type == EventType.PROPOSAL_CREATED:
                label = "Proposta criada"
            elif event.type == EventType.ANALYSIS_COMPLETED:
                label = f"Análise de {event.payload.get('specialist', 'especialista')} concluída"
            elif event.type == EventType.GOAL_CONFLICT_FOUND:
                label = "⚠️ Conflito de objetivo detectado"
            elif event.type == EventType.CUSTOMER_DECISION_REQUIRED:
                label = "❓ Decisão necessária"
            elif event.type == EventType.RESULT_READY:
                label = "✅ Resposta pronta"

            if label:
                chips.append(Chip(
                    id=f"event_{event.id}",
                    label=label,
                    category=ChipCategory.EVENT,
                    state=ChipState.COMPLETED if event.type != EventType.CUSTOMER_DECISION_REQUIRED else ChipState.WAITING
                ))
        return chips

    @staticmethod
    def _build_intention_chips(events: List[Event]) -> List[Chip]:
        chips = []
        # Procura evento de intenções extraídas
        for event in events:
            if event.type == EventType.INTENTIONS_EXTRACTED:
                intentions = event.payload.get("intentions", [])
                for idx, intention in enumerate(intentions):
                    chips.append(Chip(
                        id=f"intent_{idx}_{intention['value']}",
                        label=intention["value"],
                        category=ChipCategory(intention["type"]) if intention["type"] in ["ingredient", "goal", "restriction", "preference"] else ChipCategory.GOAL,
                        state=ChipState.ACTIVE if not intention.get("confirmed", False) else ChipState.COMPLETED
                    ))
                break
        return chips