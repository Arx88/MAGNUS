@echo off
echo @echo off > "%~dp0debug_start_bat.log"
echo [LOG] Automated start.bat started at %%TIME%% >> "%~dp0debug_start_bat.log"
setlocal

echo Iniciando MANUS-like System (automated)...

echo [LOG] Verificando Docker... >> "%~dp0debug_start_bat.log"
docker --version >nul 2>&1
if errorlevel 1 (
    echo Error: Docker no está instalado o no está ejecutándose.
    echo [LOG] Docker check FAILED. Exiting start.bat. >> "%~dp0debug_start_bat.log"
    echo Por favor, inicia Docker Desktop y vuelve a intentarlo.
    exit /b 1
) else (
    echo Docker check OK.
    echo [LOG] Docker check OK. >> "%~dp0debug_start_bat.log"
)

echo [LOG] Verificando si Ollama ya está en ejecución (port 11434)... >> "%~dp0debug_start_bat.log"
netstat -ano | findstr /R /C:"LISTENING" | findstr ":11434" >nul
if errorlevel 1 (
    echo Iniciando Ollama en segundo plano...
    echo [LOG] Ollama not found listening. Attempting 'start /B ollama serve'. >> "%~dp0debug_start_bat.log"
    start /B ollama serve
    echo [LOG] 'start /B ollama serve' command issued. >> "%~dp0debug_start_bat.log"
    echo [LOG] Esperando brevemente para que Ollama inicie... >> "%~dp0debug_start_bat.log"
    timeout /t 5 /nobreak >nul
) else (
    echo Ollama ya parece estar en ejecución.
    echo [LOG] Ollama already running or port in use. >> "%~dp0debug_start_bat.log"
)

echo [LOG] Creando red MCP... >> "%~dp0debug_start_bat.log"
docker network create mcp-network 2>nul
echo [LOG] Red MCP check/creation attempt done. >> "%~dp0debug_start_bat.log"

echo [LOG] Iniciando servicios con docker-compose en segundo plano... >> "%~dp0debug_start_bat.log"
docker-compose up -d
echo [LOG] 'docker-compose up -d' command issued. >> "%~dp0debug_start_bat.log"

echo.
echo Servicios del sistema MANUS-like (Docker, Ollama, docker-compose) iniciados en segundo plano.
echo Frontend deberia estar en: http://localhost:3000
echo Backend API deberia estar en: http://localhost:5000
echo [LOG] Automated start.bat finished at %%TIME%%. >> "%~dp0debug_start_bat.log"

endlocal
exit /b 0
