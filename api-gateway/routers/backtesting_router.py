"""
Backtesting Router

API endpoints for running backtests and retrieving backtest results.

Endpoints:
- POST /backtests - Run a new backtest
- GET /backtests/{backtest_id} - Get backtest results
- GET /backtests/algorithm/{algorithm_id} - Get all backtests for algorithm
- DELETE /backtests/{backtest_id} - Delete backtest
"""
from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
import logging

from config.database import get_db_session
from routers.auth_router import get_current_user
from services.backtesting_engine import (
    get_backtesting_engine,
    BacktestingEngine,
    PositionSizingModel,
    SlippageModel,
    BacktestStatus
)
from sqlalchemy import text

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/backtests", tags=["Backtesting"])


# Request/Response Models

class BacktestRequest(BaseModel):
    """Request to run a backtest"""
    algorithm_id: str = Field(..., description="Algorithm ID to backtest")
    start_date: datetime = Field(..., description="Backtest start date")
    end_date: datetime = Field(..., description="Backtest end date")
    initial_capital: float = Field(100000.0, description="Initial capital", ge=1000)

    # Position sizing
    position_sizing: PositionSizingModel = Field(
        PositionSizingModel.FIXED_PERCENTAGE,
        description="Position sizing model"
    )
    position_sizing_params: Optional[dict] = Field(
        None,
        description="Position sizing parameters (e.g., {'percentage': 0.1})"
    )

    # Slippage
    slippage_model: SlippageModel = Field(
        SlippageModel.PERCENTAGE,
        description="Slippage model"
    )
    slippage_params: Optional[dict] = Field(
        None,
        description="Slippage parameters (e.g., {'percentage': 0.001})"
    )

    # Commissions
    commission_percentage: float = Field(
        0.001,
        description="Commission percentage (0.001 = 0.1%)",
        ge=0,
        le=0.1
    )
    commission_per_trade: float = Field(
        1.0,
        description="Fixed commission per trade",
        ge=0
    )

    # Benchmark
    benchmark_symbol: Optional[str] = Field(
        None,
        description="Benchmark symbol for comparison (e.g., SPY)"
    )

    # Timeframe
    timeframe: str = Field("1day", description="Bar timeframe (1day, 1hour, etc.)")


class BacktestResponse(BaseModel):
    """Backtest execution response"""
    backtest_id: str
    status: BacktestStatus
    initial_capital: float
    final_equity: Optional[float] = None
    total_trades: Optional[int] = None
    message: Optional[str] = None


class BacktestResultsResponse(BaseModel):
    """Full backtest results"""
    backtest_id: str
    algorithm_id: str
    status: BacktestStatus
    initial_capital: float
    final_equity: Optional[float] = None

    # Configuration
    start_date: datetime
    end_date: datetime
    position_sizing: str
    slippage_model: str

    # Results
    metrics: Optional[dict] = None
    equity_curve: Optional[List[dict]] = None
    trades: Optional[List[dict]] = None
    total_trades: Optional[int] = None

    # Metadata
    created_at: datetime
    completed_at: Optional[datetime] = None
    error: Optional[str] = None


class BacktestListResponse(BaseModel):
    """List of backtests"""
    backtests: List[BacktestResultsResponse]
    total: int


# Endpoints

@router.post("/", response_model=BacktestResponse)
async def run_backtest(
    request: BacktestRequest,
    current_user: dict = Depends(get_current_user),
    db_session_factory = Depends(get_db_session)
):
    """
    Run a backtest for an algorithm

    Simulates algorithm performance on historical data with realistic:
    - Position sizing
    - Slippage modeling
    - Transaction costs
    - Performance metrics

    Returns backtest_id immediately. Use GET /backtests/{backtest_id} to retrieve results.
    """
    try:
        logger.info(
            f"User {current_user['user_id']} requesting backtest for "
            f"algorithm {request.algorithm_id}"
        )

        # Verify algorithm belongs to user
        async with db_session_factory() as db:
            result = await db.execute(text("""
                SELECT id, user_id FROM trading_algorithms
                WHERE id = :algorithm_id
            """), {'algorithm_id': request.algorithm_id})

            algorithm = result.fetchone()

            if not algorithm:
                raise HTTPException(status_code=404, detail="Algorithm not found")

            if str(algorithm.user_id) != current_user['user_id']:
                raise HTTPException(
                    status_code=403,
                    detail="Not authorized to backtest this algorithm"
                )

        # Validate date range
        if request.end_date <= request.start_date:
            raise HTTPException(
                status_code=400,
                detail="end_date must be after start_date"
            )

        # Get backtesting engine
        backtest_engine = await get_backtesting_engine(
            db_session_factory=db_session_factory
        )

        # Run backtest (this will be async in background for long backtests)
        result = await backtest_engine.run_backtest(
            algorithm_id=request.algorithm_id,
            start_date=request.start_date,
            end_date=request.end_date,
            initial_capital=request.initial_capital,
            position_sizing=request.position_sizing,
            position_sizing_params=request.position_sizing_params or {'percentage': 0.1},
            slippage_model=request.slippage_model,
            slippage_params=request.slippage_params or {'percentage': 0.001},
            commission_percentage=request.commission_percentage,
            commission_per_trade=request.commission_per_trade,
            benchmark_symbol=request.benchmark_symbol,
            timeframe=request.timeframe
        )

        return BacktestResponse(
            backtest_id=result['backtest_id'],
            status=result['status'],
            initial_capital=result['initial_capital'],
            final_equity=result.get('final_equity'),
            total_trades=result.get('total_trades'),
            message="Backtest completed successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error running backtest: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to run backtest: {str(e)}")


@router.get("/{backtest_id}", response_model=BacktestResultsResponse)
async def get_backtest_results(
    backtest_id: str,
    current_user: dict = Depends(get_current_user),
    db_session_factory = Depends(get_db_session)
):
    """
    Get backtest results by ID

    Returns comprehensive backtest results including:
    - Performance metrics
    - Equity curve
    - Trade history
    - Risk metrics
    """
    try:
        async with db_session_factory() as db:
            result = await db.execute(text("""
                SELECT
                    b.id,
                    b.algorithm_id,
                    b.start_date,
                    b.end_date,
                    b.initial_capital,
                    b.position_sizing_model,
                    b.slippage_model,
                    b.status,
                    b.results,
                    b.error,
                    b.created_at,
                    b.completed_at,
                    a.user_id
                FROM backtests b
                JOIN trading_algorithms a ON b.algorithm_id = a.id
                WHERE b.id = :backtest_id
            """), {'backtest_id': backtest_id})

            backtest = result.fetchone()

            if not backtest:
                raise HTTPException(status_code=404, detail="Backtest not found")

            # Verify ownership
            if str(backtest.user_id) != current_user['user_id']:
                raise HTTPException(
                    status_code=403,
                    detail="Not authorized to view this backtest"
                )

            # Parse results
            results = backtest.results or {}

            return BacktestResultsResponse(
                backtest_id=str(backtest.id),
                algorithm_id=str(backtest.algorithm_id),
                status=backtest.status,
                initial_capital=float(backtest.initial_capital),
                final_equity=results.get('final_equity'),
                start_date=backtest.start_date,
                end_date=backtest.end_date,
                position_sizing=backtest.position_sizing_model or 'fixed_percentage',
                slippage_model=backtest.slippage_model or 'percentage',
                metrics=results.get('metrics'),
                equity_curve=results.get('equity_curve'),
                trades=results.get('trades'),
                total_trades=results.get('total_trades'),
                created_at=backtest.created_at,
                completed_at=backtest.completed_at,
                error=backtest.error
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching backtest results: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch backtest: {str(e)}")


@router.get("/algorithm/{algorithm_id}", response_model=BacktestListResponse)
async def get_algorithm_backtests(
    algorithm_id: str,
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user),
    db_session_factory = Depends(get_db_session)
):
    """
    Get all backtests for an algorithm

    Returns list of backtests with summary information.
    Use GET /backtests/{backtest_id} for detailed results.
    """
    try:
        async with db_session_factory() as db:
            # Verify algorithm ownership
            result = await db.execute(text("""
                SELECT user_id FROM trading_algorithms
                WHERE id = :algorithm_id
            """), {'algorithm_id': algorithm_id})

            algorithm = result.fetchone()

            if not algorithm:
                raise HTTPException(status_code=404, detail="Algorithm not found")

            if str(algorithm.user_id) != current_user['user_id']:
                raise HTTPException(
                    status_code=403,
                    detail="Not authorized to view backtests for this algorithm"
                )

            # Get backtests
            result = await db.execute(text("""
                SELECT
                    id,
                    algorithm_id,
                    start_date,
                    end_date,
                    initial_capital,
                    position_sizing_model,
                    slippage_model,
                    status,
                    results,
                    error,
                    created_at,
                    completed_at
                FROM backtests
                WHERE algorithm_id = :algorithm_id
                ORDER BY created_at DESC
                LIMIT :limit OFFSET :offset
            """), {
                'algorithm_id': algorithm_id,
                'limit': limit,
                'offset': offset
            })

            backtests = result.fetchall()

            # Get total count
            count_result = await db.execute(text("""
                SELECT COUNT(*) as total
                FROM backtests
                WHERE algorithm_id = :algorithm_id
            """), {'algorithm_id': algorithm_id})

            total = count_result.fetchone().total

            # Format response
            backtest_list = []
            for bt in backtests:
                results = bt.results or {}
                backtest_list.append(BacktestResultsResponse(
                    backtest_id=str(bt.id),
                    algorithm_id=str(bt.algorithm_id),
                    status=bt.status,
                    initial_capital=float(bt.initial_capital),
                    final_equity=results.get('final_equity'),
                    start_date=bt.start_date,
                    end_date=bt.end_date,
                    position_sizing=bt.position_sizing_model or 'fixed_percentage',
                    slippage_model=bt.slippage_model or 'percentage',
                    metrics=results.get('metrics'),
                    total_trades=results.get('total_trades'),
                    created_at=bt.created_at,
                    completed_at=bt.completed_at,
                    error=bt.error
                ))

            return BacktestListResponse(
                backtests=backtest_list,
                total=total
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching algorithm backtests: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch backtests: {str(e)}")


@router.delete("/{backtest_id}")
async def delete_backtest(
    backtest_id: str,
    current_user: dict = Depends(get_current_user),
    db_session_factory = Depends(get_db_session)
):
    """
    Delete a backtest

    Removes backtest record and all associated data.
    """
    try:
        async with db_session_factory() as db:
            # Verify ownership
            result = await db.execute(text("""
                SELECT a.user_id
                FROM backtests b
                JOIN trading_algorithms a ON b.algorithm_id = a.id
                WHERE b.id = :backtest_id
            """), {'backtest_id': backtest_id})

            backtest = result.fetchone()

            if not backtest:
                raise HTTPException(status_code=404, detail="Backtest not found")

            if str(backtest.user_id) != current_user['user_id']:
                raise HTTPException(
                    status_code=403,
                    detail="Not authorized to delete this backtest"
                )

            # Delete backtest
            await db.execute(text("""
                DELETE FROM backtests
                WHERE id = :backtest_id
            """), {'backtest_id': backtest_id})

            await db.commit()

            return {
                "message": "Backtest deleted successfully",
                "backtest_id": backtest_id
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting backtest: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to delete backtest: {str(e)}")
