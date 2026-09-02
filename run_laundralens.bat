@echo off
title LaundraLens X - Financial Crime Intelligence
echo =====================================================================
echo  LaundraLens X - Agentic Anti-Money Laundering Intelligence Platform
echo =====================================================================
echo.
echo Starting FastAPI Engine on http://127.0.0.1:8000 ...
start /B uvicorn laundralens-x.src.api.main:app --host 127.0.0.1 --port 8000
timeout /t 3 /nobreak >nul

echo Starting Streamlit Workstation on http://localhost:8501 ...
streamlit run laundralens-x/dashboard/app.py
pause
