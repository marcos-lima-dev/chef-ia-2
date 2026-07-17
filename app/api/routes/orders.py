from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.api.schemas.order import (
    OrderCreateRequest,
    OrderCreateResponse,
    ChipConfirmRequest,
    OrderStateResponse,
    OrderResultResponse,
)
from app.services.order_orchestrator_persistent import OrderOrchestratorPersistent
from app.core.exceptions import OrderNotFoundError, InvalidStateError
from app.infrastructure.database.base import get_db

router = APIRouter(prefix="/api/v1/orders", tags=["orders"])

@router.post("/", response_model=OrderCreateResponse)
async def create_order(
    request: OrderCreateRequest,
    db: Session = Depends(get_db),
):
    try:
        orchestrator = OrderOrchestratorPersistent(db)
        result = orchestrator.create_order("session_default", request.message)
        return OrderCreateResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{order_id}", response_model=OrderStateResponse)
async def get_order_state(
    order_id: str,
    db: Session = Depends(get_db),
):
    try:
        orchestrator = OrderOrchestratorPersistent(db)
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
    db: Session = Depends(get_db),
):
    try:
        orchestrator = OrderOrchestratorPersistent(db)
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
    db: Session = Depends(get_db),
):
    try:
        orchestrator = OrderOrchestratorPersistent(db)
        result = orchestrator.get_result(order_id)
        return OrderResultResponse(**result)
    except OrderNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except InvalidStateError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
