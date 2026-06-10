import csv
import io
import logging
from typing import Annotated, Optional

import yfinance as yf
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

CsvFile = Annotated[UploadFile, File(description="CSV with columns: ticker, shares, avg_cost")]

from app.models.portfolio import Holding
from app.schemas.schemas import AddHoldingRequest, PortfolioHolding
from app.services.database import get_db

router = APIRouter(tags=["portfolio"])
logger = logging.getLogger(__name__)

_STATIC_PRICES: dict[str, float] = {
    "AAPL": 187.50, "MSFT": 415.20, "NVDA": 875.40, "TSLA": 175.30, "AMZN": 185.60,
}

Db = Annotated[Optional[AsyncSession], Depends(get_db)]

_DEFAULT_USER = "default"


def _enrich(holding: Holding) -> PortfolioHolding:
    sym = holding.ticker.upper()
    current_price: Optional[float] = None

    # Try Alpaca first
    try:
        from app.services.alpaca_service import get_live_price
        current_price = get_live_price(sym)
    except Exception:
        pass

    # Fall back to yfinance
    if current_price is None:
        try:
            lp = yf.Ticker(sym).fast_info.last_price
            if lp is not None:
                current_price = float(lp)
        except Exception:
            pass

    # Final fallback
    if current_price is None:
        current_price = _STATIC_PRICES.get(sym, float(holding.avg_cost))

    cost_basis = holding.shares * holding.avg_cost
    market_value = holding.shares * current_price
    gain_loss = market_value - cost_basis
    gain_loss_pct = (gain_loss / cost_basis * 100) if cost_basis > 0 else 0.0

    return PortfolioHolding(
        ticker=sym,
        name=holding.name,
        shares=holding.shares,
        avg_cost=round(holding.avg_cost, 2),
        current_price=round(current_price, 2),
        market_value=round(market_value, 2),
        gain_loss=round(gain_loss, 2),
        gain_loss_pct=round(gain_loss_pct, 2),
    )


async def _upsert_holding(
    db: AsyncSession,
    ticker: str,
    name: str,
    shares: float,
    avg_cost: float,
) -> Holding:
    result = await db.execute(
        select(Holding).where(
            Holding.user_id == _DEFAULT_USER,
            Holding.ticker == ticker,
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        existing.shares = shares
        existing.avg_cost = avg_cost
        existing.name = name
        return existing
    holding = Holding(
        user_id=_DEFAULT_USER,
        ticker=ticker,
        name=name,
        shares=shares,
        avg_cost=avg_cost,
    )
    db.add(holding)
    return holding


@router.get("/portfolio", response_model=list[PortfolioHolding])
async def get_portfolio(db: Db) -> list[PortfolioHolding]:
    if db is None:
        return []
    try:
        result = await db.execute(
            select(Holding).where(Holding.user_id == _DEFAULT_USER).order_by(Holding.created_at)
        )
        return [_enrich(h) for h in result.scalars().all()]
    except Exception as exc:
        logger.warning("DB read failed: %s", exc)
        return []


@router.post("/portfolio", response_model=PortfolioHolding, status_code=201)
async def add_holding(body: AddHoldingRequest, db: Db) -> PortfolioHolding:
    if db is None:
        raise HTTPException(status_code=503, detail="Database not configured")
    try:
        holding = await _upsert_holding(
            db,
            ticker=body.ticker.upper(),
            name=body.name,
            shares=body.shares,
            avg_cost=body.avg_cost,
        )
        await db.commit()
        await db.refresh(holding)
        return _enrich(holding)
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Database unavailable: {exc}") from exc


@router.post("/portfolio/sync-alpaca", response_model=list[PortfolioHolding])
async def sync_from_alpaca(db: Db) -> list[PortfolioHolding]:
    if db is None:
        raise HTTPException(status_code=503, detail="Database not configured")
    try:
        from app.services.alpaca_service import get_portfolio_from_alpaca
        positions = get_portfolio_from_alpaca()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    if not positions:
        raise HTTPException(status_code=404, detail="No open positions found in Alpaca account")

    try:
        for pos in positions:
            await _upsert_holding(
                db,
                ticker=pos["ticker"],
                name=pos["name"],
                shares=pos["quantity"],
                avg_cost=pos["avg_entry_price"],
            )
        await db.commit()
        result = await db.execute(
            select(Holding).where(Holding.user_id == _DEFAULT_USER).order_by(Holding.created_at)
        )
        return [_enrich(h) for h in result.scalars().all()]
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Database unavailable: {exc}") from exc


@router.post("/portfolio/upload-csv", response_model=list[PortfolioHolding])
async def upload_csv(file: CsvFile, db: Db) -> list[PortfolioHolding]:
    if db is None:
        raise HTTPException(status_code=503, detail="Database not configured")

    raw = await file.read()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File must be UTF-8 encoded")

    reader = csv.DictReader(io.StringIO(text))
    rows = list(reader)

    if not rows:
        raise HTTPException(status_code=400, detail="CSV file is empty")

    field_names_lower = {f.lower().strip() for f in (reader.fieldnames or [])}
    missing = {"ticker", "shares", "avg_cost"} - field_names_lower
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"CSV missing required columns: {', '.join(sorted(missing))}. Expected: ticker, shares, avg_cost",
        )

    parsed = []
    for i, row in enumerate(rows, 1):
        try:
            r = {k.lower().strip(): v.strip() for k, v in row.items() if v is not None}
            ticker = r["ticker"].upper()
            shares = float(r["shares"])
            avg_cost = float(r["avg_cost"])
            name = r.get("name") or ticker
            if shares <= 0 or avg_cost <= 0:
                raise ValueError("shares and avg_cost must be positive")
            parsed.append((ticker, name, shares, avg_cost))
        except (KeyError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=f"Row {i} invalid: {exc}") from exc

    try:
        for ticker, name, shares, avg_cost in parsed:
            await _upsert_holding(db, ticker=ticker, name=name, shares=shares, avg_cost=avg_cost)
        await db.commit()
        result = await db.execute(
            select(Holding).where(Holding.user_id == _DEFAULT_USER).order_by(Holding.created_at)
        )
        return [_enrich(h) for h in result.scalars().all()]
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Database unavailable: {exc}") from exc


@router.delete("/portfolio/{ticker}", status_code=204)
async def delete_holding(ticker: str, db: Db) -> None:
    if db is None:
        raise HTTPException(status_code=503, detail="Database not configured")
    await db.execute(
        delete(Holding).where(
            Holding.user_id == _DEFAULT_USER,
            Holding.ticker == ticker.upper(),
        )
    )
    await db.commit()
