# app/db.py
import json
import os
import sqlite3
from pathlib import Path

# Railway: set DATABASE_PATH env var to a persistent volume (e.g. /data/weather_farm.db).
# Locally this falls back to the project's database/ directory.
_default_db = Path(__file__).resolve().parent / "weather_farm.db"
DB = Path(os.getenv("DATABASE_PATH", str(_default_db)))
DB.parent.mkdir(parents=True, exist_ok=True)

def conn():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c

def init_db():
    with conn() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS locations(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT, lat REAL, lon REAL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP);

        CREATE TABLE IF NOT EXISTS weather_logs(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            location_id INTEGER REFERENCES locations(id),
            temp REAL, humidity REAL, wind REAL, rain_prob REAL,
            alerts TEXT,
            fetched_at TEXT DEFAULT CURRENT_TIMESTAMP);

        CREATE TABLE IF NOT EXISTS crop_analyses(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            location_id INTEGER REFERENCES locations(id),
            crop TEXT, growth_stage TEXT, image_path TEXT,
            observations TEXT,      -- JSON from vision step
            recommendation TEXT,    -- final weather-aware advice
            created_at TEXT DEFAULT CURRENT_TIMESTAMP);

        CREATE TABLE IF NOT EXISTS chat_history(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT, content TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP);
        """)

def get_or_create_location(name, lat, lon):
    with conn() as c:
        row = c.execute("SELECT id FROM locations WHERE name=?", (name,)).fetchone()
        if row: return row["id"]
        return c.execute("INSERT INTO locations(name,lat,lon) VALUES(?,?,?)",
                         (name, lat, lon)).lastrowid

def save_weather(loc_id, cur, alerts):
    with conn() as c:
        c.execute("""INSERT INTO weather_logs(location_id,temp,humidity,wind,rain_prob,alerts)
                     VALUES(?,?,?,?,?,?)""",
                  (loc_id, cur["temp"], cur["humidity"], cur["wind"],
                   cur["rain_prob"], json.dumps(alerts)))

def save_crop_analysis(loc_id, crop, stage, path, obs, rec):
    with conn() as c:
        c.execute("""INSERT INTO crop_analyses
                     (location_id,crop,growth_stage,image_path,observations,recommendation)
                     VALUES(?,?,?,?,?,?)""",
                  (loc_id, crop, stage, path, json.dumps(obs), rec))

def recent_crop_analyses(limit=5):
    with conn() as c:
        return [dict(r) for r in c.execute(
            "SELECT crop,growth_stage,observations,recommendation,created_at "
            "FROM crop_analyses ORDER BY id DESC LIMIT ?", (limit,))]

def save_chat(role, content):
    with conn() as c:
        c.execute("INSERT INTO chat_history(role,content) VALUES(?,?)", (role, content))