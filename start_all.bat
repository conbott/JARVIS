@echo off
echo ===================================================
echo Starting Local RAG and Voice Assistant Services...
echo ===================================================

echo [1/3] Launching Ollama...
start "Ollama Engine (11434)" cmd /k "ollama serve"

echo [2/3] Launching FastAPI Backend (8000)...
start "FastAPI Backend (8000)" cmd /k "cd /d "%~dp0backend" && .venv\Scripts\python.exe -m uvicorn main:app --port 8000 --reload"

echo [3/3] Launching Vite Frontend (5173)...
start "Vite Frontend (5173)" cmd /k "cd /d "%~dp0frontend" && npm run dev"

echo ===================================================
echo All services launched in dedicated windows!
echo Web UI will be available at: http://localhost:5173
echo ===================================================
