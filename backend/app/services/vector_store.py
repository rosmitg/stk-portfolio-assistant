from langchain_voyageai import VoyageAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document

from app.core.config import settings

_embeddings: VoyageAIEmbeddings | None = None
_vector_store: Chroma | None = None


def get_embeddings() -> VoyageAIEmbeddings:
    global _embeddings
    if _embeddings is None:
        _embeddings = VoyageAIEmbeddings(
            voyage_api_key=settings.voyage_api_key,
            model="voyage-3-lite",
        )
    return _embeddings


def get_vector_store() -> Chroma:
    global _vector_store
    if _vector_store is None:
        _vector_store = Chroma(
            collection_name=settings.chroma_collection_name,
            embedding_function=get_embeddings(),
            persist_directory=settings.chroma_persist_dir,
        )
    return _vector_store


async def ingest_documents(documents: list[Document]) -> int:
    store = get_vector_store()
    ids = store.add_documents(documents)
    return len(ids)


def get_document_count() -> int:
    try:
        store = get_vector_store()
        return store._collection.count()
    except Exception:
        return 0
