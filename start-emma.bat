@echo off
title eMMA - Enterprise Monitoring App
cd /d "%~dp0"
powershell -ExecutionPolicy Bypass -File "start-emma.ps1" %*
pause
