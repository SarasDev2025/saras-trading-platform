# services/rebalancing_service.py

from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from decimal import Decimal, ROUND_HALF_UP
import math

class RebalancingStrategy:
    """Rebalancing strategy constants"""
    EQUAL_WEIGHT = "equal_weight"
    MARKET_CAP = "market_cap"
    MOMENTUM = "momentum"
    VOLATILITY_ADJUSTED = "volatility_adjusted"

class RebalancingService:
    """Service for portfolio rebalancing algorithms"""
    
    @staticmethod
    def calculate_equal_weight_rebalancing(stocks: List[Dict]) -> List[Dict]:
        """Calculate equal weight rebalancing suggestions"""
        if not stocks:
            return []
        
        equal_weight = 100.0 / len(stocks)
        
        suggestions = []
        for stock in stocks:
            current_weight = stock["target_weight"]
            suggested_weight = equal_weight
            weight_change = suggested_weight - current_weight
            
            suggestions.append({
                "stock_id": stock["stock_id"],
                "symbol": stock["symbol"],
                "current_weight": round(current_weight, 2),
                "suggested_weight": round(suggested_weight, 2),
                "weight_change": round(weight_change, 2),
                "action": "increase" if weight_change > 0.5 else "decrease" if weight_change < -0.5 else "hold",
                "reason": "Equal weight distribution for balanced diversification"
            })
        
        return suggestions
    
    @staticmethod
    def calculate_market_cap_weighted_rebalancing(stocks: List[Dict]) -> List[Dict]:
        """Calculate market cap weighted rebalancing"""
        if not stocks:
            return []
        
        total_market_cap = sum(stock["market_cap"] for stock in stocks)
        
        if total_market_cap == 0:
            return RebalancingService.calculate_equal_weight_rebalancing(stocks)
        
        suggestions = []
        for stock in stocks:
            current_weight = stock["target_weight"]
            market_cap_weight = (stock["market_cap"] / total_market_cap) * 100
            
            # Cap individual positions at 30% for risk management
            suggested_weight = min(market_cap_weight, 30.0)
            weight_change = suggested_weight - current_weight
            
            suggestions.append({
                "stock_id": stock["stock_id"],
                "symbol": stock["symbol"],
                "current_weight": round(current_weight, 2),
                "suggested_weight": round(suggested_weight, 2),
                "weight_change": round(weight_change, 2),
                "action": "increase" if weight_change > 0.5 else "decrease" if weight_change < -0.5 else "hold",
                "reason": f"Market cap weighted (₹{stock['market_cap']:,} market cap)"
            })
        
        # Normalize weights to ensure they sum to 100%
        total_suggested = sum(s["suggested_weight"] for s in suggestions)
        if total_suggested > 0:
            for suggestion in suggestions:
                normalized_weight = (suggestion["suggested_weight"] / total_suggested) * 100
                suggestion["suggested_weight"] = round(normalized_weight, 2)
                suggestion["weight_change"] = round(
                    suggestion["suggested_weight"] - suggestion["current_weight"], 2
                )
        
        return suggestions
    
    @staticmethod
    def calculate_momentum_based_rebalancing(stocks: List[Dict]) -> List[Dict]:
        """Calculate momentum-based rebalancing (favor recent performers)"""
        if not stocks:
            return []
        
        # Calculate momentum scores (30-day performance with volatility adjustment)
        scored_stocks = []
        for stock in stocks:
            perf_30d = stock["performance"]["price_change_30d"]
            volatility = stock["performance"]["volatility_30d"]
            
            # Momentum score: performance adjusted for volatility
            momentum_score = perf_30d / max(volatility, 5.0) if volatility > 0 else perf_30d / 15.0
            
            scored_stocks.append({
                **stock,
                "momentum_score": momentum_score
            })
        
        # Sort by momentum score
        scored_stocks.sort(key=lambda x: x["momentum_score"], reverse=True)
        
        # Assign weights based on momentum ranking
        suggestions = []
        total_stocks = len(scored_stocks)
        
        for i, stock in enumerate(scored_stocks):
            # Higher weight for better momentum (exponential decay)
            rank_weight = (total_stocks - i) / total_stocks
            base_weight = 100 / total_stocks
            momentum_weight = base_weight * (1 + rank_weight * 0.6)  # Up to 60% bonus
            
            # Cap at 35% for risk management
            suggested_weight = min(momentum_weight, 35.0)
            current_weight = stock["target_weight"]
            weight_change = suggested_weight - current_weight
            
            suggestions.append({
                "stock_id": stock["stock_id"],
                "symbol": stock["symbol"],
                "current_weight": round(current_weight, 2),
                "suggested_weight": round(suggested_weight, 2),
                "weight_change": round(weight_change, 2),
                "action": "increase" if weight_change > 0.5 else "decrease" if weight_change < -0.5 else "hold",
                "reason": f"Momentum score: {stock['momentum_score']:.2f} (30d: {stock['performance']['price_change_30d']:.1f}%)",
                "momentum_score": stock["momentum_score"]
            })
        
        # Normalize to 100%
        total_suggested = sum(s["suggested_weight"] for s in suggestions)
        if total_suggested > 0:
            for suggestion in suggestions:
                normalized_weight = (suggestion["suggested_weight"] / total_suggested) * 100
                suggestion["suggested_weight"] = round(normalized_weight, 2)
                suggestion["weight_change"] = round(
                    suggestion["suggested_weight"] - suggestion["current_weight"], 2
                )
        
        return suggestions
    
    @staticmethod
    def calculate_volatility_adjusted_rebalancing(stocks: List[Dict]) -> List[Dict]:
        """Calculate volatility-adjusted rebalancing (inverse volatility weighting)"""
        if not stocks:
            return []
        
        # Calculate inverse volatility weights
        inv_vol_weights = []
        for stock in stocks:
            volatility = max(stock["performance"]["volatility_30d"], 5.0)  # Minimum 5% volatility
            inv_vol_weight = 1 / volatility
            inv_vol_weights.append(inv_vol_weight)
        
        total_inv_vol = sum(inv_vol_weights)
        
        suggestions = []
        for i, stock in enumerate(stocks):
            current_weight = stock["target_weight"]
            vol_adjusted_weight = (inv_vol_weights[i] / total_inv_vol) * 100
            
            # Cap at 25% for risk management
            suggested_weight = min(vol_adjusted_weight, 25.0)
            weight_change = suggested_weight - current_weight
            
            suggestions.append({
                "stock_id": stock["stock_id"],
                "symbol": stock["symbol"],
                "current_weight": round(current_weight, 2),
                "suggested_weight": round(suggested_weight, 2),
                "weight_change": round(weight_change, 2),
                "action": "increase" if weight_change > 0.5 else "decrease" if weight_change < -0.5 else "hold",
                "reason": f"Risk-adjusted (volatility: {stock['performance']['volatility_30d']:.1f}%)",
                "volatility": stock["performance"]["volatility_30d"]
            })
        
        # Final normalization
        total_suggested = sum(s["suggested_weight"] for s in suggestions)
        if total_suggested > 0:
            for suggestion in suggestions:
                normalized_weight = (suggestion["suggested_weight"] / total_suggested) * 100
                suggestion["suggested_weight"] = round(normalized_weight, 2)
                suggestion["weight_change"] = round(
                    suggestion["suggested_weight"] - suggestion["current_weight"], 2
                )
        
        return suggestions
    
    @staticmethod
    def generate_rebalancing_suggestions(
        stocks: List[Dict],
        strategy: str = RebalancingStrategy.EQUAL_WEIGHT
    ) -> Dict[str, Any]:
        """Generate rebalancing suggestions based on selected strategy"""
        
        # Apply selected strategy
        if strategy == RebalancingStrategy.EQUAL_WEIGHT:
            suggestions = RebalancingService.calculate_equal_weight_rebalancing(stocks)
            strategy_name = "Equal Weight"
        elif strategy == RebalancingStrategy.MARKET_CAP:
            suggestions = RebalancingService.calculate_market_cap_weighted_rebalancing(stocks)
            strategy_name = "Market Cap Weighted"
        elif strategy == RebalancingStrategy.MOMENTUM:
            suggestions = RebalancingService.calculate_momentum_based_rebalancing(stocks)
            strategy_name = "Momentum Based"
        elif strategy == RebalancingStrategy.VOLATILITY_ADJUSTED:
            suggestions = RebalancingService.calculate_volatility_adjusted_rebalancing(stocks)
            strategy_name = "Risk Adjusted"
        else:
            suggestions = RebalancingService.calculate_equal_weight_rebalancing(stocks)
            strategy_name = "Equal Weight"
        
        # Calculate summary metrics
        total_changes = sum(abs(s["weight_change"]) for s in suggestions)
        significant_changes = [s for s in suggestions if abs(s["weight_change"]) > 1.0]
        
        return {
            "strategy": strategy,
            "strategy_name": strategy_name,
            "suggestions": suggestions,
            "summary": {
                "total_weight_changes": round(total_changes, 2),
                "significant_changes": len(significant_changes),
                "strategy_description": RebalancingService._get_strategy_description(strategy),
                "generated_at": datetime.now(timezone.utc).isoformat()
            }
        }
    
    @staticmethod
    def _get_strategy_description(strategy: str) -> str:
        """Get description for rebalancing strategy"""
        descriptions = {
            RebalancingStrategy.EQUAL_WEIGHT: "Equal allocation across all stocks for balanced diversification",
            RebalancingStrategy.MARKET_CAP: "Weights based on market capitalization with risk caps",
            RebalancingStrategy.MOMENTUM: "Higher allocation to recent outperformers with volatility adjustment",
            RebalancingStrategy.VOLATILITY_ADJUSTED: "Inverse volatility weighting to minimize portfolio risk"
        }
        return descriptions.get(strategy, "Custom rebalancing strategy")
    
    @staticmethod
    def get_available_strategies() -> List[Dict[str, Any]]:
        """Get available rebalancing strategies with metadata"""
        return [
            {
                "id": RebalancingStrategy.EQUAL_WEIGHT,
                "name": "Equal Weight",
                "description": "Distribute investments equally across all stocks",
                "risk_level": "Medium",
                "best_for": "Balanced diversification"
            },
            {
                "id": RebalancingStrategy.MARKET_CAP,
                "name": "Market Cap Weighted",
                "description": "Weight stocks by their market capitalization",
                "risk_level": "Medium-Low",
                "best_for": "Index-like exposure"
            },
            {
                "id": RebalancingStrategy.MOMENTUM,
                "name": "Momentum Based",
                "description": "Favor recent outperformers with volatility adjustment",
                "risk_level": "Medium-High",
                "best_for": "Growth-oriented investors"
            },
            {
                "id": RebalancingStrategy.VOLATILITY_ADJUSTED,
                "name": "Risk Adjusted",
                "description": "Inverse volatility weighting to minimize portfolio risk",
                "risk_level": "Low-Medium",
                "best_for": "Conservative investors"
            }
        ]
