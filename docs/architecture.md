# Romanian Tax Multi-Agent System - Architecture

## System Overview

```mermaid
graph TB
    subgraph Legend
        direction LR
        L1[Completed - LLM powered]:::completed
        L2[Completed - Deterministic logic]:::logic
        L3[Mock - To be replaced]:::mock
        L4[Not implemented]:::notimpl
    end

    USER((User)) --> |message| GRAPH

    subgraph GRAPH["LangGraph Orchestration"]
        direction TB

        subgraph ORCH["Layer 1: Orchestration"]
            EA["Entry Agent\n(GPT-4o intent classification\n+ entity extraction)"]:::completed
            ROUTER["Router\n(confidence threshold 0.7\n+ intent-to-agent mapping)"]:::logic
            CLARIFY["Request Clarification\n(LLM asks for more info)"]:::completed
        end

        subgraph DOMAIN["Layer 2: Domain Agents (all LLM-powered)"]
            PFA["PFA Agent\n- CAS/CASS guidance\n- D212 filing"]:::completed
            PROP["Property Sale Agent\n- Tax rate selection\n- Payment guidance"]:::completed
            RENT["Rental Income Agent\n- Contract registration\n- Tax guidance"]:::completed
            CERT["Certificate Agent\n- Fiscal attestation\n- Document guidance"]:::completed
            EFACT["E-Factura Agent\n- B2B/B2C invoicing\n- Status checking"]:::completed
        end

        subgraph SERVICES["Layer 3: Shared Services"]
            CALC["Calculation Agent\n(deterministic tax math)"]:::logic
            RAG_NODE["RAG Agent\n(Tax Code Knowledge\nvia ChromaDB + embeddings)"]:::completed
            DOC["Document Intake\n(OCR + validation)"]:::mock
            PAY["Payment Agent\n(Ghiseul.ro integration)"]:::mock
        end

        subgraph MOCKS["Layer 4: External Systems (all mocked)"]
            SPV["ANAF SPV\n(D212 submit, certificates,\ncontract registration)"]:::mock
            GHIS["Ghiseul.ro\n(payment processing)"]:::mock
            EFAC_SYS["E-Factura System\n(invoice upload, status)"]:::mock
            OCR["OCR Service\n(document scanning)"]:::mock
        end

        subgraph NOTIMPL["Not Yet Implemented"]
            UIPATH["UiPath RPA\n(process automation)"]:::notimpl
            RAG_SYS["RAG System\n(vector store +\ntax code documents)"]:::notimpl
            AUTH["User Auth\n(SPV login, sessions)"]:::notimpl
            MULTI["Multi-turn Memory\n(conversation persistence)"]:::notimpl
        end
    end

    %% Orchestration flow
    EA --> |"intent + confidence\n+ extracted entities"| ROUTER
    ROUTER --> |"confidence < 0.7"| CLARIFY
    ROUTER --> |"pfa_d212_filing\npfa_cas_cass"| PFA
    ROUTER --> |"property_sale_tax"| PROP
    ROUTER --> |"rental_contract_\nregistration"| RENT
    ROUTER --> |"fiscal_certificate"| CERT
    ROUTER --> |"efactura_b2b\nefactura_b2c"| EFACT
    ROUTER --> |"general_question"| RAG_NODE

    %% Domain agents to services
    PFA --> |"calculation_type:\npfa_contributions"| CALC
    PFA --> |"D212 data"| SPV
    PROP --> |"calculation_type:\nproperty_sale_tax"| CALC
    RENT --> |"calculation_type:\nrental_income_tax"| CALC
    RENT --> |"contract data"| SPV
    CERT --> |"certificate request"| SPV
    EFACT --> |"invoice XML"| EFAC_SYS

    %% Services to mocks
    PAY --> GHIS
    DOC --> OCR

    %% Styling
    classDef completed fill:#4CAF50,stroke:#2E7D32,color:#fff
    classDef logic fill:#2196F3,stroke:#1565C0,color:#fff
    classDef mock fill:#FF9800,stroke:#E65100,color:#fff
    classDef notimpl fill:#9E9E9E,stroke:#616161,color:#fff
```

## Detailed Flow

```mermaid
sequenceDiagram
    participant U as User
    participant EA as Entry Agent
    participant R as Router
    participant DA as Domain Agent
    participant CS as Calculation Service
    participant EXT as External System (Mock)

    U->>EA: "Vreau sa calculez CAS pentru PFA cu venit 100.000 RON"

    Note over EA: GPT-4o structured output
    EA->>EA: Classify intent: pfa_cas_cass (0.95)
    EA->>EA: Extract entities: annual_income=100000

    EA->>R: state.detected_intent = "pfa_cas_cass"
    R->>R: confidence 0.95 >= 0.7 threshold
    R->>DA: Route to PFA Agent

    DA->>CS: calculation_type: pfa_contributions
    Note over CS: Deterministic math:<br/>CAS = 25% × 39,600 = 9,900<br/>CASS = 10% × 19,800 = 1,980
    CS-->>DA: cas_amount, cass_amount

    Note over DA: GPT-4o presents results<br/>with system prompt context
    DA-->>U: Natural language response with calculated values

    U->>EA: "Da, vreau sa depun D212"
    EA->>R: intent: pfa_d212_filing
    R->>DA: Route to PFA Agent
    DA->>EXT: mock_spv_submit_d212(data)
    Note over EXT: Returns fake<br/>submission_id + timestamp
    EXT-->>DA: SPVSubmissionResult
    Note over DA: GPT-4o presents<br/>submission confirmation
    DA-->>U: Confirmation with submission details
```

## State Flow

```mermaid
stateDiagram-v2
    [*] --> EntryAgent: User message

    EntryAgent --> Router: intent + confidence + entities

    state Router <<choice>>
    Router --> Clarification: confidence < 0.7
    Router --> PFAAgent: pfa_*
    Router --> PropertySaleAgent: property_sale_tax
    Router --> RentalIncomeAgent: rental_contract
    Router --> CertificateAgent: fiscal_certificate
    Router --> EFacturaAgent: efactura_*
    Router --> RAGAgent: general_question

    Clarification --> [*]: Ask user for more info

    PFAAgent --> CalculationService: needs CAS/CASS calc
    PFAAgent --> MockSPV: D212 submission
    PropertySaleAgent --> CalculationService: needs tax calc
    RentalIncomeAgent --> CalculationService: needs rental tax calc
    RentalIncomeAgent --> MockSPV: contract registration
    EFacturaAgent --> MockEFactura: invoice operations

    CalculationService --> PFAAgent: results
    CalculationService --> PropertySaleAgent: results
    CalculationService --> RentalIncomeAgent: results
    MockSPV --> PFAAgent: submission result
    MockSPV --> RentalIncomeAgent: registration result
    MockEFactura --> EFacturaAgent: upload result

    PFAAgent --> [*]: LLM response
    PropertySaleAgent --> [*]: LLM response
    RentalIncomeAgent --> [*]: LLM response
    CertificateAgent --> [*]: LLM response
    EFacturaAgent --> [*]: LLM response
    RAGAgent --> [*]: LLM response
```

## Completion Status

```mermaid
pie title Implementation Status
    "Completed (LLM-powered)" : 8
    "Completed (Deterministic)" : 3
    "Mocked (needs real integration)" : 6
    "Not implemented" : 4
```

### Detailed Status

| Component | Status | Details |
|-----------|--------|---------|
| **Entry Agent** | ✅ Completed | GPT-4o structured output, intent classification, entity extraction |
| **Router** | ✅ Completed | Confidence-based routing, intent-to-agent mapping |
| **PFA Agent** | ✅ Completed | LLM-powered responses, CAS/CASS guidance, D212 flow |
| **Property Sale Agent** | ✅ Completed | LLM-powered, tax rate selection, payment guidance |
| **Rental Income Agent** | ✅ Completed | LLM-powered, contract registration flow |
| **Certificate Agent** | ✅ Completed | LLM-powered, certificate request flow |
| **E-Factura Agent** | ✅ Completed | LLM-powered, B2B/B2C, status checking |
| **RAG Agent** | ✅ Completed | LLM tax code expert (but no RAG - relies on GPT knowledge) |
| **Calculation Service** | ✅ Completed | Deterministic tax math (CAS/CASS/property/rental) |
| **Settings/Config** | ✅ Completed | Pydantic settings, tax rates, thresholds |
| **Validators** | ✅ Completed | CNP and CUI validation |
| **Document Intake** | 🟡 Mock | Uses mock OCR, no real document processing |
| **Payment Agent** | 🟡 Mock | Simulated Ghiseul.ro payments |
| **ANAF SPV** | 🟡 Mock | Fake D212 submission, certificate requests |
| **Ghiseul.ro** | 🟡 Mock | Fake payment processing |
| **E-Factura System** | 🟡 Mock | Fake invoice upload/status |
| **OCR** | 🟡 Mock | Returns hardcoded extracted data |
| **RAG / Knowledge Base** | ❌ Not built | No vector store, no tax code document ingestion |
| **UiPath RPA** | ❌ Not built | SDK mocked but no real automation |
| **User Authentication** | ❌ Not built | No real SPV login/sessions |
| **Multi-turn Persistence** | ❌ Not built | No conversation memory across sessions |

### Knowledge Source

```mermaid
graph LR
    subgraph "Current (Prompt-based)"
        SP["System Prompts\n(static rules)"]:::current
        CTX["Dynamic Context\n(settings + calc results)"]:::current
        LLM["GPT-4o Pre-trained\nKnowledge"]:::current
    end

    subgraph "Future (RAG-based)"
        DOCS["Tax Code Documents\n(Codul Fiscal, norms)"]:::future
        CHUNK["Chunking +\nEmbeddings"]:::future
        VS["Vector Store\n(ChromaDB)"]:::future
        RET["Retriever\n(similarity search)"]:::future
    end

    SP --> AGENT["Agent LLM Call"]
    CTX --> AGENT
    LLM --> AGENT

    DOCS -.-> CHUNK -.-> VS -.-> RET -.-> AGENT

    classDef current fill:#4CAF50,stroke:#2E7D32,color:#fff
    classDef future fill:#9E9E9E,stroke:#616161,color:#fff,stroke-dasharray: 5 5
```
