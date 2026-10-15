@echo off
title Omni Extractor - Auto Sync & Render Deploy
cls
echo ================================================================
echo    Omni Extractor -- Syncing & Deploying to Render Cloud
echo ================================================================
python deploy_render.py %*
echo.
pause
