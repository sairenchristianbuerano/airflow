@echo off
REM Airflow Component Generator - Service Startup Script
REM This script starts the component generator service with auto-reload

echo ========================================
echo Airflow Component Generator Service
echo ========================================
echo.

REM Kill any existing Python processes running the service
echo Stopping any existing service instances...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *uvicorn*" 2>nul
timeout /t 2 /nobreak >nul

REM Navigate to component-generator directory
cd /d "%~dp0component-generator"

REM Check if .env file exists
if not exist "..\\.env" (
    echo ERROR: .env file not found!
    echo Please copy .env.example to .env and add your ANTHROPIC_API_KEY
    pause
    exit /b 1
)

echo.
echo Starting service with Phase 2 enhancements...
echo - Static analysis integration (mypy, ruff)
echo - Enhanced test generation with XCom/templates
echo - Model routing by complexity (Haiku for simple)
echo - Comprehensive troubleshooting documentation
echo.
echo Service will be available at: http://localhost:8095
echo Press Ctrl+C to stop the service
echo.

REM Start the service with auto-reload
python -m uvicorn src.service:app --host 0.0.0.0 --port 8095 --reload

pause
