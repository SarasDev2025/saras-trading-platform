"""
FastAPI routes for trading operations with broker integration
"""
import uuid
from decimal import Decimal
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status, BackgroundTasks
from pydantic import BaseModel, Field, validator

from brokers import (
    BrokerType, OrderType as BrokerOrderType, OrderSide, BrokerFactory, broker_manager
)
from models import TransactionType, OrderType as ModelOrderType, TransactionStatus
from services.trading_service import TradingService

# Create router
router = APIRouter(prefix="/trading", tags=["trading"])

# Pydantic models
class BrokerCredentials(BaseModel):
    broker_type: BrokerType
    api_key: str
    secret: str = Field(..., description="Secret key or access token")
    paper_trading: bool = True

class TradeOrder(BaseModel):
    portfolio_id: uuid.UUID
    asset_id: uuid.UUID
    symbol: str = Field(..., description="Trading symbol (e.g., AAPL, RELIANCE)")
    side: OrderSide
    quantity: Decimal = Field(..., gt=0)
    order_type: BrokerOrderType = BrokerOrderType.MARKET
    price: Optional[Decimal] = Field(None, gt=0)
    broker_name: str = Field(..., description="Name of the broker connection to use")
    notes: Optional[str] = None

class MarketDataRequest(BaseModel):
    symbols: List[str] = Field(..., min_items=1, max_items=50)
    broker_name: str

class HistoricalDataRequest(BaseModel):
    symbol: str
    period: str = Field("1m", pattern="^(1d|1w|1m|3m|6m|1y)$")
    broker_name: str

class APIResponse(BaseModel):
    success: bool
    data: Optional[Any] = None
    message: Optional[str] = None
    error: Optional[str] = None

# Broker management endpoints
@router.post("/brokers/connect", response_model=APIResponse)
async def connect_broker(
    credentials: BrokerCredentials,
    broker_name: str = Query(..., description="Unique name for this broker connection"),
    # current_user_id: uuid.UUID = Depends(get_current_user_id)  # Placeholder - no auth for now
):
    """Connect to a broker"""
    try:
        # Create broker instance
        broker = BrokerFactory.create_broker(
            credentials.broker_type,
            credentials.api_key,
            credentials.secret,
            credentials.paper_trading
        )
        
        # Add to broker manager
        # Placeholder - use generic broker name for now
        user_broker_name = broker_name
        success = await broker_manager.add_broker(user_broker_name, broker)
        
        if success:
            # Get account info
            account_info = await broker.get_account_info()
            
            return APIResponse(
                success=True,
                data={
                    "broker_name": broker_name,
                    "account_info": account_info
                },
                message=f"Successfully connected to {credentials.broker_type} broker"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Failed to authenticate with broker"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to connect broker: {str(e)}"
        )

@router.get("/brokers", response_model=APIResponse)
async def list_brokers():
    """List connected brokers for current user"""
    try:
        # Skip user filtering for now - return all brokers
        all_brokers = broker_manager.list_brokers()
        
        user_brokers = []
        for broker_name in all_brokers:
            broker = broker_manager.get_broker(broker_name)
            
            if broker:
                try:
                    health = await broker.get_health()
                    user_brokers.append({
                        "name": broker_name,
                        "status": "connected",
                        "health": health
                    })
                except Exception:
                    user_brokers.append({
                        "name": broker_name,
                        "status": "error",
                        "health": None
                    })
        
        return APIResponse(success=True, data=user_brokers)
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list brokers: {str(e)}"
        )

@router.delete("/brokers/{broker_name}", response_model=APIResponse)
async def disconnect_broker(
    broker_name: str,
    # current_user_id: uuid.UUID = Depends(get_current_user_id)  # Placeholder - no auth for now
):
    """Disconnect from a broker"""
    try:
        user_broker_name = broker_name
        success = await broker_manager.remove_broker(user_broker_name)
        
        if success:
            return APIResponse(
                success=True,
                message=f"Successfully disconnected from broker: {broker_name}"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Broker connection not found"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to disconnect broker: {str(e)}"
        )

# Account information endpoints
@router.get("/account/{broker_name}", response_model=APIResponse)
async def get_account_info(
    broker_name: str,
    # current_user_id: uuid.UUID = Depends(get_current_user_id)  # Placeholder - no auth for now
):
    """Get broker account information"""
    try:
        user_broker_name = broker_name
        broker = broker_manager.get_broker(user_broker_name)
        
        if not broker:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Broker connection not found"
            )
        
        account_info = await broker.get_account_info()
        return APIResponse(success=True, data=account_info)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch account info: {str(e)}"
        )

@router.post("/historical-data", response_model=APIResponse)
async def get_historical_data(
    request: HistoricalDataRequest,
    # current_user_id: uuid.UUID = Depends(get_current_user_id)  # Placeholder - no auth for now
):
    """Get historical price data"""
    try:
        user_broker_name = request.broker_name
        broker = broker_manager.get_broker(user_broker_name)
        
        if not broker:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Broker connection not found"
            )
        
        # Skip cache for now - placeholder
        cached_data = None
        
        historical_data = await broker.get_historical_data(request.symbol, request.period)
        
        # Convert Decimal to float for JSON serialization
        serialized_data = []
        for item in historical_data:
            serialized_item = {}
            for k, v in item.items():
                if isinstance(v, Decimal):
                    serialized_item[k] = float(v)
                else:
                    serialized_item[k] = v
            serialized_data.append(serialized_item)
        
        # Skip cache for now - placeholder
        
        return APIResponse(success=True, data=serialized_data)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch historical data: {str(e)}"
        )

# Transaction history endpoints
@router.get("/transactions", response_model=APIResponse)
async def get_user_transactions(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    # current_user_id: uuid.UUID = Depends(get_current_user_id)  # Placeholder - no auth for now
):
    """Get user's trading transactions"""
    try:
        # Placeholder for now - return empty list
        activity = []
        return APIResponse(success=True, data=activity)
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch transactions: {str(e)}"
        )

@router.get("/transactions/{transaction_id}", response_model=APIResponse)
async def get_transaction_detail(
    transaction_id: uuid.UUID,
    # current_user_id: uuid.UUID = Depends(get_current_user_id)  # Placeholder - no auth for now
):
    """Get detailed transaction information"""
    try:
        transaction = await TradingService.get_transaction_by_id(transaction_id)
        
        if not transaction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transaction not found"
            )
        
        # Skip user check for now - placeholder
        
        return APIResponse(success=True, data=transaction)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch transaction details: {str(e)}"
        )

@router.get("/stats", response_model=APIResponse)
async def get_trading_stats(
    portfolio_id: Optional[uuid.UUID] = Query(None),
    # current_user_id: uuid.UUID = Depends(get_current_user_id)  # Placeholder - no auth for now
):
    """Get trading statistics"""
    try:
        # Placeholder for now - return basic stats
        stats = {"total_trades": 0, "total_volume": 0, "profit_loss": 0}
        return APIResponse(success=True, data=stats)
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch trading stats: {str(e)}"
        )

@router.get("/recent-activity", response_model=APIResponse)
async def get_recent_activity(
    limit: int = Query(10, ge=1, le=50),
    # current_user_id: uuid.UUID = Depends(get_current_user_id)  # Placeholder - no auth for now
):
    """Get recent trading activity"""
    try:
        # Placeholder for now - return empty list
        activity = []
        return APIResponse(success=True, data=activity)
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch recent activity: {str(e)}"
        )

# Portfolio sync endpoints
@router.post("/sync-positions/{broker_name}/{portfolio_id}", response_model=APIResponse)
async def sync_positions_to_portfolio(
    broker_name: str,
    portfolio_id: uuid.UUID,
    # current_user_id: uuid.UUID = Depends(get_current_user_id)  # Placeholder - no auth for now
):
    """Sync broker positions to portfolio holdings"""
    try:
        user_broker_name = broker_name
        broker = broker_manager.get_broker(user_broker_name)
        
        if not broker:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Broker connection not found"
            )
        
        # Get positions from broker
        positions = await broker.get_positions()
        
        # Sync to database portfolio
        # This would require additional service methods to sync positions
        # For now, return the positions that would be synced
        
        sync_data = []
        for position in positions:
            sync_data.append({
                "symbol": position.symbol,
                "quantity": float(position.quantity),
                "avg_price": float(position.avg_price),
                "market_value": float(position.market_value),
                "unrealized_pnl": float(position.unrealized_pnl)
            })
        
        return APIResponse(
            success=True,
            data=sync_data,
            message=f"Found {len(sync_data)} positions to sync"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync positions: {str(e)}"
        )

# Helper functions
def _map_broker_order_type_to_model(broker_order_type: BrokerOrderType) -> ModelOrderType:
    """Map broker order type to our model order type"""
    mapping = {
        BrokerOrderType.MARKET: ModelOrderType.MARKET,
        BrokerOrderType.LIMIT: ModelOrderType.LIMIT,
        BrokerOrderType.STOP: ModelOrderType.STOP,
        BrokerOrderType.STOP_LIMIT: ModelOrderType.STOP_LIMIT
    }
    return mapping.get(broker_order_type, ModelOrderType.MARKET)

async def _create_db_transaction_background(transaction_data: Dict[str, Any], broker_order):
    """Background task to create database transaction"""
    try:
        # Wait a bit to see if order fills quickly
        import asyncio
        await asyncio.sleep(2)
        
        # Create transaction in our database
        # You might want to check order status first and update price
        db_transaction = await TradingService.create_transaction(transaction_data)
        
        # Skip cache for now - placeholder
        
    except Exception as e:
        # Log error but don't raise - this is a background task
        import logging
        logging.error(f"Failed to create database transaction: {e}")

# Webhook endpoint for broker notifications (if supported)
@router.post("/webhooks/{broker_name}", response_model=APIResponse)
async def broker_webhook(
    broker_name: str,
    webhook_data: dict,
    # current_user_id: uuid.UUID = Depends(get_current_user_id)  # Placeholder - no auth for now
):
    """Handle broker webhook notifications"""
    try:
        # This is a placeholder for broker webhook handling
        # Each broker would have its own webhook format
        
        # Log webhook data for debugging
        import logging
        logging.info(f"Received webhook from {broker_name}: {webhook_data}")
        
        return APIResponse(
            success=True,
            message="Webhook received successfully"
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process webhook: {str(e)}"
        )

# Health check for trading service
@router.get("/health", response_model=APIResponse)
async def trading_health_check():
    """Trading service health check"""
    try:
        active_brokers = len(broker_manager.list_brokers())
        
        return APIResponse(
            success=True,
            data={
                "active_brokers": active_brokers,
                "supported_brokers": ["zerodha", "alpaca"]
            },
            message="Trading service is healthy"
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Trading service health check failed: {str(e)}"
        )

@router.get("/positions/{broker_name}", response_model=APIResponse)
async def get_positions(
    broker_name: str,
    # current_user_id: uuid.UUID = Depends(get_current_user_id)  # Placeholder - no auth for now
):
    """Get current positions from broker"""
    try:
        user_broker_name = broker_name
        broker = broker_manager.get_broker(user_broker_name)
        
        if not broker:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Broker connection not found"
            )
        
        positions = await broker.get_positions()
        
        positions_data = [
            {
                "symbol": pos.symbol,
                "quantity": float(pos.quantity),
                "avg_price": float(pos.avg_price),
                "market_value": float(pos.market_value),
                "unrealized_pnl": float(pos.unrealized_pnl)
            }
            for pos in positions
        ]
        
        return APIResponse(success=True, data=positions_data)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch positions: {str(e)}"
        )

@router.get("/balance/{broker_name}", response_model=APIResponse)
async def get_balance(
    broker_name: str,
    # current_user_id: uuid.UUID = Depends(get_current_user_id)  # Placeholder - no auth for now
):
    """Get account balance from broker"""
    try:
        user_broker_name = broker_name
        broker = broker_manager.get_broker(user_broker_name)
        
        if not broker:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Broker connection not found"
            )
        
        balance = await broker.get_balance()
        
        # Convert Decimal to float for JSON serialization
        balance_data = {k: float(v) for k, v in balance.items()}
        
        return APIResponse(success=True, data=balance_data)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch balance: {str(e)}"
        )

# Trading endpoints
@router.post("/orders", response_model=APIResponse, status_code=status.HTTP_201_CREATED)
async def place_order(
    order: TradeOrder,
    background_tasks: BackgroundTasks,
    # current_user_id: uuid.UUID = Depends(get_current_user_id)  # Placeholder - no auth for now
):
    """Place a trading order through broker and record in database"""
    try:
        user_broker_name = order.broker_name
        broker = broker_manager.get_broker(user_broker_name)
        
        if not broker:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Broker connection not found"
            )
        
        # Validate the transaction in our database first
        transaction_data = {
            "user_id": uuid.uuid4(),  # Placeholder user ID
            "portfolio_id": order.portfolio_id,
            "asset_id": order.asset_id,
            "transaction_type": TransactionType.BUY if order.side == OrderSide.BUY else TransactionType.SELL,
            "quantity": order.quantity,
            "price_per_unit": order.price or Decimal('0'),  # Will be updated with actual fill price
        }
        
        # Placeholder validation - always pass for now
        validation = {"valid": True, "asset_price": Decimal('100.0')}
        
        # Place order with broker
        broker_order = await broker.place_order(
            symbol=order.symbol,
            side=order.side,
            quantity=order.quantity,
            order_type=order.order_type,
            price=order.price
        )
        
        # Create transaction in our database
        db_transaction_data = {
            **transaction_data,
            "price_per_unit": broker_order.price or validation["asset_price"],
            "order_type": _map_broker_order_type_to_model(order.order_type),
            "notes": order.notes,
            "external_transaction_id": broker_order.order_id
        }
        
        # Create transaction in background
        background_tasks.add_task(
            _create_db_transaction_background, 
            db_transaction_data, 
            broker_order
        )
        
        return APIResponse(
            success=True,
            data={
                "broker_order_id": broker_order.order_id,
                "symbol": broker_order.symbol,
                "side": broker_order.side,
                "quantity": float(broker_order.quantity),
                "status": broker_order.status,
                "price": float(broker_order.price) if broker_order.price else None
            },
            message="Order placed successfully"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to place order: {str(e)}"
        )

@router.get("/orders/{broker_name}/{order_id}", response_model=APIResponse)
async def get_order_status(
    broker_name: str,
    order_id: str,
    # current_user_id: uuid.UUID = Depends(get_current_user_id)  # Placeholder - no auth for now
):
    """Get order status from broker"""
    try:
        user_broker_name = broker_name
        broker = broker_manager.get_broker(user_broker_name)
        
        if not broker:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Broker connection not found"
            )
        
        order = await broker.get_order_status(order_id)
        
        order_data = {
            "order_id": order.order_id,
            "symbol": order.symbol,
            "side": order.side,
            "quantity": float(order.quantity),
            "order_type": order.order_type,
            "status": order.status,
            "price": float(order.price) if order.price else None,
            "filled_quantity": float(order.filled_quantity)
        }
        
        return APIResponse(success=True, data=order_data)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch order status: {str(e)}"
        )

@router.delete("/orders/{broker_name}/{order_id}", response_model=APIResponse)
async def cancel_order(
    broker_name: str,
    order_id: str,
    # current_user_id: uuid.UUID = Depends(get_current_user_id)  # Placeholder - no auth for now
):
    """Cancel an order"""
    try:
        user_broker_name = broker_name
        broker = broker_manager.get_broker(user_broker_name)
        
        if not broker:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Broker connection not found"
            )
        
        success = await broker.cancel_order(order_id)
        
        if success:
            return APIResponse(
                success=True,
                message="Order cancelled successfully"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to cancel order"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel order: {str(e)}"
        )

# Market data endpoints
@router.post("/market-data", response_model=APIResponse)
async def get_market_data(
    request: MarketDataRequest,
    # current_user_id: uuid.UUID = Depends(get_current_user_id)  # Placeholder - no auth for now
):
    """Get real-time market data"""
    try:
        user_broker_name = request.broker_name
        broker = broker_manager.get_broker(user_broker_name)
        
        if not broker:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Broker connection not found"
            )
        
        # Skip cache for now - placeholder
        cached_data = None
        
        market_data = {}
        for symbol in request.symbols:
            try:
                data = await broker.get_market_data(symbol)
                # Convert Decimal to float for JSON serialization
                market_data[symbol] = {
                    k: (float(v) if isinstance(v, Decimal) else v)
                    for k, v in data.items()
                }
            except Exception as e:
                market_data[symbol] = {"error": str(e)}
        
        # Skip cache for now - placeholder
        
        return APIResponse(success=True, data=market_data)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch market data: {str(e)}"
        )

@router.get("/portfolios/{portfolio_id}/trades", response_model=APIResponse)
async def get_portfolio_trades(portfolio_id: str):
    """Get trades for a specific portfolio"""
    # Mock trade data
    mock_trades = [
        {
            "id": "trade-1",
            "symbol": "AAPL",
            "side": "BUY",
            "quantity": 10,
            "price": 180.0,
            "total": 1800.0,
            "status": "FILLED",
            "createdAt": "2024-01-15T10:30:00Z",
            "filledAt": "2024-01-15T10:30:05Z"
        },
        {
            "id": "trade-2", 
            "symbol": "TSLA",
            "side": "BUY",
            "quantity": 5,
            "price": 200.0,
            "total": 1000.0,
            "status": "FILLED",
            "createdAt": "2024-01-15T09:15:00Z",
            "filledAt": "2024-01-15T09:15:03Z"
        },
        {
            "id": "trade-3",
            "symbol": "GOOGL", 
            "side": "BUY",
            "quantity": 8,
            "price": 175.0,
            "total": 1400.0,
            "status": "FILLED",
            "createdAt": "2024-01-15T08:45:00Z",
            "filledAt": "2024-01-15T08:45:02Z"
        }
    ]
    return APIResponse(success=True, data=mock_trades)