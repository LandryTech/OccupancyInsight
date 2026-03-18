@echo off
REM ========================================
REM Gym Occupancy Logger - Auto-Start Script
REM ========================================

REM Move the context to the directory where this batch file lives
cd /d "%~dp0"

REM Open PowerShell and run the Python script
REM We no longer need to 'cd' inside the PowerShell command
powershell -NoExit -Command "python gym_occupancy_logger.py"
