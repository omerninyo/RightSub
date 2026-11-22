@echo off
where python >nul 2>&1
if %errorlevel% equ 0 (
    python "%~dp0rightsub.py" %*
    exit /b %errorlevel%
)
py -3 "%~dp0rightsub.py" %*
exit /b %errorlevel%
