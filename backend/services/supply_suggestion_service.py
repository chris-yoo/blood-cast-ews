#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Supply Suggestion Service - Blood supply redistribution suggestions
Based on distance and surplus availability
"""

from typing import List, Dict, Optional
from services.forecast_service import ForecastService, get_forecast_service
from services.distance_service import (
    get_distance,
    is_transfer_feasible,
    get_nearby_regions,
)


class SupplySuggestion:
    """Represents a suggestion to transfer blood from one region to another"""

    def __init__(
        self, source_region: str, blood_type: str, amount: float, distance: float
    ):
        self.source_region = source_region
        self.blood_type = blood_type
        self.amount = amount
        self.distance = distance

    def to_dict(self) -> Dict:
        return {
            "sourceRegion": self.source_region,
            "bloodType": self.blood_type,
            "amount": round(self.amount, 2),
            "distance": round(self.distance, 1),
        }


def calculate_baseline(
    forecast_service: ForecastService, region: str, bloodtype: str
) -> float:
    """
    Calculate baseline (recent 12-month average) for a region and blood type

    Args:
        forecast_service: ForecastService instance
        region: Region name
        bloodtype: Blood type

    Returns:
        Baseline value (average)
    """
    ts = forecast_service.get_time_series(region, bloodtype)
    if ts is None:
        return 0.0

    if len(ts) >= 12:
        return ts.iloc[-12:].mean()
    else:
        return ts.mean()


def get_supply_suggestions(
    shortage_region: str,
    blood_type: str,
    month: int,
    forecast_service: Optional[ForecastService] = None,
) -> List[SupplySuggestion]:
    """
    Get supply redistribution suggestions for a shortage

    Args:
        shortage_region: Region experiencing shortage
        blood_type: Blood type in shortage
        month: Month ahead (1, 2, or 3)
        forecast_service: ForecastService instance (optional, will create if None)

    Returns:
        List of SupplySuggestion objects
    """
    if forecast_service is None:
        forecast_service = get_forecast_service()

    # Get forecast for shortage region
    shortage_forecasts = forecast_service.forecast(
        shortage_region, blood_type, n_months=month
    )
    if len(shortage_forecasts) < month:
        return []

    shortage_forecast_value = shortage_forecasts[month - 1]

    # Calculate baseline and shortage amount
    shortage_baseline = calculate_baseline(
        forecast_service, shortage_region, blood_type
    )
    shortage_amount = shortage_baseline - shortage_forecast_value

    # If no shortage (forecast >= baseline), return empty list
    if shortage_amount <= 0:
        return []

    # Calculate severity of shortage
    shortage_severity = forecast_service.calculate_severity(
        shortage_region, blood_type, shortage_forecast_value, month
    )

    # Check if severity is 주의 (Yellow) or higher (주의, 경계, 심각)
    is_urgent = shortage_severity in ["주의", "경계", "심각"]

    # Find all regions with surplus for the same blood type and month
    # Priority 1: Regions with -5% or better (forecast >= baseline * 0.95)
    surplus_regions = []
    # Priority 2: For urgent cases, also consider normal and 관심 regions
    normal_regions = []  # 정상 (-10% 이상)
    attention_regions = []  # 관심 (-10% ~ -20%)

    for region in forecast_service.regions:
        if region == shortage_region:
            continue

        # Get forecast for this region
        region_forecasts = forecast_service.forecast(region, blood_type, n_months=month)
        if len(region_forecasts) < month:
            continue

        region_forecast_value = region_forecasts[month - 1]
        region_baseline = calculate_baseline(forecast_service, region, blood_type)

        if region_baseline <= 0:
            continue

        # Calculate percentage change
        pct_change = ((region_forecast_value - region_baseline) / region_baseline) * 100

        # Check if transfer is feasible
        if not is_transfer_feasible(region, shortage_region):
            continue

        distance = get_distance(region, shortage_region)

        # Priority 1: Regions with -5% or better (forecast >= baseline * 0.95)
        if region_forecast_value >= region_baseline * 0.95:
            surplus_amount = region_forecast_value - region_baseline
            surplus_regions.append(
                {
                    "region": region,
                    "surplus": surplus_amount,
                    "distance": distance,
                    "pct_change": pct_change,
                }
            )
        # Priority 2: For urgent cases, also consider normal and 관심 regions
        elif is_urgent:
            # 정상 (-10% 이상, -5% 미만)
            if pct_change >= -10:
                # 십시일반: 각 지역에서 baseline의 5% 정도만 가져오기
                available_amount = region_baseline * 0.05
                normal_regions.append(
                    {
                        "region": region,
                        "available": available_amount,
                        "distance": distance,
                        "pct_change": pct_change,
                    }
                )
            # 관심 (-10% ~ -20%)
            elif pct_change >= -20:
                # 십시일반: 각 지역에서 baseline의 3% 정도만 가져오기
                available_amount = region_baseline * 0.03
                attention_regions.append(
                    {
                        "region": region,
                        "available": available_amount,
                        "distance": distance,
                        "pct_change": pct_change,
                    }
                )

    # Sort by distance (closest first)
    surplus_regions.sort(key=lambda x: x["distance"])
    normal_regions.sort(key=lambda x: x["distance"])
    attention_regions.sort(key=lambda x: x["distance"])

    # Allocate shortage amount starting from closest regions
    suggestions = []
    remaining_shortage = shortage_amount

    # Step 1: First, try to get from regions with -5% or better
    for surplus_info in surplus_regions:
        if remaining_shortage <= 0:
            break

        source_region = surplus_info["region"]
        available_surplus = surplus_info["surplus"]
        distance = surplus_info["distance"]

        # Take as much as needed, but not more than available
        transfer_amount = min(remaining_shortage, available_surplus)

        if transfer_amount > 0:
            suggestions.append(
                SupplySuggestion(
                    source_region=source_region,
                    blood_type=blood_type,
                    amount=transfer_amount,
                    distance=distance,
                )
            )
            remaining_shortage -= transfer_amount

    # Step 2: If urgent and still short, get from normal regions (십시일반)
    if is_urgent and remaining_shortage > 0:
        for normal_info in normal_regions:
            if remaining_shortage <= 0:
                break

            source_region = normal_info["region"]
            available_amount = normal_info["available"]
            distance = normal_info["distance"]

            # Take as much as needed, but not more than available
            transfer_amount = min(remaining_shortage, available_amount)

            if transfer_amount > 0:
                suggestions.append(
                    SupplySuggestion(
                        source_region=source_region,
                        blood_type=blood_type,
                        amount=transfer_amount,
                        distance=distance,
                    )
                )
                remaining_shortage -= transfer_amount

    # Step 3: If still short, get from 관심 regions (십시일반)
    if is_urgent and remaining_shortage > 0:
        for attention_info in attention_regions:
            if remaining_shortage <= 0:
                break

            source_region = attention_info["region"]
            available_amount = attention_info["available"]
            distance = attention_info["distance"]

            # Take as much as needed, but not more than available
            transfer_amount = min(remaining_shortage, available_amount)

            if transfer_amount > 0:
                suggestions.append(
                    SupplySuggestion(
                        source_region=source_region,
                        blood_type=blood_type,
                        amount=transfer_amount,
                        distance=distance,
                    )
                )
                remaining_shortage -= transfer_amount

    return suggestions


def get_supply_suggestions_summary(
    shortage_region: str,
    blood_type: str,
    month: int,
    forecast_service: Optional[ForecastService] = None,
) -> Dict:
    """
    Get supply suggestions with summary information

    Args:
        shortage_region: Region experiencing shortage
        blood_type: Blood type in shortage
        month: Month ahead (1, 2, or 3)
        forecast_service: ForecastService instance (optional)

    Returns:
        Dictionary with suggestions and summary
    """
    if forecast_service is None:
        forecast_service = get_forecast_service()

    # Get forecast and baseline
    shortage_forecasts = forecast_service.forecast(
        shortage_region, blood_type, n_months=month
    )
    if len(shortage_forecasts) < month:
        return {
            "shortageRegion": shortage_region,
            "bloodType": blood_type,
            "month": month,
            "shortageAmount": 0,
            "totalSuggested": 0,
            "suggestions": [],
        }

    shortage_forecast_value = shortage_forecasts[month - 1]
    shortage_baseline = calculate_baseline(
        forecast_service, shortage_region, blood_type
    )
    shortage_amount = max(0, shortage_baseline - shortage_forecast_value)

    # Get suggestions
    suggestions = get_supply_suggestions(
        shortage_region, blood_type, month, forecast_service
    )

    total_suggested = sum(s.amount for s in suggestions)

    return {
        "shortageRegion": shortage_region,
        "bloodType": blood_type,
        "month": month,
        "shortageAmount": round(shortage_amount, 2),
        "forecastValue": round(shortage_forecast_value, 2),
        "baseline": round(shortage_baseline, 2),
        "totalSuggested": round(total_suggested, 2),
        "suggestions": [s.to_dict() for s in suggestions],
    }
