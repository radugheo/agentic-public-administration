"""Demo script for the Romanian Tax Agents system.

This script demonstrates the multi-agent system handling various
tax-related queries.
"""

import uuid
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage

from ro_tax_agents.orchestration.main_graph import compile_graph, get_initial_state

# Load environment variables
load_dotenv()



def run_demo():
    """Run demo conversations with the tax agent system."""

    # Compile the graph
    print("Initializing Romanian Tax Agents system...")
    graph = compile_graph()
    print("System ready!\n")
    print("=" * 60)

    # Demo scenarios
    demos = [
        {
            "name": "PFA Contributions Calculation",
            "message": "Am un PFA si am avut venituri de 150000 RON anul trecut. Cat am de platit CAS si CASS?",
        },
        {
            "name": "Property Sale Tax",
            "message": "Am vandut un apartament cu 100000 euro, l-am detinut 5 ani. Care este impozitul?",
        },
        {
            "name": "Rental Income",
            "message": "Vreau sa inchiriez un apartament cu 500 EUR pe luna. Ce taxe trebuie sa platesc?",
        },
        {
            "name": "E-Factura B2B",
            "message": "Trebuie sa emit o factura electronica catre o firma. Cum procedez?",
        },
        {
            "name": "Fiscal Certificate",
            "message": "Am nevoie de un certificat de atestare fiscala pentru firma mea.",
        },
    ]

    for demo in demos:
        print(f"\n{'='*60}")
        print(f"Demo: {demo['name']}")
        print(f"{'='*60}")
        print(f"\nUser: {demo['message']}\n")

        # Create a new session for each demo
        session_id = str(uuid.uuid4())
        config = {"configurable": {"thread_id": session_id}}

        # Create initial state with user message
        initial_state = get_initial_state(session_id)
        initial_state["messages"] = [HumanMessage(content=demo["message"])]

        try:
            # Run the graph
            result = graph.invoke(initial_state, config)

            # Print the response
            print("Agent Response:")
            print("-" * 40)

            # Get the last AI message
            for msg in reversed(result.get("messages", [])):
                if hasattr(msg, "content") and msg.type == "ai":
                    print(msg.content)
                    break

            # Print detected intent
            print(f"\n[Intent: {result.get('detected_intent', 'N/A')} "
                  f"(confidence: {result.get('intent_confidence', 0):.0%})]")

        except Exception as e:
            print(f"Error: {e}")
            print("Note: Make sure OPENAI_API_KEY is set in .env file")

        print()


def interactive_demo():
    """Run an interactive conversation with the tax agent system."""

    print("=" * 60)
    print("Romanian Tax Agents - Interactive Demo")
    print("=" * 60)
    print("\nInitializing system...")

    graph = compile_graph()
    session_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": session_id}}

    print("System ready! Type 'quit' to exit.\n")
    print("Available services:")
    print("- PFA/D212 filing and CAS/CASS calculations")
    print("- Property sale tax (1%/3%)")
    print("- Rental income and contract registration")
    print("- Fiscal certificates")
    print("- E-Factura (B2B/B2C)")
    print()

    while True:
        user_input = input("You: ").strip()

        if user_input.lower() in ["quit", "exit", "q"]:
            print("La revedere!")
            break

        if not user_input:
            continue

        # Create state with user message
        state = get_initial_state(session_id)
        state["messages"] = [HumanMessage(content=user_input)]

        try:
            result = graph.invoke(state, config)

            # Print response
            print("\nAgent:", end=" ")
            for msg in reversed(result.get("messages", [])):
                if hasattr(msg, "content") and msg.type == "ai":
                    print(msg.content)
                    break
            print()

        except Exception as e:
            print(f"\nError: {e}")
            print("Make sure OPENAI_API_KEY is set correctly.\n")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        interactive_demo()
    else:
        run_demo()
