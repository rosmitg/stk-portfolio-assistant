import asyncio

import yfinance as yf
from langchain_core.documents import Document

from app.services.vector_store import ingest_documents

TICKERS = ["AAPL", "MSFT", "NVDA", "TSLA", "AMZN"]


def _fetch_ticker_documents(ticker: str) -> list[Document]:
    stock = yf.Ticker(ticker)
    info = stock.info
    hist = stock.history(period="5d")

    name = info.get("longName", ticker)
    sector = info.get("sector", "N/A")
    industry = info.get("industry", "N/A")
    market_cap = info.get("marketCap") or 0
    pe_trailing = info.get("trailingPE", "N/A")
    pe_forward = info.get("forwardPE", "N/A")
    week_high = info.get("fiftyTwoWeekHigh", "N/A")
    week_low = info.get("fiftyTwoWeekLow", "N/A")
    current_price = info.get("currentPrice") or info.get("regularMarketPrice", "N/A")
    div_yield = info.get("dividendYield")
    div_pct = f"{div_yield * 100:.2f}%" if isinstance(div_yield, float) else "N/A"
    summary = (info.get("longBusinessSummary") or "")[:500]

    info_doc = Document(
        page_content=(
            f"Stock: {ticker} ({name})\n"
            f"Sector: {sector}\n"
            f"Industry: {industry}\n"
            f"Current Price: ${current_price}\n"
            f"Market Cap: ${market_cap:,.0f}\n"
            f"P/E Ratio (Trailing): {pe_trailing}\n"
            f"P/E Ratio (Forward): {pe_forward}\n"
            f"52-Week High: ${week_high}\n"
            f"52-Week Low: ${week_low}\n"
            f"Dividend Yield: {div_pct}\n"
            f"Business Summary: {summary}"
        ),
        metadata={"ticker": ticker, "name": name, "type": "company_info", "source": f"{ticker}_info"},
    )

    documents: list[Document] = [info_doc]

    if not hist.empty:
        lines = [
            f"{date.strftime('%Y-%m-%d')}: Open={row['Open']:.2f}, High={row['High']:.2f}, "
            f"Low={row['Low']:.2f}, Close={row['Close']:.2f}, Volume={int(row['Volume']):,}"
            for date, row in hist.tail(5).iterrows()
        ]
        history_doc = Document(
            page_content=f"Recent price history for {ticker} ({name}):\n" + "\n".join(lines),
            metadata={"ticker": ticker, "name": name, "type": "price_history", "source": f"{ticker}_history"},
        )
        documents.append(history_doc)

    return documents


async def fetch_and_ingest_ticker_data() -> int:
    loop = asyncio.get_event_loop()
    all_documents: list[Document] = []

    for ticker in TICKERS:
        try:
            docs = await loop.run_in_executor(None, _fetch_ticker_documents, ticker)
            all_documents.extend(docs)
        except Exception as exc:
            print(f"[data_ingestion] failed to fetch {ticker}: {exc}")

    if not all_documents:
        return 0

    return await ingest_documents(all_documents)
