import logging
from typing import Annotated, Optional

import yfinance as yf
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.portfolio import Holding
from app.schemas.schemas import AddHoldingRequest, PortfolioHolding
from app.services.database import get_db

router = APIRouter(tags=["portfolio"])
logger = logging.getLogger(__name__)

_MOCK_PORTFOLIO: list[PortfolioHolding] = [
    PortfolioHolding(
        ticker="AAPL", name="Apple Inc.", shares=50.0, avg_cost=145.00,
        current_price=187.50, market_value=9375.00, gain_loss=2125.00, gain_loss_pct=29.31,
    ),
    PortfolioHolding(
        ticker="MSFT", name="Microsoft Corporation", shares=30.0, avg_cost=280.00,
        current_price=415.20, market_value=12456.00, gain_loss=4056.00, gain_loss_pct=48.29,
    ),
    PortfolioHolding(
        ticker="NVDA", name="NVIDIA Corporation", shares=15.0, avg_cost=420.00,
        current_price=875.40, market_value=13131.00, gain_loss=6831.00, gain_loss_pct=108.43,
    ),
    PortfolioHolding(
        ticker="TSLA", name="Tesla, Inc.", shares=25.0, avg_cost=200.00,
        current_price=175.30, market_value=4382.50, gain_loss=-617.50, gain_loss_pct=-12.35,
    ),
    PortfolioHolding(
        ticker="AMZN", name="Amazon.com, Inc.", shares=20.0, avg_cost=130.00,
        current_price=185.60, market_value=3712.00, gain_loss=1112.00, gain_loss_pct=42.77,
    ),
]

_STATIC_PRICES: dict[str, float] = {
    "AAPL": 187.50, "MSFT": 415.20, "NVDA": 875.40, "TSLA": 175.30, "AMZN": 185.60,
}

Db = Annotated[Optional[AsyncSession], Depends(get_db)]

_DEFAULT_USER = "default"


def _enrich(holding: Holding) -> PortfolioHolding:
    sym = holding.ticker.upper()
    current_price = float(holding.avg_cost)
    try:
        lp = yf.Ticker(sym).fast_info.last_price
        if lp is not None:
            current_price = float(lp)
    except Exception:
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


@router.get("/portfolio", response_model=list[PortfolioHolding])
async def get_portfolio(db: Db) -> list[PortfolioHolding]:
    if db is None:
        return _MOCK_PORTFOLIO
    result = await db.execute(
        select(Holding).where(Holding.user_id == _DEFAULT_USER).order_by(Holding.created_at)
    )
    holdings = result.scalars().all()
    if not holdings:
        return _MOCK_PORTFOLIO
    return [_enrich(h) for h in holdings]


@router.post("/portfolio", response_model=PortfolioHolding, status_code=201)
async def add_holding(body: AddHoldingRequest, db: Db) -> PortfolioHolding:
    if db is None:
        raise HTTPException(status_code=503, detail="Database not configured")
    holding = Holding(
        user_id=_DEFAULT_USER,
        ticker=body.ticker.upper(),
        name=body.name,
        shares=body.shares,
        avg_cost=body.avg_cost,
    )
    db.add(holding)
    await db.commit()
    await db.refresh(holding)
    return _enrich(holding)


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
