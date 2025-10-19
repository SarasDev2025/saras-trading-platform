"""
Algorithm Router
API endpoints for algorithmic trading
"""
import uuid
import json
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
    stock_universe: Optional[Dict[str, Any]] = Field(default=None)

    # Flexible scheduling fields
    scheduling_type: str = Field(default='interval')  # 'interval', 'time_windows', 'single_time', 'continuous'
    execution_time_windows: List[Dict[str, str]] = Field(default_factory=list)  # [{"start": "09:30", "end": "10:30"}]
    execution_times: List[str] = Field(default_factory=list)  # ["10:00", "14:30"]
    run_continuously: bool = Field(default=False)

    # Duration controls
    run_duration_type: str = Field(default='forever')  # 'forever', 'days', 'months', 'years', 'until_date'
    run_duration_value: Optional[int] = None
    run_start_date: Optional[datetime] = None
    run_end_date: Optional[datetime] = None

    # Auto-stop controls
    auto_stop_on_loss: bool = Field(default=False)
    auto_stop_loss_threshold: Optional[float] = None


class UpdateAlgorithmRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    builder_type: Optional[str] = None  # Added to support visual recompilation
    strategy_code: Optional[str] = None
    visual_config: Optional[Dict[str, Any]] = None  # Added to support visual recompilation
    parameters: Optional[Dict[str, Any]] = None
    auto_run: Optional[bool] = None
    execution_interval: Optional[str] = None
    max_positions: Optional[int] = None
    risk_per_trade: Optional[float] = None
    stock_universe: Optional[Dict[str, Any]] = None

    # Flexible scheduling fields
    scheduling_type: Optional[str] = None
    execution_time_windows: Optional[List[Dict[str, str]]] = None
    execution_times: Optional[List[str]] = None
    run_continuously: Optional[bool] = None

    # Duration controls
    run_duration_type: Optional[str] = None
    run_duration_value: Optional[int] = None
    run_start_date: Optional[datetime] = None
    run_end_date: Optional[datetime] = None

    # Auto-stop controls
    auto_stop_on_loss: Optional[bool] = None
    auto_stop_loss_threshold: Optional[float] = None


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
                target_broker, stock_universe, status,
                scheduling_type, execution_time_windows, execution_times, run_continuously,
                run_duration_type, run_duration_value, run_start_date, run_end_date,
                auto_stop_on_loss, auto_stop_loss_threshold
            )
            VALUES (
                :user_id, :name, :description, :language, :builder_type, :strategy_code,
                :visual_config, :parameters, :auto_run, :execution_interval,
                :max_positions, :risk_per_trade, :allowed_regions, :allowed_trading_modes,
                :target_broker, :stock_universe, 'inactive',
                :scheduling_type, :execution_time_windows, :execution_times, :run_continuously,
                :run_duration_type, :run_duration_value, :run_start_date, :run_end_date,
                :auto_stop_on_loss, :auto_stop_loss_threshold
            )
            RETURNING id, name, status, builder_type, created_at
        """), {
            "user_id": user_id,
            "name": request.name,
            "description": request.description,
            "language": request.language,
            "builder_type": request.builder_type,
            "strategy_code": strategy_code,
            "visual_config": json.dumps(request.visual_config) if request.visual_config else None,
            "parameters": json.dumps(request.parameters) if request.parameters else '{}',
            "auto_run": request.auto_run,
            "execution_interval": request.execution_interval,
            "max_positions": request.max_positions,
            "risk_per_trade": request.risk_per_trade,
            "allowed_regions": request.allowed_regions,
            "allowed_trading_modes": request.allowed_trading_modes,
            "target_broker": request.target_broker,
            "stock_universe": json.dumps(request.stock_universe) if request.stock_universe else None,
            "scheduling_type": request.scheduling_type,
            "execution_time_windows": json.dumps(request.execution_time_windows) if request.execution_time_windows else '[]',
            "execution_times": json.dumps(request.execution_times) if request.execution_times else '[]',
            "run_continuously": request.run_continuously,
            "run_duration_type": request.run_duration_type,
            "run_duration_value": request.run_duration_value,
            "run_start_date": request.run_start_date,
            "run_end_date": request.run_end_date,
            "auto_stop_on_loss": request.auto_stop_on_loss,
            "auto_stop_loss_threshold": request.auto_stop_loss_threshold
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

# =====================================================
# Visual/No-Code Algorithm Endpoints
# =====================================================

@router.get("/visual-blocks", response_model=APIResponse)
async def get_visual_blocks():
    """Get available building blocks for visual algorithm builder (public endpoint)"""
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
                builder_type, visual_config, stock_universe,
                status, last_run_at, last_error,
                total_executions, successful_executions,
                scheduling_type, execution_time_windows, execution_times, run_continuously,
                run_duration_type, run_duration_value, run_start_date, run_end_date,
                auto_stop_on_loss, auto_stop_loss_threshold,
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
                "builder_type": algo.builder_type,
                "strategy_code": algo.strategy_code,
                "visual_config": algo.visual_config,
                "stock_universe": algo.stock_universe,
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
                "scheduling_type": algo.scheduling_type,
                "execution_time_windows": algo.execution_time_windows,
                "execution_times": algo.execution_times,
                "run_continuously": algo.run_continuously,
                "run_duration_type": algo.run_duration_type,
                "run_duration_value": algo.run_duration_value,
                "run_start_date": algo.run_start_date.isoformat() if algo.run_start_date else None,
                "run_end_date": algo.run_end_date.isoformat() if algo.run_end_date else None,
                "auto_stop_on_loss": algo.auto_stop_on_loss,
                "auto_stop_loss_threshold": float(algo.auto_stop_loss_threshold) if algo.auto_stop_loss_threshold else None,
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

        # Handle visual config updates (recompile to code)
        if request.visual_config is not None:
            # Validate visual configuration
            validation = VisualAlgorithmCompiler.validate_visual_config(request.visual_config)
            if not validation['valid']:
                raise HTTPException(status_code=400, detail=validation['error'])

            # Compile visual config to Python code
            strategy_code = VisualAlgorithmCompiler.compile_visual_to_code(request.visual_config)

            # Update both visual_config AND strategy_code
            updates.append("visual_config = :visual_config")
            updates.append("strategy_code = :strategy_code")
            params["visual_config"] = json.dumps(request.visual_config)
            params["strategy_code"] = strategy_code

            logger.info(f"Recompiled visual config to code for algorithm {algorithm_id}")

        elif request.strategy_code is not None:
            # Manual code mode: validate Python code
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

        if request.stock_universe is not None:
            updates.append("stock_universe = :stock_universe")
            params["stock_universe"] = json.dumps(request.stock_universe)

        # Flexible scheduling fields
        if request.scheduling_type is not None:
            updates.append("scheduling_type = :scheduling_type")
            params["scheduling_type"] = request.scheduling_type

        if request.execution_time_windows is not None:
            updates.append("execution_time_windows = :execution_time_windows")
            params["execution_time_windows"] = json.dumps(request.execution_time_windows)

        if request.execution_times is not None:
            updates.append("execution_times = :execution_times")
            params["execution_times"] = json.dumps(request.execution_times)

        if request.run_continuously is not None:
            updates.append("run_continuously = :run_continuously")
            params["run_continuously"] = request.run_continuously

        # Duration controls
        if request.run_duration_type is not None:
            updates.append("run_duration_type = :run_duration_type")
            params["run_duration_type"] = request.run_duration_type

        if request.run_duration_value is not None:
            updates.append("run_duration_value = :run_duration_value")
            params["run_duration_value"] = request.run_duration_value

        if request.run_start_date is not None:
            updates.append("run_start_date = :run_start_date")
            params["run_start_date"] = request.run_start_date

        if request.run_end_date is not None:
            updates.append("run_end_date = :run_end_date")
            params["run_end_date"] = request.run_end_date

        # Auto-stop controls
        if request.auto_stop_on_loss is not None:
            updates.append("auto_stop_on_loss = :auto_stop_on_loss")
            params["auto_stop_on_loss"] = request.auto_stop_on_loss

        if request.auto_stop_loss_threshold is not None:
            updates.append("auto_stop_loss_threshold = :auto_stop_loss_threshold")
            params["auto_stop_loss_threshold"] = request.auto_stop_loss_threshold

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
# Interactive Chart Builder Preview Endpoints
# =====================================================

class PreviewDataRequest(BaseModel):
    symbol: str
    days: int = Field(default=90, ge=7, le=365)

class PreviewSignalsRequest(BaseModel):
    price_data: List[Dict[str, Any]]
    entry_conditions: List[Dict[str, Any]]
    exit_conditions: List[Dict[str, Any]]
    initial_capital: Optional[float] = Field(default=10000, description="Initial capital for portfolio simulation")
    start_date: Optional[str] = Field(default=None, description="Start date for portfolio simulation (YYYY-MM-DD)")

@router.get("/visual/preview-data", response_model=APIResponse)
async def get_preview_data(
    symbol: str = Query(..., description="Stock symbol"),
    days: int = Query(90, ge=7, le=365, description="Number of days of historical data"),
    current_user: Annotated[Dict[str, Any], Depends(get_enhanced_current_user)] = None,
):
    """Fetch historical price data with calculated indicators for chart preview"""
    try:
        from services.data_providers import DataProviderFactory
        from datetime import timedelta
        import pandas as pd

        # Calculate date range
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)

        # Get user region for data provider
        region = current_user.get('region', 'US')

        # Create data provider
        provider = DataProviderFactory.create_provider(
            broker='alpaca',
            region=region,
            config={'region': region}
        )

        # Fetch historical data
        historical_data = await provider.get_historical_data(
            symbols=[symbol],
            start_date=start_date,
            end_date=end_date,
            region=region
        )

        if not historical_data or symbol not in historical_data:
            raise HTTPException(status_code=404, detail=f"No data found for symbol {symbol}")

        df = historical_data[symbol]

        if df is None or df.empty:
            raise HTTPException(status_code=404, detail=f"No data found for symbol {symbol}")

        # Calculate common indicators
        # RSI
        if 'close' in df.columns:
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['rsi'] = 100 - (100 / (1 + rs))

        # SMA
        if 'close' in df.columns:
            df['sma_20'] = df['close'].rolling(window=20).mean()
            df['sma_50'] = df['close'].rolling(window=50).mean()

        # EMA
        if 'close' in df.columns:
            df['ema_20'] = df['close'].ewm(span=20, adjust=False).mean()

        # Convert to JSON-serializable format
        df_copy = df.copy()
        df_copy['date'] = df_copy['date'].dt.strftime('%Y-%m-%d')
        price_data = df_copy.fillna(0).to_dict('records')

        return APIResponse(
            success=True,
            data={
                "symbol": symbol,
                "price_data": price_data,
                "data_points": len(price_data)
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch preview data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/visual/preview-signals", response_model=APIResponse)
async def preview_signals(
    request: PreviewSignalsRequest,
    current_user: Annotated[Dict[str, Any], Depends(get_enhanced_current_user)] = None,
):
    """Simulate signals based on conditions and historical data"""
    try:
        import pandas as pd

        # Convert price data to DataFrame
        df = pd.DataFrame(request.price_data)
        df['date'] = pd.to_datetime(df['date'])

        # Dynamically calculate any missing indicators based on conditions
        all_conditions = request.entry_conditions + request.exit_conditions
        for condition in all_conditions:
            if condition.get('type') == 'indicator_crossover':
                # Calculate SMAs/EMAs for crossover conditions
                indicator1 = condition.get('indicator1')
                indicator2 = condition.get('indicator2')
                period1 = condition.get('period1', 20)
                period2 = condition.get('period2', 50)

                if indicator1 == 'SMA':
                    col_name = f"sma_{period1}"
                    if col_name not in df.columns and 'close' in df.columns:
                        df[col_name] = df['close'].rolling(window=period1).mean()

                if indicator2 == 'SMA':
                    col_name = f"sma_{period2}"
                    if col_name not in df.columns and 'close' in df.columns:
                        df[col_name] = df['close'].rolling(window=period2).mean()

                if indicator1 == 'EMA':
                    col_name = f"ema_{period1}"
                    if col_name not in df.columns and 'close' in df.columns:
                        df[col_name] = df['close'].ewm(span=period1, adjust=False).mean()

                if indicator2 == 'EMA':
                    col_name = f"ema_{period2}"
                    if col_name not in df.columns and 'close' in df.columns:
                        df[col_name] = df['close'].ewm(span=period2, adjust=False).mean()

            elif condition.get('type') == 'indicator_comparison':
                # Calculate indicators for comparison conditions (e.g., RSI < 30)
                indicator = condition.get('indicator')
                period = condition.get('period', 14)  # Default period for indicators

                if indicator == 'RSI' and 'rsi' not in df.columns and 'close' in df.columns:
                    # Calculate RSI
                    delta = df['close'].diff()
                    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
                    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
                    rs = gain / loss
                    df['rsi'] = 100 - (100 / (1 + rs))

                elif indicator == 'SMA':
                    col_name = f"sma_{period}"
                    if col_name not in df.columns and 'close' in df.columns:
                        df[col_name] = df['close'].rolling(window=period).mean()

                elif indicator == 'EMA':
                    col_name = f"ema_{period}"
                    if col_name not in df.columns and 'close' in df.columns:
                        df[col_name] = df['close'].ewm(span=period, adjust=False).mean()

        signals = []
        in_position = False  # Track position state to avoid duplicate signals

        # Signal detection logic with position tracking
        for i in range(1, len(df)):
            current_row = df.iloc[i]
            prev_row = df.iloc[i-1]

            # Check entry conditions (only when NOT in position)
            if not in_position:
                entry_triggered = evaluate_conditions(
                    request.entry_conditions,
                    current_row,
                    prev_row
                )

                if entry_triggered:
                    signals.append({
                        "date": current_row['date'].strftime('%Y-%m-%d'),
                        "type": "buy",
                        "price": float(current_row['close']),
                        "reason": format_condition_reason(request.entry_conditions)
                    })
                    in_position = True  # Mark as in position

            # Check exit conditions (only when IN position)
            elif in_position:
                exit_triggered = evaluate_conditions(
                    request.exit_conditions,
                    current_row,
                    prev_row
                )

                if exit_triggered:
                    signals.append({
                        "date": current_row['date'].strftime('%Y-%m-%d'),
                        "type": "sell",
                        "price": float(current_row['close']),
                        "reason": format_condition_reason(request.exit_conditions)
                    })
                    in_position = False  # Mark as out of position

        # Calculate basic statistics
        buy_signals = [s for s in signals if s['type'] == 'buy']
        sell_signals = [s for s in signals if s['type'] == 'sell']

        # Estimate win rate and return
        estimated_win_rate = None
        estimated_return = None

        if len(buy_signals) > 0 and len(sell_signals) > 0:
            # Pair up buy and sell signals
            trades = []
            for i in range(min(len(buy_signals), len(sell_signals))):
                buy_price = buy_signals[i]['price']
                sell_price = sell_signals[i]['price']
                profit_pct = ((sell_price - buy_price) / buy_price) * 100
                trades.append(profit_pct)

            if trades:
                winning_trades = [t for t in trades if t > 0]
                estimated_win_rate = (len(winning_trades) / len(trades)) * 100
                estimated_return = sum(trades)

        # Portfolio simulation (if initial_capital provided)
        portfolio_simulation = None
        if request.initial_capital and len(signals) > 0:
            import pandas as pd
            from datetime import datetime as dt

            # Determine start date for simulation
            sim_start_date = request.start_date if request.start_date else df['date'].iloc[0].strftime('%Y-%m-%d')
            sim_end_date = df['date'].iloc[-1].strftime('%Y-%m-%d')

            # Filter signals from start date onwards
            filtered_signals = [s for s in signals if s['date'] >= sim_start_date]

            cash = float(request.initial_capital)
            shares = 0
            trades_executed = 0
            current_symbol = df.iloc[0].get('symbol', 'Unknown') if 'symbol' in df.columns else 'Unknown'

            # Simulate trading
            for signal in filtered_signals:
                if signal['type'] == 'buy' and shares == 0:
                    # Buy: invest all cash
                    shares = cash / signal['price']
                    cash = 0
                    trades_executed += 1

                elif signal['type'] == 'sell' and shares > 0:
                    # Sell: liquidate all shares
                    cash = shares * signal['price']
                    shares = 0
                    trades_executed += 1

            # Calculate final value (liquidate any remaining shares at last price)
            last_price = float(df['close'].iloc[-1])
            if shares > 0:
                final_value = shares * last_price
                current_position_shares = shares
                current_position_value = final_value
                cash_remaining = 0
            else:
                final_value = cash
                current_position_shares = 0
                current_position_value = 0
                cash_remaining = cash

            # Calculate P&L
            total_pnl_dollar = final_value - float(request.initial_capital)
            total_pnl_percent = (total_pnl_dollar / float(request.initial_capital)) * 100

            portfolio_simulation = {
                "initial_capital": float(request.initial_capital),
                "start_date": sim_start_date,
                "end_date": sim_end_date,
                "final_value": round(final_value, 2),
                "total_pnl_dollar": round(total_pnl_dollar, 2),
                "total_pnl_percent": round(total_pnl_percent, 2),
                "current_position": {
                    "shares": round(current_position_shares, 4),
                    "symbol": current_symbol,
                    "value": round(current_position_value, 2)
                },
                "trades_executed": trades_executed,
                "cash_remaining": round(cash_remaining, 2)
            }

        return APIResponse(
            success=True,
            data={
                "signals": signals,
                "estimated_win_rate": estimated_win_rate,
                "estimated_return": estimated_return,
                "portfolio_simulation": portfolio_simulation
            }
        )

    except Exception as e:
        logger.error(f"Failed to preview signals: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def evaluate_conditions(conditions: List[Dict[str, Any]], current_row, prev_row) -> bool:
    """Evaluate if conditions are met"""
    if not conditions:
        return False

    results = []

    for condition in conditions:
        cond_type = condition.get('type')

        if cond_type == 'indicator_comparison':
            indicator = condition.get('indicator')
            operator = condition.get('operator')
            value = condition.get('value')

            if indicator and operator and value is not None:
                indicator_value = current_row.get(indicator.lower())
                if indicator_value is not None and indicator_value != 0:
                    if operator == 'below':
                        results.append(indicator_value < value)
                    elif operator == 'above':
                        results.append(indicator_value > value)

        elif cond_type == 'indicator_crossover':
            indicator1 = condition.get('indicator1')
            indicator2 = condition.get('indicator2')
            direction = condition.get('direction')

            if indicator1 and indicator2 and direction:
                # Get indicator values with period suffixes
                period1 = condition.get('period1', 20)
                period2 = condition.get('period2', 50)

                # Try to find the right column name
                ind1_current = current_row.get(f"{indicator1.lower()}_{period1}") or current_row.get(indicator1.lower())
                ind2_current = current_row.get(f"{indicator2.lower()}_{period2}") or current_row.get(indicator2.lower())
                ind1_prev = prev_row.get(f"{indicator1.lower()}_{period1}") or prev_row.get(indicator1.lower())
                ind2_prev = prev_row.get(f"{indicator2.lower()}_{period2}") or prev_row.get(indicator2.lower())

                if all(v is not None and v != 0 for v in [ind1_current, ind2_current, ind1_prev, ind2_prev]):
                    if direction == 'above':
                        # Crosses above: was below, now above
                        results.append(ind1_prev < ind2_prev and ind1_current > ind2_current)
                    elif direction == 'below':
                        # Crosses below: was above, now below
                        results.append(ind1_prev > ind2_prev and ind1_current < ind2_current)

    # Combine with AND logic (all conditions must be true)
    return all(results) if results else False


def format_condition_reason(conditions: List[Dict[str, Any]]) -> str:
    """Format conditions into a human-readable reason"""
    if not conditions:
        return "No conditions"

    reasons = []
    for condition in conditions:
        cond_type = condition.get('type')

        if cond_type == 'indicator_comparison':
            indicator = condition.get('indicator', 'Unknown')
            operator = condition.get('operator', 'Unknown')
            value = condition.get('value', 0)
            reasons.append(f"{indicator} {operator} {value}")

        elif cond_type == 'indicator_crossover':
            indicator1 = condition.get('indicator1', 'Unknown')
            indicator2 = condition.get('indicator2', 'Unknown')
            direction = condition.get('direction', 'Unknown')
            reasons.append(f"{indicator1} crosses {direction} {indicator2}")

    return " AND ".join(reasons)


@router.post("/visual/suggest-strategies", response_model=APIResponse)
async def suggest_strategies(
    symbol: str = Query(..., description="Stock symbol"),
    days: int = Query(90, ge=7, le=365, description="Number of days of historical data"),
    style: str = Query('balanced', description="Trading style: conservative, balanced, or aggressive"),
    current_user: Annotated[Dict[str, Any], Depends(get_enhanced_current_user)] = None,
):
    """Analyze historical data and suggest optimal trading strategies"""
    try:
        from services.data_providers import DataProviderFactory
        from services.strategy_optimizer import StrategyOptimizer
        from datetime import timedelta
        import pandas as pd

        logger.info(f"Generating strategy suggestions for {symbol} ({days} days, {style} style)")

        # Calculate date range
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)

        # Get user region for data provider
        region = current_user.get('region', 'US')

        # Create data provider
        provider = DataProviderFactory.create_provider(
            broker='alpaca',
            region=region,
            config={'region': region}
        )

        # Fetch historical data
        historical_data = await provider.get_historical_data(
            symbols=[symbol],
            start_date=start_date,
            end_date=end_date,
            region=region
        )

        if not historical_data or symbol not in historical_data:
            raise HTTPException(status_code=404, detail=f"No data found for symbol {symbol}")

        df = historical_data[symbol]

        if df is None or df.empty:
            raise HTTPException(status_code=404, detail=f"No data found for symbol {symbol}")

        # Calculate indicators
        if 'close' in df.columns:
            # RSI
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['rsi'] = 100 - (100 / (1 + rs))

            # SMA
            df['sma_20'] = df['close'].rolling(window=20).mean()
            df['sma_50'] = df['close'].rolling(window=50).mean()

            # EMA
            df['ema_20'] = df['close'].ewm(span=20, adjust=False).mean()

        # Analyze and suggest strategies
        result = StrategyOptimizer.analyze_and_suggest_strategies(
            df=df,
            symbol=symbol,
            style=style,
            top_n=5
        )

        return APIResponse(
            success=True,
            data=result,
            message=f"Generated {len(result['suggestions'])} strategy suggestions"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to suggest strategies: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =====================================================
# Performance Analytics Endpoints
# =====================================================

@router.get("/{algorithm_id}/performance", response_model=APIResponse)
async def get_algorithm_performance(
    algorithm_id: str,
    current_user: Annotated[Dict[str, Any], Depends(get_enhanced_current_user)],
    db: AsyncSession = Depends(get_db),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    benchmark_symbol: str = Query('SPY', description="Benchmark symbol for comparison")
):
    """
    Get comprehensive performance metrics for an algorithm

    Returns:
    - Return metrics (total return, CAGR, daily/monthly returns)
    - Risk metrics (Sharpe, Sortino, max drawdown, volatility, beta, alpha)
    - Trade metrics (win rate, profit factor, expectancy, payoff ratio)
    - Equity curve data
    """
    try:
        from services.performance_analytics import get_performance_analytics
        from config.database import async_session

        user_id = current_user["id"]

        # Verify ownership
        result = await db.execute(text("""
            SELECT id FROM trading_algorithms
            WHERE id = :algorithm_id AND user_id = :user_id
        """), {"algorithm_id": algorithm_id, "user_id": user_id})

        if not result.fetchone():
            raise HTTPException(status_code=404, detail="Algorithm not found")

        # Get performance analytics service
        analytics = await get_performance_analytics(db_session_factory=async_session)

        # Calculate performance metrics
        start_dt = datetime.combine(start_date, datetime.min.time()) if start_date else None
        end_dt = datetime.combine(end_date, datetime.max.time()) if end_date else None

        performance = await analytics.calculate_algorithm_performance(
            algorithm_id=algorithm_id,
            start_date=start_dt,
            end_date=end_dt,
            benchmark_symbol=benchmark_symbol
        )

        return APIResponse(success=True, data=performance)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get algorithm performance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{algorithm_id}/equity-curve", response_model=APIResponse)
async def get_equity_curve(
    algorithm_id: str,
    current_user: Annotated[Dict[str, Any], Depends(get_enhanced_current_user)],
    db: AsyncSession = Depends(get_db),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None)
):
    """
    Get equity curve data for an algorithm

    Returns time series of portfolio value over time
    """
    try:
        user_id = current_user["id"]

        # Verify ownership
        result = await db.execute(text("""
            SELECT id FROM trading_algorithms
            WHERE id = :algorithm_id AND user_id = :user_id
        """), {"algorithm_id": algorithm_id, "user_id": user_id})

        if not result.fetchone():
            raise HTTPException(status_code=404, detail="Algorithm not found")

        # Build query
        query = """
            SELECT
                snapshot_date as date,
                total_value as equity,
                cumulative_pnl,
                daily_pnl
            FROM algorithm_performance_snapshots
            WHERE algorithm_id = :algorithm_id
        """

        params = {"algorithm_id": algorithm_id}

        if start_date:
            query += " AND snapshot_date >= :start_date"
            params["start_date"] = start_date

        if end_date:
            query += " AND snapshot_date <= :end_date"
            params["end_date"] = end_date

        query += " ORDER BY snapshot_date ASC"

        result = await db.execute(text(query), params)

        equity_curve = []
        for row in result.fetchall():
            equity_curve.append({
                "date": row.date.isoformat(),
                "equity": float(row.equity),
                "cumulative_pnl": float(row.cumulative_pnl) if row.cumulative_pnl else 0,
                "daily_pnl": float(row.daily_pnl) if row.daily_pnl else 0
            })

        return APIResponse(
            success=True,
            data={
                "equity_curve": equity_curve,
                "data_points": len(equity_curve)
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get equity curve: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{algorithm_id}/trade-history", response_model=APIResponse)
async def get_trade_history(
    algorithm_id: str,
    current_user: Annotated[Dict[str, Any], Depends(get_enhanced_current_user)],
    db: AsyncSession = Depends(get_db),
    limit: int = Query(100, le=500),
    offset: int = Query(0, ge=0)
):
    """
    Get trade history for an algorithm

    Returns list of executed trades with P&L information
    """
    try:
        user_id = current_user["id"]

        # Verify ownership
        result = await db.execute(text("""
            SELECT id FROM trading_algorithms
            WHERE id = :algorithm_id AND user_id = :user_id
        """), {"algorithm_id": algorithm_id, "user_id": user_id})

        if not result.fetchone():
            raise HTTPException(status_code=404, detail="Algorithm not found")

        # Get trades
        result = await db.execute(text("""
            SELECT
                id,
                symbol,
                action,
                quantity,
                executed_price,
                total_amount,
                pnl,
                executed_at,
                status
            FROM trades
            WHERE algorithm_id = :algorithm_id
            AND status = 'executed'
            ORDER BY executed_at DESC
            LIMIT :limit OFFSET :offset
        """), {
            "algorithm_id": algorithm_id,
            "limit": limit,
            "offset": offset
        })

        trades = []
        for row in result.fetchall():
            trades.append({
                "id": str(row.id),
                "symbol": row.symbol,
                "action": row.action,
                "quantity": float(row.quantity),
                "executed_price": float(row.executed_price) if row.executed_price else 0,
                "total_amount": float(row.total_amount) if row.total_amount else 0,
                "pnl": float(row.pnl) if row.pnl else 0,
                "executed_at": row.executed_at.isoformat(),
                "status": row.status
            })

        # Get total count
        count_result = await db.execute(text("""
            SELECT COUNT(*) as total
            FROM trades
            WHERE algorithm_id = :algorithm_id
            AND status = 'executed'
        """), {"algorithm_id": algorithm_id})

        total = count_result.fetchone().total

        return APIResponse(
            success=True,
            data={
                "trades": trades,
                "total": total,
                "limit": limit,
                "offset": offset
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get trade history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


