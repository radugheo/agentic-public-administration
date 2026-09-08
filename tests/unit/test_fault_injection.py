"""Tests for L3 controlled fault injection."""

import pytest
from unittest.mock import patch
from dataclasses import dataclass

from ro_tax_agents.mocks.fault_injection import (
    EnvironmentFaultInjector,
    fault_injector,
    with_fault_injection,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

@dataclass
class _SampleDC:
    a: str
    b: int


def _enabled(**overrides):
    """Return a patch context that enables fault injection."""
    defaults = {
        "l3_fault_injection_enabled": True,
        "l3_fault_injection_rate": 1.0,
        "l3_fault_injection_seed": 42,
        "l3_fault_max_delay_ms": 0,  # no actual sleeping
    }
    defaults.update(overrides)
    return patch.multiple("ro_tax_agents.mocks.fault_injection.settings", **defaults)


def _disabled():
    return patch(
        "ro_tax_agents.mocks.fault_injection.settings.l3_fault_injection_enabled",
        False,
    )


# ---------------------------------------------------------------------------
# EnvironmentFaultInjector — unit tests
# ---------------------------------------------------------------------------

class TestInjectorDisabled:
    """When disabled the injector must be a transparent pass-through."""

    def test_returns_payload_unchanged(self):
        with _disabled():
            inj = EnvironmentFaultInjector(seed=1, rate=1.0)
            payload = {"key": "value"}
            assert inj.inject("op", payload) is payload

    def test_no_events_recorded(self):
        with _disabled():
            inj = EnvironmentFaultInjector(seed=1, rate=1.0)
            inj.inject("op", {"x": 1})
            assert inj.events == []


class TestInjectorTimeout:
    def test_raises_timeout(self):
        with _enabled():
            inj = EnvironmentFaultInjector(seed=42, rate=1.0, max_delay_ms=0)
            got_timeout = False
            for _ in range(50):
                try:
                    inj.inject("op", {"a": 1})
                except TimeoutError:
                    got_timeout = True
                    break
            # With 4 operators and 50 tries at rate=1.0, probability of
            # never hitting timeout is (3/4)^50 ≈ 5.6e-7
            assert got_timeout


class TestInjectorDelay:
    def test_delay_returns_original_payload(self):
        """Delay operator must return the original payload (not mutated)."""
        with _enabled(l3_fault_max_delay_ms=0):
            inj = EnvironmentFaultInjector(seed=0, rate=1.0, max_delay_ms=0)
            # Collect non-timeout results
            originals_returned = []
            payload = {"x": 1}
            for _ in range(100):
                inj.reset()
                try:
                    result = inj.inject("op", payload)
                except TimeoutError:
                    continue
                if any(e["fault_type"] == "delay" for e in inj.events):
                    originals_returned.append(result is payload)
                    break
            if originals_returned:
                assert originals_returned[0] is True


class TestInjectorPartial:
    def test_dict_field_becomes_none(self):
        with _enabled():
            inj = EnvironmentFaultInjector(seed=42, rate=1.0, max_delay_ms=0)
            for _ in range(50):
                inj.reset()
                try:
                    result = inj.inject("op", {"a": 1, "b": 2})
                except TimeoutError:
                    continue
                if any(e["fault_type"] == "partial" for e in inj.events):
                    assert None in result.values()
                    break

    def test_dataclass_field_becomes_none(self):
        with _enabled():
            inj = EnvironmentFaultInjector(seed=42, rate=1.0, max_delay_ms=0)
            for _ in range(50):
                inj.reset()
                try:
                    result = inj.inject("op", _SampleDC(a="x", b=1))
                except TimeoutError:
                    continue
                if any(e["fault_type"] == "partial" for e in inj.events):
                    assert result.a is None or result.b is None
                    break


class TestInjectorCorruption:
    def test_dict_field_becomes_corrupted(self):
        with _enabled():
            inj = EnvironmentFaultInjector(seed=42, rate=1.0, max_delay_ms=0)
            for _ in range(50):
                inj.reset()
                try:
                    result = inj.inject("op", {"a": 1, "b": 2})
                except TimeoutError:
                    continue
                if any(e["fault_type"] == "corruption" for e in inj.events):
                    assert "__CORRUPTED__" in result.values()
                    break

    def test_bytes_becomes_corrupted(self):
        with _enabled():
            inj = EnvironmentFaultInjector(seed=42, rate=1.0, max_delay_ms=0)
            for _ in range(50):
                inj.reset()
                try:
                    result = inj.inject("op", b"some bytes")
                except TimeoutError:
                    continue
                if any(e["fault_type"] == "corruption" for e in inj.events):
                    assert result == b"__CORRUPTED__"
                    break


class TestInjectorListPayload:
    def test_list_element_mutated(self):
        """Lists must be handled — one element replaced by marker."""
        with _enabled():
            inj = EnvironmentFaultInjector(seed=42, rate=1.0, max_delay_ms=0)
            payload = [{"id": 1}, {"id": 2}]
            for _ in range(50):
                inj.reset()
                try:
                    result = inj.inject("op", payload)
                except TimeoutError:
                    continue
                if any(e["fault_type"] in ("partial", "corruption") for e in inj.events):
                    assert result != payload  # at least one element changed
                    break


class TestDeterminism:
    def test_same_seed_same_sequence(self):
        """Two injectors with the same seed must produce identical event sequences."""
        with _enabled():
            results_a, results_b = [], []
            for seed in (7, 7):
                inj = EnvironmentFaultInjector(seed=seed, rate=1.0, max_delay_ms=0)
                events = []
                for i in range(20):
                    try:
                        inj.inject(f"op_{i}", {"k": "v"})
                    except TimeoutError:
                        pass
                    events.append(inj.events[-1]["fault_type"] if inj.events else None)
                (results_a if not results_a else results_b).append(events)
            assert results_a == results_b


class TestReset:
    def test_reset_clears_events(self):
        with _enabled():
            inj = EnvironmentFaultInjector(seed=1, rate=1.0, max_delay_ms=0)
            try:
                inj.inject("op", {"x": 1})
            except TimeoutError:
                pass
            inj.reset()
            assert inj.events == []


# ---------------------------------------------------------------------------
# @with_fault_injection decorator
# ---------------------------------------------------------------------------

class TestDecorator:
    def test_passthrough_when_disabled(self):
        with _disabled():
            @with_fault_injection("test_op")
            def fn():
                return {"value": 42}

            assert fn() == {"value": 42}

    def test_preserves_function_metadata(self):
        @with_fault_injection("test_op")
        def my_func():
            """Docstring."""
            return 1

        assert my_func.__name__ == "my_func"
        assert my_func.__doc__ == "Docstring."

    def test_works_on_method(self):
        class Svc:
            @with_fault_injection("svc.do")
            def do(self, x: int) -> dict:
                return {"result": x * 2}

        with _disabled():
            assert Svc().do(5) == {"result": 10}


# ---------------------------------------------------------------------------
# Event tracking
# ---------------------------------------------------------------------------

class TestEventTracking:
    def test_events_recorded(self):
        with _enabled():
            inj = EnvironmentFaultInjector(seed=99, rate=1.0, max_delay_ms=0)
            for _ in range(5):
                try:
                    inj.inject("op", {"k": 1})
                except TimeoutError:
                    pass
            assert len(inj.events) == 5
            assert all("operation" in e and "fault_type" in e for e in inj.events)
