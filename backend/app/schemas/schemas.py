from typing import Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    portfolio_holdings: Optional[list[dict]] = None


class ChatResponse(BaseModel):
    answer: str
    sources: list[str] = []


class PortfolioHolding(BaseModel):
    ticker: str
    name: str
    shares: float
    avg_cost: float
    current_price: float
    market_value: float
    gain_loss: float
    gain_loss_pct: float


class AddHoldingRequest(BaseModel):
    ticker: str = Field(..., min_length=1, max_length=10)
    name: str = Field(..., min_length=1, max_length=255)
    shares: float = Field(..., gt=0)
    avg_cost: float = Field(..., gt=0)
