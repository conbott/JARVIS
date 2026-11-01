@echo off
echo ===================================================
echo Stopping Local RAG Services...
echo ===================================================

taskkill /F /IM uvicorn.exe /T 2>nul
taskkill /F /IM node.exe /T 2>nul
taskkill /F /FI "WINDOWTITLE eq Ollama Engine (11434)*" /T 2>nul
taskkill /F /FI "WINDOWTITLE eq FastAPI Backend (8000)*" /T 2>nul
taskkill /F /FI "WINDOWTITLE eq Vite Frontend (5173)*" /T 2>nul

echo All services stopped cleanly.
pause
