@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion

:: ============================================================
:: eMMA Docker Script (Batch)
:: ============================================================
:: Usage: emma-docker.bat [start|stop|restart|logs|status|clean|build]
:: ============================================================

cd /d "%~dp0"

:: Farben (ANSI)
set "INFO=[INFO]"
set "OK=[OK]"
set "WARN=[WARN]"
set "ERR=[ERROR]"

:: Argumente pruefen
if "%1"=="" goto :start
if /i "%1"=="start" goto :start
if /i "%1"=="stop" goto :stop
if /i "%1"=="restart" goto :restart
if /i "%1"=="logs" goto :logs
if /i "%1"=="status" goto :status
if /i "%1"=="clean" goto :clean
if /i "%1"=="build" goto :build
if /i "%1"=="help" goto :help
if /i "%1"=="-h" goto :help
if /i "%1"=="--help" goto :help
goto :help

:banner
echo.
echo ============================================================
echo   eMMA Docker - Enterprise Multi-Model Agent Management
echo ============================================================
echo.
goto :eof

:help
call :banner
echo Usage: emma-docker.bat [COMMAND]
echo.
echo Commands:
echo   start     Startet eMMA mit Docker (Standard)
echo   build     Startet mit Rebuild der Images
echo   stop      Stoppt eMMA
echo   restart   Startet eMMA neu
echo   logs      Zeigt die Logs an
echo   status    Zeigt den Status der Container
echo   clean     Stoppt und entfernt alle Container/Volumes
echo   help      Zeigt diese Hilfe
echo.
goto :end

:check_docker
echo %INFO% Pruefe Docker...
docker info >nul 2>&1
if errorlevel 1 (
    echo %ERR% Docker laeuft nicht! Bitte Docker Desktop starten.
    exit /b 1
)
echo %OK% Docker laeuft
goto :eof

:init_env
if not exist ".env" (
    echo %INFO% Erstelle .env aus .env.example...
    if exist ".env.example" (
        copy ".env.example" ".env" >nul
        echo %OK% .env erstellt
    ) else (
        echo %WARN% .env.example nicht gefunden, erstelle minimale .env...
        (
            echo # eMMA Configuration
            echo ENVIRONMENT=development
            echo DEBUG=true
            echo SECRET_KEY=dev-secret-key-change-in-production
            echo DB_PASSWORD=emma_dev_password
            echo ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173
            echo LOG_LEVEL=DEBUG
        ) > ".env"
        echo %OK% Minimale .env erstellt
    )
) else (
    echo %INFO% .env existiert bereits
)
goto :eof

:clear_network_conflicts
echo %INFO% Pruefe auf Netzwerk-Konflikte...
for /f "tokens=*" %%n in ('docker network ls --format "{{.Name}}" 2^>nul') do (
    echo %%n | findstr /i "emma" >nul
    if not errorlevel 1 (
        echo %%n | findstr /i "emma-repo_emma-network" >nul
        if errorlevel 1 (
            echo %WARN% Entferne konfliktierendes Netzwerk: %%n
            docker network rm %%n >nul 2>&1
        )
    )
)
goto :eof

:start
call :banner
call :check_docker
if errorlevel 1 goto :end

call :init_env
call :clear_network_conflicts

echo %INFO% Starte eMMA...
docker-compose up -d

if errorlevel 1 (
    echo %ERR% Fehler beim Starten von eMMA
    goto :end
)

echo.
echo %OK% eMMA wurde gestartet!
echo.
timeout /t 3 /nobreak >nul
call :status
echo.
echo API:  http://localhost:8000
echo Docs: http://localhost:8000/docs
echo.
goto :end

:build
call :banner
call :check_docker
if errorlevel 1 goto :end

call :init_env
call :clear_network_conflicts

echo %INFO% Starte eMMA mit Rebuild...
docker-compose up -d --build

if errorlevel 1 (
    echo %ERR% Fehler beim Starten von eMMA
    goto :end
)

echo.
echo %OK% eMMA wurde gestartet!
echo.
timeout /t 3 /nobreak >nul
call :status
echo.
echo API:  http://localhost:8000
echo Docs: http://localhost:8000/docs
echo.
goto :end

:stop
call :banner
echo %INFO% Stoppe eMMA...
docker-compose down
echo %OK% eMMA wurde gestoppt
goto :end

:restart
call :stop
call :start
goto :end

:logs
echo %INFO% Zeige Logs (Ctrl+C zum Beenden)...
docker-compose logs -f
goto :end

:status
echo %INFO% Container-Status:
docker-compose ps
goto :end

:clean
call :banner
echo %WARN% Stoppe und entferne alle eMMA Container und Volumes...
docker-compose down -v --remove-orphans
echo %OK% Bereinigung abgeschlossen
goto :end

:end
endlocal
