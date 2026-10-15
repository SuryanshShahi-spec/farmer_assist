"""
SQLAlchemy Models for FarmCast AI Database.
Stores weather searches, crop leaf analyses, recommendations, and hazards.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, Text, DateTime
from database import Base


class WeatherSearchLog(Base):
    __tablename__ = "weather_search_logs"

    id = Column(Integer, primary_key=True, index=True)
    location = Column(String(120), index=True, nullable=False)
    temperature = Column(Float, nullable=False)
    condition = Column(String(80), nullable=False)
    condition_code = Column(String(40), default="partly_cloudy")
    humidity = Column(Integer, default=60)
    wind_speed = Column(Float, default=12.0)
    created_at = Column(DateTime, default=datetime.utcnow)


class CropAnalysisRecord(Base):
    __tablename__ = "crop_analyses"

    id = Column(Integer, primary_key=True, index=True)
    crop_name = Column(String(80), index=True, nullable=False)
    growth_stage = Column(String(80), nullable=False)
    finding = Column(String(200), nullable=False)
    confidence_score = Column(Integer, default=80)
    severity = Column(String(40), default="Medium")
    visible_symptoms = Column(Text, nullable=True)  # JSON or newline-separated
    possible_concerns = Column(Text, nullable=True)
    weather_context = Column(Text, nullable=True)
    recommended_next_steps = Column(Text, nullable=True)
    expert_advisory = Column(Text, nullable=True)
    image_filename = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class RecommendationRecord(Base):
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(150), nullable=False)
    crop = Column(String(80), nullable=False)
    summary = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class AlertRecord(Base):
    __tablename__ = "weather_alerts"

    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(String(40), unique=True, index=True, nullable=False)
    severity = Column(String(20), default="warning")  # danger, warning, info
    category = Column(String(40), default="rainfall")  # rainfall, wind, humidity
    title = Column(String(150), nullable=False)
    location = Column(String(120), nullable=False)
    time_window = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    suggested_action = Column(Text, nullable=False)
    affected_crops = Column(String(200), default="All Crops")
    read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
