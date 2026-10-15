"""
Seed Data Script for FarmCast AI Database.
Initializes starter weather alerts, recommendations, and past logs.
"""

from datetime import datetime
from database import SessionLocal, engine, Base
from models import AlertRecord, RecommendationRecord, WeatherSearchLog, CropAnalysisRecord


def seed():
    # Create all tables first
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # 1. Seed Alerts if none exist
        if db.query(AlertRecord).count() == 0:
            alerts = [
                AlertRecord(
                    alert_id="alt-001",
                    severity="warning",
                    category="rainfall",
                    title="Heavy Rainfall Risk on Thursday & Friday",
                    location="Jalgaon, Maharashtra",
                    time_window="Thursday 14:00 - Friday 22:00",
                    description="A low-pressure convective trough may bring 45-65mm localized downpours with strong gusts up to 40 km/h across central farming blocks.",
                    suggested_action="Ensure field drainage channels in cotton and soybean plots are cleared. Delay chemical foliar spraying until rain subsides.",
                    affected_crops="Cotton, Soybean, Tomato, Chilli",
                    read=False,
                    created_at=datetime.utcnow()
                ),
                AlertRecord(
                    alert_id="alt-002",
                    severity="info",
                    category="humidity",
                    title="High Microclimate Humidity (Fungal Spore Risk)",
                    location="Jalgaon, Maharashtra",
                    time_window="Next 48 Hours",
                    description="Relative humidity sustained >80% combined with temperatures between 26-29°C creates conducive conditions for foliar pathogens like leaf spot and downy mildew.",
                    suggested_action="Scout lower leaf canopy closely. Ensure adequate spacing and avoid flood irrigation during evening hours.",
                    affected_crops="Tomato, Onion, Chilli, Grapes",
                    read=False,
                    created_at=datetime.utcnow()
                ),
                AlertRecord(
                    alert_id="alt-003",
                    severity="warning",
                    category="wind",
                    title="Gusty Winds Exceeding 38 km/h Expected",
                    location="Jalgaon, Maharashtra",
                    time_window="Wednesday Afternoon",
                    description="Sudden convective gusts may cause lodging in tall grain crops and physical damage to young sapling stakes.",
                    suggested_action="Inspect and strengthen crop staking in tomato trellises and banana orchards. Postpone high-pressure spray operations.",
                    affected_crops="Maize, Sugarcane, Banana, Tomato",
                    read=True,
                    created_at=datetime.utcnow()
                )
            ]
            db.add_all(alerts)
            db.commit()
            print("[+] Seeded Weather Alerts")

        # 2. Seed Recommendations if none exist
        if db.query(RecommendationRecord).count() == 0:
            recos = [
                RecommendationRecord(
                    title="Pre-Rainfall Drainage Preparation",
                    crop="Cotton & Soybean",
                    summary="Clear field trenches to avoid standing water; delay nitrogen top-dressing until heavy showers cease.",
                    created_at=datetime.utcnow()
                ),
                RecommendationRecord(
                    title="Copper Oxychloride Prophylactic Spray",
                    crop="Tomato",
                    summary="Apply preventative bio-fungicide or copper spray in morning hours before atmospheric humidity increases.",
                    created_at=datetime.utcnow()
                )
            ]
            db.add_all(recos)
            db.commit()
            print("[+] Seeded Farming Recommendations")

        # 3. Seed Initial Weather Log
        if db.query(WeatherSearchLog).count() == 0:
            db.add(WeatherSearchLog(
                location="Jalgaon, Maharashtra",
                temperature=29.5,
                condition="Partly Cloudy",
                condition_code="partly_cloudy",
                humidity=64,
                wind_speed=14.8,
                created_at=datetime.utcnow()
            ))
            db.commit()
            print("[+] Seeded Initial Weather Log")

    finally:
        db.close()


if __name__ == "__main__":
    seed()
