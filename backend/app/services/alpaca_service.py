import logging
from typing import Optional

logger = logging.getLogger(__name__)


def _get_api():
    from app.core.config import settings
    if not (settings.alpaca_api_key and settings.alpaca_secret_key):
        return None
    import alpaca_trade_api as tradeapi
    return tradeapi.REST(
        key_id=settings.alpaca_api_key,
        secret_key=settings.alpaca_secret_key,
        base_url=settings.alpaca_base_url,
        api_version="v2",
    )


def get_live_price(ticker: str) -> Optional[float]:
    """Fetch real-time price from Alpaca. Returns None if unavailable."""
    api = _get_api()
    if api is None:
        return None
    sym = ticker.upper().strip()
    try:
        trade = api.get_latest_trade(sym)
        return round(float(trade.price), 2)
    except Exception as exc:
        logger.warning("Alpaca price fetch failed for %s: %s", sym, exc)
        return None


def get_portfolio_from_alpaca() -> list[dict]:
    """Return all open positions from the Alpaca paper trading account."""
    api = _get_api()
    if api is None:
        raise ValueError("Alpaca API keys not configured — set ALPACA_API_KEY and ALPACA_SECRET_KEY")
    try:
        positions = api.list_positions()
    except Exception as exc:
        raise RuntimeError(f"Failed to fetch Alpaca positions: {exc}") from exc

    result = []
    for pos in positions:
        sym = pos.symbol.upper()
        name = sym
        try:
            asset = api.get_asset(sym)
            name = asset.name or sym
        except Exception:
            pass
        result.append({
            "ticker": sym,
            "name": name,
            "quantity": float(pos.qty),
            "avg_entry_price": float(pos.avg_entry_price),
        })
    return result
