import json
import logging
from typing import AsyncGenerator, Optional

import yfinance as yf
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import tool
from langsmith import traceable

from app.core.config import settings
from app.services.llm import get_llm
from app.services.prompt_registry import load_prompt
from app.services.rag import run_rag_query

logger = logging.getLogger(__name__)

_STATIC_STOCK_DATA: dict[str, dict] = {
    "AAPL": {"name": "Apple Inc.", "sector": "Technology", "price": 195.0},
    "MSFT": {"name": "Microsoft Corp.", "sector": "Technology", "price": 415.0},
    "GOOGL": {"name": "Alphabet Inc.", "sector": "Technology", "price": 175.0},
    "AMZN": {"name": "Amazon.com Inc.", "sector": "Consumer Discretionary", "price": 185.0},
    "NVDA": {"name": "NVIDIA Corp.", "sector": "Technology", "price": 875.0},
}


@tool
def ticker_info(ticker: str) -> str:
    """Get the current stock price and basic market info for a ticker symbol (e.g. AAPL, MSFT)."""
    sym = ticker.upper().strip()

    # Try Alpaca first for real-time price
    try:
        from app.services.alpaca_service import get_live_price
        price = get_live_price(sym)
        if price is not None:
            return json.dumps({"ticker": sym, "price": price, "source": "alpaca"})
    except Exception:
        pass

    # Fall back to yfinance
    try:
        fi = yf.Ticker(sym).fast_info
        price = fi.last_price
        if price is None:
            raise ValueError("null price")
        return json.dumps({
            "ticker": sym,
            "price": round(float(price), 2),
            "currency": getattr(fi, "currency", "USD"),
            "market_cap": getattr(fi, "market_cap", None),
            "52w_high": getattr(fi, "year_high", None),
            "52w_low": getattr(fi, "year_low", None),
            "source": "yfinance",
        })
    except Exception as exc:
        logger.warning("yfinance error for %s (%s), using static fallback", sym, exc)

    static = _STATIC_STOCK_DATA.get(sym)
    if static:
        return json.dumps({
            "ticker": sym,
            "name": static["name"],
            "price": static["price"],
            "note": "static fallback — live data unavailable",
        })
    return json.dumps({"error": f"Could not retrieve data for {sym}"})


@tool
def news_headlines(ticker: str) -> str:
    """Fetch the latest 5 news headlines and descriptions for a stock ticker."""
    if not settings.news_api_key:
        return json.dumps({"error": "NEWS_API_KEY not configured"})
    sym = ticker.upper().strip()
    try:
        from newsapi import NewsApiClient
        client = NewsApiClient(api_key=settings.news_api_key)
        company = _STATIC_STOCK_DATA.get(sym, {}).get("name", sym)
        resp = client.get_everything(
            q=f"{sym} OR \"{company}\"",
            language="en",
            sort_by="publishedAt",
            page_size=5,
        )
        articles = resp.get("articles", [])[:5]
        return json.dumps({
            "ticker": sym,
            "headlines": [
                {
                    "title": a["title"],
                    "description": a.get("description") or "",
                    "published_at": a.get("publishedAt") or "",
                    "source": a.get("source", {}).get("name") or "",
                }
                for a in articles
            ],
        })
    except Exception as exc:
        logger.error("NewsAPI error: %s", exc)
        return json.dumps({"error": str(exc)})


@tool
def portfolio_calculator(holdings_json: str) -> str:
    """Calculate portfolio metrics from a JSON list of holdings.

    Each holding must include: ticker (str), quantity (float), avg_buy_price (float).
    Returns total value, gain/loss per holding, and allocation percentages.

    Example input:
      '[{"ticker": "AAPL", "quantity": 10, "avg_buy_price": 150.0},
        {"ticker": "MSFT", "quantity": 5, "avg_buy_price": 300.0}]'
    """
    try:
        holdings = json.loads(holdings_json)
    except json.JSONDecodeError as exc:
        return json.dumps({"error": f"Invalid JSON: {exc}"})

    rows = []
    total_cost = 0.0
    total_value = 0.0

    for h in holdings:
        sym = h["ticker"].upper().strip()
        qty = float(h["quantity"])
        avg_buy = float(h["avg_buy_price"])

        current_price: float = avg_buy  # safe default
        try:
            fi = yf.Ticker(sym).fast_info
            lp = fi.last_price
            if lp is not None:
                current_price = float(lp)
        except Exception:
            current_price = _STATIC_STOCK_DATA.get(sym, {}).get("price", avg_buy)

        cost_basis = qty * avg_buy
        market_value = qty * current_price
        gain_loss = market_value - cost_basis
        gain_loss_pct = (gain_loss / cost_basis * 100) if cost_basis > 0 else 0.0

        total_cost += cost_basis
        total_value += market_value
        rows.append({
            "ticker": sym,
            "quantity": qty,
            "avg_buy_price": round(avg_buy, 2),
            "current_price": round(current_price, 2),
            "cost_basis": round(cost_basis, 2),
            "market_value": round(market_value, 2),
            "gain_loss": round(gain_loss, 2),
            "gain_loss_pct": round(gain_loss_pct, 2),
        })

    total_gain = total_value - total_cost
    total_gain_pct = (total_gain / total_cost * 100) if total_cost > 0 else 0.0

    for row in rows:
        row["allocation_pct"] = round(row["market_value"] / total_value * 100, 2) if total_value > 0 else 0.0

    return json.dumps({
        "holdings": rows,
        "summary": {
            "total_cost": round(total_cost, 2),
            "total_value": round(total_value, 2),
            "total_gain_loss": round(total_gain, 2),
            "total_gain_loss_pct": round(total_gain_pct, 2),
        },
    })


@tool
async def rag_search(query: str) -> str:
    """Search the portfolio knowledge base for in-depth research, fundamentals, or analysis about stocks."""
    answer, _ = await run_rag_query(query)
    return answer


def _build_executor(portfolio_context: str) -> AgentExecutor:
    system_text = load_prompt("agent_system_prompt")["system"]
    if portfolio_context:
        system_text += f"\n\nUser's current portfolio holdings:\n{portfolio_context}"

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_text),
        ("human", "{input}"),
        MessagesPlaceholder("agent_scratchpad"),
    ])

    llm = get_llm()
    tools = [ticker_info, news_headlines, portfolio_calculator, rag_search]
    agent = create_tool_calling_agent(llm, tools, prompt)
    return AgentExecutor(
        agent=agent,
        tools=tools,
        max_iterations=10,
        max_execution_time=60,
        return_intermediate_steps=True,
    )


def _extract_sources(intermediate_steps: list) -> list[str]:
    tickers: set[str] = set()
    for action, _ in intermediate_steps:
        tool_input = action.tool_input
        if isinstance(tool_input, dict):
            val = tool_input.get("ticker") or tool_input.get("holdings_json") or ""
            if isinstance(val, str) and 1 <= len(val) <= 6 and val.isalpha():
                tickers.add(val.upper())
            # portfolio_calculator JSON
            try:
                items = json.loads(val) if val else []
                if isinstance(items, list):
                    for item in items:
                        if isinstance(item, dict) and "ticker" in item:
                            tickers.add(item["ticker"].upper())
            except (json.JSONDecodeError, TypeError):
                pass
        elif isinstance(tool_input, str):
            # Might be a raw ticker or JSON string
            stripped = tool_input.strip().upper()
            if 1 <= len(stripped) <= 6 and stripped.isalpha():
                tickers.add(stripped)
            else:
                try:
                    items = json.loads(tool_input)
                    if isinstance(items, list):
                        for item in items:
                            if isinstance(item, dict) and "ticker" in item:
                                tickers.add(item["ticker"].upper())
                except (json.JSONDecodeError, TypeError):
                    pass
    return sorted(tickers)


async def stream_agent_query(
    message: str,
    portfolio_holdings: Optional[list[dict]] = None,
) -> AsyncGenerator[dict, None]:
    portfolio_context = ""
    if portfolio_holdings:
        lines = [
            f"- {h.get('ticker', '').upper()}: {h.get('quantity', 0)} shares @ avg ${float(h.get('avg_buy_price', 0)):.2f}"
            for h in portfolio_holdings
        ]
        portfolio_context = "\n".join(lines)

    executor = _build_executor(portfolio_context)
    sources: set[str] = set()

    async for event in executor.astream_events({"input": message}, version="v2"):
        kind = event["event"]

        if kind == "on_chat_model_stream":
            chunk = event["data"].get("chunk")
            if not chunk:
                continue
            content = chunk.content
            if isinstance(content, list):
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        text = block.get("text", "")
                        if text:
                            yield {"type": "token", "text": text}
            elif isinstance(content, str) and content:
                yield {"type": "token", "text": content}

        elif kind == "on_tool_end":
            tool_name = event.get("name", "")
            inp = event["data"].get("input") or {}
            if tool_name in ("ticker_info", "news_headlines"):
                ticker = (inp.get("ticker") or "").upper()
                if ticker and 1 <= len(ticker) <= 6:
                    sources.add(ticker)
            elif tool_name == "portfolio_calculator":
                try:
                    items = json.loads(inp.get("holdings_json") or "[]")
                    for item in items:
                        if isinstance(item, dict) and "ticker" in item:
                            sources.add(item["ticker"].upper())
                except (json.JSONDecodeError, TypeError):
                    pass

    yield {"type": "done", "sources": sorted(sources)}


@traceable(name="portfolio-agent-query", run_type="chain")
async def run_agent_query(
    message: str,
    portfolio_holdings: Optional[list[dict]] = None,
) -> tuple[str, list[str]]:
    portfolio_context = ""
    if portfolio_holdings:
        lines = [
            f"- {h.get('ticker', '').upper()}: {h.get('quantity', 0)} shares @ avg ${float(h.get('avg_buy_price', 0)):.2f}"
            for h in portfolio_holdings
        ]
        portfolio_context = "\n".join(lines)

    executor = _build_executor(portfolio_context)
    result = await executor.ainvoke({"input": message})

    raw = result.get("output", "")
    if isinstance(raw, list):
        answer = " ".join(
            block["text"] if isinstance(block, dict) else str(block)
            for block in raw
            if not isinstance(block, dict) or block.get("type") != "tool_use"
        )
    else:
        answer = raw
    sources = _extract_sources(result.get("intermediate_steps", []))
    return answer, sources
