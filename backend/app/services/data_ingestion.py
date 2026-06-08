import asyncio
import logging
import time

import requests
import yfinance as yf
from langchain_core.documents import Document

from app.services.vector_store import ingest_documents

logger = logging.getLogger(__name__)

TICKERS = ["AAPL", "MSFT", "NVDA", "TSLA", "AMZN"]

_USER_AGENT = "stk-portfolio-assistant/0.1 (portfolio research tool)"
_MAX_RETRIES = 3
_BACKOFF_SECONDS = [2, 4, 8]
_INTER_TICKER_DELAY = 2

# Static fallback data — used when Yahoo Finance is unavailable or rate-limited.
# Prices and ratios are representative ranges, not real-time quotes.
_STATIC_DATA: dict[str, dict] = {
    "AAPL": {
        "name": "Apple Inc.",
        "sector": "Technology",
        "industry": "Consumer Electronics",
        "current_price": 187.50,
        "market_cap": 2_900_000_000_000,
        "pe_trailing": 29.4,
        "pe_forward": 27.1,
        "week_high": 199.62,
        "week_low": 164.08,
        "div_pct": "0.53%",
        "summary": (
            "Apple Inc. designs, manufactures, and markets smartphones, personal computers, "
            "tablets, wearables, and accessories. Its flagship products include iPhone, Mac, "
            "iPad, Apple Watch, and AirPods. The company also operates a growing Services "
            "segment encompassing the App Store, Apple Music, iCloud, and Apple TV+."
        ),
        "history": [
            "2025-05-28: Open=186.10, High=188.45, Low=185.60, Close=187.50, Volume=54,321,000",
            "2025-05-27: Open=184.80, High=187.20, Low=183.95, Close=186.10, Volume=61,450,000",
            "2025-05-23: Open=183.50, High=185.30, Low=182.70, Close=184.80, Volume=48,900,000",
            "2025-05-22: Open=182.00, High=184.10, Low=181.40, Close=183.50, Volume=52,100,000",
            "2025-05-21: Open=180.75, High=182.60, Low=179.90, Close=182.00, Volume=59,700,000",
        ],
    },
    "MSFT": {
        "name": "Microsoft Corporation",
        "sector": "Technology",
        "industry": "Software — Infrastructure",
        "current_price": 415.20,
        "market_cap": 3_080_000_000_000,
        "pe_trailing": 35.8,
        "pe_forward": 31.2,
        "week_high": 468.35,
        "week_low": 385.00,
        "div_pct": "0.72%",
        "summary": (
            "Microsoft Corporation develops and licenses software, services, and hardware. "
            "Its segments include Productivity and Business Processes (Office 365, LinkedIn), "
            "Intelligent Cloud (Azure, SQL Server), and More Personal Computing (Windows, Xbox, "
            "Surface). Azure is the world's second-largest cloud platform and a primary growth driver."
        ),
        "history": [
            "2025-05-28: Open=413.50, High=416.80, Low=412.60, Close=415.20, Volume=21,340,000",
            "2025-05-27: Open=410.20, High=414.10, Low=409.30, Close=413.50, Volume=24,560,000",
            "2025-05-23: Open=407.80, High=411.50, Low=406.90, Close=410.20, Volume=19,870,000",
            "2025-05-22: Open=405.10, High=408.60, Low=404.20, Close=407.80, Volume=22,100,000",
            "2025-05-21: Open=402.30, High=406.40, Low=401.50, Close=405.10, Volume=25,430,000",
        ],
    },
    "NVDA": {
        "name": "NVIDIA Corporation",
        "sector": "Technology",
        "industry": "Semiconductors",
        "current_price": 875.40,
        "market_cap": 2_150_000_000_000,
        "pe_trailing": 68.2,
        "pe_forward": 39.5,
        "week_high": 974.00,
        "week_low": 435.00,
        "div_pct": "0.03%",
        "summary": (
            "NVIDIA Corporation designs graphics processing units (GPUs) and system-on-chip units. "
            "Its Data Center segment supplies GPUs and networking solutions powering AI training and "
            "inference workloads at hyperscale. Products like the H100 and Blackwell architecture "
            "have made NVIDIA the dominant provider of AI compute infrastructure globally."
        ),
        "history": [
            "2025-05-28: Open=870.10, High=879.50, Low=868.30, Close=875.40, Volume=42,150,000",
            "2025-05-27: Open=862.40, High=872.00, Low=860.80, Close=870.10, Volume=48,320,000",
            "2025-05-23: Open=855.20, High=864.70, Low=853.40, Close=862.40, Volume=39,780,000",
            "2025-05-22: Open=847.50, High=857.30, Low=845.60, Close=855.20, Volume=44,500,000",
            "2025-05-21: Open=839.80, High=849.60, Low=837.90, Close=847.50, Volume=51,230,000",
        ],
    },
    "TSLA": {
        "name": "Tesla, Inc.",
        "sector": "Consumer Cyclical",
        "industry": "Auto Manufacturers",
        "current_price": 175.30,
        "market_cap": 558_000_000_000,
        "pe_trailing": 46.1,
        "pe_forward": 65.3,
        "week_high": 271.00,
        "week_low": 138.80,
        "div_pct": "N/A",
        "summary": (
            "Tesla, Inc. designs, develops, manufactures, and sells electric vehicles, energy "
            "generation, and storage systems. Its vehicle lineup includes Model 3, Model Y, Model S, "
            "Model X, and Cybertruck. Tesla also operates a global Supercharger network and offers "
            "energy products such as Powerwall and Megapack. FSD software is a key long-term revenue lever."
        ),
        "history": [
            "2025-05-28: Open=173.60, High=177.20, Low=172.80, Close=175.30, Volume=98,450,000",
            "2025-05-27: Open=170.90, High=174.50, Low=169.70, Close=173.60, Volume=112,300,000",
            "2025-05-23: Open=168.40, High=172.10, Low=167.50, Close=170.90, Volume=89,670,000",
            "2025-05-22: Open=165.80, High=169.60, Low=164.90, Close=168.40, Volume=104,200,000",
            "2025-05-21: Open=163.10, High=167.30, Low=162.40, Close=165.80, Volume=118,900,000",
        ],
    },
    "AMZN": {
        "name": "Amazon.com, Inc.",
        "sector": "Consumer Cyclical",
        "industry": "Internet Retail",
        "current_price": 185.60,
        "market_cap": 1_960_000_000_000,
        "pe_trailing": 52.7,
        "pe_forward": 38.4,
        "week_high": 215.90,
        "week_low": 151.61,
        "div_pct": "N/A",
        "summary": (
            "Amazon.com, Inc. operates as a technology and e-commerce conglomerate. Its segments "
            "include North America and International retail, and Amazon Web Services (AWS), the "
            "world's largest cloud platform. Amazon also operates Prime Video, Alexa, Kindle, "
            "Whole Foods, and a rapidly growing advertising business. AWS contributes the majority "
            "of Amazon's operating income."
        ),
        "history": [
            "2025-05-28: Open=184.10, High=186.80, Low=183.40, Close=185.60, Volume=35,670,000",
            "2025-05-27: Open=181.90, High=184.70, Low=181.20, Close=184.10, Volume=39,450,000",
            "2025-05-23: Open=179.50, High=182.60, Low=178.80, Close=181.90, Volume=31,230,000",
            "2025-05-22: Open=177.20, High=180.40, Low=176.50, Close=179.50, Volume=33,800,000",
            "2025-05-21: Open=174.80, High=178.10, Low=174.10, Close=177.20, Volume=40,120,000",
        ],
    },
}


def _static_documents(ticker: str) -> list[Document]:
    d = _STATIC_DATA[ticker]
    name = d["name"]
    info_doc = Document(
        page_content=(
            f"Stock: {ticker} ({name})\n"
            f"Sector: {d['sector']}\n"
            f"Industry: {d['industry']}\n"
            f"Current Price: ${d['current_price']:.2f}\n"
            f"Market Cap: ${d['market_cap']:,.0f}\n"
            f"P/E Ratio (Trailing): {d['pe_trailing']}\n"
            f"P/E Ratio (Forward): {d['pe_forward']}\n"
            f"52-Week High: ${d['week_high']}\n"
            f"52-Week Low: ${d['week_low']}\n"
            f"Dividend Yield: {d['div_pct']}\n"
            f"Business Summary: {d['summary']}"
        ),
        metadata={"ticker": ticker, "name": name, "type": "company_info", "source": f"{ticker}_info_static"},
    )
    history_doc = Document(
        page_content=f"Recent price history for {ticker} ({name}):\n" + "\n".join(d["history"]),
        metadata={"ticker": ticker, "name": name, "type": "price_history", "source": f"{ticker}_history_static"},
    )
    return [info_doc, history_doc]


def _make_session() -> requests.Session:
    s = requests.Session()
    s.headers.update({"User-Agent": _USER_AGENT})
    return s


def _fetch_ticker_documents(ticker: str, session: requests.Session) -> list[Document]:
    stock = yf.Ticker(ticker, session=session)
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


def _fetch_ticker_with_retry(ticker: str, session: requests.Session) -> list[Document]:
    """Fetch live documents for one ticker with exponential backoff, falling back to static data."""
    last_exc: Exception | None = None
    for attempt in range(_MAX_RETRIES):
        try:
            docs = _fetch_ticker_documents(ticker, session)
            logger.info("[%s] fetched live data — %d document(s)", ticker, len(docs))
            return docs
        except Exception as exc:
            last_exc = exc
            if attempt < _MAX_RETRIES - 1:
                wait = _BACKOFF_SECONDS[attempt]
                logger.warning(
                    "[%s] attempt %d/%d failed (%s) — retrying in %ds",
                    ticker, attempt + 1, _MAX_RETRIES, exc, wait,
                )
                time.sleep(wait)

    logger.warning(
        "[%s] all %d live attempts failed (%s) — using static fallback data",
        ticker, _MAX_RETRIES, last_exc,
    )
    return _static_documents(ticker)


def _ingest_all_sync() -> list[Document]:
    """Fetch all tickers sequentially with a delay between each."""
    session = _make_session()
    all_documents: list[Document] = []

    for i, ticker in enumerate(TICKERS):
        if i > 0:
            time.sleep(_INTER_TICKER_DELAY)
        docs = _fetch_ticker_with_retry(ticker, session)
        all_documents.extend(docs)

    return all_documents


async def fetch_and_ingest_ticker_data() -> int:
    loop = asyncio.get_event_loop()
    all_documents = await loop.run_in_executor(None, _ingest_all_sync)

    if not all_documents:
        logger.error("[data_ingestion] no documents produced — ingestion aborted")
        return 0

    count = await ingest_documents(all_documents)
    logger.info("[data_ingestion] ingestion complete — %d documents stored", count)
    return count
