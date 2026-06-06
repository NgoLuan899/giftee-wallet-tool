@echo off
setlocal

echo Installing Python dependencies...
python -m pip install -r "%~dp0requirements.txt"
if errorlevel 1 goto error

echo.
echo Installing Node dependencies...
cd /d "%~dp0"
npm install
if errorlevel 1 goto error

echo.
echo Done. Run run_giftee_desktop_tool_qt.bat to start the app.
pause
exit /b 0

:error
echo.
echo Install failed. Check Python, Node.js, npm and internet connection.
pause
exit /b 1
