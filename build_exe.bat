@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ======================================
echo Stock Query V13.6 - Windows EXE Builder
echo ======================================
where py >nul 2>&1
if %errorlevel%==0 (
  set "PY=py"
) else (
  set "PY=python"
)
%PY% --version
if errorlevel 1 goto fail
%PY% -m pip install --upgrade pyinstaller yfinance pandas openpyxl twstock
if errorlevel 1 goto fail
if exist "stock_1.ico" (
  %PY% -m PyInstaller --noconfirm --clean --onefile --windowed --name "StockQuery_V13_6" --icon "stock_1.ico" --add-data "stock_1.ico;." --collect-all yfinance --collect-all twstock stock_query_v13_6.py
) else (
  %PY% -m PyInstaller --noconfirm --clean --onefile --windowed --name "StockQuery_V13_6" --collect-all yfinance --collect-all twstock stock_query_v13_6.py
)
if errorlevel 1 goto fail
echo.
echo SUCCESS: dist\StockQuery_V13_6.exe
pause
exit /b 0
:fail
echo.
echo Build failed. Please review the error messages above.
pause
exit /b 1
