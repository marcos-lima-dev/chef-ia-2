from typing import List, Callable, Dict, Any
from app.domain.models.event import Event
import uuid
from datetime import datetime


class EventPublisher:
    """Publicador de eventos in-memory. Futuramente substituído por Redis/Kafka."""

    def __init__(self):
        self._handlers: Dict[str, List[Callable]] = {}
        self._events: List[Event] = []

    def subscribe(self, event_type: str, handler: Callable):
        """Registra um handler para um tipo de evento."""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    def publish(self, event: Event) -> None:
        """Publica um evento e notifica os handlers."""
        # Armazena o evento
        self._events.append(event)

        # Notifica handlers
        if event.type.value in self._handlers:
            for handler in self._handlers[event.type.value]:
                handler(event)

    def get_events(self, order_id: str) -> List[Event]:
        """Retorna todos os eventos de um pedido."""
        return [e for e in self._events if e.order_id == order_id]

    def create_event(
        self,
        order_id: str,
        event_type: str,
        source: str,
        payload: Dict[str, Any] = None
    ) -> Event:
        """Cria um novo evento."""
        return Event(
            id=f"evt_{uuid.uuid4().hex[:12]}",
            order_id=order_id,
            type=event_type,
            source=source,
            payload=payload or {},
            timestamp=datetime.now()
        )