from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import os
from dotenv import load_dotenv
import openai
import numpy as np
from datetime import datetime

from models import (
    AnalyzeRequest,
    AnalyzeResponse,
    ChatRequest,
    ChatResponse,
    ForecastsResponse,
    ShortageResponse,
    RegionsResponse,
    BloodTypesResponse,
    SupplySuggestionRequest,
    SupplySuggestionResponse,
)
from services.forecast_service import get_forecast_service
from services.supply_suggestion_service import get_supply_suggestions_summary
from services.context_helper import (
    collect_context,
    format_context_for_chat,
    format_context_for_report,
)

load_dotenv()

app = FastAPI(title="Bloodcast API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize OpenAI client
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Initialize forecast service (lazy loaded on first request)
forecast_service = None


@app.get("/")
def read_root():
    return {"message": "Bloodcast API is running"}


@app.get("/api/forecasts", response_model=ForecastsResponse)
async def get_forecasts(include_all: bool = True):
    """
    Get all forecasts for 1, 2, 3 months ahead with severity levels.

    Args:
        include_all: If True, include all forecasts even without severity warnings.
                    If False, only include forecasts with severity warnings.
    """
    global forecast_service
    if forecast_service is None:
        forecast_service = get_forecast_service()

    forecasts_data = forecast_service.get_all_forecasts(include_all=include_all)
    forecasts = [ShortageResponse(**f) for f in forecasts_data]

    return ForecastsResponse(
        forecasts=forecasts,
        lastDate=forecast_service.last_date.strftime("%Y-%m-%d"),
        totalRegions=len(forecast_service.regions),
        totalBloodTypes=len(forecast_service.bloodtypes),
    )


@app.get("/api/regions", response_model=RegionsResponse)
async def get_regions():
    """Get all unique region names from the data"""
    global forecast_service
    if forecast_service is None:
        forecast_service = get_forecast_service()

    return RegionsResponse(regions=forecast_service.regions)


@app.get("/api/bloodtypes", response_model=BloodTypesResponse)
async def get_bloodtypes():
    """Get all unique blood types from the data"""
    global forecast_service
    if forecast_service is None:
        forecast_service = get_forecast_service()

    return BloodTypesResponse(bloodTypes=forecast_service.bloodtypes)


@app.post("/api/supply-suggestion", response_model=SupplySuggestionResponse)
async def get_supply_suggestion(request: SupplySuggestionRequest):
    """
    Get blood supply redistribution suggestions for a shortage region.
    Suggests which regions to source blood from based on distance and surplus availability.
    """
    global forecast_service
    if forecast_service is None:
        forecast_service = get_forecast_service()

    # Validate region and bloodtype
    if request.region not in forecast_service.regions:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid region: {request.region}. Valid regions: {forecast_service.regions}",
        )

    if request.bloodType not in forecast_service.bloodtypes:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid blood type: {request.bloodType}. Valid types: {forecast_service.bloodtypes}",
        )

    if request.month not in [1, 2, 3]:
        raise HTTPException(
            status_code=400,
            detail="Month must be 1, 2, or 3",
        )

    try:
        summary = get_supply_suggestions_summary(
            request.region, request.bloodType, request.month, forecast_service
        )

        return SupplySuggestionResponse(**summary)

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error generating supply suggestions: {str(e)}"
        )


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze_shortage(request: AnalyzeRequest):
    """
    Analyze a blood supply shortage and generate a detailed report.
    Uses real forecast data if available.
    """
    global forecast_service
    if forecast_service is None:
        forecast_service = get_forecast_service()

    # Validate region and bloodtype
    if request.region not in forecast_service.regions:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid region: {request.region}. Valid regions: {forecast_service.regions}",
        )

    if request.bloodType not in forecast_service.bloodtypes:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid blood type: {request.bloodType}. Valid types: {forecast_service.bloodtypes}",
        )

    if request.month not in [1, 2, 3]:
        raise HTTPException(
            status_code=400,
            detail="Month must be 1, 2, or 3",
        )

    try:
        # Collect comprehensive context
        context = collect_context(
            request.region, request.bloodType, request.month, forecast_service
        )

        if not context:
            raise HTTPException(
                status_code=404,
                detail=f"No data available for {request.region}, {request.bloodType}",
            )

        # Format context for report
        context_text = format_context_for_report(context)

        # Get current forecast info
        if request.month == 1:
            forecast_value = context["forecast_1m"]
            severity = context["severity_1m"]
            pct_decrease = context["pct_decrease_1m"]
            decrease = context["decrease_1m"]
        elif request.month == 2:
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
        supply = context["supply_suggestions"]

        system_prompt = """You are an expert blood supply analyst with deep knowledge of healthcare logistics and blood bank management.
You specialize in analyzing blood supply shortages and providing actionable recommendations based on forecast data, seasonal patterns, and demographic insights.
Always consider the analysis context (직업별 특성, 근무 시간, 날씨/계절, 헌혈 상품/인센티브) when making recommendations.
Write reports in Korean."""

        user_prompt = f"""{context_text}

## 리포트 작성 지침

위의 context를 바탕으로 다음 내용을 포함한 종합 분석 리포트를 작성해주세요:

### 1. 전반적인 분석
- 현재 상황 분석 (어떠어떠한 상황인지)
- 얼마나 부족할 예정인지 (부족량, 감소율)
- 경보 단계의 의미와 심각성

### 2. 원인 분석
- 분석 context를 바탕으로 왜 이런 부족이 발생할 수 있는지 분석
- 계절적 요인 ({season}) 고려
- 직업별, 연령대별, 성별 특성 고려

### 3. 조달 제안
- 부족한 상황이라면 어떻게 지역에서 조달을 받아야 하는지
- 조달 가능 지역과 조달량 제안
- 거리와 실현 가능성 고려

### 4. 헌혈량 증진을 위한 활동 제안
분석 context를 바탕으로 다음을 고려하여 구체적인 활동을 제안:
- **군인 대상 캠페인**: 입대 시즌, 훈련소 입대 인원 고려
- **직장인 대상 헌혈 버스**: 평일 근무 시간, 공휴일, 점심시간 캠페인
- **대학생 대상 캠페인**: 학사 일정(시험 기간, 방학) 고려
- **고령층 대상 캠페인**: 날씨 및 계절 영향 고려 (폭염, 한파 주의보)
- **여성 대상 캠페인**: 헌혈 기념품(Goods), 유명 아이돌 포토카드, 올리브영 상품권 프로모션
- **남성 대상 캠페인**: 군 가산점, 예비군 훈련 시간 인정 등 실질적 혜택
- **계절별 특성**: {season}철 특성에 맞는 활동 제안

### 5. 위험 평가 및 대응 방안
- 위험 수준 평가
- 대응 우선순위

리포트는 한글로 작성하고, 구체적인 수치와 데이터를 포함하여 작성해주세요."""

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.7,
            max_tokens=2000,
        )

        report = response.choices[0].message.content

        return AnalyzeResponse(
            report=report,
            region=request.region,
            bloodType=request.bloodType,
            month=request.month,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error generating report: {str(e)}"
        )


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Handle conversational Q&A about blood supply forecasts.
    Validates region and bloodtype against actual data.
    """
    global forecast_service
    if forecast_service is None:
        forecast_service = get_forecast_service()

    # Validate region and bloodtype
    if request.region not in forecast_service.regions:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid region: {request.region}. Valid regions: {forecast_service.regions}",
        )

    if request.bloodType not in forecast_service.bloodtypes:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid blood type: {request.bloodType}. Valid types: {forecast_service.bloodtypes}",
        )

    if request.month not in [1, 2, 3]:
        raise HTTPException(
            status_code=400,
            detail="Month must be 1, 2, or 3",
        )

    try:
        # Collect comprehensive context
        context = collect_context(
            request.region, request.bloodType, request.month, forecast_service
        )

        if not context:
            raise HTTPException(
                status_code=404,
                detail=f"No data available for {request.region}, {request.bloodType}",
            )

        # Format context for chat
        context_text = format_context_for_chat(context)

        system_prompt = f"""You are a helpful AI assistant specialized in blood supply management and forecasting. 
You are currently discussing blood supply for {request.region}, specifically Type {request.bloodType}, {request.month} months ahead.

You have access to comprehensive forecast data and analysis context. Use this information to provide accurate, helpful answers.
Always consider the analysis context (직업별 특성, 근무 시간, 날씨/계절, 헌혈 상품/인센티브) when answering questions.
Be concise but informative, and provide specific numbers and insights from the data when relevant.
Answer in Korean."""

        user_prompt = f"""{context_text}

## 사용자 질문
{request.message}

위의 context를 바탕으로 사용자의 질문에 답변해주세요. 예측값, 경보 단계, 조달 제안, 계절적 특성 등을 고려하여 답변해주세요."""

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.7,
            max_tokens=1000,
        )

        ai_response = response.choices[0].message.content

        return ChatResponse(response=ai_response)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing chat: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
