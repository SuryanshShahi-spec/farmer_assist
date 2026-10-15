"""
Pydantic Schemas for FarmCast AI API Contracts.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class WeatherRequest(BaseModel):
    location: str = Field(min_length=1, max_length=120)


class CurrentWeatherResponse(BaseModel):
    is_demo: bool = False
    location: str
    timestamp: str
    temperature: float
    feels_like: float
    condition: str
    condition_code: str
    humidity: int
    wind_speed_kmh: float
    wind_direction: str
    rain_probability_pct: int
    uv_index: int
    pressure_hpa: int
    sunrise: str
    sunset: str
    summary: str


class ForecastDay(BaseModel):
    day: str
    date: str
    iso_date: str
    condition: str
    condition_code: str
    temp_max: float
    temp_min: float
    rain_probability: int
    humidity: int
    wind_speed: float


class HourlyForecastItem(BaseModel):
    time: str
    temp: float
    rain_prob: int
    humidity: int


class ForecastResponse(BaseModel):
    is_demo: bool = False
    location: str
    days: List[ForecastDay]
    hourly: List[HourlyForecastItem]


class AlertItem(BaseModel):
    id: str
    severity: str
    category: str
    title: str
    location: str
    time_window: str
    description: str
    suggested_action: str
    affected_crops: List[str]
    read: bool
    created_at: str


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    location: Optional[str] = Field(default="Jalgaon, Maharashtra", max_length=120)
    weather_context: Optional[str] = Field(default=None, max_length=1600)


class ChatResponse(BaseModel):
    is_demo: bool = False
    answer: str
    location: str
    timestamp: str
    weather_evidence: List[str]
    farming_warnings: List[str]


class CropAnalysisResponse(BaseModel):
    is_demo: bool = False
    crop_name: str
    growth_stage: str
    analyzed_at: str
    finding: str
    confidence_score: int
    confidence_uncertainty: str
    visible_symptoms: List[str]
    possible_concerns: List[str]
    weather_context: str
    recommended_next_steps: List[str]
    expert_advisory: str


class WeatherHistoryItem(BaseModel):
    id: str
    location: str
    temp: float
    condition: str
    date: str


class CropHistoryItem(BaseModel):
    id: str
    crop_name: str
    growth_stage: str
    finding: str
    confidence_score: int
    severity: str
    date: str
    thumbnail: Optional[str] = None


class RecommendationHistoryItem(BaseModel):
    id: str
    title: str
    crop: str
    date: str
    summary: str
