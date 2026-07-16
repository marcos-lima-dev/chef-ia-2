from fastapi import APIRouter, HTTPException, Depends
from app.api.schemas.order import (
    OrderCreateRequest,
    OrderCreateResponse,
    ChipConfirmRequest,
    OrderStateResponse,
    OrderResultResponse,
)
from app.services.order_orchestrator import OrderOrchestrator
from app.core.exceptions import OrderNotFoundError, InvalidStateError

router = APIRouter(prefix="/api/v1/orders", tags=["orders"])

# 🔥 Instância única (singleton) do orquestrador
_orchestrator = OrderOrchestrator()

def get_orchestrator():
    """Retorna a mesma instância do orquestrador para todas as requisições."""
    return _orchestrator


@router.post("/", response_model=OrderCreateResponse)
async def create_order(
    request: OrderCreateRequest,
    orchestrator: OrderOrchestrator = Depends(get_orchestrator),
):
    """Cria um novo pedido e inicia o workflow."""
    try:
        result = orchestrator.create_order("session_default", request.message)
        return OrderCreateResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{order_id}", response_model=OrderStateResponse)
async def get_order_state(
    order_id: str,
    orchestrator: OrderOrchestrator = Depends(get_orchestrator),
):
    """Retorna o estado atual do pedido."""
    try:
        state = orchestrator.get_order_state(order_id)
        return OrderStateResponse(**state)
    except OrderNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{order_id}/confirm")
async def confirm_intentions(
    order_id: str,
    request: ChipConfirmRequest,
    orchestrator: OrderOrchestrator = Depends(get_orchestrator),
):
    """Confirma as intenções do cliente e retoma o workflow."""
    try:
        result = orchestrator.confirm_intentions(order_id, request.chips)
        return result
    except OrderNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except InvalidStateError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{order_id}/result", response_model=OrderResultResponse)
async def get_result(
    order_id: str,
    orchestrator: OrderOrchestrator = Depends(get_orchestrator),
):
    """Obtém o resultado final do pedido."""
    try:
        result = orchestrator.get_result(order_id)
        return OrderResultResponse(**result)
    except OrderNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except InvalidStateError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))