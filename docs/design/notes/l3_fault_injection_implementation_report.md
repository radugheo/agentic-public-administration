# L3 Fault Injection Implementation Report

## Scope

**L3 controlled fault injection** on the **mocked environment** only.

- No MAT integration
- Logging via Python's standard `logging` module
- Maximum separation between injector and original project code

---

## Design Principle: Decorator-Based Separation

The fault injector is decoupled from the mock implementations using a
**decorator pattern**. Mock function bodies contain only normal mock logic;
fault injection is applied as a cross-cutting concern through
`@with_fault_injection("operation_name")`.

```
┌──────────────────┐       ┌──────────────────────────┐
│  fault_injection  │       │  tools / external_systems │
│  ─────────────── │       │  ───────────────────────  │
│  Injector class   │◄─dec─│  @with_fault_injection    │
│  Decorator func   │       │  Pure mock function body  │
│  Settings read    │       │  No injection logic       │
└──────────────────┘       └──────────────────────────┘
```

**Benefits:**
- Mock function bodies are completely clean — only mock logic
- Removing fault injection = remove decorator annotations + import
- Each injection point is self-documenting (visible in the `@` annotation)
- Zero overhead when disabled (injector short-circuits in `_should_inject`)

---

## Files Changed

### New: `src/ro_tax_agents/mocks/fault_injection.py`

| Component | Purpose |
|-----------|---------|
| `EnvironmentFaultInjector` | Core class: RNG, operators, event tracking |
| `fault_injector` | Module-level singleton |
| `with_fault_injection(op)` | Decorator — sole integration point with mocks |

**Fault operators (uniform random selection):**

| Operator | Effect |
|----------|--------|
| `timeout` | Raises `TimeoutError` |
| `delay` | Sleeps 1 … `max_delay_ms` ms, returns original payload |
| `partial` | Sets one field/element to `None` |
| `corruption` | Sets one field/element to `"__CORRUPTED__"` |

**Payload types handled:** `dict`, `dataclass`, `list`, `bytes`, `str`

**Logging:** Logger `ro_tax_agents.l3_fault_injection`, WARNING level.
Format: `L3 fault injected | op=<operation> | type=<operator>`

### Updated: `src/ro_tax_agents/config/settings.py`

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `l3_fault_injection_enabled` | `bool` | `False` | Master toggle |
| `l3_fault_injection_rate` | `float [0,1]` | `0.0` | Per-call injection probability |
| `l3_fault_injection_seed` | `int` | `17` | Deterministic RNG seed |
| `l3_fault_max_delay_ms` | `int ≥ 0` | `250` | Upper bound for delay faults |
| `l3_fault_log_level` | `str` | `"INFO"` | Logger level |

### Updated: `src/ro_tax_agents/mocks/tools.py`

Decorator applied to **8 functions** (bodies unchanged):

1. `mock_spv_login`
2. `mock_spv_submit_d212`
3. `mock_spv_register_contract`
4. `mock_ghiseul_payment`
5. `mock_ocr_document` *(newly instrumented)*
6. `mock_efactura_submit`
7. `mock_efactura_status`
8. `mock_fiscal_certificate_request`

### Updated: `src/ro_tax_agents/mocks/external_systems.py`

Decorator applied to **11 methods** across 3 classes (bodies unchanged):

| Class | Methods |
|-------|---------|
| `MockANAFSPV` | `authenticate`, `submit_declaration`, `get_fiscal_certificate`, `check_declaration_status` |
| `MockGhiseulRo` | `initiate_payment`, `check_payment_status`, `get_payment_receipt` |
| `MockEFacturaSystem` | `upload_invoice`, `check_status`, `download_invoice`, `get_messages` |

### New: `tests/unit/test_fault_injection.py`

15 unit tests covering:
- Pass-through when disabled
- Each operator (timeout, delay, partial, corruption)
- Dict, dataclass, list, and bytes payload handling
- Deterministic seed reproducibility
- Decorator on functions and methods
- Event tracking

---

## Behavioural Summary

When a decorated mock function executes:

1. Function body runs normally → produces response payload
2. Decorator passes payload to `fault_injector.inject(operation, payload)`
3. Injector checks: `enabled && random() < rate`
4. If **no** → payload returned unchanged
5. If **yes** → one operator selected (uniform random), applied, logged
6. Mutated payload (or `TimeoutError`) returned to caller

---

## Bugs Fixed vs. GPT's Original Implementation

| Issue | Fix |
|-------|-----|
| Injection logic mixed into mock function bodies | Extracted to `@with_fault_injection` decorator |
| `mock_ocr_document` not instrumented | Now decorated |
| `list` payloads silently ignored by `_mutate_payload` | Added `list` branch (mutates random element) |
| `is_dataclass()` matched classes, not just instances | Added `not isinstance(payload, type)` guard |
| `logging.basicConfig()` side-effect in constructor | Removed; logger uses standard hierarchy |
| No event tracking for observability | Added `injector.events` list |
| No `reset()` for test isolation | Added `reset(seed)` method |

---

## How To Run

Set environment variables (shell or `.env`):

```bash
L3_FAULT_INJECTION_ENABLED=true
L3_FAULT_INJECTION_RATE=1.0
L3_FAULT_INJECTION_SEED=17
L3_FAULT_MAX_DELAY_MS=250
```

Quick verification:

```bash
L3_FAULT_INJECTION_ENABLED=true \
L3_FAULT_INJECTION_RATE=1.0 \
.venv/bin/python -c "
from ro_tax_agents.mocks.tools import mock_fiscal_certificate_request
print(mock_fiscal_certificate_request('RO12345678', 'atestare_fiscala'))
"
```

Run tests:

```bash
# Fault injection unit tests (always pass — use internal mocking)
.venv/bin/python -m pytest tests/unit/test_fault_injection.py -v

# All tests with injection disabled (55/55 pass)
L3_FAULT_INJECTION_ENABLED=false .venv/bin/python -m pytest tests/ -v

# All tests with injection at 100% (integration tests fail as expected)
L3_FAULT_INJECTION_ENABLED=true L3_FAULT_INJECTION_RATE=1.0 \
  .venv/bin/python -m pytest tests/ -v
```

---

## Out of Scope

1. MAT ledger / containment contracts
2. L4 governance / policy shield
3. Fault persistence beyond standard logs
4. Non-mocked boundary injection
