@echo off
REM Double-click this file to start the Job Application Tracker on Windows.
cd /d "%~dp0"
python -m job_tracker.app
if errorlevel 1 pause
