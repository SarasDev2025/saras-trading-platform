"""
Test Management Router

API endpoints for running tests, viewing results, and managing test runs.
"""
import logging
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from config.database import get_db_session, get_db
from services.test_runner_service import get_test_runner_service, TestRunnerService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tests", tags=["Test Management"])


# Request/Response Models

class RunTestsRequest(BaseModel):
    """Request to run tests"""
    test_type: str = Field("all", description="Type of tests: api, ui, integration, all")
    test_files: Optional[List[str]] = Field(None, description="Specific test files to run")
    markers: Optional[List[str]] = Field(None, description="Pytest markers to filter tests")
    version: Optional[str] = Field(None, description="Version being tested")
    git_commit: Optional[str] = Field(None, description="Git commit hash")


class TestRunResponse(BaseModel):
    """Test run response"""
    id: str
    version: Optional[str]
    git_commit: Optional[str]
    started_at: Optional[str]
    completed_at: Optional[str]
    status: str
    total_tests: int
    passed_tests: int
    failed_tests: int
    skipped_tests: int
    error_tests: Optional[int]
    coverage_pct: float
    test_type: str
    environment: str
    duration_ms: Optional[int]
    triggered_by: str


# Endpoints

@router.post("/run", response_model=dict)
async def run_tests(
    request: RunTestsRequest
):
    """
    Run tests and return test run ID

    Tests are executed in the background. Use GET /tests/runs/{id} to check status.
    """
    try:
        logger.info(
            f"Test run requested: {request.test_type}"
        )

        test_runner = await get_test_runner_service(db_session_factory=get_db_session)

        test_run_id = await test_runner.run_tests(
            test_type=request.test_type,
            test_files=request.test_files,
            markers=request.markers,
            version=request.version,
            git_commit=request.git_commit,
            triggered_by='test-runner'
        )

        return {
            "success": True,
            "test_run_id": test_run_id,
            "message": f"Test run started. Use GET /api/v1/tests/runs/{test_run_id} to check status."
        }

    except Exception as e:
        logger.error(f"Error starting test run: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to start test run: {str(e)}")


@router.get("/runs/{test_run_id}", response_model=TestRunResponse)
async def get_test_run(
    test_run_id: str
):
    """
    Get test run details by ID

    Returns comprehensive information about a test run including all results.
    """
    try:
        test_runner = await get_test_runner_service(db_session_factory=get_db_session)
        test_run = await test_runner.get_test_run(test_run_id)

        if not test_run:
            raise HTTPException(status_code=404, detail="Test run not found")

        return test_run

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting test run: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get test run: {str(e)}")


@router.get("/runs", response_model=dict)
async def list_test_runs(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status: Optional[str] = Query(None),
    test_type: Optional[str] = Query(None)
):
    """
    List test runs with optional filtering

    Returns paginated list of test runs with summary information.
    """
    try:
        test_runner = await get_test_runner_service(db_session_factory=get_db_session)

        test_runs = await test_runner.list_test_runs(
            limit=limit,
            offset=offset,
            status=status,
            test_type=test_type
        )

        return {
            "success": True,
            "data": test_runs,
            "total": len(test_runs),
            "limit": limit,
            "offset": offset
        }

    except Exception as e:
        logger.error(f"Error listing test runs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to list test runs: {str(e)}")


@router.get("/runs/{test_run_id}/results", response_model=dict)
async def get_test_results(
    test_run_id: str,
    status: Optional[str] = Query(None, description="Filter by status: passed, failed, skipped"),
    db = Depends(get_db)
):
    """
    Get detailed test results for a test run

    Returns list of individual test results with error messages and traces.
    """
    try:
        if True:  # Keep indentation
            from sqlalchemy import text

            query = """
                SELECT
                    id, test_name, test_file, test_class, test_function,
                    status, duration_ms, error_message, error_trace,
                    markers, executed_at
                FROM test_results
                WHERE test_run_id = :test_run_id
            """

            params = {'test_run_id': test_run_id}

            if status:
                query += " AND status = :status"
                params['status'] = status

            query += " ORDER BY test_file, test_name"

            result = await db.execute(text(query), params)
            rows = result.fetchall()

            test_results = [
                {
                    'id': str(row.id),
                    'test_name': row.test_name,
                    'test_file': row.test_file,
                    'test_class': row.test_class,
                    'test_function': row.test_function,
                    'status': row.status,
                    'duration_ms': row.duration_ms,
                    'error_message': row.error_message,
                    'error_trace': row.error_trace,
                    'markers': row.markers,
                    'executed_at': row.executed_at.isoformat() if row.executed_at else None
                }
                for row in rows
            ]

            return {
                "success": True,
                "test_run_id": test_run_id,
                "data": test_results,
                "total": len(test_results)
            }

    except Exception as e:
        logger.error(f"Error getting test results: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get test results: {str(e)}")


@router.get("/screenshots/{filename}")
async def get_screenshot(filename: str):
    """
    Get screenshot file from test execution

    Returns the screenshot image file.
    """
    try:
        from pathlib import Path
        from fastapi.responses import FileResponse

        screenshot_path = Path(__file__).parent.parent / "screenshots" / filename

        if not screenshot_path.exists():
            raise HTTPException(status_code=404, detail="Screenshot not found")

        # Verify it's actually in the screenshots directory (security check)
        if "screenshots" not in str(screenshot_path.resolve()):
            raise HTTPException(status_code=403, detail="Invalid screenshot path")

        return FileResponse(screenshot_path, media_type="image/png")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting screenshot: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get screenshot: {str(e)}")


@router.get("/screenshots", response_model=dict)
async def list_screenshots():
    """
    List all available screenshots from recent test runs

    Returns list of screenshot filenames with metadata.
    """
    try:
        from pathlib import Path
        import os

        screenshots_dir = Path(__file__).parent.parent / "screenshots"

        if not screenshots_dir.exists():
            return {
                "success": True,
                "screenshots": []
            }

        screenshots = []
        for screenshot_file in screenshots_dir.glob("*.png"):
            stat = screenshot_file.stat()
            screenshots.append({
                "filename": screenshot_file.name,
                "size": stat.st_size,
                "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "url": f"/api/v1/tests/screenshots/{screenshot_file.name}"
            })

        # Sort by creation time, newest first
        screenshots.sort(key=lambda x: x['created_at'], reverse=True)

        return {
            "success": True,
            "total": len(screenshots),
            "screenshots": screenshots
        }

    except Exception as e:
        logger.error(f"Error listing screenshots: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to list screenshots: {str(e)}")


@router.get("/coverage", response_model=dict)
async def get_coverage_report():
    """
    Get latest coverage report

    Returns coverage statistics and file-level coverage data.
    """
    try:
        import json
        from pathlib import Path

        coverage_file = Path(__file__).parent.parent / "coverage.json"

        if not coverage_file.exists():
            return {
                "success": False,
                "message": "No coverage report available. Run tests first."
            }

        with open(coverage_file, 'r') as f:
            coverage_data = json.load(f)

        return {
            "success": True,
            "data": coverage_data
        }

    except Exception as e:
        logger.error(f"Error getting coverage report: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get coverage report: {str(e)}")


@router.get("/discover", response_model=dict)
async def discover_tests():
    """
    Discover all available tests

    Returns list of all test files and individual test cases with their source code.
    """
    try:
        import subprocess
        import json
        from pathlib import Path
        import ast
        import inspect

        # Run pytest in collect-only mode to discover tests
        result = subprocess.run(
            ['pytest', '--collect-only', '-q', 'tests/'],
            cwd=Path(__file__).parent.parent,
            capture_output=True,
            text=True,
            timeout=30
        )

        # Parse pytest output to get test names
        test_items = []
        for line in result.stdout.split('\n'):
            if '::' in line and not line.startswith(' '):
                test_items.append(line.strip())

        # Now read the test files to get source code and descriptions
        tests = []
        tests_dir = Path(__file__).parent.parent / 'tests'

        for test_file in tests_dir.glob('test_*.py'):
            try:
                with open(test_file, 'r') as f:
                    source = f.read()
                    tree = ast.parse(source)

                # Process tree.body directly (not using ast.walk which doesn't preserve structure)
                for node in tree.body:
                    if isinstance(node, ast.ClassDef) and node.name.startswith('Test'):
                        # Tests inside classes
                        class_name = node.name

                        # Get class-level markers
                        class_markers = []
                        for decorator in node.decorator_list:
                            if isinstance(decorator, ast.Attribute):
                                # Handle @pytest.mark.marker_name
                                if hasattr(decorator.value, 'attr') and decorator.value.attr == 'mark':
                                    if hasattr(decorator.value.value, 'id') and decorator.value.value.id == 'pytest':
                                        class_markers.append(decorator.attr)
                            elif isinstance(decorator, ast.Call):
                                # Handle @pytest.mark.marker_name(...)
                                if isinstance(decorator.func, ast.Attribute):
                                    if hasattr(decorator.func.value, 'attr') and decorator.func.value.attr == 'mark':
                                        if hasattr(decorator.func.value.value, 'id') and decorator.func.value.value.id == 'pytest':
                                            class_markers.append(decorator.func.attr)

                        # Process methods in class (both sync and async)
                        for item in node.body:
                            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and item.name.startswith('test_'):
                                # Get function source code
                                func_source = ast.get_source_segment(source, item)

                                # Get docstring if available
                                docstring = ast.get_docstring(item) or "No description"

                                # Get method-level markers (combine with class markers)
                                markers = class_markers.copy()
                                for decorator in item.decorator_list:
                                    if isinstance(decorator, ast.Attribute):
                                        # Handle @pytest.mark.marker_name
                                        if hasattr(decorator.value, 'attr') and decorator.value.attr == 'mark':
                                            if hasattr(decorator.value.value, 'id') and decorator.value.value.id == 'pytest':
                                                if decorator.attr not in markers:
                                                    markers.append(decorator.attr)
                                    elif isinstance(decorator, ast.Call):
                                        # Handle @pytest.mark.marker_name(...)
                                        if isinstance(decorator.func, ast.Attribute):
                                            if hasattr(decorator.func.value, 'attr') and decorator.func.value.attr == 'mark':
                                                if hasattr(decorator.func.value.value, 'id') and decorator.func.value.value.id == 'pytest':
                                                    if decorator.func.attr not in markers:
                                                        markers.append(decorator.func.attr)

                                test_id = f"{test_file.name}::{class_name}::{item.name}"

                                tests.append({
                                    'id': test_id,
                                    'name': item.name,
                                    'class': class_name,
                                    'file': str(test_file.relative_to(tests_dir.parent)),
                                    'description': docstring,
                                    'source_code': func_source or '',
                                    'markers': markers,
                                    'line_number': item.lineno
                                })

                    elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith('test_'):
                        # Standalone test functions (not in classes, both sync and async)
                        # Get function source code
                        func_source = ast.get_source_segment(source, node)

                        # Get docstring if available
                        docstring = ast.get_docstring(node) or "No description"

                        # Get markers
                        markers = []
                        for decorator in node.decorator_list:
                            if isinstance(decorator, ast.Attribute):
                                # Handle @pytest.mark.marker_name
                                if hasattr(decorator.value, 'attr') and decorator.value.attr == 'mark':
                                    if hasattr(decorator.value.value, 'id') and decorator.value.value.id == 'pytest':
                                        markers.append(decorator.attr)
                            elif isinstance(decorator, ast.Call):
                                # Handle @pytest.mark.marker_name(...)
                                if isinstance(decorator.func, ast.Attribute):
                                    if hasattr(decorator.func.value, 'attr') and decorator.func.value.attr == 'mark':
                                        if hasattr(decorator.func.value.value, 'id') and decorator.func.value.value.id == 'pytest':
                                            markers.append(decorator.func.attr)

                        test_id = f"{test_file.name}::{node.name}"

                        tests.append({
                            'id': test_id,
                            'name': node.name,
                            'class': None,
                            'file': str(test_file.relative_to(tests_dir.parent)),
                            'description': docstring,
                            'source_code': func_source or '',
                            'markers': markers,
                            'line_number': node.lineno
                        })
            except Exception as e:
                logger.warning(f"Error parsing test file {test_file}: {e}")

        return {
            "success": True,
            "total": len(tests),
            "tests": tests
        }

    except Exception as e:
        logger.error(f"Error discovering tests: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to discover tests: {str(e)}")


@router.get("/stats", response_model=dict)
async def get_test_stats(
    days: int = Query(7, ge=1, le=90, description="Number of days to analyze"),
    db = Depends(get_db)
):
    """
    Get test statistics and trends

    Returns aggregated statistics over the specified time period.
    """
    try:
        if True:  # Keep indentation
            from sqlalchemy import text

            result = await db.execute(
                text(f"""
                    SELECT
                        COUNT(*) as total_runs,
                        COUNT(*) FILTER (WHERE status = 'passed') as passed_runs,
                        COUNT(*) FILTER (WHERE status = 'failed') as failed_runs,
                        AVG(coverage_pct) as avg_coverage,
                        AVG(duration_ms) as avg_duration_ms,
                        AVG(total_tests) as avg_total_tests,
                        AVG(CASE WHEN total_tests > 0 THEN (passed_tests::float / total_tests * 100) ELSE 0 END) as avg_pass_rate
                    FROM test_runs
                    WHERE started_at >= NOW() - INTERVAL '{days} days'
                    AND status != 'running'
                """)
            )

            stats = result.fetchone()

            return {
                "success": True,
                "data": {
                    "total_runs": stats.total_runs or 0,
                    "passed_runs": stats.passed_runs or 0,
                    "failed_runs": stats.failed_runs or 0,
                    "avg_coverage_pct": float(stats.avg_coverage or 0),
                    "avg_duration_ms": int(stats.avg_duration_ms or 0),
                    "avg_total_tests": int(stats.avg_total_tests or 0),
                    "avg_pass_rate_pct": float(stats.avg_pass_rate or 0),
                    "period_days": days
                }
            }

    except Exception as e:
        logger.error(f"Error getting test stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get test stats: {str(e)}")
