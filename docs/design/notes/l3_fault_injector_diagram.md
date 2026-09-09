# L3 Fault Injector Flow

This diagram shows how L3 controlled fault injection works in the mocked environment.

```mermaid
flowchart TD
    A[Agent calls mocked tool\nexample: mock_efactura_submit] --> B[Tool builds normal mock response]
    B --> C[fault_injector.inject operation payload]

    C --> D{Injection enabled and\nrandom check passes?}
    D -- No --> E[Return original payload]

    D -- Yes --> F[Pick operator\ntimeout | delay | partial | corruption]

    F --> G{Operator type}
    G -- timeout --> H[Raise TimeoutError]
    G -- delay --> I[Sleep up to max delay ms\nreturn original payload]
    G -- partial --> J[Mutate one field to null\nreturn mutated payload]
    G -- corruption --> K[Mutate one field to __CORRUPTED__\nreturn mutated payload]

    H --> L[Tool/agent receives exception]
    I --> M[Tool/agent receives payload]
    J --> M
    K --> M

    F --> N[Write warning log\nL3 fault injected | op=... | type=...]

    classDef start fill:#e8f5e9,stroke:#2e7d32,stroke-width:1px;
    classDef action fill:#e3f2fd,stroke:#1565c0,stroke-width:1px;
    classDef decision fill:#fff8e1,stroke:#f9a825,stroke-width:1px;
    classDef fault fill:#ffebee,stroke:#c62828,stroke-width:1px;

    class A,B,C,E action;
    class D,G decision;
    class F,H,I,J,K,N,L,M fault;
```

## Notes

- L3 injection is applied at mocked external boundaries only.
- No MAT layer is used.
- Logging is basic Python logging using logger name ro_tax_agents.l3_fault_injection.
- If injection is disabled or probability check fails, behavior is unchanged.
