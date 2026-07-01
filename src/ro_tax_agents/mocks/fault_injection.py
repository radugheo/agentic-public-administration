"""L3 controlled fault injection for mocked environment boundaries.

Fault injection is applied as a cross-cutting concern via the
``@with_fault_injection`` decorator.  Mock function bodies remain free
of injection logic — they contain only normal mock behaviour.

Fault operators
---------------
- **timeout**    — raises ``TimeoutError``
- **delay**      — adds latency (1 … max_delay_ms milliseconds)
- **partial**    — nullifies one payload field
- **corruption** — replaces one payload field with a sentinel value
"""

from __future__ import annotations

import functools
import logging
import time
from dataclasses import fields, is_dataclass, replace
from random import Random
from typing import Any, Callable, TypeVar

from ro_tax_agents.config.settings import settings

F = TypeVar("F", bound=Callable[..., Any])

logger = logging.getLogger("ro_tax_agents.l3_fault_injection")

OPERATORS = ("timeout", "delay", "partial", "corruption")


# ---------------------------------------------------------------------------
# Core injector
# ---------------------------------------------------------------------------

class EnvironmentFaultInjector:
    """Controlled fault injector for mocked external-environment boundaries."""

    def __init__(
        self,
        *,
        seed: int | None = None,
        rate: float | None = None,
        max_delay_ms: int | None = None,
    ) -> None:
        self._seed = seed if seed is not None else settings.l3_fault_injection_seed
        self._rate = rate if rate is not None else settings.l3_fault_injection_rate
        self._max_delay_ms = (
            max_delay_ms if max_delay_ms is not None else settings.l3_fault_max_delay_ms
        )
        self._rng = Random(self._seed)
        self.events: list[dict[str, Any]] = []

    def reset(self, seed: int | None = None) -> None:
        """Re-seed the RNG and clear recorded events."""
        self._rng = Random(seed if seed is not None else self._seed)
        self.events.clear()

    # -- decision ----------------------------------------------------------

    def _should_inject(self) -> bool:
        return (
            settings.l3_fault_injection_enabled
            and self._rng.random() < self._rate
        )

    # -- operators ---------------------------------------------------------

    def _inject_delay(self) -> float:
        if self._max_delay_ms <= 0:
            return 0.0
        delay_ms = self._rng.randint(1, self._max_delay_ms)
        time.sleep(delay_ms / 1000.0)
        return float(delay_ms)

    def _mutate_payload(self, payload: Any, marker: Any) -> Any:
        """Replace a single element/field in *payload* with *marker*."""
        if isinstance(payload, dict) and payload:
            mutated = dict(payload)
            key = self._rng.choice(list(mutated.keys()))
            mutated[key] = marker
            return mutated

        if is_dataclass(payload) and not isinstance(payload, type):
            field_names = [f.name for f in fields(payload)]
            if field_names:
                key = self._rng.choice(field_names)
                return replace(payload, **{key: marker})

        if isinstance(payload, list) and payload:
            mutated = list(payload)
            idx = self._rng.randrange(len(mutated))
            mutated[idx] = marker
            return mutated

        if isinstance(payload, bytes):
            return b"__CORRUPTED__"

        if isinstance(payload, str):
            return "__CORRUPTED__"

        return payload

    # -- public entry point ------------------------------------------------

    def inject(self, operation: str, payload: Any) -> Any:
        """Conditionally apply a fault to *payload*.

        Returns the (possibly mutated) payload, or raises ``TimeoutError``.
        """
        if not self._should_inject():
            return payload

        operator = self._rng.choice(list(OPERATORS))
        event: dict[str, Any] = {"operation": operation, "fault_type": operator}

        if operator == "timeout":
            logger.warning("L3 fault injected | op=%s | type=timeout", operation)
            self.events.append(event)
            raise TimeoutError(
                f"Injected timeout at mocked environment boundary: {operation}"
            )

        if operator == "delay":
            delay = self._inject_delay()
            event["delay_ms"] = delay
            logger.warning(
                "L3 fault injected | op=%s | type=delay | ms=%.0f", operation, delay
            )
            self.events.append(event)
            return payload

        if operator == "partial":
            mutated = self._mutate_payload(payload, None)
            logger.warning("L3 fault injected | op=%s | type=partial", operation)
            self.events.append(event)
            return mutated

        # corruption
        mutated = self._mutate_payload(payload, "__CORRUPTED__")
        logger.warning("L3 fault injected | op=%s | type=corruption", operation)
        self.events.append(event)
        return mutated


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

fault_injector = EnvironmentFaultInjector()


# ---------------------------------------------------------------------------
# Decorator — the sole integration point between mocks and fault injection
# ---------------------------------------------------------------------------

def with_fault_injection(operation: str) -> Callable[[F], F]:
    """Decorator that routes a function's return value through the injector.

    The decorated function's body stays free of fault-injection logic::

        @with_fault_injection("mock_spv_login")
        def mock_spv_login(username: str, password: str) -> dict:
            return {"success": True, ...}
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            result = func(*args, **kwargs)
            return fault_injector.inject(operation, result)

        return wrapper  # type: ignore[return-value]

    return decorator
