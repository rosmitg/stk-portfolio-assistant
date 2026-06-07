from langchain_core.prompts import ChatPromptTemplate

from app.services.llm import get_llm
from app.services.vector_store import get_vector_store

_SYSTEM_PROMPT = """\
You are a knowledgeable stock portfolio assistant. Use the provided context about \
portfolio holdings and market data to answer questions accurately and concisely. \
If the context does not contain enough information to fully answer the question, \
say so and answer as best you can.

Context:
{context}"""

_RAG_PROMPT = ChatPromptTemplate.from_messages([
    ("system", _SYSTEM_PROMPT),
    ("human", "{question}"),
])


def _format_docs(docs: list) -> str:
    return "\n\n".join(doc.page_content for doc in docs)


async def run_rag_query(question: str) -> tuple[str, list[str]]:
    llm = get_llm()
    vector_store = get_vector_store()
    retriever = vector_store.as_retriever(search_kwargs={"k": 4})

    docs = await retriever.ainvoke(question)
    context = _format_docs(docs)
    sources = list({doc.metadata.get("ticker", "") for doc in docs if doc.metadata.get("ticker")})

    messages = _RAG_PROMPT.format_messages(context=context, question=question)
    response = await llm.ainvoke(messages)

    return response.content, sources
