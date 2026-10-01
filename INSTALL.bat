@echo off
cd /d "%~dp0"
python INSTALL.py || py INSTALL.py
pause
