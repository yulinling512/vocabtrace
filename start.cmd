@echo off
cd /d "%~dp0"
where node >nul 2>nul
if errorlevel 1 (
  echo.
  echo   Node.js not found.
  echo   Install it from https://nodejs.org  then run this file again.
  echo.
  pause
  exit /b
)
start "" "app\index.html"
echo.
echo   Starting judge proxy ...
echo   Keep this window open while you study.
echo.
node proxy.js
pause
