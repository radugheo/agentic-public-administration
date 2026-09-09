#!/usr/bin/env python3
"""Reproduce Table 1 of the KES 2026 paper: fault injection results.

    Agentic AI for Public Administration: A Multi-Agent Architecture and
    Controlled Fault Injection Evaluation

The experiment measures, per external service boundary call, whether an
injected fault is *detectable* by the citizen-facing workflow or whether it
passes through *silently*.

What this harness measures
--------------------------
Detectability is decided structurally, not by inspecting generated prose:

  timeout     -> always DETECTABLE (raises TimeoutError, exception propagates)
  delay       -> always SILENT     (payload returned intact)
  partial     -> DETECTABLE iff the nullified field is the branching field
  corruption  -> DETECTABLE iff the corrupted field is the branching field

This is exactly the criterion the closed-form prediction in the paper is about,
and it removes the LLM from the measurement loop, so the table is reproducible
without model access, API keys or network calls. The branching field of each
boundary is the field the calling agent actually tests; every entry in
BOUNDARIES below cites the source line that does the test.

Expected value
--------------
With operators drawn uniformly and a response of |F| fields whose branch reads
exactly one of them:

    P(silent) = 0.25          (delay)
              + 2 x 0.25 x (1 - 1/|F|)   (partial, corruption)

For |F| = 4 this is 0.625. The measured value is slightly higher because the
eight instrumented boundaries mix 4-field and 5-field payloads.

Allocation modes
----------------
--allocation stratified (default)
    The number of injected faults is round(eta * N), and operators are dealt
    round-robin so each is used as close to N/4 times as possible. This is a
    variance-reduction design: at N = 100 it estimates the silent *rate*, which
    is the quantity of interest, without the operator-count noise that i.i.d.
    sampling adds. This is the allocation used for Table 1 in the paper.

--allocation bernoulli
    The literal runtime behaviour described in Section 3.2: one Bernoulli(eta)
    draw per call, then a uniform choice among the four operators. Use this to
    see the sampling noise the stratified design removes.

Usage
-----
    python scripts/run_fault_experiment.py
    python scripts/run_fault_experiment.py --allocation bernoulli --seed 17
    python scripts/run_fault_experiment.py --n 1000 --csv results.csv
"""

from __future__ import annotations

import argparse
import csv
import sys
from dataclasses import dataclass, fields as dc_fields, is_dataclass
from pathlib import Path
from random import Random
from typing import Any, Callable

_SRC = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(_SRC))


def _load_package_without_init() -> None:
    """Register ``ro_tax_agents`` as a namespace-style package.

    The real ``ro_tax_agents/__init__.py`` imports the LangGraph state machine,
    which drags in langgraph, langchain and a model gateway. This harness only
    needs the mock payload shapes and the injector, so we bind the package name
    to its directory and let submodule imports resolve normally without running
    the package __init__. Keeps the experiment runnable with pydantic alone.
    """
    import importlib.machinery
    import types

    if "ro_tax_agents" in sys.modules:
        return
    pkg = types.ModuleType("ro_tax_agents")
    pkg.__path__ = [str(_SRC / "ro_tax_agents")]
    pkg.__spec__ = importlib.machinery.ModuleSpec(
        "ro_tax_agents", loader=None, is_package=True
    )
    pkg.__spec__.submodule_search_locations = pkg.__path__
    sys.modules["ro_tax_agents"] = pkg


_load_package_without_init()

from ro_tax_agents.mocks.fault_injection import (  # noqa: E402
    OPERATORS,
    EnvironmentFaultInjector,
)

DEFAULT_N = 100
DEFAULT_SEED = 17
DEFAULT_MAX_DELAY_MS = 250
DEFAULT_RATES = (0.00, 0.25, 0.50, 0.75, 1.00)


# ---------------------------------------------------------------------------
# The instrumented boundaries
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Boundary:
    """One instrumented external service boundary.

    Attributes:
        operation: the operation name passed to @with_fault_injection.
        branching_field: the response field the calling agent branches on.
        build: returns a fresh nominal payload, as the mock would.
        weight: relative invocation frequency across the five demo workflows.
        branch_source: where the branching predicate lives, for auditability.
    """

    operation: str
    branching_field: str
    build: Callable[[], Any]
    weight: float
    branch_source: str


def _boundaries() -> list[Boundary]:
    """Build the boundary table from the real mock payload shapes."""
    from ro_tax_agents.mocks.tools import SPVSubmissionResult
    from ro_tax_agents.models.documents import OCRResult
    from ro_tax_agents.models.payments import PaymentResult

    return [
        Boundary(
            "mock_spv_login", "success",
            lambda: {
                "success": True,
                "session_token": "mock_session_0123456789abcdef",
                "user_cui": "RO12345678",
                "expires_at": "2026-12-31T23:59:59",
            },
            weight=1.0, branch_source="tools.py (login gate)",
        ),
        Boundary(
            "mock_spv_submit_d212", "status",
            lambda: SPVSubmissionResult(
                status="success",
                submission_id="D212-01B66C85C3",
                message="Declaratia D212 a fost depusa cu succes",
                timestamp="2026-03-27T22:20:32",
            ),
            weight=1.0, branch_source="agents/pfa.py:171",
        ),
        Boundary(
            "mock_spv_register_contract", "status",
            lambda: {
                "status": "success",
                "registration_number": "CONTR-9F2A1B7C",
                "registration_date": "2026-03-27T22:20:32",
                "message": "Contractul de inchiriere a fost inregistrat",
            },
            weight=1.0, branch_source="agents/rental_income.py:160",
        ),
        Boundary(
            "mock_ghiseul_payment", "status",
            lambda: PaymentResult(
                status="success",
                transaction_id="GH-4C1D9E8F2A3B",
                message="Plata a fost procesata cu succes",
                redirect_url="https://ghiseul.ro/payment/abcdef12",
            ),
            weight=1.0, branch_source="services/payment.py:57",
        ),
        Boundary(
            "mock_ocr_document", "confidence",
            lambda: OCRResult(
                document_type="D212_FORM",
                extracted_data={"fiscal_year": 2026, "total_income": 150000.00},
                confidence=0.94,
                raw_text="...",
                processing_time_ms=120,
            ),
            weight=1.0, branch_source="services/document_intake.py:43",
        ),
        Boundary(
            "mock_efactura_submit", "status",
            lambda: {
                "status": "success",
                "upload_index": "EF-7A2B9C1D3E",
                "message": "Factura a fost incarcata in sistemul E-Factura",
                "validation_status": "valid",
                "timestamp": "2026-03-27T22:20:32",
            },
            weight=1.0, branch_source="agents/efactura.py:65",
        ),
        Boundary(
            "mock_efactura_status", "status",
            lambda: {
                "upload_index": "EF-7A2B9C1D3E",
                "status": "processed",
                "state_message": "ok",
                "processing_date": "2026-03-27T22:20:32",
                "errors": [],
            },
            weight=1.0, branch_source="agents/efactura.py:65",
        ),
        Boundary(
            "mock_fiscal_certificate_request", "status",
            lambda: {
                "status": "success",
                "request_id": "CERT-3B8D1F0A",
                "certificate_type": "atestare_fiscala",
                "estimated_completion": "24 hours",
                "message": "Cererea de certificat fiscal a fost inregistrata",
            },
            weight=1.0, branch_source="agents/certificate.py:81",
        ),
    ]


# ---------------------------------------------------------------------------
# Payload inspection
# ---------------------------------------------------------------------------

def field_names(payload: Any) -> list[str]:
    """Field names of a payload, matching what the injector can mutate."""
    if isinstance(payload, dict):
        return list(payload.keys())
    if is_dataclass(payload) and not isinstance(payload, type):
        return [f.name for f in dc_fields(payload)]
    model_fields = getattr(type(payload), "model_fields", None)
    if model_fields:  # pydantic BaseModel
        return list(model_fields.keys())
    return []


def field_value(payload: Any, name: str) -> Any:
    if isinstance(payload, dict):
        return payload.get(name)
    return getattr(payload, name, None)


def branch_field_changed(nominal: Any, mutated: Any, branching_field: str) -> bool:
    """True if the perturbation touched the field the agent branches on."""
    return field_value(nominal, branching_field) != field_value(mutated, branching_field)


def payload_unchanged(nominal: Any, mutated: Any) -> bool:
    """True if the injector returned the payload untouched."""
    return all(
        field_value(nominal, n) == field_value(mutated, n)
        for n in field_names(nominal)
    )


# ---------------------------------------------------------------------------
# Trial execution
# ---------------------------------------------------------------------------

@dataclass
class Trial:
    operation: str
    operator: str | None
    silent: bool | None      # None when no fault was injected
    noop: bool = False       # payload type the injector cannot mutate


def run_trial(injector: EnvironmentFaultInjector, boundary: Boundary,
              operator: str) -> Trial:
    """Apply one operator to one boundary and classify the outcome."""
    nominal = boundary.build()

    if operator == "timeout":
        # Raises TimeoutError in production; the exception propagates to the
        # agent, so the citizen sees a failure.
        return Trial(boundary.operation, "timeout", silent=False)

    if operator == "delay":
        # Payload intact: nothing downstream can notice.
        return Trial(boundary.operation, "delay", silent=True)

    marker = None if operator == "partial" else "__CORRUPTED__"
    mutated = injector._mutate_payload(nominal, marker)

    if payload_unchanged(nominal, mutated):
        # The injector's _mutate_payload handles dict / dataclass / list /
        # bytes / str. Any other payload type falls through unchanged, so the
        # fault is logged but has no effect. Reported separately below.
        return Trial(boundary.operation, operator, silent=True, noop=True)

    hit_branch = branch_field_changed(nominal, mutated, boundary.branching_field)
    return Trial(boundary.operation, operator, silent=not hit_branch)


def stratified_operators(n_faults: int, rng: Random) -> list[str]:
    """Deal operators round-robin so counts are as balanced as possible."""
    ops = [OPERATORS[i % len(OPERATORS)] for i in range(n_faults)]
    rng.shuffle(ops)
    return ops


def run_rate(rate: float, n: int, seed: int, allocation: str) -> list[Trial]:
    """Run n boundary-crossing trials at injection rate `rate`."""
    injector = EnvironmentFaultInjector(seed=seed, rate=rate, max_delay_ms=0)
    rng = Random(seed)
    boundaries = _boundaries()
    weights = [b.weight for b in boundaries]

    trials: list[Trial] = []

    if allocation == "stratified":
        n_faults = round(rate * n)
        schedule = [True] * n_faults + [False] * (n - n_faults)
        rng.shuffle(schedule)
        operators = stratified_operators(n_faults, rng)
        op_iter = iter(operators)
        for inject in schedule:
            boundary = rng.choices(boundaries, weights=weights, k=1)[0]
            if not inject:
                trials.append(Trial(boundary.operation, None, None))
            else:
                trials.append(run_trial(injector, boundary, next(op_iter)))
    else:  # bernoulli
        for _ in range(n):
            boundary = rng.choices(boundaries, weights=weights, k=1)[0]
            if rng.random() < rate:
                trials.append(run_trial(injector, boundary, rng.choice(list(OPERATORS))))
            else:
                trials.append(Trial(boundary.operation, None, None))

    return trials


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def summarise(trials: list[Trial]) -> dict[str, Any]:
    injected = [t for t in trials if t.operator is not None]
    counts = {op: sum(1 for t in injected if t.operator == op) for op in OPERATORS}
    silent = sum(1 for t in injected if t.silent)
    return {
        "faults": len(injected),
        **counts,
        "silent": silent,
        "detectable": len(injected) - silent,
        "silent_pct": (silent / len(injected) * 100) if injected else None,
        "noops": sum(1 for t in injected if t.noop),
    }


def print_table(rows: list[tuple[float, dict[str, Any]]], n: int, seed: int,
                max_delay_ms: int, allocation: str) -> None:
    print()
    print(f"Table 1. Fault injection results "
          f"(N={n}, s={seed}, dt_max={max_delay_ms} ms, allocation={allocation}).")
    print()
    print(f"{'eta':>5}  {'Faults':>6}  {'TO':>3}  {'DL':>3}  {'PT':>3}  {'CR':>3}  "
          f"{'Silent':>13}  {'Detectable':>13}")
    print("-" * 68)
    for rate, s in rows:
        if s["faults"] == 0:
            silent_cell, detect_cell = "0 ( n/a )", "0 ( n/a )"
        else:
            silent_cell = f"{s['silent']} ({s['silent_pct']:.0f}%)"
            detect_cell = f"{s['detectable']} ({100 - s['silent_pct']:.0f}%)"
        print(f"{rate:>5.2f}  {s['faults']:>6}  {s['timeout']:>3}  {s['delay']:>3}  "
              f"{s['partial']:>3}  {s['corruption']:>3}  {silent_cell:>13}  {detect_cell:>13}")
    print("-" * 68)
    print("TO, DL, PT, CR: timeout, delay, partial, corruption.")

    noops = sum(s["noops"] for _, s in rows)
    if noops:
        print()
        print(f"NOTE: {noops} partial/corruption injections left the payload unchanged.")
        print("      EnvironmentFaultInjector._mutate_payload handles dict, dataclass,")
        print("      list, bytes and str; pydantic BaseModel payloads (PaymentResult,")
        print("      OCRResult) fall through untouched. Those faults are logged but")
        print("      have no effect, and are counted as silent here. Fixing the")
        print("      mutator to support pydantic models would move them into the")
        print("      schema-governed 1 - 1/|F| population.")


def expected_silent_rate() -> tuple[float, float]:
    """Closed-form expectation over the actual boundary field counts."""
    boundaries = _boundaries()
    per_tool = []
    for b in boundaries:
        payload = b.build()
        n_fields = len(field_names(payload))
        per_tool.append(1 - 1 / n_fields if n_fields else 1.0)
    mean_miss = sum(per_tool) / len(per_tool)
    return mean_miss, 0.25 + 0.5 * mean_miss


def main() -> int:
    ap = argparse.ArgumentParser(description="Reproduce Table 1 of the KES 2026 paper.")
    ap.add_argument("--n", type=int, default=DEFAULT_N, help="boundary calls per rate")
    ap.add_argument("--seed", type=int, default=DEFAULT_SEED)
    ap.add_argument("--max-delay-ms", type=int, default=DEFAULT_MAX_DELAY_MS)
    ap.add_argument("--allocation", choices=("stratified", "bernoulli"),
                    default="stratified")
    ap.add_argument("--rates", type=float, nargs="+", default=list(DEFAULT_RATES))
    ap.add_argument("--csv", type=Path, help="also write per-rate results here")
    args = ap.parse_args()

    rows = [(rate, summarise(run_rate(rate, args.n, args.seed, args.allocation)))
            for rate in args.rates]

    print_table(rows, args.n, args.seed, args.max_delay_ms, args.allocation)

    mean_miss, expected = expected_silent_rate()
    print()
    print("Closed-form prediction")
    print(f"  mean P(fault misses branching field) over the 8 boundaries = {mean_miss:.4f}")
    print(f"  P(silent) = 0.25 + 2 x 0.25 x {mean_miss:.4f} = {expected:.4f}")
    print(f"  paper's simplified figure, taking |F| = 4 throughout      = 0.6250")

    if args.csv:
        with args.csv.open("w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["eta", "faults", "timeout", "delay", "partial",
                        "corruption", "silent", "detectable", "silent_pct"])
            for rate, s in rows:
                w.writerow([rate, s["faults"], s["timeout"], s["delay"],
                            s["partial"], s["corruption"], s["silent"],
                            s["detectable"],
                            f"{s['silent_pct']:.1f}" if s["silent_pct"] is not None else ""])
        print(f"\nWrote {args.csv}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
