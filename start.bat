@echo off
REM Multi-Agent System - Start Script for Windows

echo ========================================
echo Multi-Agent System - Startup
echo ========================================
echo.

REM Check if virtual environment exists
if not exist "venv\" (
    echo Virtual environment not found. Creating...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install/update dependencies
echo Installing dependencies...
pip install -r requirements.txt

REM Check if .env exists
if not exist ".env" (
    echo.
    echo Warning: .env file not found!
    echo Creating .env from .env.example...
    copy .env.example .env
    echo.
    echo Please edit .env file with your API keys before running the application.
    echo.
)

REM Ask user which mode to run
echo.
echo Select mode to run:
echo 1) API Server (FastAPI)
echo 2) CLI Interactive Mode
echo 3) CLI Query Mode
echo 4) Run Examples
echo 5) Run Tests
echo.
set /p choice="Enter choice [1-5]: "

if "%choice%"=="1" (
    echo.
    echo Starting API server...
    echo API will be available at http://localhost:8000
    echo API documentation at http://localhost:8000/docs
    python src\api.py
) else if "%choice%"=="2" (
    echo.
    echo Starting interactive CLI...
    python src\main.py --mode interactive
) else if "%choice%"=="3" (
    set /p query="Enter your query: "
    set /p location="Enter location (default: London): "
    if "%location%"=="" set location=London
    python src\main.py --mode query --query "%query%" --location "%location%"
) else if "%choice%"=="4" (
    echo.
    echo Running examples...
    python examples\examples.py
) else if "%choice%"=="5" (
    echo.
    echo Running tests...
    python test_basic.py
) else (
    echo Invalid choice. Exiting.
    exit /b 1
)
