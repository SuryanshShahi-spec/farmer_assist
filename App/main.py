import base64
import json
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated, Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import requests
from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from Assets.recommendations import get_farming_recommendations
from Assets.schema import ChatRequest, WeatherRequest
from database.database import (
    get_or_create_location,
    init_db,
    recent_crop_analyses,
    save_chat,
    save_crop_analysis,
    save_weather,
)

STATIC_DIR = Path(__file__).resolve().parent / "static"
load_dotenv(PROJECT_ROOT / ".env")

WEATHERSTACK_URL = "http://api.weatherstack.com/current"
GROQ_CHAT_URL = "https://api.groq.com/openai/v1/chat/completions"
DEEPSEEK_CHAT_URL = "https://api.deepseek.com/chat/completions"
MAX_IMAGE_BYTES = 8 * 1024 * 1024


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title="FarmCast", version="1.0.0", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


def require_groq_key() -> str:
    key = os.getenv("GROQ_API_KEY")
    if not key:
        raise HTTPException(
            status_code=503,
            detail="GROQ_API_KEY is missing. Add it to the project's .env file.",
        )
    return key


def groq_completion(
    messages: list[dict[str, Any]], model: str, *, max_tokens: int = 700
) -> str:
    try:
        response = requests.post(
            GROQ_CHAT_URL,
            headers={"Authorization": f"Bearer {require_groq_key()}"},
            json={
                "model": model,
                "messages": messages,
                "temperature": 0.3,
                "max_tokens": max_tokens,
            },
            timeout=60,
        )
        response.raise_for_status()
        payload = response.json()
        return payload["choices"][0]["message"]["content"].strip()
    except HTTPException:
        raise
    except requests.exceptions.Timeout as error:
        raise HTTPException(status_code=504, detail="Groq request timed out.") from error
    except requests.exceptions.HTTPError as error:
        status = error.response.status_code if error.response is not None else 502
        raise HTTPException(
            status_code=502,
            detail=f"Groq API returned HTTP {status}. Check the configured model and API key.",
        ) from error
    except (requests.exceptions.RequestException, KeyError, IndexError, TypeError, ValueError) as error:
        raise HTTPException(
            status_code=502,
            detail="Could not get a valid response from the Groq API.",
        ) from error


def require_deepseek_key() -> str:
    key = os.getenv("DEEPSEEK_API_KEY") or os.getenv("DEEPSEEK_API")
    if not key:
        raise HTTPException(
            status_code=503,
            detail="DEEPSEEK_API (or DEEPSEEK_API_KEY) is missing. Add it to the project's .env file.",
        )
    return key


def deepseek_completion(
    messages: list[dict[str, Any]], model: str, *, max_tokens: int = 700
) -> str:
    try:
        response = requests.post(
            DEEPSEEK_CHAT_URL,
            headers={"Authorization": f"Bearer {require_deepseek_key()}"},
            json={
                "model": model,
                "messages": messages,
                "temperature": 0.3,
                "max_tokens": max_tokens,
            },
            timeout=60,
        )
        response.raise_for_status()
        payload = response.json()
        return payload["choices"][0]["message"]["content"].strip()
    except HTTPException:
        raise
    except requests.exceptions.Timeout as error:
        raise HTTPException(status_code=504, detail="DeepSeek request timed out.") from error
    except requests.exceptions.HTTPError as error:
        status = error.response.status_code if error.response is not None else 502
        raise HTTPException(
            status_code=502,
            detail=f"DeepSeek API returned HTTP {status}. Check the configured model and API key.",
        ) from error
    except (requests.exceptions.RequestException, KeyError, IndexError, TypeError, ValueError) as error:
        raise HTTPException(
            status_code=502,
            detail="Could not get a valid response from the DeepSeek API.",
        ) from error


@app.get("/")
def home() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "FarmCast API"}


@app.post("/api/weather")
def current_weather(request: WeatherRequest) -> dict[str, Any]:
    api_key = os.getenv("WEATHERSTACK_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=503,
            detail="WEATHERSTACK_API_KEY is missing. Add it to the project's .env file.",
        )

    try:
        response = requests.get(
            WEATHERSTACK_URL,
            params={"access_key": api_key, "query": request.location.strip(), "units": "m"},
            timeout=15,
        )
        response.raise_for_status()
        payload = response.json()
    except requests.exceptions.Timeout as error:
        raise HTTPException(status_code=504, detail="Weather lookup timed out.") from error
    except requests.exceptions.RequestException as error:
        raise HTTPException(status_code=502, detail="Could not connect to Weatherstack.") from error
    except ValueError as error:
        raise HTTPException(status_code=502, detail="Weatherstack returned invalid data.") from error

    if payload.get("success") is False:
        error_info = payload.get("error", {})
        raise HTTPException(
            status_code=502,
            detail=error_info.get("info", "Weatherstack could not find that location."),
        )

    try:
        place = payload["location"]
        current = payload["current"]
        location = f"{place['name']}, {place['country']}"
        weather = {
            "location": location,
            "temperature": current["temperature"],
            "feels_like": current.get("feelslike"),
            "condition": (current.get("weather_descriptions") or ["Unknown"])[0],
            "humidity": current["humidity"],
            "wind_speed_kmh": current["wind_speed"],
            "wind_direction": current.get("wind_dir"),
            "precipitation_mm": current.get("precip"),
            "observation_time": current.get("observation_time"),
            "icon_url": (current.get("weather_icons") or [None])[0],
        }
    except (KeyError, TypeError) as error:
        raise HTTPException(
            status_code=502,
            detail="Weatherstack response did not include current weather fields.",
        ) from error

    location_id = get_or_create_location(location, place.get("lat"), place.get("lon"))
    save_weather(
        location_id,
        {
            "temp": weather["temperature"],
            "humidity": weather["humidity"],
            "wind": weather["wind_speed_kmh"],
            "rain_prob": None,
        },
        [],
    )
    return weather


@app.post("/api/assistant")
def farming_assistant(request: ChatRequest) -> dict[str, str]:
    location = (request.location or "").strip() or "your location"
    question = request.question.strip()
    if not question:
        raise HTTPException(status_code=422, detail="Enter a question for the assistant.")

    weather = request.weather_context or "Current weather data has not been provided."
    answer = groq_completion(
        [
            {
                "role": "system",
                "content": (
                    "You are FarmCast, a careful agricultural advisor. Give concise, "
                    "practical crop and farm guidance. Clearly distinguish general "
                    "guidance from diagnosis, and advise local expert confirmation "
                    "before pesticide or disease treatment."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Location: {location}\nWeather context: {weather}\n"
                    f"Farmer's question: {question}"
                ),
            },
        ],
        os.getenv("CHAT_MODEL", "qwen/qwen3.8-27b"),
    )
    save_chat("user", question)
    save_chat("assistant", answer)
    return {"answer": answer, "location": location}


def decode_analysis(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.removeprefix("```json").removeprefix("```")
        cleaned = cleaned.removesuffix("```").strip()
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        return {
            "finding": cleaned,
            "visible_symptoms": [],
            "possible_concerns": [],
            "recommended_next_steps": [
                "Use this as preliminary guidance and confirm with a local agriculture expert."
            ],
            "expert_advisory": "AI-generated visual assessment; not a definitive diagnosis.",
            "severity": "Review",
        }
    if not isinstance(parsed, dict):
        raise HTTPException(status_code=502, detail="Plant analysis returned invalid data.")
    return parsed


def text_list(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value.strip()] if value.strip() else []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return []


@app.post("/api/plants/analyze")
def analyze_plant(
    image: Annotated[UploadFile, File()],
    crop: Annotated[str, Form(min_length=1, max_length=80)],
    growth_stage: Annotated[str, Form(min_length=1, max_length=80)],
    location: Annotated[str, Form(max_length=120)] = "Jalgaon, Maharashtra",
    temperature: Annotated[float | None, Form()] = None,
    humidity: Annotated[float | None, Form()] = None,
    rain_probability: Annotated[float | None, Form()] = None,
) -> dict[str, Any]:
    allowed_types = {"image/jpeg", "image/png", "image/webp"}
    if image.content_type not in allowed_types:
        raise HTTPException(status_code=415, detail="Upload a JPG, PNG, or WEBP leaf image.")

    image_bytes = image.file.read(MAX_IMAGE_BYTES + 1)
    if len(image_bytes) > MAX_IMAGE_BYTES:
        raise HTTPException(status_code=413, detail="Image must be 8 MB or smaller.")
    if not image_bytes:
        raise HTTPException(status_code=400, detail="The uploaded image is empty.")

    mime = image.content_type
    encoded_image = base64.b64encode(image_bytes).decode("ascii")
    prompt = (
        "Assess this crop leaf photo. Return only JSON with keys: finding (string), "
        "visible_symptoms (array of strings), possible_concerns (array of strings), "
        "recommended_next_steps (array of strings), expert_advisory (string), "
        "severity (Low, Medium, High, or Uncertain), confidence_score (integer 0-100). "
        "Do not claim certainty from an image alone. If the crop or issue is unclear, "
        "say so. Crop: "
        f"{crop.strip()}. Growth stage: {growth_stage.strip()}."
    )
    result_text = groq_completion(
        [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{mime};base64,{encoded_image}"},
                    },
                ],
            }
        ],
        os.getenv("GROQ_VISION_MODEL", "qwen/qwen3.8-27b"),
        max_tokens=900,
    )
    analysis = decode_analysis(result_text)
    analysis["finding"] = str(analysis.get("finding") or "No clear finding could be determined.")
    analysis["visible_symptoms"] = text_list(analysis.get("visible_symptoms"))
    analysis["possible_concerns"] = text_list(analysis.get("possible_concerns"))
    finding_and_concerns = " ".join(
        [analysis["finding"], *analysis["possible_concerns"]]
    )
    recommendation_tips = get_farming_recommendations(
        finding_and_concerns,
        temperature=temperature,
        humidity=humidity,
        rain_probability=rain_probability,
    )
    next_steps = text_list(analysis.get("recommended_next_steps"))
    analysis["recommended_next_steps"] = list(dict.fromkeys(next_steps + recommendation_tips))
    analysis["expert_advisory"] = str(analysis.get("expert_advisory") or "")
    location_id = get_or_create_location(location.strip() or "Unknown", None, None)
    save_crop_analysis(
        location_id,
        crop.strip(),
        growth_stage.strip(),
        image.filename,
        analysis,
        "\n".join(analysis.get("recommended_next_steps", [])),
    )
    return {
        "crop": crop.strip(),
        "growth_stage": growth_stage.strip(),
        "analysis": analysis,
    }


@app.get("/api/plants/history")
def plant_history() -> list[dict[str, Any]]:
    return recent_crop_analyses()


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("App.main:app", host="0.0.0.0", port=port, reload=True)
