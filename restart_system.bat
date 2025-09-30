@echo off
REM ============================================================================
REM VoidCat RDC - CCC System Restart Manager
REM Covenant Command Cycle - Graceful Service Recovery & Restart
REM Contact: SorrowsCry86@voidcat.org | @sorrowscry86 | CashApp $WykeveTF
REM Organization: VoidCat RDC
REM ============================================================================

setlocal EnableDelayedExpansion

echo.
echo ===================================================
echo  VoidCat RDC - System Restart Manager
echo ===================================================
echo  Executing Graceful Service Recovery...
echo ===================================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.8+ and add it to your PATH
    pause
    exit /b 1
)

echo [INFO] Python version:
python --version
echo.

REM Phase 1: Graceful Shutdown
echo [PHASE 1] Initiating graceful shutdown sequence...
echo.

REM Try to stop services gracefully first
echo [SHUTDOWN] Attempting graceful service termination...

REM Stop Python processes (this will stop both server and any HTTP servers)
tasklist /FI "IMAGENAME eq python.exe" 2>nul | find /I "python.exe" >nul
if not errorlevel 1 (
    echo [INFO] Found running Python processes
    echo [ACTION] Sending termination signal to Python processes...
    taskkill /IM python.exe /T >nul 2>&1
    timeout /t 3 /nobreak >nul
    
    REM Check if processes are still running
    tasklist /FI "IMAGENAME eq python.exe" 2>nul | find /I "python.exe" >nul
    if not errorlevel 1 (
        echo [WARNING] Some processes did not respond to graceful shutdown
        echo [ACTION] Forcing termination...
        taskkill /F /IM python.exe /T >nul 2>&1
        timeout /t 2 /nobreak >nul
    )
    echo [SUCCESS] Python processes terminated
) else (
    echo [INFO] No Python processes found running
)

REM Stop any CMD windows that might be running CCC services
tasklist /FI "IMAGENAME eq cmd.exe" 2>nul | find /I "cmd.exe" >nul
if not errorlevel 1 (
    echo [INFO] Checking for CCC-related CMD processes...
    taskkill /F /IM cmd.exe /FI "WINDOWTITLE eq CCC-*" >nul 2>&1
    echo [SUCCESS] CCC CMD processes cleaned up
)

REM Clean up any temporary files from previous launches
echo [CLEANUP] Removing temporary files...
if exist temp_server.bat (
    del temp_server.bat >nul 2>&1
    echo [INFO] Removed temp_server.bat
)
if exist temp_lab.bat (
    del temp_lab.bat >nul 2>&1
    echo [INFO] Removed temp_lab.bat
)

REM Check for port conflicts
echo [SYSTEM] Checking for port conflicts...
netstat -an | find ":5111" >nul 2>&1
if not errorlevel 1 (
    echo [WARNING] Port 5111 may still be in use
    echo [ACTION] Waiting for port to be released...
    timeout /t 5 /nobreak >nul
)

netstat -an | find ":8080" >nul 2>&1
if not errorlevel 1 (
    echo [INFO] Port 8080 in use - will find alternative for lab
)

echo.
echo [SUCCESS] Shutdown sequence completed
echo.

REM Phase 2: System Verification
echo [PHASE 2] Verifying system readiness...
echo.

REM Check required files
echo [VERIFICATION] Checking system components...

if not exist "proxy_server.py" (
    echo [ERROR] proxy_server.py not found
    goto :error_exit
)

if not exist "resonant_loop_lab.html" (
    echo [ERROR] resonant_loop_lab.html not found  
    goto :error_exit
)

if not exist "requirements.txt" (
    echo [ERROR] requirements.txt not found
    goto :error_exit
)

echo [SUCCESS] All required components verified
echo.

REM Check and update dependencies
echo [SYSTEM] Updating dependencies...
pip install -r requirements.txt >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Some dependencies may not have updated properly
) else (
    echo [SUCCESS] Dependencies updated
)

REM Check environment configuration
if "%OPENAI_API_KEY%"=="" (
    echo [WARNING] OPENAI_API_KEY not found in system environment variables
    echo [INFO] This may cause server startup issues
    echo.
    echo [ACTION REQUIRED] Please set your OpenAI API Key as a system environment variable:
    echo   1. Open System Properties ^> Advanced ^> Environment Variables
    echo   2. Add new System Variable: OPENAI_API_KEY = your_api_key_here
    echo   3. Restart this command prompt to reload environment variables
    echo.
    echo [ALTERNATIVE] You can also set it for this session only:
    echo   set OPENAI_API_KEY=your_api_key_here
    echo.
) else (
    echo [SUCCESS] OPENAI_API_KEY found in system environment
    echo [INFO] API Key: %OPENAI_API_KEY:~0,8%... ^(truncated for security^)
)

echo.
echo [SUCCESS] System verification completed
echo.

REM Phase 3: Service Restart
echo [PHASE 3] Restarting services...
echo.

REM Prompt user for restart options
echo [OPTIONS] Select restart mode:
echo [1] Restart Server Only
echo [2] Restart Laboratory Only  
echo [3] Restart Both Services
echo [4] Cancel Restart
echo.
set /p "restart_choice=Enter your choice (1-4): "

if "%restart_choice%"=="1" goto :restart_server
if "%restart_choice%"=="2" goto :restart_lab
if "%restart_choice%"=="3" goto :restart_both
if "%restart_choice%"=="4" goto :cancel_restart

echo [ERROR] Invalid choice. Defaulting to restart both services.
goto :restart_both

:restart_server
echo [LAUNCH] Starting CCC Proxy Server...
call launch_server.bat
goto :end

:restart_lab
echo [LAUNCH] Starting Resonant Loop Laboratory...
call launch_lab.bat
goto :end

:restart_both
echo [LAUNCH] Starting both services...
call launch_all.bat
goto :end

:cancel_restart
echo [INFO] Restart cancelled by user
echo.
echo ===================================================
echo  VoidCat RDC - System Status: READY FOR MANUAL START
echo ===================================================
echo.
echo [OPTIONS] You can manually start services using:
echo   - launch_server.bat (Server only)
echo   - launch_lab.bat (Laboratory only)
echo   - launch_all.bat (Both services)
echo.
goto :end

:error_exit
echo.
echo ===================================================
echo  VoidCat RDC - System Status: RESTART FAILED
echo ===================================================
echo.
echo [ERROR] System restart failed
echo [INFO] Please check the error messages above
echo [SUGGESTION] Try running the individual launch scripts directly
echo.
pause
exit /b 1

:end
echo.
echo ===================================================
echo  VoidCat RDC - Restart Manager: OPERATION COMPLETE
echo ===================================================
echo.
echo Press any key to exit...
pause >nul
exit /b 0