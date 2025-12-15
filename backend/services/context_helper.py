#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Context Helper - Collects comprehensive context for LLM prompts
"""

from typing import Dict, Optional, List
from datetime import datetime
import numpy as np
import pandas as pd
from services.forecast_service import ForecastService
from services.supply_suggestion_service import get_supply_suggestions_summary, calculate_baseline


# 분석으로 알게된 context (하드코딩)
ANALYSIS_CONTEXT = """
**1. 직업별 특성 (대학생 vs 군인/자영업)**

* **대학생(20대):** '학사 일정'에 가장 민감합니다. **시험 기간(중간/기말)**과 **방학** 시즌에는 헌혈량이 급격히 감소합니다.

* **군인(20대 남성):** 학사 일정보다는 **'입대 시즌'**과 **'훈련소 입대 인원'**에 정비례하여 헌혈량이 변동합니다.

* **자영업/가사:** 학사 일정의 영향이 거의 없으며 상대적으로 독립적인 패턴을 보입니다.

**2. 근무 시간 및 요일 영향 (직장인 vs 그 외)**

* **직장인/공무원(30-40대):** **평일 근무 시간**과 헌혈의 집 운영 시간이 겹쳐 접근성이 떨어집니다. 따라서 **'공휴일'**이나 **'점심시간'** 캠페인 여부에 민감합니다.

* **자영업:** 근무 시간 조절이 비교적 자유로워 평일 낮 시간대 참여 가능성이 더 높습니다.

**3. 날씨 및 계절 영향 (고령층)**

* **고령층(50대 이상):** **'기온'**과 **'계절'**에 매우 민감합니다. **폭염**이나 **한파** 주의보가 발령되거나 강수량이 많은 날에는 이동성이 떨어져 헌혈량이 급감합니다.

* **청년층:** 날씨보다는 학사 일정이나 이벤트 유무에 더 큰 영향을 받습니다.

**4. 헌혈 상품 및 인센티브 (성별 차이)**

* **여성(특히 10대~20대):** **'헌혈 기념품(Goods)'**에 매우 민감하게 반응합니다. 특히 **유명 아이돌 포토카드**나 **올리브영 상품권** 프로모션이 있을 때 참여율이 유의미하게 상승합니다.

* **남성:** 기념품보다는 군 가산점, 예비군 훈련 시간 인정 등 **실질적 혜택**이나 **사회적 의무감**에 더 반응하는 경향이 있습니다.
"""


def get_season(month: int) -> str:
    """Get season name from month number"""
    if month in [12, 1, 2]:
        return "겨울"
    elif month in [3, 4, 5]:
        return "봄"
    elif month in [6, 7, 8]:
        return "여름"
    else:
        return "가을"


def get_season_context(season: str) -> str:
    """Get season-specific context"""
    if season == "겨울":
        return "겨울철에는 한파로 인해 고령층의 헌혈 참여가 감소하며, 특히 폭설이나 강추위 시 이동성이 크게 떨어집니다. 실내 헌혈 버스나 따뜻한 헌혈의 집 운영이 중요합니다."
    elif season == "여름":
        return "여름철에는 폭염으로 인해 고령층의 헌혈 참여가 감소하며, 휴가철로 인해 청년층의 헌혈도 감소할 수 있습니다. 시원한 헌혈의 집이나 실내 헌혈 버스 운영이 중요합니다."
    elif season == "봄":
        return "봄철에는 대학생들의 학사 일정(중간고사)으로 인해 헌혈량이 감소할 수 있습니다. 대학 캠퍼스 헌혈 버스나 시험 기간 전 캠페인이 효과적입니다."
    else:  # 가을
        return "가을철에는 대학생들의 학사 일정(기말고사)으로 인해 헌혈량이 감소할 수 있습니다. 대학 캠퍼스 헌혈 버스나 시험 기간 전 캠페인이 효과적입니다."


def collect_context(
    region: str,
    blood_type: str,
    month: int,
    forecast_service: ForecastService,
) -> Dict:
    """
    Collect comprehensive context for LLM prompts
    
    Args:
        region: Region name
        blood_type: Blood type
        month: Month ahead (1, 2, or 3)
        forecast_service: ForecastService instance
    
    Returns:
        Dictionary with all context information
    """
    # Get time series
    ts = forecast_service.get_time_series(region, blood_type)
    if ts is None:
        return {}
    
    # Get last actual value (바로 전달의 실제 값)
    last_actual_value = float(ts.iloc[-1]) if len(ts) > 0 else None
    
    # Calculate baseline (1년 평균값)
    if len(ts) >= 12:
        baseline = float(ts.iloc[-12:].mean())
    else:
        baseline = float(ts.mean())
    
    # Get forecasts for 1, 2, 3 months ahead
    forecasts = forecast_service.forecast(region, blood_type, n_months=3)
    forecast_1m = float(forecasts[0]) if not np.isnan(forecasts[0]) else None
    forecast_2m = float(forecasts[1]) if not np.isnan(forecasts[1]) else None
    forecast_3m = float(forecasts[2]) if not np.isnan(forecasts[2]) else None
    
    # Calculate severity for each forecast
    severity_1m = forecast_service.calculate_severity(region, blood_type, forecast_1m, 1) if forecast_1m else None
    severity_2m = forecast_service.calculate_severity(region, blood_type, forecast_2m, 2) if forecast_2m else None
    severity_3m = forecast_service.calculate_severity(region, blood_type, forecast_3m, 3) if forecast_3m else None
    
    # Calculate percentage decrease from baseline for each forecast
    pct_decrease_1m = ((forecast_1m - baseline) / baseline * 100) if forecast_1m and baseline > 0 else None
    pct_decrease_2m = ((forecast_2m - baseline) / baseline * 100) if forecast_2m and baseline > 0 else None
    pct_decrease_3m = ((forecast_3m - baseline) / baseline * 100) if forecast_3m and baseline > 0 else None
    
    # Calculate absolute decrease
    decrease_1m = (baseline - forecast_1m) if forecast_1m else None
    decrease_2m = (baseline - forecast_2m) if forecast_2m else None
    decrease_3m = (baseline - forecast_3m) if forecast_3m else None
    
    # Get forecast date and season
    last_date = forecast_service.last_date
    forecast_date_1m = last_date + pd.DateOffset(months=1)
    forecast_date_2m = last_date + pd.DateOffset(months=2)
    forecast_date_3m = last_date + pd.DateOffset(months=3)
    
    season_1m = get_season(forecast_date_1m.month)
    season_2m = get_season(forecast_date_2m.month)
    season_3m = get_season(forecast_date_3m.month)
    
    # Get supply suggestions for the requested month
    supply_suggestions = get_supply_suggestions_summary(
        region, blood_type, month, forecast_service
    )
    
    # Get the specific forecast and severity for the requested month
    if month == 1:
        forecast_value = forecast_1m
        severity = severity_1m
        pct_decrease = pct_decrease_1m
        decrease = decrease_1m
        forecast_date = forecast_date_1m
        season = season_1m
    elif month == 2:
        forecast_value = forecast_2m
        severity = severity_2m
        pct_decrease = pct_decrease_2m
        decrease = decrease_2m
        forecast_date = forecast_date_2m
        season = season_2m
    else:  # month == 3
        forecast_value = forecast_3m
        severity = severity_3m
        pct_decrease = pct_decrease_3m
        decrease = decrease_3m
        forecast_date = forecast_date_3m
        season = season_3m
    
    return {
        "region": region,
        "blood_type": blood_type,
        "month": month,
        "last_actual_value": last_actual_value,
        "baseline": baseline,
        "forecast_1m": forecast_1m,
        "forecast_2m": forecast_2m,
        "forecast_3m": forecast_3m,
        "severity_1m": severity or "정상",
        "severity_2m": severity_2m or "정상",
        "severity_3m": severity_3m or "정상",
        "pct_decrease_1m": pct_decrease,
        "pct_decrease_2m": pct_decrease_2m,
        "pct_decrease_3m": pct_decrease_3m,
        "decrease_1m": decrease,
        "decrease_2m": decrease_2m,
        "decrease_3m": decrease_3m,
        "forecast_date": forecast_date,
        "season": season,
        "supply_suggestions": supply_suggestions,
        "analysis_context": ANALYSIS_CONTEXT,
        "season_context": get_season_context(season),
    }


def format_context_for_chat(context: Dict) -> str:
    """Format context for chat prompt"""
    region = context["region"]
    blood_type = context["blood_type"]
    month = context["month"]
    
    # Current forecast info
    if month == 1:
        forecast_value = context["forecast_1m"]
        severity = context["severity_1m"]
        pct_decrease = context["pct_decrease_1m"]
        decrease = context["decrease_1m"]
    elif month == 2:
        forecast_value = context["forecast_2m"]
        severity = context["severity_2m"]
        pct_decrease = context["pct_decrease_2m"]
        decrease = context["decrease_2m"]
    else:
        forecast_value = context["forecast_3m"]
        severity = context["severity_3m"]
        pct_decrease = context["pct_decrease_3m"]
        decrease = context["decrease_3m"]
    
    forecast_date = context["forecast_date"]
    season = context["season"]
    
    # Helper function to format forecast info
    def format_forecast_info(forecast_val, sev, dec, pct_dec):
        if forecast_val is None:
            return "- **예측값**: 데이터 없음\n- **경보 단계**: 데이터 없음\n- **평균 대비 감소**: 데이터 없음"
        return f"- **예측값**: {forecast_val:.0f}건\n- **경보 단계**: {sev}\n- **평균 대비 감소**: {dec:.0f}건 ({pct_dec:.1f}%)" if dec is not None and pct_dec is not None else f"- **예측값**: {forecast_val:.0f}건\n- **경보 단계**: {sev}\n- **평균 대비 감소**: 데이터 없음"
    
    context_text = f"""## 현재 분석 중인 세그멘트
- **지역**: {region}
- **혈액형**: {blood_type}
- **예측 기간**: {month}개월 후 ({forecast_date.strftime('%Y년 %m월')}, {season})

## 실제 데이터
- **바로 전달의 실제 값**: {context["last_actual_value"]:.0f}건
- **1년 평균값 (baseline)**: {context["baseline"]:.0f}건

## 예측값 및 경보 단계
### 1개월 후 예측
{format_forecast_info(context["forecast_1m"], context["severity_1m"], context["decrease_1m"], context["pct_decrease_1m"])}

### 2개월 후 예측
{format_forecast_info(context["forecast_2m"], context["severity_2m"], context["decrease_2m"], context["pct_decrease_2m"])}

### 3개월 후 예측
{format_forecast_info(context["forecast_3m"], context["severity_3m"], context["decrease_3m"], context["pct_decrease_3m"])}

## 현재 예측 ({month}개월 후)
{format_forecast_info(forecast_value, severity, decrease, pct_decrease)}
- **예측 월**: {forecast_date.strftime('%Y년 %m월')} ({season})

## 조달 제안
"""
    
    supply = context["supply_suggestions"]
    if supply["suggestions"]:
        context_text += f"- **부족량**: {supply["shortageAmount"]:.0f}건\n"
        context_text += f"- **제안된 조달량**: {supply["totalSuggested"]:.0f}건\n"
        context_text += "- **조달 가능 지역**:\n"
        for sug in supply["suggestions"]:
            context_text += f"  - {sug['sourceRegion']}: {sug['amount']:.0f}건 (거리: {sug['distance']:.0f}km)\n"
    else:
        context_text += "- 조달 가능한 지역이 없습니다.\n"
    
    context_text += f"""
## 분석 Context (항상 고려해야 할 사항)
{context["analysis_context"]}

## 계절별 특성 ({season})
{context["season_context"]}
"""
    
    return context_text


def format_context_for_report(context: Dict) -> str:
    """Format context for report generation prompt"""
    region = context["region"]
    blood_type = context["blood_type"]
    month = context["month"]
    
    # Current forecast info
    if month == 1:
        forecast_value = context["forecast_1m"]
        severity = context["severity_1m"]
        pct_decrease = context["pct_decrease_1m"]
        decrease = context["decrease_1m"]
    elif month == 2:
        forecast_value = context["forecast_2m"]
        severity = context["severity_2m"]
        pct_decrease = context["pct_decrease_2m"]
        decrease = context["decrease_2m"]
    else:
        forecast_value = context["forecast_3m"]
        severity = context["severity_3m"]
        pct_decrease = context["pct_decrease_3m"]
        decrease = context["decrease_3m"]
    
    forecast_date = context["forecast_date"]
    season = context["season"]
    
    # Helper function to format forecast info
    def format_forecast_info(forecast_val, sev, dec, pct_dec):
        if forecast_val is None:
            return "- **예측값**: 데이터 없음\n- **경보 단계**: 데이터 없음\n- **평균 대비 감소**: 데이터 없음"
        return f"- **예측값**: {forecast_val:.0f}건\n- **경보 단계**: {sev}\n- **평균 대비 감소**: {dec:.0f}건 ({pct_dec:.1f}%)" if dec is not None and pct_dec is not None else f"- **예측값**: {forecast_val:.0f}건\n- **경보 단계**: {sev}\n- **평균 대비 감소**: 데이터 없음"
    
    context_text = f"""## 분석 대상 세그멘트
- **지역**: {region}
- **혈액형**: {blood_type}
- **예측 기간**: {month}개월 후 ({forecast_date.strftime('%Y년 %m월')}, {season})

## 실제 데이터
- **바로 전달의 실제 값**: {context["last_actual_value"]:.0f}건
- **1년 평균값 (baseline)**: {context["baseline"]:.0f}건

## 예측값 및 경보 단계
### 1개월 후 예측
{format_forecast_info(context["forecast_1m"], context["severity_1m"], context["decrease_1m"], context["pct_decrease_1m"])}

### 2개월 후 예측
{format_forecast_info(context["forecast_2m"], context["severity_2m"], context["decrease_2m"], context["pct_decrease_2m"])}

### 3개월 후 예측
{format_forecast_info(context["forecast_3m"], context["severity_3m"], context["decrease_3m"], context["pct_decrease_3m"])}

## 현재 예측 ({month}개월 후)
{format_forecast_info(forecast_value, severity, decrease, pct_decrease)}
- **예측 월**: {forecast_date.strftime('%Y년 %m월')} ({season})

## 조달 제안
"""
    
    supply = context["supply_suggestions"]
    if supply["suggestions"]:
        context_text += f"- **부족량**: {supply["shortageAmount"]:.0f}건\n"
        context_text += f"- **제안된 조달량**: {supply["totalSuggested"]:.0f}건\n"
        context_text += "- **조달 가능 지역**:\n"
        for sug in supply["suggestions"]:
            context_text += f"  - {sug['sourceRegion']}: {sug['amount']:.0f}건 (거리: {sug['distance']:.0f}km)\n"
    else:
        context_text += "- 조달 가능한 지역이 없습니다.\n"
    
    context_text += f"""
## 분석 Context (항상 고려해야 할 사항)
{context["analysis_context"]}

## 계절별 특성 ({season})
{context["season_context"]}
"""
    
    return context_text

