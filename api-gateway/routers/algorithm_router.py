"""
Algorithm Router
API endpoints for algorithmic trading
"""
import uuid
import logging
from datetime import date, datetime
from decimal import Decimal
from typing import Dict, List, Any, Optional, Annotated

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from config.database import get_db
from system.dependencies.enhanced_auth_deps import get_enhanced_current_user
from services.algorithm_engine import AlgorithmEngine
from services.backtesting_service import BacktestingService
from services.signal_processor import SignalProcessor
from services.visual_algorithm_compiler import VisualAlgorithmCompiler

router = APIRouter()
logger = logging.getLogger(__name__)


# =====================================================
# Pydantic Models
# =====================================================

class CreateAlgorithmRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    language: str = Field(default='python')
    builder_type: str = Field(default='code')  # 'code' or 'visual'
    strategy_code: Optional[str] = None
    visual_config: Optional[Dict[str, Any]] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)
    auto_run: bool = Field(default=False)
    execution_interval: str = Field(default='manual')
    max_positions: int = Field(default=5, ge=1, le=50)
    risk_per_trade: float = Field(default=2.0, ge=0.1, le=10.0)
    allowed_regions: List[str] = Field(default_factory=lambda: ['IN', 'US'])
    allowed_trading_modes: List[str] = Field(default_factory=lambda: ['paper', 'live'])
    target_broker: Optional[str] = None


class UpdateAlgorithmRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    strategy_code: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    auto_run: Optional[bool] = None
    execution_interval: Optional[str] = None
    max_positions: Optional[int] = None
    risk_per_trade: Optional[float] = None


class BacktestRequest(BaseModel):
    start_date: date
    end_date: date
    initial_capital: float = Field(..., gt=0)
    backtest_name: Optional[str] = None


class ValidateCodeRequest(BaseModel):
    code: str


class APIResponse(BaseModel):
    success: bool
    data: Optional[Any] = None
    message: Optional[str] = None
    error: Optional[str] = None


# =====================================================
# Algorithm CRUD Endpoints
# =====================================================

@router.post("", response_model=APIResponse)
@router.post("/", response_model=APIResponse)
async def create_algorithm(
    request: CreateAlgorithmRequest,
    current_user: Annotated[Dict[str, Any], Depends(get_enhanced_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """Create a new trading algorithm (code or visual mode)"""
    try:
        user_id = current_user["id"]

        # Handle visual vs code mode
        if request.builder_type == 'visual':
            # Visual mode: validate visual config and compile to code
            if not request.visual_config:
                raise HTTPException(status_code=400, detail="visual_config is required for visual mode")

            # Validate visual configuration
            validation = VisualAlgorithmCompiler.validate_visual_config(request.visual_config)
            if not validation['valid']:
                raise HTTPException(status_code=400, detail=validation['error'])

            # Compile visual config to Python code
            strategy_code = VisualAlgorithmCompiler.compile_visual_to_code(request.visual_config)

        else:
            # Code mode: validate Python code
            if not request.strategy_code:
                raise HTTPException(status_code=400, detail="strategy_code is required for code mode")

            strategy_code = request.strategy_code

            # Validate code
            validation = await AlgorithmEngine.validate_algorithm_code(strategy_code)
            if not validation['valid']:
                raise HTTPException(status_code=400, detail=validation['error'])

        # Create algorithm
        result = await db.execute(text("""
            INSERT INTO trading_algorithms (
                user_id, name, description, language, builder_type, strategy_code,
                visual_config, parameters, auto_run, execution_interval,
                max_positions, risk_per_trade, allowed_regions, allowed_trading_modes,
                target_broker, status
            )
            VALUES (
                :user_id, :name, :description, :language, :builder_type, :strategy_code,
                :visual_config, :parameters, :auto_run, :execution_interval,
                :max_positions, :risk_per_trade, :allowed_regions, :allowed_trading_modes,
                :target_broker, 'inactive'
            )
            RETURNING id, name, status, builder_type, created_at
        """), {
            "user_id": user_id,
            "name": request.name,
            "description": request.description,
            "language": request.language,
            "builder_type": request.builder_type,
            "strategy_code": strategy_code,
            "visual_config": request.visual_config,
            "parameters": request.parameters,
            "auto_run": request.auto_run,
            "execution_interval": request.execution_interval,
            "max_positions": request.max_positions,
            "risk_per_trade": request.risk_per_trade,
            "allowed_regions": request.allowed_regions,
            "allowed_trading_modes": request.allowed_trading_modes,
            "target_broker": request.target_broker
        })

        algo = result.fetchone()
        await db.commit()

        return APIResponse(
            success=True,
            data={
                "id": str(algo.id),
                "name": algo.name,
                "status": algo.status,
                "created_at": algo.created_at.isoformat()
            },
            message="Algorithm created successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create algorithm: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=APIResponse)
@router.get("/", response_model=APIResponse)
async def list_algorithms(
    current_user: Annotated[Dict[str, Any], Depends(get_enhanced_current_user)],
    db: AsyncSession = Depends(get_db),
    status: Optional[str] = Query(None),
    limit: int = Query(100, le=500)
):
    """List user's algorithms"""
    try:
        user_id = current_user["id"]

        # Build query
        where_clause = "WHERE user_id = :user_id"
        params = {"user_id": user_id, "limit": limit}

        if status:
            where_clause += " AND status = :status"
            params["status"] = status

        result = await db.execute(text(f"""
            SELECT
                id, name, description, status, auto_run,
                execution_interval, last_run_at, total_executions,
                successful_executions, created_at, updated_at
            FROM trading_algorithms
            {where_clause}
            ORDER BY updated_at DESC
            LIMIT :limit
        """), params)

        algorithms = []
        for row in result.fetchall():
            algorithms.append({
                "id": str(row.id),
                "name": row.name,
                "description": row.description,
                "status": row.status,
                "auto_run": row.auto_run,
                "execution_interval": row.execution_interval,
                "last_run_at": row.last_run_at.isoformat() if row.last_run_at else None,
                "total_executions": row.total_executions,
                "successful_executions": row.successful_executions,
                "created_at": row.created_at.isoformat(),
                "updated_at": row.updated_at.isoformat()
            })

        return APIResponse(success=True, data=algorithms)

    except Exception as e:
        logger.error(f"Failed to list algorithms: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dashboard", response_model=APIResponse)
async def get_dashboard(
    current_user: Annotated[Dict[str, Any], Depends(get_enhanced_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """Get algorithm dashboard summary"""
    try:
        user_id = current_user["id"]

        # Get algorithm stats
        stats_result = await db.execute(text("""
            SELECT
                COUNT(*) FILTER (WHERE status = 'active') as active_count,
                COUNT(*) as total_count,
                SUM(total_executions) as total_executions,
                SUM(successful_executions) as successful_executions
            FROM trading_algorithms
            WHERE user_id = :user_id
        """), {"user_id": user_id})

        stats = stats_result.fetchone()

        # Get today's performance
        perf_result = await db.execute(text("""
            SELECT
                COALESCE(SUM(daily_pnl), 0) as total_pnl,
                COALESCE(SUM(daily_trades), 0) as total_trades,
                COALESCE(AVG(win_rate), 0) as avg_win_rate
            FROM algorithm_performance_snapshots
            WHERE user_id = :user_id
            AND snapshot_date = CURRENT_DATE
        """), {"user_id": user_id})

        perf = perf_result.fetchone()

        return APIResponse(
            success=True,
            data={
                "active_algorithms": stats.active_count or 0,
                "total_algorithms": stats.total_count or 0,
                "total_executions": stats.total_executions or 0,
                "successful_executions": stats.successful_executions or 0,
                "today_pnl": float(perf.total_pnl) if perf.total_pnl else 0,
                "today_trades": perf.total_trades or 0,
                "avg_win_rate": float(perf.avg_win_rate) if perf.avg_win_rate else 0
            }
        )

    except Exception as e:
        logger.error(f"Failed to get dashboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{algorithm_id}", response_model=APIResponse)
async def get_algorithm(
    algorithm_id: str,
    current_user: Annotated[Dict[str, Any], Depends(get_enhanced_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """Get algorithm details"""
    try:
        user_id = current_user["id"]

        result = await db.execute(text("""
            SELECT
                id, name, description, language, strategy_code, parameters,
                auto_run, execution_interval, max_positions, risk_per_trade,
                allowed_regions, allowed_trading_modes, target_broker,
                status, last_run_at, last_error,
                total_executions, successful_executions,
                created_at, updated_at
            FROM trading_algorithms
            WHERE id = :algorithm_id AND user_id = :user_id
        """), {"algorithm_id": algorithm_id, "user_id": user_id})

        algo = result.fetchone()
        if not algo:
            raise HTTPException(status_code=404, detail="Algorithm not found")

        return APIResponse(
            success=True,
            data={
                "id": str(algo.id),
                "name": algo.name,
                "description": algo.description,
                "language": algo.language,
                "strategy_code": algo.strategy_code,
                "parameters": algo.parameters,
                "auto_run": algo.auto_run,
                "execution_interval": algo.execution_interval,
                "max_positions": algo.max_positions,
                "risk_per_trade": float(algo.risk_per_trade),
                "allowed_regions": algo.allowed_regions,
                "allowed_trading_modes": algo.allowed_trading_modes,
                "target_broker": algo.target_broker,
                "status": algo.status,
                "last_run_at": algo.last_run_at.isoformat() if algo.last_run_at else None,
                "last_error": algo.last_error,
                "total_executions": algo.total_executions,
                "successful_executions": algo.successful_executions,
                "created_at": algo.created_at.isoformat(),
                "updated_at": algo.updated_at.isoformat()
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get algorithm: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{algorithm_id}", response_model=APIResponse)
async def update_algorithm(
    algorithm_id: str,
    request: UpdateAlgorithmRequest,
    current_user: Annotated[Dict[str, Any], Depends(get_enhanced_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """Update algorithm"""
    try:
        user_id = current_user["id"]

        # Build update query
        updates = []
        params = {"algorithm_id": algorithm_id, "user_id": user_id}

        if request.name is not None:
            updates.append("name = :name")
            params["name"] = request.name

        if request.description is not None:
            updates.append("description = :description")
            params["description"] = request.description

        if request.strategy_code is not None:
            # Validate code
            validation = await AlgorithmEngine.validate_algorithm_code(request.strategy_code)
            if not validation['valid']:
                raise HTTPException(status_code=400, detail=validation['error'])

            updates.append("strategy_code = :strategy_code")
            params["strategy_code"] = request.strategy_code

        if request.parameters is not None:
            updates.append("parameters = :parameters")
            params["parameters"] = request.parameters

        if request.auto_run is not None:
            updates.append("auto_run = :auto_run")
            params["auto_run"] = request.auto_run

        if request.execution_interval is not None:
            updates.append("execution_interval = :execution_interval")
            params["execution_interval"] = request.execution_interval

        if request.max_positions is not None:
            updates.append("max_positions = :max_positions")
            params["max_positions"] = request.max_positions

        if request.risk_per_trade is not None:
            updates.append("risk_per_trade = :risk_per_trade")
            params["risk_per_trade"] = request.risk_per_trade

        if not updates:
            raise HTTPException(status_code=400, detail="No fields to update")

        updates.append("updated_at = NOW()")

        await db.execute(text(f"""
            UPDATE trading_algorithms
            SET {', '.join(updates)}
            WHERE id = :algorithm_id AND user_id = :user_id
        """), params)

        await db.commit()

        return APIResponse(success=True, message="Algorithm updated successfully")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update algorithm: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{algorithm_id}", response_model=APIResponse)
async def delete_algorithm(
    algorithm_id: str,
    current_user: Annotated[Dict[str, Any], Depends(get_enhanced_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """Delete algorithm"""
    try:
        user_id = current_user["id"]

        result = await db.execute(text("""
            DELETE FROM trading_algorithms
            WHERE id = :algorithm_id AND user_id = :user_id
            RETURNING id
        """), {"algorithm_id": algorithm_id, "user_id": user_id})

        if not result.fetchone():
            raise HTTPException(status_code=404, detail="Algorithm not found")

        await db.commit()

        return APIResponse(success=True, message="Algorithm deleted successfully")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete algorithm: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{algorithm_id}/toggle", response_model=APIResponse)
async def toggle_algorithm(
    algorithm_id: str,
    current_user: Annotated[Dict[str, Any], Depends(get_enhanced_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """Toggle algorithm active/inactive status"""
    try:
        user_id = current_user["id"]

        result = await db.execute(text("""
            UPDATE trading_algorithms
            SET
                status = CASE
                    WHEN status = 'active' THEN 'inactive'
                    WHEN status = 'inactive' THEN 'active'
                    ELSE status
                END,
                updated_at = NOW()
            WHERE id = :algorithm_id AND user_id = :user_id
            RETURNING status
        """), {"algorithm_id": algorithm_id, "user_id": user_id})

        algo = result.fetchone()
        if not algo:
            raise HTTPException(status_code=404, detail="Algorithm not found")

        await db.commit()

        return APIResponse(
            success=True,
            data={"status": algo.status},
            message=f"Algorithm is now {algo.status}"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to toggle algorithm: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# =====================================================
# Execution Endpoints
# =====================================================

@router.post("/{algorithm_id}/execute", response_model=APIResponse)
async def execute_algorithm(
    algorithm_id: str,
    current_user: Annotated[Dict[str, Any], Depends(get_enhanced_current_user)],
    db: AsyncSession = Depends(get_db),
    dry_run: bool = Query(False)
):
    """Manually execute an algorithm"""
    try:
        user_id = current_user["id"]

        result = await AlgorithmEngine.execute_algorithm(
            db=db,
            algorithm_id=uuid.UUID(algorithm_id),
            user_id=uuid.UUID(user_id),
            execution_type='manual',
            dry_run=dry_run
        )

        return APIResponse(
            success=result['success'],
            data=result,
            message="Algorithm executed successfully" if result['success'] else None,
            error=result.get('error')
        )

    except Exception as e:
        logger.error(f"Failed to execute algorithm: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{algorithm_id}/signals", response_model=APIResponse)
async def get_signals(
    algorithm_id: str,
    current_user: Annotated[Dict[str, Any], Depends(get_enhanced_current_user)],
    db: AsyncSession = Depends(get_db),
    limit: int = Query(50, le=200)
):
    """Get recent signals for an algorithm"""
    try:
        user_id = current_user["id"]

        # Verify ownership
        algo_check = await db.execute(text("""
            SELECT id FROM trading_algorithms
            WHERE id = :algorithm_id AND user_id = :user_id
        """), {"algorithm_id": algorithm_id, "user_id": user_id})

        if not algo_check.fetchone():
            raise HTTPException(status_code=404, detail="Algorithm not found")

        # Get signals
        signals = await SignalProcessor.get_pending_signals(
            db=db,
            algorithm_id=uuid.UUID(algorithm_id),
            limit=limit
        )

        return APIResponse(success=True, data=signals)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get signals: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =====================================================
# Backtesting Endpoints
# =====================================================

@router.post("/{algorithm_id}/backtest", response_model=APIResponse)
async def run_backtest(
    algorithm_id: str,
    request: BacktestRequest,
    current_user: Annotated[Dict[str, Any], Depends(get_enhanced_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """Run a backtest for an algorithm"""
    try:
        user_id = current_user["id"]

        result = await BacktestingService.run_backtest(
            db=db,
            algorithm_id=uuid.UUID(algorithm_id),
            user_id=uuid.UUID(user_id),
            start_date=request.start_date,
            end_date=request.end_date,
            initial_capital=Decimal(str(request.initial_capital)),
            backtest_name=request.backtest_name
        )

        return APIResponse(
            success=result['success'],
            data=result,
            message="Backtest completed successfully"
        )

    except Exception as e:
        logger.error(f"Backtest failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{algorithm_id}/backtest-results", response_model=APIResponse)
async def get_backtest_results(
    algorithm_id: str,
    current_user: Annotated[Dict[str, Any], Depends(get_enhanced_current_user)],
    db: AsyncSession = Depends(get_db),
    limit: int = Query(10, le=50)
):
    """Get backtest results list for an algorithm"""
    try:
        user_id = current_user["id"]

        result = await db.execute(text("""
            SELECT
                id, backtest_name, start_date, end_date,
                initial_capital, final_capital, total_return_pct,
                sharpe_ratio, max_drawdown_pct, total_trades,
                win_rate, created_at
            FROM algorithm_backtest_results
            WHERE algorithm_id = :algorithm_id AND user_id = :user_id
            ORDER BY created_at DESC
            LIMIT :limit
        """), {
            "algorithm_id": algorithm_id,
            "user_id": user_id,
            "limit": limit
        })

        backtests = []
        for row in result.fetchall():
            backtests.append({
                "id": str(row.id),
                "backtest_name": row.backtest_name,
                "start_date": row.start_date.isoformat(),
                "end_date": row.end_date.isoformat(),
                "initial_capital": float(row.initial_capital),
                "final_capital": float(row.final_capital) if row.final_capital else 0,
                "total_return_pct": float(row.total_return_pct) if row.total_return_pct else 0,
                "sharpe_ratio": float(row.sharpe_ratio) if row.sharpe_ratio else 0,
                "max_drawdown_pct": float(row.max_drawdown_pct) if row.max_drawdown_pct else 0,
                "total_trades": row.total_trades,
                "win_rate": float(row.win_rate) if row.win_rate else 0,
                "created_at": row.created_at.isoformat()
            })

        return APIResponse(success=True, data=backtests)

    except Exception as e:
        logger.error(f"Failed to get backtest results: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =====================================================
# Validation & Utility Endpoints
# =====================================================

@router.post("/validate", response_model=APIResponse)
async def validate_code(
    request: ValidateCodeRequest,
    current_user: Annotated[Dict[str, Any], Depends(get_enhanced_current_user)]
):
    """Validate algorithm code"""
    try:
        validation = await AlgorithmEngine.validate_algorithm_code(request.code)

        return APIResponse(
            success=validation['valid'],
            data=validation,
            message=validation.get('message'),
            error=validation.get('error')
        )

    except Exception as e:
        logger.error(f"Code validation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =====================================================
# Visual/No-Code Algorithm Endpoints
# =====================================================

@router.get("/visual-blocks", response_model=APIResponse)
async def get_visual_blocks():
    """Get available building blocks for visual algorithm builder"""
    try:
        blocks = VisualAlgorithmCompiler.get_available_blocks()
        return APIResponse(success=True, data=blocks)

    except Exception as e:
        logger.error(f"Failed to get visual blocks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/visual/compile", response_model=APIResponse)
async def compile_visual_algorithm(
    visual_config: Dict[str, Any],
    current_user: Annotated[Dict[str, Any], Depends(get_enhanced_current_user)]
):
    """Compile visual configuration to Python code (preview)"""
    try:
        # Validate configuration
        validation = VisualAlgorithmCompiler.validate_visual_config(visual_config)
        if not validation['valid']:
            raise HTTPException(status_code=400, detail=validation['error'])

        # Compile to code
        code = VisualAlgorithmCompiler.compile_visual_to_code(visual_config)

        return APIResponse(
            success=True,
            data={
                'code': code,
                'validation': validation
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to compile visual algorithm: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/visual/validate", response_model=APIResponse)
async def validate_visual_algorithm(
    visual_config: Dict[str, Any],
    current_user: Annotated[Dict[str, Any], Depends(get_enhanced_current_user)]
):
    """Validate visual configuration"""
    try:
        validation = VisualAlgorithmCompiler.validate_visual_config(visual_config)
        return APIResponse(
            success=validation['valid'],
            data=validation
        )

    except Exception as e:
        logger.error(f"Failed to validate visual algorithm: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/visual-templates", response_model=APIResponse)
async def get_visual_templates(
    category: Optional[str] = Query(None),
    difficulty: Optional[str] = Query(None),
    current_user: Annotated[Dict[str, Any], Depends(get_enhanced_current_user)] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get visual strategy templates"""
    try:
        # Build query
        query = """
            SELECT
                id, name, description, category, difficulty_level,
                visual_config, default_parameters,
                compatible_regions, compatible_brokers
            FROM visual_strategy_templates
            WHERE is_active = true
        """

        params = {}

        if category:
            query += " AND category = :category"
            params['category'] = category

        if difficulty:
            query += " AND difficulty_level = :difficulty"
            params['difficulty'] = difficulty

        query += " ORDER BY usage_count DESC, name ASC"

        result = await db.execute(text(query), params)

        templates = []
        for row in result.fetchall():
            templates.append({
                'id': str(row.id),
                'name': row.name,
                'description': row.description,
                'category': row.category,
                'difficulty_level': row.difficulty_level,
                'visual_config': row.visual_config,
                'default_parameters': row.default_parameters,
                'compatible_regions': row.compatible_regions,
                'compatible_brokers': row.compatible_brokers
            })

        return APIResponse(success=True, data=templates)

    except Exception as e:
        logger.error(f"Failed to get visual templates: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/visual-templates/{template_id}/use", response_model=APIResponse)
async def use_visual_template(
    template_id: str,
    current_user: Annotated[Dict[str, Any], Depends(get_enhanced_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """Increment usage count for a template and return its configuration"""
    try:
        # Get template
        result = await db.execute(text("""
            SELECT visual_config, default_parameters, name
            FROM visual_strategy_templates
            WHERE id = :template_id AND is_active = true
        """), {"template_id": template_id})

        template = result.fetchone()
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")

        # Increment usage count
        await db.execute(text("""
            UPDATE visual_strategy_templates
            SET usage_count = usage_count + 1
            WHERE id = :template_id
        """), {"template_id": template_id})

        await db.commit()

        return APIResponse(
            success=True,
            data={
                'name': template.name,
                'visual_config': template.visual_config,
                'default_parameters': template.default_parameters
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to use visual template: {e}")
        raise HTTPException(status_code=500, detail=str(e))
