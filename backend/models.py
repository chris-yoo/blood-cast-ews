"""
Pydantic models for API requests and responses
"""

from pydantic import BaseModel
from typing import List, Optional, Literal


class ForecastRequest(BaseModel):
    """Request model for forecast endpoint"""

    region: Optional[str] = None
    bloodType: Optional[str] = None
    month: Optional[int] = None


class ShortageResponse(BaseModel):
    """Response model for shortage forecast"""

    id: str
    region: str
    bloodType: str
    month: int
    forecastValue: float
    severity: Literal["관심", "주의", "경계", "심각", "정상"]


class ForecastsResponse(BaseModel):
    """Response model for forecasts endpoint"""

    forecasts: List[ShortageResponse]
    lastDate: str
    totalRegions: int
    totalBloodTypes: int


class AnalyzeRequest(BaseModel):
    """Request model for analyze endpoint"""

    region: str
    bloodType: str
    month: int


class AnalyzeResponse(BaseModel):
    """Response model for analyze endpoint"""

    report: str
    region: str
    bloodType: str
    month: int


class ChatRequest(BaseModel):
    """Request model for chat endpoint"""

    message: str
    region: str
    bloodType: str
    month: int = 1  # Default to 1 month ahead


class ChatResponse(BaseModel):
    """Response model for chat endpoint"""

    response: str


class RegionsResponse(BaseModel):
    """Response model for regions endpoint"""

    regions: List[str]


class BloodTypesResponse(BaseModel):
    """Response model for bloodtypes endpoint"""

    bloodTypes: List[str]


class SupplySuggestionItem(BaseModel):
    """Individual supply suggestion item"""

    sourceRegion: str
    bloodType: str
    amount: float
    distance: float


class SupplySuggestionRequest(BaseModel):
    """Request model for supply suggestion endpoint"""

    region: str
    bloodType: str
    month: int


class SupplySuggestionResponse(BaseModel):
    """Response model for supply suggestion endpoint"""

    shortageRegion: str
    bloodType: str
    month: int
    shortageAmount: float
    forecastValue: float
    baseline: float
    totalSuggested: float
    suggestions: List[SupplySuggestionItem]
