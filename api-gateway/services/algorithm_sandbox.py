"""
Lightweight sandbox for executing user-supplied algorithm code.

Provides a constrained global namespace and enforces execution timeouts so that
algorithm strategies cannot access sensitive runtime primitives.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, Optional


logger = logging.getLogger(__name__)


class AlgorithmSandboxError(RuntimeError):
    """Raised when sandbox execution fails or times out."""


class AlgorithmSandbox:
    """Utility for running strategy code with restricted globals."""

    DEFAULT_TIMEOUT_SECONDS = 2.0

    _SAFE_BUILTINS = {
        "abs": abs,
        "all": all,
        "any": any,
        "bool": bool,
        "dict": dict,
        "enumerate": enumerate,
        "float": float,
        "int": int,
        "len": len,
        "list": list,
        "max": max,
        "min": min,
        "pow": pow,
        "range": range,
        "round": round,
        "sorted": sorted,
        "sum": sum,
        "tuple": tuple,
        "zip": zip,
        "ValueError": ValueError,
        "TypeError": TypeError,
        "Exception": Exception,
    }

    @classmethod
    async def execute(
        cls,
        *,
        code: str,
        extra_globals: Dict[str, Any],
        local_context: Dict[str, Any],
        timeout: Optional[float] = None,
    ) -> None:
        """
        Execute the supplied code within the sandbox.

        Args:
            code: Strategy source code.
            extra_globals: Additional names exposed to the sandbox (e.g. helpers, pandas).
            local_context: Mutable context dict shared with the strategy.
            timeout: Optional timeout in seconds (defaults to DEFAULT_TIMEOUT_SECONDS).
        """
        sandbox_globals = cls._build_globals(extra_globals)
        effective_timeout = timeout or cls.DEFAULT_TIMEOUT_SECONDS

        def _runner():
            exec(code, sandbox_globals, local_context)

        try:
            await asyncio.wait_for(asyncio.to_thread(_runner), effective_timeout)
        except asyncio.TimeoutError as exc:
            logger.warning("Algorithm execution timed out after %.2fs", effective_timeout)
            raise AlgorithmSandboxError("Algorithm execution timed out") from exc
        except AlgorithmSandboxError:
            raise
        except Exception as exc:  # pylint: disable=broad-except
            raise AlgorithmSandboxError(str(exc)) from exc

    @classmethod
    def _build_globals(cls, extra_globals: Dict[str, Any]) -> Dict[str, Any]:
        sandbox_globals: Dict[str, Any] = {"__builtins__": cls._SAFE_BUILTINS.copy()}
        sandbox_globals.update(extra_globals)
        return sandbox_globals
