from fastapi import APIRouter

from app.schemas.schemas import PortfolioHolding

router = APIRouter(tags=["portfolio"])

_MOCK_PORTFOLIO: list[PortfolioHolding] = [
    PortfolioHolding(
        ticker="AAPL",
        name="Apple Inc.",
        shares=50.0,
        avg_cost=145.00,
        current_price=187.50,
        market_value=9375.00,
        gain_loss=2125.00,
        gain_loss_pct=29.31,
    ),
    PortfolioHolding(
        ticker="MSFT",
        name="Microsoft Corporation",
        shares=30.0,
        avg_cost=280.00,
        current_price=415.20,
        market_value=12456.00,
        gain_loss=4056.00,
        gain_loss_pct=48.29,
    ),
    PortfolioHolding(
        ticker="NVDA",
        name="NVIDIA Corporation",
        shares=15.0,
        avg_cost=420.00,
        current_price=875.40,
        market_value=13131.00,
        gain_loss=6831.00,
        gain_loss_pct=108.43,
    ),
    PortfolioHolding(
        ticker="TSLA",
        name="Tesla, Inc.",
        shares=25.0,
        avg_cost=200.00,
        current_price=175.30,
        market_value=4382.50,
        gain_loss=-617.50,
        gain_loss_pct=-12.35,
    ),
    PortfolioHolding(
        ticker="AMZN",
        name="Amazon.com, Inc.",
        shares=20.0,
        avg_cost=130.00,
        current_price=185.60,
        market_value=3712.00,
        gain_loss=1112.00,
        gain_loss_pct=42.77,
    ),
]


@router.get("/portfolio", response_model=list[PortfolioHolding])
async def get_portfolio() -> list[PortfolioHolding]:
    return _MOCK_PORTFOLIO
