@echo off
REM LinkedIn Message Analyzer - Windows Startup Script
REM For those who fear the command line

setlocal enabledelayedexpansion

echo.
echo  **** LINKEDIN MESSAGE ANALYZER ****
echo  64K RAM SYSTEM  38911 BASIC BYTES FREE
echo.
echo  READY.
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo  ?PYTHON NOT FOUND ERROR
    echo.
    echo  Please install Python 3.9+ from https://python.org
    pause
    exit /b 1
)

REM Check if messages.csv exists in current directory
if not exist "messages.csv" (
    echo  Looking for messages.csv...
    echo.

    REM Check common locations
    if exist "%USERPROFILE%\Downloads\messages.csv" (
        echo  Found messages.csv in Downloads folder!
        set "CSV_FILE=%USERPROFILE%\Downloads\messages.csv"
    ) else (
        echo  ?FILE NOT FOUND ERROR
        echo.
        echo  Please place your LinkedIn messages.csv in this folder
        echo  or drag and drop it onto this script.
        echo.
        echo  To get your messages:
        echo  1. Go to LinkedIn Settings ^> Data Privacy ^> Get a copy of your data
        echo  2. Select "Messages" and request your data
        echo  3. Wait for LinkedIn to email you (~24 hours)
        echo  4. Extract messages.csv from the download
        echo.
        pause
        exit /b 1
    )
) else (
    set "CSV_FILE=messages.csv"
)

REM Handle drag-and-drop (file passed as argument)
if not "%~1"=="" (
    set "CSV_FILE=%~1"
)

echo  LOAD"%CSV_FILE%",8,1
echo.

:menu
echo  ========================================
echo  SELECT MODE:
echo  ========================================
echo.
echo  [1] Quick Analysis (console output)
echo  [2] Web Dashboard (C64 style!)
echo  [3] Full Report (HTML export)
echo  [4] Analysis + LLM (requires API key)
echo  [5] Exit
echo.
set /p choice="  Enter choice (1-5): "

if "%choice%"=="1" goto quick
if "%choice%"=="2" goto web
if "%choice%"=="3" goto html
if "%choice%"=="4" goto llm
if "%choice%"=="5" goto end

echo  ?SYNTAX ERROR
goto menu

:quick
echo.
echo  RUN
echo.
python linkedin_message_analyzer.py "%CSV_FILE%" --health-score
pause
goto menu

:web
echo.
echo  LOADING WEB DASHBOARD...
echo.
echo  Open http://localhost:6502 in your browser
echo  Press Ctrl+C to stop
echo.
python linkedin_message_analyzer.py "%CSV_FILE%" --web
goto menu

:html
echo.
set /p htmlfile="  Output filename (default: report.html): "
if "%htmlfile%"=="" set "htmlfile=report.html"
echo.
echo  SAVING...
python linkedin_message_analyzer.py "%CSV_FILE%" --export-html "%htmlfile%" --health-score --trend
echo.
echo  Report saved to %htmlfile%
echo  Opening in browser...
start "" "%htmlfile%"
pause
goto menu

:llm
echo.
echo  Available LLM providers:
echo    - openai (requires OPENAI_API_KEY)
echo    - anthropic (requires ANTHROPIC_API_KEY)
echo    - ollama (FREE - local, no API key!)
echo    - gemini (requires GOOGLE_API_KEY)
echo    - groq (requires GROQ_API_KEY)
echo    - mistral (requires MISTRAL_API_KEY)
echo.
set /p provider="  Enter provider (or 'ollama' for free): "
if "%provider%"=="" set "provider=ollama"
echo.
python linkedin_message_analyzer.py "%CSV_FILE%" --llm %provider% --summarize --health-score
pause
goto menu

:end
echo.
echo  READY.
echo.
