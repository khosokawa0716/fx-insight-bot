"""
Firestore Data Models - Pydantic models for Firestore collections
"""

from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field


# Type Aliases
Sentiment = Literal[-2, -1, 0, 1, 2]
TimeHorizon = Literal["immediate", "short-term", "medium-term", "long-term"]
Signal = Literal["BUY_CANDIDATE", "SELL_CANDIDATE", "RISK_OFF", "IGNORE"]
TradeSide = Literal["buy", "sell"]
TradeStatus = Literal["open", "closed", "cancelled"]


class NewsEvent(BaseModel):
    """News event with AI analysis results"""

    news_id: str
    source: str
    title: str
    url: str
    published_at: datetime
    collected_at: datetime
    content_raw: Optional[str] = None
    summary_raw: Optional[str] = None
    topic: Optional[str] = None
    sentiment: Sentiment
    impact_usdjpy: int = Field(ge=1, le=5)
    impact_eurjpy: int = Field(ge=1, le=5)
    time_horizon: TimeHorizon
    summary_ai: str
    rationale: Optional[str] = None
    signal: Signal
    rule_version: str
    tweet_text: Optional[str] = None
    is_tweeted: bool = False
    tweeted_at: Optional[datetime] = None

    class Config:
        json_schema_extra = {
            "example": {
                "news_id": "news_20250101_001",
                "source": "Gemini Grounding",
                "title": "日銀が金利据え置き決定",
                "url": "https://example.com/news/12345",
                "published_at": "2025-01-01T10:00:00Z",
                "collected_at": "2025-01-01T10:05:00Z",
                "topic": "金融政策",
                "sentiment": 0,
                "impact_usdjpy": 4,
                "impact_eurjpy": 2,
                "time_horizon": "short-term",
                "summary_ai": "日銀が政策金利を据え置き。市場は予想通りと受け止め。",
                "rationale": "金融政策の現状維持により市場への影響は限定的",
                "signal": "IGNORE",
                "rule_version": "v1.0",
                "is_tweeted": False,
            }
        }


class Trade(BaseModel):
    """Trading record"""

    trade_id: str
    news_id: Optional[str] = None
    pair: str
    side: TradeSide
    opened_at: datetime
    closed_at: Optional[datetime] = None
    entry_price: float
    exit_price: Optional[float] = None
    units: int
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    result_pips: Optional[float] = None
    result_jpy: Optional[float] = None
    status: TradeStatus
    rule_version: str
    memo: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "trade_id": "trade_20250101_001",
                "news_id": "news_20250101_001",
                "pair": "USD/JPY",
                "side": "buy",
                "opened_at": "2025-01-01T10:30:00Z",
                "entry_price": 148.50,
                "units": 1000,
                "stop_loss": 148.30,
                "take_profit": 148.90,
                "status": "open",
                "rule_version": "v1.0",
                "created_at": "2025-01-01T10:30:00Z",
                "updated_at": "2025-01-01T10:30:00Z",
            }
        }


class Position(BaseModel):
    """Current open position"""

    position_id: str
    trade_id: str
    pair: str
    side: TradeSide
    units: int
    entry_price: float
    current_price: float
    unrealized_pnl: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    opened_at: datetime
    updated_at: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "position_id": "pos_123456",
                "trade_id": "trade_20250101_001",
                "pair": "USD/JPY",
                "side": "buy",
                "units": 1000,
                "entry_price": 148.50,
                "current_price": 148.65,
                "unrealized_pnl": 150.0,
                "stop_loss": 148.30,
                "take_profit": 148.90,
                "opened_at": "2025-01-01T10:30:00Z",
                "updated_at": "2025-01-01T12:00:00Z",
            }
        }


class SystemConfig(BaseModel):
    """System configuration"""

    config_id: str
    version: str
    active: bool
    config_data: dict
    created_at: datetime
    updated_at: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "config_id": "signal_rules",
                "version": "v1.0",
                "active": True,
                "config_data": {
                    "buy_conditions": {
                        "sentiment_min": 1,
                        "impact_usdjpy_min": 4,
                        "topics": ["金融政策", "経済指標"],
                    },
                    "sell_conditions": {
                        "sentiment_max": -1,
                        "impact_usdjpy_min": 4,
                    },
                },
                "created_at": "2025-01-01T00:00:00Z",
                "updated_at": "2025-01-01T00:00:00Z",
            }
        }
