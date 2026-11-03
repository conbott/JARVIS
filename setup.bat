@echo off
echo ===================================================
echo Setting up Jarvis Local RAG ^& Voice Assistant
echo ===================================================

echo [1/4] Checking environment configuration...
if not exist "%~dp0backend\.env" (
    echo Creating backend\.env from .env.example...
    copy "%~dp0backend\.env.example" "%~dp0backend\.env" >nul
) else (
    echo backend\.env already exists.
)

echo [2/4] Setting up Python virtual environment...
if not exist "%~dp0backend\.venv" (
    echo Creating Python venv at backend\.venv...
    python -m venv "%~dp0backend\.venv"
)
echo Installing backend dependencies...
"%~dp0backend\.venv\Scripts\python.exe" -m pip install --upgrade pip
"%~dp0backend\.venv\Scripts\pip.exe" install -r "%~dp0backend\requirements.txt"

echo [3/4] Installing frontend packages...
cd /d "%~dp0frontend"
call npm install
cd /d "%~dp0"

echo [4/4] Environment setup complete!
echo.
echo Recommended local Ollama models:
echo   - LLM Generation:  ollama pull qwen2.5-coder:7b (or llama3.2:3b for low-spec PCs)
echo   - Dense Embedding: ollama pull qwen3-embedding:0.6b
echo.
echo ===================================================
echo To launch all services together, run:
echo   .\start_all.bat
echo ===================================================
pause
