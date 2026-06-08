import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.evaluator import (
    EVAL_DATASET,
    _parse_score,
    answer_relevance_eval,
    faithfulness_eval,
    run_evaluation,
)


# ── _parse_score ───────────────────────────────────────────────────────────────

def test_parse_score_plain_integer():
    assert _parse_score("8") == 0.8


def test_parse_score_with_label():
    assert _parse_score("Score: 7") == 0.7


def test_parse_score_fraction():
    assert _parse_score("9/10") == 0.9


def test_parse_score_ten():
    assert _parse_score("10") == 1.0


def test_parse_score_zero():
    assert _parse_score("0") == 0.0


def test_parse_score_unparseable_defaults():
    assert _parse_score("no number here") == 0.5


# ── answer_relevance_eval ──────────────────────────────────────────────────────

def test_answer_relevance_eval_high_score():
    mock_response = MagicMock()
    mock_response.content = "9"

    async def _run():
        with patch("app.services.evaluator.get_llm") as mock_get_llm:
            mock_llm = MagicMock()
            mock_llm.ainvoke = AsyncMock(return_value=mock_response)
            mock_get_llm.return_value = mock_llm

            score = await answer_relevance_eval(
                question="What is AAPL's price?",
                answer="Apple's current stock price is $187.50.",
            )
        return score

    score = asyncio.run(_run())
    assert score == pytest.approx(0.9)


def test_answer_relevance_eval_low_score():
    mock_response = MagicMock()
    mock_response.content = "2"

    async def _run():
        with patch("app.services.evaluator.get_llm") as mock_get_llm:
            mock_llm = MagicMock()
            mock_llm.ainvoke = AsyncMock(return_value=mock_response)
            mock_get_llm.return_value = mock_llm

            score = await answer_relevance_eval(
                question="What is AAPL's price?",
                answer="The weather in Paris is sunny today.",
            )
        return score

    score = asyncio.run(_run())
    assert score == pytest.approx(0.2)


def test_answer_relevance_eval_llm_error_returns_zero():
    async def _run():
        with patch("app.services.evaluator.get_llm") as mock_get_llm:
            mock_llm = MagicMock()
            mock_llm.ainvoke = AsyncMock(side_effect=RuntimeError("network error"))
            mock_get_llm.return_value = mock_llm

            score = await answer_relevance_eval("q", "a")
        return score

    assert asyncio.run(_run()) == 0.0


# ── faithfulness_eval ──────────────────────────────────────────────────────────

def test_faithfulness_eval_with_context():
    mock_response = MagicMock()
    mock_response.content = "8"

    async def _run():
        with patch("app.services.evaluator.get_llm") as mock_get_llm:
            mock_llm = MagicMock()
            mock_llm.ainvoke = AsyncMock(return_value=mock_response)
            mock_get_llm.return_value = mock_llm

            score = await faithfulness_eval(
                question="What sector is NVDA in?",
                answer="NVIDIA is in the semiconductor sector.",
                context="NVIDIA Corporation is a semiconductor company.",
            )
        return score

    assert asyncio.run(_run()) == pytest.approx(0.8)


def test_faithfulness_eval_without_context():
    mock_response = MagicMock()
    mock_response.content = "6"

    async def _run():
        with patch("app.services.evaluator.get_llm") as mock_get_llm:
            mock_llm = MagicMock()
            mock_llm.ainvoke = AsyncMock(return_value=mock_response)
            mock_get_llm.return_value = mock_llm

            score = await faithfulness_eval(
                question="What is Tesla's market cap?",
                answer="Tesla's market cap is roughly $500 billion.",
            )
        return score

    assert asyncio.run(_run()) == pytest.approx(0.6)


def test_faithfulness_eval_llm_error_returns_zero():
    async def _run():
        with patch("app.services.evaluator.get_llm") as mock_get_llm:
            mock_llm = MagicMock()
            mock_llm.ainvoke = AsyncMock(side_effect=RuntimeError("timeout"))
            mock_get_llm.return_value = mock_llm

            return await faithfulness_eval("q", "a")

    assert asyncio.run(_run()) == 0.0


# ── run_evaluation ─────────────────────────────────────────────────────────────

def test_run_evaluation_returns_correct_structure():
    async def _run():
        with (
            patch("app.services.evaluator.run_agent_query") as mock_agent,
            patch("app.services.evaluator.answer_relevance_eval") as mock_rel,
            patch("app.services.evaluator.faithfulness_eval") as mock_faith,
        ):
            mock_agent.return_value = ("The answer is 42.", ["AAPL"])
            mock_rel.return_value = 0.9
            mock_faith.return_value = 0.8

            # Wrap sync mocks so they behave as coroutines
            mock_agent.__call__ = AsyncMock(return_value=("The answer is 42.", ["AAPL"]))
            mock_rel.__call__ = AsyncMock(return_value=0.9)
            mock_faith.__call__ = AsyncMock(return_value=0.8)

            result = await run_evaluation()
        return result

    result = asyncio.run(_run())
    assert "results" in result
    assert "summary" in result
    assert result["summary"]["total_questions"] == len(EVAL_DATASET)
    assert "average_relevance" in result["summary"]
    assert "average_faithfulness" in result["summary"]


def test_run_evaluation_agent_error_continues():
    """If one agent call fails, run_evaluation should continue and record empty answer."""
    call_count = 0

    async def fake_agent(question, portfolio_holdings=None):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise RuntimeError("agent blew up")
        return ("Some answer.", [])

    async def fake_score(*args, **kwargs):
        return 0.7

    async def _run():
        with (
            patch("app.services.evaluator.run_agent_query", side_effect=fake_agent),
            patch("app.services.evaluator.answer_relevance_eval", side_effect=fake_score),
            patch("app.services.evaluator.faithfulness_eval", side_effect=fake_score),
        ):
            return await run_evaluation()

    result = asyncio.run(_run())
    # First result has empty answer due to the error
    assert result["results"][0]["answer"] == ""
    assert result["summary"]["total_questions"] == len(EVAL_DATASET)


# ── dataset sanity ─────────────────────────────────────────────────────────────

def test_eval_dataset_has_ten_items():
    assert len(EVAL_DATASET) == 10


def test_eval_dataset_covers_all_tools():
    tools_covered = {item["tool"] for item in EVAL_DATASET}
    assert tools_covered == {"ticker_info", "news_headlines", "portfolio_calculator", "rag_search"}


def test_eval_dataset_all_items_have_required_keys():
    for item in EVAL_DATASET:
        assert "question" in item
        assert "expected_answer" in item
        assert "tool" in item
