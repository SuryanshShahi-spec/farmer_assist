# FarmCast

FarmCast is a FastAPI application with a web dashboard for weather, the DeepSeek
farming assistant, and Groq-powered plant image analysis.

## Deploy on Railway

1. Push this project to a GitHub repository and create a Railway project from it.
   Railway will build the root `Dockerfile`.
2. Add these secrets in the Railway service's **Variables** settings. Do not
   commit `.env` or put API keys in deployment configuration.
   - `WEATHERSTACK_API_KEY` — required for live weather.
   - `DEEPSEEK_API` — required for assistant chat. `DEEPSEEK_API_KEY` is also
     accepted.
   - `GROQ_API_KEY` — required for plant image analysis.
   - `DEEPSEEK_MODEL` — optional; defaults to `deepseek-chat`.
   - `GROQ_VISION_MODEL` — optional; defaults to
     `meta-llama/llama-4-scout-17b-16e-instruct`.
3. For persistent SQLite data, add a Railway volume mounted at `/data` and set
   `DATABASE_PATH` to `/data/weather_farm.db`. Without a volume, the service can
   run, but local SQLite data may be lost when Railway replaces the container.
4. Generate a public domain for the service. The app listens on Railway's
   injected `PORT`; `/api/health` is its health-check endpoint.

For an existing service still using Railway Config as Code, `railway.toml`
selects the Dockerfile builder and configures its health check. For a new service,
set the health-check path to `/api/health` in Railway's service settings if it is
not picked up automatically. Railway's Config as Code files are deprecated for
new services; the Dockerfile and injected `PORT` also allow deployment when that
legacy configuration is not used.

## Run locally

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn App.main:app --reload
```

Open `http://127.0.0.1:8000`.
