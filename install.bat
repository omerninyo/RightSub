@echo off
setlocal enabledelayedexpansion

echo ===================================================
echo     RightSub Windows Installer (CMD / PowerShell)
echo ===================================================
echo.

:: 1. Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [-] Python 3 is not detected in your PATH.
    echo [*] Please install Python 3.9+ from https://www.python.org/ or Microsoft Store.
    echo [*] Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('python --version') do set PY_VER=%%i
echo [✓] Detected: %PY_VER%

:: 2. Check FFmpeg (Warning only)
ffmpeg -version >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Note: ffmpeg is not currently in your PATH.
    echo     Subtitle extraction from video files requires FFmpeg.
    echo     You can install it easily with: winget install Gyan.FFmpeg
    echo.
) else (
    echo [✓] Detected: FFmpeg is available.
)

:: 3. Install Python dependencies
echo [*] Installing required Python packages from requirements.txt...
python -m pip install -q -r "%~dp0requirements.txt"
if %errorlevel% neq 0 (
    echo [-] Warning: Failed to install some dependencies. Please check network connection.
) else (
    echo [✓] Dependencies installed successfully.
)

:: 4. Register RightSub in Windows User PATH automatically via PowerShell
echo [*] Registering RightSub in your Windows User PATH...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$dir = '%~dp0'.TrimEnd('\'); $p = [Environment]::GetEnvironmentVariable('Path', 'User'); if ($p -notlike \"*$dir*\") { [Environment]::SetEnvironmentVariable('Path', \"$p;$dir\", 'User'); Write-Host '[✓] Added RightSub to Windows User PATH.' } else { Write-Host '[✓] RightSub is already in Windows User PATH.' }"

echo.
echo ===================================================
echo [✓] RightSub v1.5.0 is ready on Windows!
echo ===================================================
echo.
echo Quick Commands (open a new CMD or PowerShell window):
echo     rightsub                (Launch Interactive Wizard)
echo     rightsub setup          (Run Setup, Hooks ^& MCP Agent Wizard)
echo     rightsub mcp --install  (Connect to Claude, Antigravity, Cursor, Windsurf)
echo     rightsub auto "C:\path\to\movie.mkv"
echo.
pause
