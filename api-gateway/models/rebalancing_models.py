# models/rebalancing_models.py

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

class RebalancingRequest(BaseModel):
    """Request model for rebalancing suggestions"""
    strategy: str = Field(
        default="equal_weight",
        description="Rebalancing strategy to use",
        pattern="^(equal_weight|market_cap|momentum|volatility_adjusted)$"  # Changed from regex to pattern
    )

class RebalancingSuggestion(BaseModel):
    """Individual stock rebalancing suggestion"""
    stock_id: str = Field(description="Unique identifier for the stock")
    symbol: str = Field(description="Stock symbol")
    current_weight: float = Field(description="Current weight percentage in portfolio")
    suggested_weight: float = Field(description="Suggested new weight percentage")
    weight_change: float = Field(description="Change in weight (suggested - current)")
    action: str = Field(
        description="Recommended action",
        pattern="^(increase|decrease|hold)$"  # Changed from regex to pattern
    )
    reason: str = Field(description="Explanation for the suggested change")

class RebalancingSummary(BaseModel):
    """Summary of rebalancing suggestions"""
    total_weight_changes: float = Field(description="Total absolute weight changes")
    significant_changes: int = Field(description="Number of significant weight changes")
    strategy_description: str = Field(description="Description of the strategy used")
    generated_at: datetime = Field(description="When suggestions were generated")

class RebalancingResponse(BaseModel):
    """Complete rebalancing suggestions response"""
    smallcase_id: str = Field(description="Smallcase identifier")
    strategy: str = Field(description="Strategy used for rebalancing")
    strategy_name: str = Field(description="Human-readable strategy name")
    suggestions: List[RebalancingSuggestion] = Field(description="List of rebalancing suggestions")
    summary: RebalancingSummary = Field(description="Summary metrics")

class ApplyRebalancingRequest(BaseModel):
    """Request to apply rebalancing changes"""
    suggestions: List[Dict[str, Any]] = Field(
        description="List of suggestions to apply",
        min_items=1
    )

class RebalancingStrategy(BaseModel):
    """Available rebalancing strategy information"""
    id: str = Field(description="Strategy identifier")
    name: str = Field(description="Human-readable strategy name")
    description: str = Field(description="Strategy description")
    risk_level: str = Field(description="Risk level assessment")
    best_for: str = Field(description="Best suited for what type of investor")

class StockPerformance(BaseModel):
    """Stock performance metrics"""
    price_change_1d: float = Field(description="1-day price change percentage")
    price_change_7d: float = Field(description="7-day price change percentage")
    price_change_30d: float = Field(description="30-day price change percentage")
    volatility_30d: float = Field(description="30-day volatility percentage")

class StockComposition(BaseModel):
    """Individual stock in portfolio composition"""
    stock_id: str = Field(description="Stock identifier")
    symbol: str = Field(description="Stock symbol")
    stock_name: str = Field(description="Full stock name")
    sector: str = Field(description="Stock sector/industry")
    current_price: float = Field(description="Current stock price")
    market_cap: int = Field(description="Market capitalization")
    target_weight: float = Field(description="Current weight in portfolio")
    volume_avg_30d: int = Field(description="30-day average volume")
    pb_ratio: Optional[float] = Field(description="Price-to-book ratio")
    dividend_yield: Optional[float] = Field(description="Dividend yield percentage")
    beta: Optional[float] = Field(description="Beta coefficient")
    performance: StockPerformance = Field(description="Performance metrics")

class PortfolioComposition(BaseModel):
    """Complete portfolio composition"""
    smallcase_id: str = Field(description="Smallcase identifier")
    total_stocks: int = Field(description="Total number of stocks")
    total_target_weight: float = Field(description="Sum of all target weights")
    total_market_value: float = Field(description="Total market value")
    stocks: List[StockComposition] = Field(description="List of stocks in portfolio")
    last_updated: datetime = Field(description="Last update timestamp")

class ApplyRebalancingResult(BaseModel):
    """Result of applying rebalancing changes"""
    success: bool = Field(description="Whether the operation was successful")
    message: str = Field(description="Result message")
    updated_stocks: List[Dict[str, Any]] = Field(description="List of updated stocks")
    total_changes: int = Field(description="Number of stocks changed")
    applied_at: datetime = Field(description="When changes were applied")
    smallcase_name: str = Field(description="Name of the smallcase")

class RebalancingErrorResponse(BaseModel):
    """Error response for rebalancing operations"""
    success: bool = Field(default=False, description="Operation success status")
    error: str = Field(description="Error type")
    detail: str = Field(description="Detailed error message")
    code: Optional[str] = Field(description="Error code if available")