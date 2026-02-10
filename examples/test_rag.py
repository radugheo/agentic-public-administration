"""Script interactiv pentru testarea serviciului RAG."""

from dotenv import load_dotenv

load_dotenv()

from ro_tax_agents.services.rag_service import rag_service


def main():
    print("=" * 60)
    print("       Test RAG ")
    print("=" * 60)

    print("\nUiPath Context Grounding RAG ready.\n")
    print("-" * 60)
    print("Agenti: pfa, rental_income, certificate")
    print("'exit' pentru a iesi")
    print("-" * 60)

    # Alege agentul o singură dată
    while True:
        tip_agent = input("\nAgent: ").strip().lower()

        if tip_agent == "exit":
           
            return

        if tip_agent not in ("pfa", "rental_income", "certificate"):
            print("Agent invalid. Alege din: pfa, rental_income, certificate")
            continue

        break

    print(f"\nAgent selectat: {tip_agent}")
    print("Scrie întrebările tale. 'schimba' pentru alt agent, 'exit' pentru ieșire.\n")

    # Loop de întrebări
    while True:
        intrebare = input("Întrebare: ").strip()

        if not intrebare:
            continue

        if intrebare.lower() == "exit":
            print("La revedere!")
            return

        if intrebare.lower() == "schimba":
            while True:
                tip_agent = input("Agent nou: ").strip().lower()
                if tip_agent in ("pfa", "rental_income", "certificate"):
                    print(f"Agent schimbat la: {tip_agent}\n")
                    break
                print("Agent invalid. Alege din: pfa, rental_income, certificate")
            continue

        # Interogare RAG
        print("\nSe caută răspunsul...\n")
        raspuns = rag_service.query(intrebare, tip_agent)
        print(f"Răspuns:\n{raspuns}\n")
        print("-" * 60)


if __name__ == "__main__":
    main()
