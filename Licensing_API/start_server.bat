@echo off
echo ========================================
echo SMATCH Licensing API - Server Starter
echo ========================================
echo.

REM Start the server on port 5000
echo.
echo Starting server on http://localhost:5000
echo.
echo Press CTRL+C to stop the server
echo ========================================

cd /d "%~dp0"
python -m uvicorn licensing_api.main:app --host 0.0.0.0 --port 8000 --reload --log-level info
