import logging
import re

from app.services.agent import run_agent_query
from app.services.llm import get_llm

logger = logging.getLogger(__name__)

EVAL_DATASET: list[dict] = [
    # --- ticker_info ---
    {
        "question": "What is the current stock price of Apple (AAPL)?",
        "expected_answer": "Current AAPL stock price with market data such as price, market cap, or 52-week range.",
        "tool": "ticker_info",
    },
    {
        "question": "What is NVIDIA's current market cap?",
        "expected_answer": "NVIDIA's current market capitalisation figure in dollars.",
        "tool": "ticker_info",
    },
    {
        "question": "What is Tesla's 52-week high and low?",
        "expected_answer": "Tesla's 52-week high and low stock prices.",
        "tool": "ticker_info",
    },
    # --- news_headlines ---
    {
        "question": "What are the latest news headlines for Microsoft?",
        "expected_answer": "A list of recent news headlines or articles related to Microsoft stock.",
        "tool": "news_headlines",
    },
    {
        "question": "Give me the most recent news about Amazon.",
        "expected_answer": "Recent news headlines or stories about Amazon (AMZN).",
        "tool": "news_headlines",
    },
    # --- portfolio_calculator ---
    {
        "question": "I own 10 shares of AAPL with an average buy price of $150. What is my current gain or loss?",
        "expected_answer": "Dollar gain/loss and percentage return for 10 AAPL shares bought at $150.",
        "tool": "portfolio_calculator",
    },
    {
        "question": "Calculate portfolio metrics for 5 MSFT shares at $350 average and 15 TSLA shares at $180 average.",
        "expected_answer": "Portfolio value, cost basis, gain/loss, and allocation percentages for MSFT and TSLA.",
        "tool": "portfolio_calculator",
    },
    {
        "question": "What is the total value of holding 20 NVDA shares bought at $800 and 50 AAPL shares bought at $170?",
        "expected_answer": "Total portfolio value and individual holding values for NVDA and AAPL.",
        "tool": "portfolio_calculator",
    },
    # --- rag_search ---
    {
        "question": "What sector does NVIDIA operate in and what is their core business?",
        "expected_answer": "NVIDIA operates in the Technology/Semiconductor sector and is known for GPUs and AI compute.",
        "tool": "rag_search",
    },
    {
        "question": "What are Apple's main product lines and revenue segments?",
        "expected_answer": "Apple's main products include iPhone, Mac, iPad, wearables, and a Services segment.",
        "tool": "rag_search",
    },
]


def _parse_score(text: str) -> float:
    """Extract the first integer 0-10 from a model response and normalise to 0-1."""
    match = re.search(r"\b(10|[0-9])\b", text.strip())
    if match:
        return int(match.group(1)) / 10.0
    logger.warning("Could not parse score from: %r — defaulting to 0.5", text)
    return 0.5


async def answer_relevance_eval(question: str, answer: str) -> float:
    """Return a 0–1 score for how relevant the answer is to the question."""
    llm = get_llm()
    prompt = (
        "You are an evaluation assistant. Rate how relevant the following answer is to the question "
        "on a scale of 0 to 10, where 0 means completely irrelevant and 10 means perfectly relevant.\n\n"
        f"Question: {question}\n\n"
        f"Answer: {answer}\n\n"
        "Respond with a single integer from 0 to 10 and nothing else."
    )
    try:
        response = await llm.ainvoke(prompt)
        return _parse_score(response.content)
    except Exception as exc:
        logger.error("answer_relevance_eval failed: %s", exc)
        return 0.0


async def faithfulness_eval(question: str, answer: str, context: str = "") -> float:
    """Return a 0–1 score for how well-grounded the answer is in facts/context."""
    llm = get_llm()
    if context:
        prompt = (
            "You are an evaluation assistant. Rate how faithful the following answer is to the "
            "provided context on a scale of 0 to 10, where 0 means the answer contradicts or "
            "ignores the context and 10 means every claim is directly supported by the context.\n\n"
            f"Context:\n{context}\n\n"
            f"Question: {question}\n\n"
            f"Answer: {answer}\n\n"
            "Respond with a single integer from 0 to 10 and nothing else."
        )
    else:
        prompt = (
            "You are an evaluation assistant. Rate how factually grounded and accurate the following "
            "answer appears on a scale of 0 to 10. Penalise vague claims, invented numbers, and "
            "obvious hallucinations. Reward specific, consistent, and verifiable statements.\n\n"
            f"Question: {question}\n\n"
            f"Answer: {answer}\n\n"
            "Respond with a single integer from 0 to 10 and nothing else."
        )
    try:
        response = await llm.ainvoke(prompt)
        return _parse_score(response.content)
    except Exception as exc:
        logger.error("faithfulness_eval failed: %s", exc)
        return 0.0


async def run_evaluation() -> dict:
    """Run every eval question through the agent and score each response."""
    results: list[dict] = []

    for item in EVAL_DATASET:
        question = item["question"]
        logger.info("[eval] running: %s", question)
        try:
            answer, sources = await run_agent_query(question)
        except Exception as exc:
            logger.error("[eval] agent error for %r: %s", question, exc)
            answer = ""
            sources = []

        relevance = await answer_relevance_eval(question, answer)
        faithfulness = await faithfulness_eval(question, answer)

        results.append(
            {
                "question": question,
                "expected_answer": item["expected_answer"],
                "tool": item["tool"],
                "answer": answer,
                "sources": sources,
                "relevance_score": round(relevance, 3),
                "faithfulness_score": round(faithfulness, 3),
            }
        )

    n = len(results)
    avg_relevance = round(sum(r["relevance_score"] for r in results) / n, 3) if n else 0.0
    avg_faithfulness = round(sum(r["faithfulness_score"] for r in results) / n, 3) if n else 0.0

    return {
        "results": results,
        "summary": {
            "total_questions": n,
            "average_relevance": avg_relevance,
            "average_faithfulness": avg_faithfulness,
        },
    }
