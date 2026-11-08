@echo off
setlocal
py -m pip install --upgrade pip
py -m pip install pyinstaller
py -m PyInstaller --noconfirm --clean --onefile --windowed --name MGU-Store-Installer app.py
if errorlevel 1 (
  echo Build failed.
  exit /b 1
)
echo.
echo Build complete: dist\MGU-Store-Installer.exe
endlocal
