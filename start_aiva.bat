@echo off
echo.
echo  🤖 AIVA - AI Voice Assistant
echo  =============================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    echo Please install Python 3.7+ from https://python.org
    pause
    exit /b 1
)

echo ✅ Python found
echo 🚀 Starting AIVA Launcher...
echo.

REM Run the launcher
python launch_aiva.py

REM Keep window open if there's an error
if errorlevel 1 (
    echo.
    echo ❌ AIVA failed to start
    pause
)