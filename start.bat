@echo off
title Omni Extractor - Local Server
cls
echo ================================================================
echo    Omni Extractor -- Universal Video & Audio Downloader
echo ================================================================
echo.
echo [*] Starting local server with 100%% cookie-free multi-client engine...
echo [*] Accessible locally at: http://localhost:8000
echo.
start http://localhost:8000
python run.py --no-tunnel
pause
