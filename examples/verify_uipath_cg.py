"""Verify UiPath Context Grounding connectivity and retrieval."""

from dotenv import load_dotenv
load_dotenv()

from uipath_langchain.retrievers import ContextGroundingRetriever
from ro_tax_agents.services.rag_service import AGENT_INDEXES
from ro_tax_agents.config.settings import settings

print("=" * 60)
print("UiPath Context Grounding - Verification")
print("=" * 60)

test_queries = {
    "pfa": "Ce contributii CAS si CASS trebuie sa platesc?",
    "rental_income": "Cum inregistrez un contract de inchiriere?",
    "certificate": "Cum obtin un certificat de atestare fiscala?",
}

for agent_type, index_name in AGENT_INDEXES.items():
    print(f"\n--- {agent_type} (index: {index_name}) ---")
    query = test_queries.get(agent_type, "test")

    try:
        retriever = ContextGroundingRetriever(
            index_name=index_name,
            number_of_results=2,
            folder_path=settings.uipath_folder_path or None,
        )
        docs = retriever.invoke(query)
        print(f"  Query: {query}")
        print(f"  Results: {len(docs)} documents")
        for i, doc in enumerate(docs):
            source = doc.metadata.get("source", "N/A")
            print(f"  [{i+1}] source={source}, content={doc.page_content[:100]}...")
    except Exception as e:
        print(f"  ERROR: {e}")

print("\n" + "=" * 60)
print("Done. If you see results above, UiPath CG is working.")
print("=" * 60)
