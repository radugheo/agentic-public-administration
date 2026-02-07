"""Serviciu RAG - Retrieval-Augmented Generation pentru knowledge base fiscal."""

from pathlib import Path

from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_core.messages import SystemMessage, HumanMessage

from ro_tax_agents.config.settings import settings


# Directorul unde se află fișierele knowledge
KNOWLEDGE_DIR = Path(__file__).parent.parent / "knowledge"

# Directorul unde ChromaDB va stoca datele persistent
CHROMA_PERSIST_DIR = Path(__file__).parent.parent.parent.parent / ".chroma"

# Maparea între tipul de agent și fișierul knowledge corespunzător
AGENT_FISIERE = {
    "pfa": "pfa_agent.txt",
    "rental_income": "rental_income_agent.txt",
    "certificate": "certificate_agent.txt",
}

# Prompt de sistem pentru răspunsurile RAG
RAG_SYSTEM_PROMPT = """Ești un expert în legislația fiscală din România.
Răspunde întrebărilor utilizatorului DOAR pe baza contextului furnizat mai jos.
Dacă informația nu se găsește în context, spune clar că nu ai informația necesară.
Răspunde în limba română, clar și concis.

Context relevant:
{context}
"""


class RAGService:
    """Serviciu RAG pentru interogarea bazei de cunoștințe fiscale.

    Încarcă fișierele .txt din directorul knowledge/, creează embeddings
    cu OpenAI și stochează vectorii în ChromaDB.

    Tipuri de agenți suportați: pfa, rental_income, certificate
    """

    def __init__(self):
        self._vector_stores: dict[str, Chroma] = {}
        self._embeddings = None
        self._llm = None
        self._initializat = False

    @property
    def embeddings(self) -> OpenAIEmbeddings:
        """Inițializare lazy pentru embeddings OpenAI."""
        if self._embeddings is None:
            self._embeddings = OpenAIEmbeddings(
                model="text-embedding-3-small",
                api_key=settings.openai_api_key or None,
            )
        return self._embeddings

    @property
    def llm(self) -> ChatOpenAI:
        """Inițializare lazy pentru LLM."""
        if self._llm is None:
            self._llm = ChatOpenAI(
                model=settings.openai_model,
                temperature=0,
                api_key=settings.openai_api_key or None,
            )
        return self._llm

    def initializeaza(self) -> None:
        """Încarcă fișierele knowledge și creează vector stores în ChromaDB.

        Procesează fiecare fișier .txt, îl împarte în chunks și creează
        un vector store separat pentru fiecare tip de agent.
        """
        if self._initializat:
            return

        # Creează directorul pentru ChromaDB dacă nu există
        CHROMA_PERSIST_DIR.mkdir(parents=True, exist_ok=True)

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n================", "\n------", "\n\n", "\n", " "],
        )

        for tip_agent, nume_fisier in AGENT_FISIERE.items():
            cale_fisier = KNOWLEDGE_DIR / nume_fisier

            if not cale_fisier.exists():
                print(f"Fișierul {cale_fisier} nu a fost găsit.")
                continue

            # Citește conținutul fișierului
            continut = cale_fisier.read_text(encoding="utf-8")

            # Împarte textul în chunks
            chunks = text_splitter.split_text(continut)

            # Creează documentele cu metadata
            documente = [
                Document(
                    page_content=chunk,
                    metadata={
                        "sursa": nume_fisier,
                        "tip_agent": tip_agent,
                        "chunk_index": i,
                    },
                )
                for i, chunk in enumerate(chunks)
            ]

            # Creează vector store-ul în ChromaDB
            cale_colectie = str(CHROMA_PERSIST_DIR / tip_agent)
            self._vector_stores[tip_agent] = Chroma.from_documents(
                documents=documente,
                embedding=self.embeddings,
                collection_name=f"knowledge_{tip_agent}",
                persist_directory=cale_colectie,
            )

            print(f"Fisier: {nume_fisier} - {len(documente)} chunks pentru '{tip_agent}'")

        self._initializat = True
        agenti = list(self._vector_stores.keys())
        print(f"Inițializare completă. Agenți disponibili: {agenti}")

    def retrieve(self, query: str, tip_agent: str, k: int = 3) -> list[Document]:
        """Returnează cele mai relevante documente pentru o întrebare.

        Args:
            query: Întrebarea utilizatorului
            tip_agent: Tipul agentului (pfa, rental_income, certificate)
            k: Numărul de documente de returnat

        Returns:
            Lista de documente relevante

        Raises:
            ValueError: Dacă tipul agentului nu este valid
        """
        if not self._initializat:
            self.initializeaza()

        if tip_agent not in self._vector_stores:
            tipuri_valide = list(AGENT_FISIERE.keys())
            raise ValueError(
                f"Tip agent invalid: '{tip_agent}'. Tipuri valide: {tipuri_valide}"
            )

        vector_store = self._vector_stores[tip_agent]
        rezultate = vector_store.similarity_search(query, k=k)
        return rezultate

    def query(self, intrebare: str, tip_agent: str, k: int = 3) -> str:
        """Interogare RAG completă: retrieval + generare răspuns cu LLM.

        Args:
            intrebare: Întrebarea utilizatorului
            tip_agent: Tipul agentului (pfa, rental_income, certificate)
            k: Numărul de documente folosite ca context

        Returns:
            Răspunsul generat de LLM pe baza contextului găsit
        """
        # Obține documentele relevante
        documente = self.retrieve(intrebare, tip_agent, k=k)

        # Construiește contextul din documentele găsite
        context = "\n\n---\n\n".join(doc.page_content for doc in documente)

        # Generează răspunsul cu LLM
        prompt_sistem = RAG_SYSTEM_PROMPT.format(context=context)

        raspuns = self.llm.invoke([
            SystemMessage(content=prompt_sistem),
            HumanMessage(content=intrebare),
        ])

        return raspuns.content


# instanta singleton, de importat mai departe
rag_service = RAGService()
