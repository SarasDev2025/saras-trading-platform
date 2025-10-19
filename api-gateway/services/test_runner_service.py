"""
Test Runner Service

Programmatically executes pytest tests and stores results in database.
Provides real-time progress updates via WebSocket.
"""
import asyncio
import subprocess
import json
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
import xml.etree.ElementTree as ET

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class TestRunnerService:
    """Service for running tests and tracking results"""

    def __init__(self, db_session_factory):
        """
        Initialize Test Runner Service

        Args:
            db_session_factory: Database session factory
        """
        self.db_session_factory = db_session_factory
        self.active_runs: Dict[str, Dict] = {}

    async def run_tests(
        self,
        test_type: str = "all",
        test_files: Optional[List[str]] = None,
        markers: Optional[List[str]] = None,
        version: Optional[str] = None,
        git_commit: Optional[str] = None,
        triggered_by: str = "manual",
        environment: str = "development"
    ) -> str:
        """
        Run tests and store results

        Args:
            test_type: Type of tests to run (api, ui, integration, all)
            test_files: Specific test files to run (optional)
            markers: Pytest markers to filter tests (optional)
            version: Version being tested
            git_commit: Git commit hash
            triggered_by: Who/what triggered the tests
            environment: Environment (development, staging, production)

        Returns:
            Test run ID
        """
        test_run_id = str(uuid.uuid4())

        try:
            # Create test run record
            await self._create_test_run(
                test_run_id=test_run_id,
                test_type=test_type,
                version=version,
                git_commit=git_commit,
                triggered_by=triggered_by,
                environment=environment
            )

            # Build pytest command
            pytest_cmd = self._build_pytest_command(
                test_type=test_type,
                test_files=test_files,
                markers=markers
            )

            # Run tests in background
            asyncio.create_task(
                self._execute_tests(test_run_id, pytest_cmd)
            )

            return test_run_id

        except Exception as e:
            logger.error(f"Error starting test run: {e}", exc_info=True)
            await self._update_test_run_status(
                test_run_id=test_run_id,
                status="error",
                error=str(e)
            )
            raise

    def _build_pytest_command(
        self,
        test_type: str,
        test_files: Optional[List[str]] = None,
        markers: Optional[List[str]] = None
    ) -> List[str]:
        """Build pytest command with appropriate arguments"""
        cmd = [
            "pytest",
            "-v",
            "--tb=short",
            "--json-report",
            "--json-report-file=test_report.json",
            "--html=test_report.html",
            "--self-contained-html",
            "--cov=.",
            "--cov-report=json:coverage.json",
            "--cov-report=html:htmlcov"
        ]

        # Add test files or specific test IDs (e.g., tests/test_auth.py::test_login)
        if test_files:
            # Ensure test files have "tests/" prefix if they don't already
            normalized_files = []
            for test_file in test_files:
                if not test_file.startswith("tests/"):
                    normalized_files.append(f"tests/{test_file}")
                else:
                    normalized_files.append(test_file)
            cmd.extend(normalized_files)
        else:
            cmd.append("tests/")

        # Add markers
        if markers:
            for marker in markers:
                cmd.extend(["-m", marker])
        elif test_type != "all":
            # Map test type to marker
            cmd.extend(["-m", test_type])

        return cmd

    async def _execute_tests(self, test_run_id: str, pytest_cmd: List[str]):
        """Execute pytest and parse results"""
        start_time = datetime.utcnow()

        try:
            # Store active run
            self.active_runs[test_run_id] = {
                'status': 'running',
                'started_at': start_time
            }

            # Ensure screenshots directory exists
            screenshots_dir = Path(__file__).parent.parent / "screenshots"
            screenshots_dir.mkdir(exist_ok=True)

            # Set up environment with PYTHONPATH and TEST_DATABASE_URL
            import os
            env = os.environ.copy()
            env['PYTHONPATH'] = str(Path(__file__).parent.parent)
            # Use Docker service name for database connection
            env['TEST_DATABASE_URL'] = 'postgresql+asyncpg://trading_user:dev_password_123@trading_postgres_dev:5432/trading_test'

            # Execute pytest
            process = await asyncio.create_subprocess_exec(
                *pytest_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=Path(__file__).parent.parent,
                env=env
            )

            stdout, stderr = await process.communicate()

            # Calculate duration
            end_time = datetime.utcnow()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)

            # Parse results
            results = await self._parse_test_results(test_run_id)

            # Determine overall status
            status = "passed" if results['failed_tests'] == 0 else "failed"

            # Update test run
            await self._update_test_run(
                test_run_id=test_run_id,
                status=status,
                total_tests=results['total_tests'],
                passed_tests=results['passed_tests'],
                failed_tests=results['failed_tests'],
                skipped_tests=results['skipped_tests'],
                error_tests=results['error_tests'],
                coverage_pct=results['coverage_pct'],
                duration_ms=duration_ms
            )

            # Store individual test results
            await self._store_test_results(
                test_run_id=test_run_id,
                test_results=results['tests']
            )

            # Remove from active runs
            self.active_runs.pop(test_run_id, None)

            logger.info(
                f"Test run {test_run_id} completed: "
                f"{results['passed_tests']}/{results['total_tests']} passed"
            )

        except Exception as e:
            logger.error(f"Error executing tests: {e}", exc_info=True)
            await self._update_test_run_status(
                test_run_id=test_run_id,
                status="error",
                error=str(e)
            )
            self.active_runs.pop(test_run_id, None)

    async def _parse_test_results(self, test_run_id: str) -> Dict:
        """Parse pytest JSON report"""
        try:
            report_file = Path(__file__).parent.parent / "test_report.json"

            if not report_file.exists():
                logger.warning("Test report file not found")
                return {
                    'total_tests': 0,
                    'passed_tests': 0,
                    'failed_tests': 0,
                    'skipped_tests': 0,
                    'error_tests': 0,
                    'coverage_pct': 0,
                    'tests': []
                }

            with open(report_file, 'r') as f:
                report = json.load(f)

            # Parse coverage
            coverage_pct = 0
            coverage_file = Path(__file__).parent.parent / "coverage.json"
            if coverage_file.exists():
                with open(coverage_file, 'r') as f:
                    coverage = json.load(f)
                    coverage_pct = coverage.get('totals', {}).get('percent_covered', 0)

            # Parse test results
            tests = []
            summary = report.get('summary', {})

            for test in report.get('tests', []):
                tests.append({
                    'test_name': test.get('nodeid', ''),
                    'test_file': test.get('filename', ''),
                    'test_class': test.get('classname'),
                    'test_function': test.get('name', ''),
                    'status': test.get('outcome', 'unknown'),
                    'duration_ms': int(test.get('duration', 0) * 1000),
                    'error_message': test.get('call', {}).get('crash', {}).get('message'),
                    'error_trace': test.get('call', {}).get('longrepr'),
                    'markers': test.get('markers', [])
                })

            return {
                'total_tests': summary.get('total', 0),
                'passed_tests': summary.get('passed', 0),
                'failed_tests': summary.get('failed', 0),
                'skipped_tests': summary.get('skipped', 0),
                'error_tests': summary.get('error', 0),
                'coverage_pct': coverage_pct,
                'tests': tests
            }

        except Exception as e:
            logger.error(f"Error parsing test results: {e}", exc_info=True)
            return {
                'total_tests': 0,
                'passed_tests': 0,
                'failed_tests': 0,
                'skipped_tests': 0,
                'error_tests': 0,
                'coverage_pct': 0,
                'tests': []
            }

    async def _create_test_run(
        self,
        test_run_id: str,
        test_type: str,
        version: Optional[str],
        git_commit: Optional[str],
        triggered_by: str,
        environment: str
    ):
        """Create test run record in database"""
        try:
            async with self.db_session_factory() as db:
                await db.execute(
                    text("""
                        INSERT INTO test_runs
                        (id, version, git_commit, test_type, triggered_by, environment, status)
                        VALUES
                        (:id, :version, :git_commit, :test_type, :triggered_by, :environment, 'running')
                    """),
                    {
                        'id': test_run_id,
                        'version': version,
                        'git_commit': git_commit,
                        'test_type': test_type,
                        'triggered_by': triggered_by,
                        'environment': environment
                    }
                )
                await db.commit()

        except Exception as e:
            logger.error(f"Error creating test run record: {e}")
            raise

    async def _update_test_run(
        self,
        test_run_id: str,
        status: str,
        total_tests: int,
        passed_tests: int,
        failed_tests: int,
        skipped_tests: int,
        error_tests: int,
        coverage_pct: float,
        duration_ms: int
    ):
        """Update test run with results"""
        try:
            async with self.db_session_factory() as db:
                await db.execute(
                    text("""
                        UPDATE test_runs
                        SET status = :status,
                            total_tests = :total_tests,
                            passed_tests = :passed_tests,
                            failed_tests = :failed_tests,
                            skipped_tests = :skipped_tests,
                            error_tests = :error_tests,
                            coverage_pct = :coverage_pct,
                            duration_ms = :duration_ms,
                            completed_at = NOW()
                        WHERE id = :id
                    """),
                    {
                        'id': test_run_id,
                        'status': status,
                        'total_tests': total_tests,
                        'passed_tests': passed_tests,
                        'failed_tests': failed_tests,
                        'skipped_tests': skipped_tests,
                        'error_tests': error_tests,
                        'coverage_pct': coverage_pct,
                        'duration_ms': duration_ms
                    }
                )
                await db.commit()

        except Exception as e:
            logger.error(f"Error updating test run: {e}")

    async def _update_test_run_status(
        self,
        test_run_id: str,
        status: str,
        error: Optional[str] = None
    ):
        """Update test run status"""
        try:
            async with self.db_session_factory() as db:
                await db.execute(
                    text("""
                        UPDATE test_runs
                        SET status = :status,
                            completed_at = NOW()
                        WHERE id = :id
                    """),
                    {
                        'id': test_run_id,
                        'status': status
                    }
                )
                await db.commit()

        except Exception as e:
            logger.error(f"Error updating test run status: {e}")

    async def _store_test_results(
        self,
        test_run_id: str,
        test_results: List[Dict]
    ):
        """Store individual test results"""
        try:
            async with self.db_session_factory() as db:
                for test in test_results:
                    await db.execute(
                        text("""
                            INSERT INTO test_results
                            (test_run_id, test_name, test_file, test_class, test_function,
                             status, duration_ms, error_message, error_trace, markers)
                            VALUES
                            (:test_run_id, :test_name, :test_file, :test_class, :test_function,
                             :status, :duration_ms, :error_message, :error_trace, :markers)
                        """),
                        {
                            'test_run_id': test_run_id,
                            'test_name': test['test_name'],
                            'test_file': test['test_file'],
                            'test_class': test['test_class'],
                            'test_function': test['test_function'],
                            'status': test['status'],
                            'duration_ms': test['duration_ms'],
                            'error_message': test['error_message'],
                            'error_trace': test['error_trace'],
                            'markers': test['markers']
                        }
                    )
                await db.commit()

        except Exception as e:
            logger.error(f"Error storing test results: {e}")

    async def get_test_run(self, test_run_id: str) -> Optional[Dict]:
        """Get test run by ID"""
        try:
            async with self.db_session_factory() as db:
                result = await db.execute(
                    text("""
                        SELECT * FROM test_runs WHERE id = :id
                    """),
                    {'id': test_run_id}
                )

                row = result.fetchone()
                if not row:
                    return None

                return {
                    'id': str(row.id),
                    'version': row.version,
                    'git_commit': row.git_commit,
                    'started_at': row.started_at.isoformat() if row.started_at else None,
                    'completed_at': row.completed_at.isoformat() if row.completed_at else None,
                    'status': row.status,
                    'total_tests': row.total_tests,
                    'passed_tests': row.passed_tests,
                    'failed_tests': row.failed_tests,
                    'skipped_tests': row.skipped_tests,
                    'error_tests': row.error_tests,
                    'coverage_pct': float(row.coverage_pct) if row.coverage_pct else 0,
                    'test_type': row.test_type,
                    'environment': row.environment,
                    'duration_ms': row.duration_ms,
                    'triggered_by': row.triggered_by
                }

        except Exception as e:
            logger.error(f"Error getting test run: {e}")
            return None

    async def list_test_runs(
        self,
        limit: int = 50,
        offset: int = 0,
        status: Optional[str] = None,
        test_type: Optional[str] = None
    ) -> List[Dict]:
        """List test runs with optional filtering"""
        try:
            async with self.db_session_factory() as db:
                query = "SELECT * FROM test_runs WHERE 1=1"
                params = {'limit': limit, 'offset': offset}

                if status:
                    query += " AND status = :status"
                    params['status'] = status

                if test_type:
                    query += " AND test_type = :test_type"
                    params['test_type'] = test_type

                query += " ORDER BY started_at DESC LIMIT :limit OFFSET :offset"

                result = await db.execute(text(query), params)
                rows = result.fetchall()

                return [
                    {
                        'id': str(row.id),
                        'version': row.version,
                        'git_commit': row.git_commit,
                        'started_at': row.started_at.isoformat() if row.started_at else None,
                        'completed_at': row.completed_at.isoformat() if row.completed_at else None,
                        'status': row.status,
                        'total_tests': row.total_tests,
                        'passed_tests': row.passed_tests,
                        'failed_tests': row.failed_tests,
                        'skipped_tests': row.skipped_tests,
                        'coverage_pct': float(row.coverage_pct) if row.coverage_pct else 0,
                        'test_type': row.test_type,
                        'environment': row.environment,
                        'duration_ms': row.duration_ms,
                        'triggered_by': row.triggered_by
                    }
                    for row in rows
                ]

        except Exception as e:
            logger.error(f"Error listing test runs: {e}")
            return []


# Singleton instance
_test_runner_service: Optional[TestRunnerService] = None


async def get_test_runner_service(db_session_factory=None) -> TestRunnerService:
    """Get or create TestRunnerService singleton"""
    global _test_runner_service

    if _test_runner_service is None:
        if db_session_factory is None:
            raise ValueError("db_session_factory required for first initialization")

        _test_runner_service = TestRunnerService(
            db_session_factory=db_session_factory
        )

    return _test_runner_service
