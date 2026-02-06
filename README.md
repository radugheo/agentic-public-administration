# Romanian Tax Agents

Multi-agent system for Romanian tax services (ANAF/Ghiseul.ro/E-Factura) built with LangGraph.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                     ORCHESTRATION LAYER                             │
│                        Entry Agent                                  │
│                  (Intent Detection & Routing)                       │
└─────────────────────────────────────────────────────────────────────┘
                                │
        ┌───────────┬───────────┼───────────┬───────────┐
        ▼           ▼           ▼           ▼           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       DOMAIN AGENTS LAYER                           │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐       │
│  │   PFA   │ │Property │ │ Rental  │ │  Cert.  │ │E-Factura│       │
│  │  Agent  │ │  Sale   │ │ Income  │ │  Agent  │ │  Agent  │       │
│  │ D212    │ │ 1%/3%   │ │Contract │ │ Fiscal  │ │ B2B/B2C │       │
│  │ CAS/CASS│ │  Tax    │ │  Reg.   │ │ Attest. │ │Invoicing│       │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘       │
└─────────────────────────────────────────────────────────────────────┘
                                │
┌─────────────────────────────────────────────────────────────────────┐
│                      SHARED SERVICES LAYER                          │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌────────────┐  │
│  │  Document    │ │  RAO Agent   │ │ Calculation  │ │  Payment   │  │
│  │   Intake     │ │  Tax Code    │ │    Agent     │ │   Agent    │  │
│  │ OCR/Validate │ │  Knowledge   │ │Tax Compute   │ │ Ghiseul.ro │  │
│  └──────────────┘ └──────────────┘ └──────────────┘ └────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                                │
┌─────────────────────────────────────────────────────────────────────┐
│                         MOCK LAYER                                  │
│  UiPath SDK | SPV Tools | External Systems (ANAF, Ghiseul, E-Fact) │
└─────────────────────────────────────────────────────────────────────┘
```

## Features

- **Entry Agent**: Intent detection and routing using GPT-4o
- **PFA Agent**: D212 filing, CAS/CASS contribution calculations
- **Property Sale Agent**: 1%/3% property tax calculations
- **Rental Income Agent**: Contract registration and rental tax
- **Certificate Agent**: Fiscal attestation certificates
- **E-Factura Agent**: B2B/B2C electronic invoicing

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd public-administration

# Install dependencies with uv
uv sync

# Copy environment template and add your OpenAI API key
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

## Usage

### Run Demo

```bash
# Run automated demo scenarios
uv run python examples/demo.py

# Run interactive mode
uv run python examples/demo.py --interactive
```

### Use as Library

```python
from langchain_core.messages import HumanMessage
from ro_tax_agents import compile_graph
from ro_tax_agents.orchestration.main_graph import get_initial_state

# Compile the graph
graph = compile_graph()

# Create initial state
state = get_initial_state("session-123")
state["messages"] = [HumanMessage(content="Am vandut un apartament cu 100000 euro, detinut 5 ani")]

# Run the graph
result = graph.invoke(state, {"configurable": {"thread_id": "session-123"}})

# Get response
for msg in reversed(result["messages"]):
    if msg.type == "ai":
        print(msg.content)
        break
```

## Testing

```bash
# Run all tests
uv run pytest

# Run unit tests
uv run pytest tests/unit -v

# Run integration tests
uv run pytest tests/integration -v
```

## Project Structure

```
public-administration/
├── src/ro_tax_agents/
│   ├── config/          # Settings and prompts
│   ├── state/           # State definitions
│   ├── orchestration/   # Entry agent and main graph
│   ├── agents/          # Domain agents
│   ├── services/        # Shared services
│   ├── mocks/           # Mock implementations
│   ├── models/          # Pydantic models
│   └── utils/           # Validators
├── tests/
│   ├── unit/
│   └── integration/
└── examples/
    └── demo.py
```

## Tax Calculations

### PFA Contributions (2024)
- **CAS (pension)**: 25% of 12 minimum salaries if income >= 39,600 RON
- **CASS (health)**: 10% of 6 minimum salaries if income >= 19,800 RON
- Minimum salary: 3,300 RON

### Property Sale Tax
- **1%** if property owned >= 3 years
- **3%** if property owned < 3 years

### Rental Income Tax
- **10%** flat tax on annual rental income

## License

MIT
