"""
GTT Order Service - Manages Good Till Triggered orders for Zerodha
Handles GTT, basket, and OCO order operations with database tracking
"""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Any, Optional
from uuid import UUID
import uuid
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from brokers.zerodha import ZerodhaBroker
from brokers.base import OrderSide

logger = logging.getLogger(__name__)


class GTTOrderService:
    """Service for managing GTT (Good Till Triggered) orders"""

    @staticmethod
    async def place_gtt_order(
        db: AsyncSession,
        broker_connection_id: str,
        symbol: str,
        side: str,
        quantity: Decimal,
        trigger_price: Decimal,
        limit_price: Optional[Decimal] = None,
        trigger_type: str = "single",
        product: str = "CNC"
    ) -> Dict[str, Any]:
        """
        Place a GTT order with Zerodha

        Args:
            db: Database session
            broker_connection_id: User's broker connection ID
            symbol: Trading symbol
            side: BUY or SELL
            quantity: Number of shares
            trigger_price: Price at which order should trigger
            limit_price: Limit price for triggered order (None for market)
            trigger_type: 'single' or 'two-leg'
            product: Product type (CNC, MIS, NRML)

        Returns:
            Dictionary with GTT order details
        """
        try:
            # Get broker connection details
            connection_result = await db.execute(text("""
                SELECT ubc.broker_type, ubc.api_key, ubc.api_secret, ubc.credentials,
                       ubc.paper_trading, ubc.status, ubc.user_id
                FROM user_broker_connections ubc
                WHERE ubc.id = :broker_connection_id
            """), {"broker_connection_id": broker_connection_id})

            connection = connection_result.fetchone()
            if not connection:
                raise ValueError(f"Broker connection {broker_connection_id} not found")

            if connection.broker_type != "zerodha":
                raise ValueError(f"GTT orders are only supported for Zerodha broker")

            if connection.status != "active":
                raise ValueError(f"Broker connection is not active: {connection.status}")

            # Extract credentials from JSONB or direct columns
            credentials = connection.credentials or {}
            api_key = connection.api_key or credentials.get("api_key", "test_key")
            access_token = credentials.get("access_token") or "paper_trading_token"

            # Initialize Zerodha broker
            broker = ZerodhaBroker(
                api_key=api_key,
                access_token=access_token,
                paper_trading=connection.paper_trading
            )

            # Authenticate
            await broker.authenticate()

            # Place GTT order
            order_side = OrderSide.BUY if side.upper() == "BUY" else OrderSide.SELL
            gtt_response = await broker.place_gtt_order(
                symbol=symbol,
                side=order_side,
                quantity=quantity,
                trigger_price=trigger_price,
                limit_price=limit_price,
                trigger_type=trigger_type,
                product=product
            )

            # Determine exchange
            exchange = broker._determine_exchange(symbol)

            # Store GTT order in database
            gtt_id = str(uuid.uuid4())
            await db.execute(text("""
                INSERT INTO gtt_orders
                (id, broker_connection_id, trigger_id, symbol, exchange, side,
                 quantity, trigger_price, limit_price, trigger_type, product,
                 status, created_at, expires_at)
                VALUES
                (:id, :broker_connection_id, :trigger_id, :symbol, :exchange, :side,
                 :quantity, :trigger_price, :limit_price, :trigger_type, :product,
                 'active', :created_at, :expires_at)
            """), {
                "id": gtt_id,
                "broker_connection_id": broker_connection_id,
                "trigger_id": gtt_response["trigger_id"],
                "symbol": symbol.upper(),
                "exchange": exchange,
                "side": side.upper(),
                "quantity": float(quantity),
                "trigger_price": float(trigger_price),
                "limit_price": float(limit_price) if limit_price else None,
                "trigger_type": trigger_type,
                "product": product,
                "created_at": datetime.fromisoformat(gtt_response["created_at"]),
                "expires_at": datetime.fromisoformat(gtt_response["expires_at"])
            })

            await db.commit()

            logger.info(f"GTT order placed: {gtt_response['trigger_id']} for {symbol}")

            return {
                "gtt_id": gtt_id,
                "trigger_id": gtt_response["trigger_id"],
                "symbol": symbol.upper(),
                "side": side.upper(),
                "quantity": float(quantity),
                "trigger_price": float(trigger_price),
                "limit_price": float(limit_price) if limit_price else None,
                "trigger_type": trigger_type,
                "product": product,
                "status": "active",
                "created_at": gtt_response["created_at"],
                "expires_at": gtt_response["expires_at"],
                "paper_trading": connection.paper_trading
            }

        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to place GTT order: {e}")
            raise

    @staticmethod
    async def get_gtt_orders(
        db: AsyncSession,
        broker_connection_id: str,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get GTT orders for a broker connection"""
        try:
            query = """
                SELECT
                    id, trigger_id, symbol, exchange, side, quantity,
                    trigger_price, limit_price, trigger_type, product,
                    status, created_at, triggered_at, expires_at, order_id
                FROM gtt_orders
                WHERE broker_connection_id = :broker_connection_id
                  AND is_active = true
            """

            params = {"broker_connection_id": broker_connection_id}

            if status:
                query += " AND status = :status"
                params["status"] = status

            query += " ORDER BY created_at DESC"

            result = await db.execute(text(query), params)
            rows = result.fetchall()

            orders = []
            for row in rows:
                orders.append({
                    "gtt_id": str(row.id),
                    "trigger_id": row.trigger_id,
                    "symbol": row.symbol,
                    "exchange": row.exchange,
                    "side": row.side,
                    "quantity": float(row.quantity),
                    "trigger_price": float(row.trigger_price),
                    "limit_price": float(row.limit_price) if row.limit_price else None,
                    "trigger_type": row.trigger_type,
                    "product": row.product,
                    "status": row.status,
                    "created_at": row.created_at.isoformat(),
                    "triggered_at": row.triggered_at.isoformat() if row.triggered_at else None,
                    "expires_at": row.expires_at.isoformat() if row.expires_at else None,
                    "order_id": row.order_id
                })

            return orders

        except Exception as e:
            logger.error(f"Failed to get GTT orders: {e}")
            raise

    @staticmethod
    async def cancel_gtt_order(
        db: AsyncSession,
        broker_connection_id: str,
        trigger_id: str
    ) -> bool:
        """Cancel a GTT order"""
        try:
            # Get broker connection details
            connection_result = await db.execute(text("""
                SELECT ubc.broker_type, ubc.api_key, ubc.api_secret, ubc.credentials, ubc.paper_trading
                FROM user_broker_connections ubc
                WHERE ubc.id = :broker_connection_id
            """), {"broker_connection_id": broker_connection_id})

            connection = connection_result.fetchone()
            if not connection:
                raise ValueError(f"Broker connection {broker_connection_id} not found")

            # Extract credentials from JSONB or direct columns
            credentials = connection.credentials or {}
            api_key = connection.api_key or credentials.get("api_key", "test_key")
            access_token = credentials.get("access_token") or "paper_trading_token"

            # Initialize Zerodha broker
            broker = ZerodhaBroker(
                api_key=api_key,
                access_token=access_token,
                paper_trading=connection.paper_trading
            )

            # Authenticate
            await broker.authenticate()

            # Cancel GTT order
            success = await broker.cancel_gtt_order(trigger_id)

            if success:
                # Update database
                await db.execute(text("""
                    UPDATE gtt_orders
                    SET status = 'cancelled', is_active = false
                    WHERE trigger_id = :trigger_id
                      AND broker_connection_id = :broker_connection_id
                """), {
                    "trigger_id": trigger_id,
                    "broker_connection_id": broker_connection_id
                })

                await db.commit()
                logger.info(f"GTT order cancelled: {trigger_id}")

            return success

        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to cancel GTT order: {e}")
            raise

    @staticmethod
    async def place_basket_order(
        db: AsyncSession,
        broker_connection_id: str,
        orders: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Place a basket order with multiple stocks

        Args:
            db: Database session
            broker_connection_id: User's broker connection ID
            orders: List of order dictionaries

        Returns:
            Basket order execution results
        """
        try:
            if len(orders) > 20:
                raise ValueError("Maximum 20 orders allowed in basket")

            # Get broker connection details
            connection_result = await db.execute(text("""
                SELECT ubc.broker_type, ubc.api_key, ubc.api_secret, ubc.credentials, ubc.paper_trading
                FROM user_broker_connections ubc
                WHERE ubc.id = :broker_connection_id
            """), {"broker_connection_id": broker_connection_id})

            connection = connection_result.fetchone()
            if not connection:
                raise ValueError(f"Broker connection {broker_connection_id} not found")

            # Extract credentials from JSONB or direct columns
            credentials = connection.credentials or {}
            api_key = connection.api_key or credentials.get("api_key", "test_key")
            access_token = credentials.get("access_token") or "paper_trading_token"

            # Initialize Zerodha broker
            broker = ZerodhaBroker(
                api_key=api_key,
                access_token=access_token,
                paper_trading=connection.paper_trading
            )

            # Authenticate
            await broker.authenticate()

            # Place basket order
            basket_response = await broker.place_basket_order(orders)

            # Store basket order in database
            import json
            basket_id = str(uuid.uuid4())
            await db.execute(text("""
                INSERT INTO basket_orders
                (id, broker_connection_id, basket_id, orders_placed,
                 success_count, failure_count, status, basket_details)
                VALUES
                (:id, :broker_connection_id, :basket_id, :orders_placed,
                 :success_count, :failure_count, :status, CAST(:basket_details AS jsonb))
            """), {
                "id": basket_id,
                "broker_connection_id": broker_connection_id,
                "basket_id": basket_response["basket_id"],
                "orders_placed": basket_response["orders_placed"],
                "success_count": basket_response["success_count"],
                "failure_count": basket_response["failure_count"],
                "status": basket_response["status"],
                "basket_details": json.dumps(basket_response)
            })

            await db.commit()

            logger.info(f"Basket order placed: {basket_response['basket_id']}")

            return {
                "basket_id": basket_id,
                "zerodha_basket_id": basket_response["basket_id"],
                "orders_placed": basket_response["orders_placed"],
                "success_count": basket_response["success_count"],
                "failure_count": basket_response["failure_count"],
                "status": basket_response["status"],
                "results": basket_response.get("results", []),
                "paper_trading": connection.paper_trading
            }

        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to place basket order: {e}")
            raise

    @staticmethod
    async def place_oco_order(
        db: AsyncSession,
        broker_connection_id: str,
        symbol: str,
        side: str,
        quantity: Decimal,
        target_price: Decimal,
        stop_loss_price: Decimal,
        product: str = "CNC"
    ) -> Dict[str, Any]:
        """
        Place an OCO (One-Cancels-Other) order

        Args:
            db: Database session
            broker_connection_id: User's broker connection ID
            symbol: Trading symbol
            side: BUY or SELL
            quantity: Number of shares
            target_price: Target profit price
            stop_loss_price: Stop loss price
            product: Product type (CNC, MIS, NRML)

        Returns:
            OCO order details
        """
        try:
            # Get broker connection details
            connection_result = await db.execute(text("""
                SELECT ubc.broker_type, ubc.api_key, ubc.api_secret, ubc.credentials, ubc.paper_trading
                FROM user_broker_connections ubc
                WHERE ubc.id = :broker_connection_id
            """), {"broker_connection_id": broker_connection_id})

            connection = connection_result.fetchone()
            if not connection:
                raise ValueError(f"Broker connection {broker_connection_id} not found")

            # Extract credentials from JSONB or direct columns
            credentials = connection.credentials or {}
            api_key = connection.api_key or credentials.get("api_key", "test_key")
            access_token = credentials.get("access_token") or "paper_trading_token"

            # Initialize Zerodha broker
            broker = ZerodhaBroker(
                api_key=api_key,
                access_token=access_token,
                paper_trading=connection.paper_trading
            )

            # Authenticate
            await broker.authenticate()

            # Place OCO order
            order_side = OrderSide.BUY if side.upper() == "BUY" else OrderSide.SELL
            oco_response = await broker.place_oco_order(
                symbol=symbol,
                side=order_side,
                quantity=quantity,
                target_price=target_price,
                stop_loss_price=stop_loss_price,
                product=product
            )

            # Determine exchange
            exchange = broker._determine_exchange(symbol)

            # Store OCO order in database
            oco_id = str(uuid.uuid4())
            await db.execute(text("""
                INSERT INTO oco_orders
                (id, broker_connection_id, trigger_id, symbol, exchange, side,
                 quantity, target_price, stop_loss_price, product, status,
                 created_at, expires_at)
                VALUES
                (:id, :broker_connection_id, :trigger_id, :symbol, :exchange, :side,
                 :quantity, :target_price, :stop_loss_price, :product, 'active',
                 :created_at, :expires_at)
            """), {
                "id": oco_id,
                "broker_connection_id": broker_connection_id,
                "trigger_id": oco_response["trigger_id"],
                "symbol": symbol.upper(),
                "exchange": exchange,
                "side": side.upper(),
                "quantity": float(quantity),
                "target_price": float(target_price),
                "stop_loss_price": float(stop_loss_price),
                "product": product,
                "created_at": datetime.fromisoformat(oco_response["created_at"]),
                "expires_at": datetime.fromisoformat(oco_response["expires_at"])
            })

            await db.commit()

            logger.info(f"OCO order placed: {oco_response['trigger_id']} for {symbol}")

            return {
                "oco_id": oco_id,
                "trigger_id": oco_response["trigger_id"],
                "symbol": symbol.upper(),
                "side": side.upper(),
                "quantity": float(quantity),
                "target_price": float(target_price),
                "stop_loss_price": float(stop_loss_price),
                "product": product,
                "status": "active",
                "created_at": oco_response["created_at"],
                "expires_at": oco_response["expires_at"],
                "paper_trading": connection.paper_trading
            }

        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to place OCO order: {e}")
            raise

    @staticmethod
    async def get_oco_orders(
        db: AsyncSession,
        broker_connection_id: str,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get OCO orders for a broker connection"""
        try:
            query = """
                SELECT
                    id, trigger_id, symbol, exchange, side, quantity,
                    target_price, stop_loss_price, product, status,
                    created_at, triggered_at, expires_at, executed_price, executed_side
                FROM oco_orders
                WHERE broker_connection_id = :broker_connection_id
                  AND is_active = true
            """

            params = {"broker_connection_id": broker_connection_id}

            if status:
                query += " AND status = :status"
                params["status"] = status

            query += " ORDER BY created_at DESC"

            result = await db.execute(text(query), params)
            rows = result.fetchall()

            orders = []
            for row in rows:
                orders.append({
                    "oco_id": str(row.id),
                    "trigger_id": row.trigger_id,
                    "symbol": row.symbol,
                    "exchange": row.exchange,
                    "side": row.side,
                    "quantity": float(row.quantity),
                    "target_price": float(row.target_price),
                    "stop_loss_price": float(row.stop_loss_price),
                    "product": row.product,
                    "status": row.status,
                    "created_at": row.created_at.isoformat(),
                    "triggered_at": row.triggered_at.isoformat() if row.triggered_at else None,
                    "expires_at": row.expires_at.isoformat() if row.expires_at else None,
                    "executed_price": float(row.executed_price) if row.executed_price else None,
                    "executed_side": row.executed_side
                })

            return orders

        except Exception as e:
            logger.error(f"Failed to get OCO orders: {e}")
            raise


__all__ = ["GTTOrderService"]
