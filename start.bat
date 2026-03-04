@echo off
REM ========================================================
REM ADI ANKASOFIA - BareMetalOS Hacker IDE Baslatıcı
REM ========================================================
echo.
echo *******************************************************
echo ADI ANKASOFIA - BareMetalOS Hacker IDE
echo *******************************************************
echo.
REM Python kontrolü
python --version >nul 2>&1
if errorlevel 1 (
echo HATA: Python bulunamadi!
echo Lutfen Python 3.8 veya ustunu yukleyin: https://python.org 
pause
exit /b 1
)
REM Port kontrolü (varsayilan: 8000)
set PORT=8000
set HOST=localhost
REM Proje dizinlerini olustur
if not exist "data" mkdir data
if not exist "logs" mkdir logs
if not exist "examples" mkdir examples
echo Proje yapisi kontrol ediliyor...
if not exist "ankasofia_server.py" (
echo HATA: ankasofia_server.py bulunamadi!
echo Lutfen proje dosyalarinin dogru dizinde oldugundan emin olun.
pause
exit /b 1
)
if not exist "ankasofia.html" (
echo HATA: ankasofia.html bulunamadi!
echo Lutfen proje dosyalarinin dogru dizinde oldugundan emin olun.
pause
exit /b 1
)
echo.
echo Proje Bilgileri:
echo -----------------------------
echo Calisma Dizini: %cd%
echo Python Versiyonu:
python --version
echo Sunucu Adresi: http://%HOST%:%PORT%
echo IDE Baslatiliyor...
echo -----------------------------
echo.
REM Gerekli Python kutuphanelerini kontrol et
echo Python kutuphaneleri kontrol ediliyor...
python -c "import http.server, socketserver, json, subprocess, os, threading, webbrowser, mimetypes, tempfile" 2>nul
if errorlevel 1 (
echo Gerekli kutuphaneler yukleniyor...
pip install -q --upgrade pip
)
REM Sunucuyu baslat (tarayici Python tarafindan acilacak)
echo Sunucu baslatiliyor...
echo IDE'ye erismek icin: http://%HOST%:%PORT%
echo Tarayici otomatik acilacak...
echo.
echo Cikmak icin Ctrl+C tuslarina basin
echo.
REM SADECE PYTHON SUNUCUSUNU BASLAT (tarayici ankasofia_server.py acacak)
python ankasofia_server.py --port %PORT%
if errorlevel 1 (
echo.
echo HATA: Sunucu baslatilamadi!
echo Port %PORT% kullanimda olabilir.
echo Farkli bir port denemek icin: start.bat 8080
pause
exit /b 1
)
pause