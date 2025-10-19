"""
GTT Order Router - Endpoints for Zerodha GTT, Basket, and OCO orders
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import List, Dict, Any, Annotated, Optional
from decimal import Decimal
from pydantic import BaseModel, Field
import logging

from config.database import get_db
from system.dependencies.enhanced_auth_deps import get_enhanced_current_user
from services.gtt_order_service import GTTOrderService
from models import APIResponse

router = APIRouter(tags=["gtt-orders"], prefix="/orders/gtt")
logger = logging.getLogger(__name__)


# Pydantic models for request validation
class GTTOrderRequest(BaseModel):
    broker_connection_id: str = Field(..., description="User's broker connection ID")
    symbol: str = Field(..., description="Trading symbol (e.g., RELIANCE, TCS)")
    side: str = Field(..., description="Order side: BUY or SELL")
    quantity: Decimal = Field(..., gt=0, description="Number of shares")
    trigger_price: Decimal = Field(..., gt=0, description="Price at which order should trigger")
    limit_price: Optional[Decimal] = Field(None, description="Limit price (None for market order)")
    trigger_type: str = Field("single", description="single or two-leg")
    product: str = Field("CNC", description="Product type: CNC, MIS, NRML")


class BasketOrderItem(BaseModel):
    symbol: str
    side: str
    quantity: Decimal
    order_type: str = "MARKET"
    price: Optional[Decimal] = None
    trigger_price: Optional[Decimal] = None
    product: str = "CNC"
    validity: str = "DAY"


class BasketOrderRequest(BaseModel):
    broker_connection_id: str
    orders: List[BasketOrderItem] = Field(..., max_items=20, description="Up to 20 orders")


class OCOOrderRequest(BaseModel):
    broker_connection_id: str
    symbol: str
    side: str
    quantity: Decimal = Field(..., gt=0)
    target_price: Decimal = Field(..., gt=0, description="Target profit price")
    stop_loss_price: Decimal = Field(..., gt=0, description="Stop loss price")
    product: str = Field("CNC", description="Product type: CNC, MIS, NRML")


@router.post("/place", response_model=APIResponse)
async def place_gtt_order(
    request: GTTOrderRequest,
    current_user: Annotated[Dict[str, Any], Depends(get_enhanced_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """
    Place a GTT (Good Till Triggered) order with Zerodha

    GTT orders remain active up to 1 year and execute when trigger price is hit.
    Funds are NOT locked until the order triggers.

    **Parameters:**
    - **symbol**: Stock symbol (e.g., RELIANCE, TCS, INFY)
    - **side**: BUY or SELL
    - **quantity**: Number of shares
    - **trigger_price**: Price at which order should trigger
    - **limit_price**: Limit price when triggered (None for market order)
    - **trigger_type**: 'single' for basic GTT, 'two-leg' for OCO
    - **product**: CNC (delivery), MIS (intraday), NRML (normal)

    **Example:**
    ```json
    {
        "broker_connection_id": "uuid",
        "symbol": "RELIANCE",
        "side": "BUY",
        "quantity": 10,
        "trigger_price": 2500.00,
        "limit_price": 2505.00,
        "trigger_type": "single",
        "product": "CNC"
    }
    ```
    """
    user_id = str(current_user["id"])

    try:
        user_id = str(current_user["id"])

        # Validate side
        if request.side.upper() not in ["BUY", "SELL"]:
            raise HTTPException(status_code=400, detail="Side must be BUY or SELL")

        # Validate trigger type
        if request.trigger_type not in ["single", "two-leg"]: # Correct the logical error?
            raise HTTPException(status_code=400, detail="Trigger type must be 'single' or 'two-leg'")

        # Validate product type
        valid_products = ["CNC", "MIS", "NRML", "CO", "BO"]
        if request.product.upper() not in valid_products:
            raise HTTPException(status_code=400, detail=f"Product must be one of: {', '.join(valid_products)}")

        # Verify broker connection belongs to user
        verify_broker = await db.execute(
            text("SELECT user_id FROM user_broker_connections WHERE id = :id"),
            {"id": request.broker_connection_id}
        )
        broker_conn = verify_result.fetchone()
        if not broker_conn or str(broker_conn.user_id) != user_id:
            raise HTTPException(status_code=403, detail="Broker connection not found or unauthorized")

        logger.info(f"User {user_id} placing GTT order for {request.symbol}")

    
        result = await GTTOrderService.place_gtt_order(
            db=db,
            broker_connection_id=request.broker_connection_id,
            symbol=request.symbol,
            side=request.side,
            quantity=request.quantity,
            trigger_price=request.trigger_price,
            limit_price=request.limit_price,
            trigger_type=request.trigger_type,
            product=request.product
        )

        return APIResponse(
            success=True,
            data=result,
            message=f"GTT order placed successfully for {request.symbol}"
        )

    except ValueError as e:
        logger.error(f"Validation error placing GTT order: {e}")
    except HTTPException as e:
        raise e
    except ValueError as e: # Handling specific exceptions before generic ones
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to place GTT order: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to place GTT order: {str(e)}")


@router.get("/list", response_model=APIResponse)
async def list_gtt_orders(
    broker_connection_id: str,
    current_user: Annotated[Dict[str, Any], Depends(get_enhanced_current_user)],
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db)

):
    """
    List GTT orders for a broker connection

    **Query Parameters:**
    - **broker_connection_id**: User's broker connection ID (required)
    - **status**: Filter by status (active, triggered, cancelled, expired)

    **Returns:**
    List of GTT orders with details including trigger price, status, and expiry
    """
    try:
        user_id = str(current_user["id"])

        # Verify broker connection belongs to user
        verify_result = await db.execute(
            text("SELECT user_id FROM user_broker_connections WHERE id = :id"),
            {"id": broker_connection_id}
        )
        broker_conn = verify_result.fetchone()
        if not broker_conn or str(broker_conn.user_id) != user_id:
            raise HTTPException(status_code=403, detail="Broker connection not found or unauthorized")

        orders = await GTTOrderService.get_gtt_orders(
            db=db,
            broker_connection_id=broker_connection_id,
            status=status
        )

        return APIResponse(
            success=True,
            data=orders,
            message=f"Found {len(orders)} GTT orders"
        )

    except Exception as e:
        logger.error(f"Failed to list GTT orders: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list GTT orders: {str(e)}")


@router.delete("/{trigger_id}/cancel", response_model=APIResponse)
async def cancel_gtt_order(
    trigger_id: str,
    broker_connection_id: str,
    current_user: Annotated[Dict[str, Any], Depends(get_enhanced_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """
    Cancel a GTT order

    **Path Parameters:**
    - **trigger_id**: Zerodha GTT trigger ID

    **Query Parameters:**
    - **broker_connection_id**: User's broker connection ID
    """
    try:
        user_id = str(current_user["id"])

        # Verify broker connection belongs to user
        verify_result = await db.execute(
            text("SELECT user_id FROM user_broker_connections WHERE id = :id"),
            {"id": broker_connection_id}
        )
        broker_conn = verify_result.fetchone()
        if not broker_conn or str(broker_conn.user_id) != user_id:
            raise HTTPException(status_code=403, detail="Broker connection not found or unauthorized")

        logger.info(f"User {user_id} cancelling GTT order {trigger_id}")

        success = await GTTOrderService.cancel_gtt_order(
            db=db,
            broker_connection_id=broker_connection_id,
            trigger_id=trigger_id
        )

        if success:
            return APIResponse(
                success=True,
                data={"trigger_id": trigger_id, "status": "cancelled"},
                message="GTT order cancelled successfully"
            )
        else:
            raise HTTPException(status_code=400, detail="Failed to cancel GTT order")

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to cancel GTT order: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to cancel GTT order: {str(e)}")


@router.post("/basket/place", response_model=APIResponse)
async def place_basket_order(
    request: BasketOrderRequest,
    current_user: Annotated[Dict[str, Any], Depends(get_enhanced_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """
    Place a basket order with multiple stocks (up to 20 orders)

    Basket orders allow you to place multiple orders simultaneously, which is ideal
    for executing smallcase portfolios efficiently.

    **Parameters:**
    - **broker_connection_id**: User's broker connection ID
    - **orders**: List of up to 20 order specifications

    **Example:**
    ```json
    {
        "broker_connection_id": "uuid",
        "orders": [
            {
                "symbol": "RELIANCE",
                "side": "BUY",
                "quantity": 10,
                "order_type": "MARKET",
                "product": "CNC"
            },
            {
                "symbol": "TCS",
                "side": "BUY",
                "quantity": 5,
                "order_type": "LIMIT",
                "price": 3500.00,
                "product": "CNC"
            }
        ]
    }
    ```
    """
    try:
        user_id = str(current_user["id"])

        if len(request.orders) > 20:
            raise HTTPException(status_code=400, detail="Maximum 20 orders allowed in basket")

        if len(request.orders) == 0:
            raise HTTPException(status_code=400, detail="At least 1 order required")

        # Verify broker connection belongs to user
        verify_result = await db.execute(
            text("SELECT user_id FROM user_broker_connections WHERE id = :id"),
            {"id": request.broker_connection_id}
        )
        broker_conn = verify_result.fetchone()
        if not broker_conn or str(broker_conn.user_id) != user_id:
            raise HTTPException(status_code=403, detail="Broker connection not found or unauthorized")

        # Convert Pydantic models to dict
        orders_dict = [order.dict() for order in request.orders]

        logger.info(f"User {user_id} placing basket order with {len(orders_dict)} orders")

        result = await GTTOrderService.place_basket_order(
            db=db,
            broker_connection_id=request.broker_connection_id,
            orders=orders_dict
        )

        return APIResponse(
            success=True,
            data=result,
            message=f"Basket order placed: {result['success_count']} succeeded, {result['failure_count']} failed"
        )

    except ValueError as e:
        logger.error(f"Validation error placing basket order: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to place basket order: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to place basket order: {str(e)}")


@router.post("/oco/place", response_model=APIResponse)
async def place_oco_order(
    request: OCOOrderRequest,
    current_user: Annotated[Dict[str, Any], Depends(get_enhanced_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """
    Place an OCO (One-Cancels-Other) order using Zerodha GTT two-leg feature

    OCO orders are advanced orders that automatically manage both profit targets
    and stop losses. When one leg is triggered, the other is automatically cancelled.

    **Use Cases:**
    - Automatic profit booking at target price
    - Stop loss protection
    - Hands-free position management

    **Parameters:**
    - **symbol**: Stock symbol
    - **side**: BUY or SELL (typically SELL for profit/loss management)
    - **quantity**: Number of shares
    - **target_price**: Price for profit booking
    - **stop_loss_price**: Price for loss protection
    - **product**: CNC, MIS, or NRML

    **Example:**
    ```json
    {
        "broker_connection_id": "uuid",
        "symbol": "RELIANCE",
        "side": "SELL",
        "quantity": 10,
        "target_price": 2600.00,
        "stop_loss_price": 2400.00,
        "product": "CNC"
    }
    ```
    """
    try:
        user_id = str(current_user["id"])

        # Validate side
        if request.side.upper() not in ["BUY", "SELL"]:
            raise HTTPException(status_code=400, detail="Side must be BUY or SELL")

        # Verify broker connection belongs to user
        verify_result = await db.execute(
            text("SELECT user_id FROM user_broker_connections WHERE id = :id"),
            {"id": request.broker_connection_id}
        )
        broker_conn = verify_result.fetchone()
        if not broker_conn or str(broker_conn.user_id) != user_id:
            raise HTTPException(status_code=403, detail="Broker connection not found or unauthorized")

        logger.info(f"User {user_id} placing OCO order for {request.symbol}")

        result = await GTTOrderService.place_oco_order(
            db=db,
            broker_connection_id=request.broker_connection_id,
            symbol=request.symbol,
            side=request.side,
            quantity=request.quantity,
            target_price=request.target_price,
            stop_loss_price=request.stop_loss_price,
            product=request.product
        )

        return APIResponse(
            success=True,
            data=result,
            message=f"OCO order placed successfully for {request.symbol}"
        )

    except ValueError as e:
        logger.error(f"Validation error placing OCO order: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to place OCO order: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to place OCO order: {str(e)}")


@router.get("/oco/list", response_model=APIResponse)
async def list_oco_orders(
    broker_connection_id: str,
    current_user: Annotated[Dict[str, Any], Depends(get_enhanced_current_user)],
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    List OCO orders for a broker connection

    **Query Parameters:**
    - **broker_connection_id**: User's broker connection ID (required)
    - **status**: Filter by status (active, target_hit, stop_hit, cancelled, expired)
    """
    try:
        user_id = str(current_user["id"])

        # Verify broker connection belongs to user
        verify_result = await db.execute(
            text("SELECT user_id FROM user_broker_connections WHERE id = :id"),
            {"id": broker_connection_id}
        )
        broker_conn = verify_result.fetchone()
        if not broker_conn or str(broker_conn.user_id) != user_id:
            raise HTTPException(status_code=403, detail="Broker connection not found or unauthorized")

        orders = await GTTOrderService.get_oco_orders(
            db=db,
            broker_connection_id=broker_connection_id,
            status=status
        )

        return APIResponse(
            success=True,
            data=orders,
            message=f"Found {len(orders)} OCO orders"
        )

    except Exception as e:
        logger.error(f"Failed to list OCO orders: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list OCO orders: {str(e)}")


# Health check endpoint for GTT system
@router.get("/health", response_model=APIResponse)
async def gtt_health_check(db: AsyncSession = Depends(get_db)):
    """
    Health check for GTT order system

    Returns statistics about GTT orders in the system
    """
    try:
        from sqlalchemy import text

        # Get statistics
        stats_result = await db.execute(text("""
            SELECT
                COUNT(*) FILTER (WHERE status = 'active') as active_gtt,
                COUNT(*) FILTER (WHERE status = 'triggered') as triggered_gtt,
                COUNT(*) FILTER (WHERE status = 'cancelled') as cancelled_gtt,
                COUNT(*) as total_gtt
            FROM gtt_orders
            WHERE is_active = true
        """))

        stats = stats_result.fetchone()

        return APIResponse(
            success=True,
            data={
                "gtt_system": "operational",
                "active_orders": stats.active_gtt if stats else 0,
                "triggered_orders": stats.triggered_gtt if stats else 0,
                "cancelled_orders": stats.cancelled_gtt if stats else 0,
                "total_orders": stats.total_gtt if stats else 0
            },
            message="GTT order system is operational"
        )

    except Exception as e:
        logger.error(f"GTT health check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


__all__ = ["router"]
