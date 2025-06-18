@echo off
REM 1. Instalar pip y PyInstaller si no están
python -m ensurepip --upgrade
python -m pip install --upgrade pip setuptools wheel

REM 2. Instalar librerías necesarias
python -m pip install --upgrade ttkbootstrap selenium beautifulsoup4 Pillow requests

REM 3. Instalar PyInstaller si no está
python -m pip install --upgrade pyinstaller

REM 4. Limpiar compilaciones previas
if exist build rd /s /q build
if exist dist rd /s /q dist
if exist mercado_comparison.spec del /q mercado_comparison.spec

REM 5. Ejecutar PyInstaller para generar .exe
pyinstaller --noconfirm --onefile --windowed ^
--add-data "favoritos.py;." ^
--add-data "favoritos.db;." ^
--add-data "precios.db;." ^
--hidden-import=selenium.webdriver.chrome ^
--hidden-import=selenium.webdriver.chrome.options ^
--hidden-import=selenium.webdriver.common.by ^
--hidden-import=selenium.webdriver.support.ui ^
--hidden-import=selenium.webdriver.support.expected_conditions ^
mercado_comparison.py

pause
