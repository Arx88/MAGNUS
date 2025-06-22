#!/usr/bin/env python3
"""
MANUS-like System - Instalador Automático Universal
==================================================

Este script instala y configura automáticamente todo el sistema MANUS-like
en Windows, Linux y macOS con un solo comando.

Uso:
    python setup.py

El script detectará automáticamente tu sistema operativo e instalará:
- Docker y Docker Compose
- Node.js y npm
- Python y dependencias
- Ollama
- Supabase CLI
- Configurará la base de datos
- Iniciará todos los servicios

Requisitos mínimos:
- Python 3.8+
- Conexión a internet
- Permisos de administrador (se solicitarán automáticamente)
"""

import os
import sys
import platform
import subprocess
import json
import time
import urllib.request
import zipfile
import shutil
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple

class Colors:
    """Colores para output en terminal"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class SystemInstaller:
    """Instalador automático del sistema MANUS-like"""
    
    def __init__(self):
        self.system = platform.system().lower()
        self.arch = platform.machine().lower()

        # Initial Python check before anything else
        if not self._check_python_installation():
            self.print_step("Critical Python setup issue detected. Please see the messages above.", "error")
            sys.exit(1)

        self.is_admin = self._check_admin()
        self.install_dir = Path.home() / "manus-system"
        self.config = {}
        
        # URLs de descarga
        self.urls = {
            "ollama": {
                "windows": "https://ollama.ai/download/windows",
                "linux": "https://ollama.ai/download/linux",
                "darwin": "https://ollama.ai/download/mac"
            },
            "docker": {
                "windows": "https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe",
                "linux": "https://get.docker.com",
                "darwin": "https://desktop.docker.com/mac/main/amd64/Docker.dmg"
            },
            "node": {
                "windows": "https://nodejs.org/dist/v20.10.0/node-v20.10.0-x64.msi",
                "linux": "https://nodejs.org/dist/v20.10.0/node-v20.10.0-linux-x64.tar.xz",
                "darwin": "https://nodejs.org/dist/v20.10.0/node-v20.10.0.pkg"
            }
        }

    def _check_python_installation(self) -> bool:
        """Checks if Python is correctly installed and accessible."""
        try:
            # Check if Python executable is found and is not the Windows Store stub
            python_exe = sys.executable
            if not python_exe or "py.exe" in python_exe.lower() or "python.exe" not in python_exe.lower():
                 # This condition might indicate the Windows Store stub or an unusual setup
                pass # Further checks will be done

            # Try running a simple command
            process = subprocess.run([python_exe, "--version"], capture_output=True, text=True, check=False)

            if process.returncode != 0 or "Python was not found" in process.stdout or "Python was not found" in process.stderr:
                self.print_step("Python execution failed or Windows Store version detected.", "error")
                self.print_step("Please ensure you have a standard Python installation (e.g., from python.org).", "warning")
                self.print_step("Follow these steps:", "info")
                self.print_step("1. Install Python: Download from https://www.python.org/downloads/", "info")
                self.print_step("2. Add to PATH: Ensure Python and Scripts directories are in your PATH environment variable.", "info")
                self.print_step("   Example: C:\\PythonXX and C:\\PythonXX\\Scripts", "info")
                self.print_step("3. Disable App Execution Alias (Windows):", "info")
                self.print_step("   - Go to 'Settings' > 'Apps' > 'Advanced app settings' (or 'Apps & features' > 'App execution aliases').", "info")
                self.print_step("   - Turn OFF 'App Installer' for 'python.exe' and 'python3.exe'.", "info")
                self.print_step("   - If you see 'python.exe' or 'python3.exe' pointing to the Microsoft Store, disable them.", "info")
                self.print_step("After fixing, please re-run this script.", "info")
                return False

            self.print_step(f"Python version check successful: {process.stdout.strip()}", "success")
            return True

        except Exception as e:
            self.print_step(f"Error during Python check: {e}", "error")
            self.print_step("This script requires a working Python 3.8+ installation.", "warning")
            self.print_step("Please ensure Python is correctly installed and added to your system PATH.", "info")
            return False

    def _check_admin(self) -> bool:
        """Verifica si se ejecuta con permisos de administrador"""
        try:
            if self.system == "windows":
                import ctypes
                return ctypes.windll.shell32.IsUserAnAdmin()
            else:
                return os.geteuid() == 0
        except:
            return False
    
    def _run_as_admin(self):
        """Ejecuta el script con permisos de administrador"""
        if self.system == "windows":
            import ctypes
            hinstance = ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, " ".join(sys.argv), None, 1
            )
            if hinstance <= 32:
                # Error codes are described at https://docs.microsoft.com/en-us/windows/win32/api/shellapi/nf-shellapi-shellexecutew
                error_code = hinstance
                error_message = f"Falló el intento de elevar privilegios (ShellExecuteW código de error: {error_code}).\n"
                if error_code == 0: # ERROR_BAD_FORMAT
                    error_message += "El archivo .exe no es válido (ERROR_BAD_FORMAT)."
                elif error_code == 2: # ERROR_FILE_NOT_FOUND
                    error_message += "El archivo especificado no fue encontrado (ERROR_FILE_NOT_FOUND)."
                elif error_code == 3: # ERROR_PATH_NOT_FOUND
                    error_message += "La ruta especificada no fue encontrada (ERROR_PATH_NOT_FOUND)."
                elif error_code == 5: # ERROR_ACCESS_DENIED
                    error_message += "Acceso denegado (ERROR_ACCESS_DENIED). ¿Canceló el diálogo UAC?"
                elif error_code == 8: # ERROR_NOT_ENOUGH_MEMORY
                    error_message += "No hay suficiente memoria para completar la operación."
                elif error_code == 31: # SE_ERR_NOASSOC
                    error_message += "No hay una aplicación asociada con la extensión de archivo especificada."
                else:
                    try:
                        # Attempt to get a Windows system error message
                        win_error = ctypes.WinError(error_code)
                        error_message += f"Error del sistema: {win_error.strerror} (Código: {win_error.winerror})"
                    except Exception: # Fallback if WinError fails for some reason
                        error_message += "Error desconocido al intentar obtener detalles del error de Windows."

                self.print_step(error_message, "error")
                self.print_step("La instalación no puede continuar sin permisos de administrador.", "error")
                sys.exit(1) # Exit the non-elevated script immediately if elevation failed to launch
        else:
            # For Linux/macOS, if execvp fails, it will raise an OSError.
            # If it succeeds, it replaces the current process, so code here won't run.
            try:
                os.execvp("sudo", ["sudo", sys.executable] + sys.argv)
            except OSError as e:
                self.print_step(f"Falló el intento de elevar privilegios con sudo: {e}", "error")
                self.print_step("La instalación no puede continuar sin permisos de administrador.", "error")
                sys.exit(1)
    
    def print_step(self, message: str, step_type: str = "info"):
        """Imprime un paso con formato"""
        colors = {
            "info": Colors.OKBLUE,
            "success": Colors.OKGREEN,
            "warning": Colors.WARNING,
            "error": Colors.FAIL,
            "header": Colors.HEADER
        }
        color = colors.get(step_type, Colors.OKBLUE)
        print(f"{color}[MANUS SETUP] {message}{Colors.ENDC}")
    
    def run_command(self, command: str, shell: bool = True, check: bool = True) -> Tuple[bool, str]:
        """Ejecuta un comando y retorna el resultado"""
        try:
            if isinstance(command, str):
                cmd = command if shell else command.split()
            else:
                cmd = command
            
            result = subprocess.run(
                cmd,
                shell=shell,
                capture_output=True,
                text=True,
                check=check
            )
            return True, result.stdout
        except subprocess.CalledProcessError as e:
            return False, e.stderr
        except Exception as e:
            return False, str(e)
    
    def download_file(self, url: str, destination: Path) -> bool:
        """Descarga un archivo"""
        try:
            self.print_step(f"Descargando {url}")
            urllib.request.urlretrieve(url, destination)
            return True
        except Exception as e:
            self.print_step(f"Error descargando {url}: {e}", "error")
            return False
    
    def install_winget_packages(self, packages: List[str]) -> bool:
        """Instala paquetes usando winget en Windows"""
        if self.system != "windows":
            return True
        
        for package in packages:
            self.print_step(f"Instalando {package} con winget")
            success, output = self.run_command(f"winget install {package} --accept-package-agreements --accept-source-agreements")
            if not success:
                self.print_step(f"Error instalando {package}: {output}", "error")
                return False
        return True
    
    def install_docker(self) -> bool:
        """Instala Docker"""
        self.print_step("Instalando Docker...")
        
        if self.system == "windows":
            # Usar winget para instalar Docker Desktop
            return self.install_winget_packages(["Docker.DockerDesktop"])
        
        elif self.system == "linux":
            # Instalar Docker en Linux
            commands = [
                "curl -fsSL https://get.docker.com -o get-docker.sh",
                "sh get-docker.sh",
                "usermod -aG docker $USER",
                "systemctl enable docker",
                "systemctl start docker"
            ]
            
            for cmd in commands:
                success, output = self.run_command(cmd)
                if not success:
                    self.print_step(f"Error ejecutando: {cmd}", "error")
                    return False
        
        elif self.system == "darwin":
            # Usar Homebrew en macOS
            success, _ = self.run_command("brew install --cask docker")
            if not success:
                self.print_step("Error instalando Docker en macOS", "error")
                return False
        
        # Verificar instalación
        time.sleep(10)  # Esperar a que Docker se inicie
        success, _ = self.run_command("docker --version")
        if success:
            self.print_step("Docker instalado correctamente", "success")
            return True
        else:
            self.print_step("Error verificando Docker", "error")
            return False
    
    def install_nodejs(self) -> bool:
        """Instala Node.js"""
        self.print_step("Instalando Node.js...")
        
        if self.system == "windows":
            return self.install_winget_packages(["OpenJS.NodeJS"])
        
        elif self.system == "linux":
            commands = [
                "curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -",
                "apt-get install -y nodejs"
            ]
            
            for cmd in commands:
                success, output = self.run_command(cmd)
                if not success:
                    self.print_step(f"Error ejecutando: {cmd}", "error")
                    return False
        
        elif self.system == "darwin":
            success, _ = self.run_command("brew install node")
            if not success:
                return False
        
        # Verificar instalación
        success, _ = self.run_command("node --version")
        if success:
            self.print_step("Node.js instalado correctamente", "success")
            return True
        else:
            self.print_step("Error verificando Node.js", "error")
            return False
    
    def install_ollama(self) -> bool:
        """Instala Ollama"""
        self.print_step("Instalando Ollama...")
        
        if self.system == "windows":
            # Descargar e instalar Ollama para Windows
            temp_dir = Path(tempfile.gettempdir())
            installer_path = temp_dir / "ollama-installer.exe"
            
            if self.download_file(self.urls["ollama"]["windows"], installer_path):
                success, _ = self.run_command(f'"{installer_path}" /S')
                if success:
                    self.print_step("Ollama instalado correctamente", "success")
                    return True
        
        elif self.system == "linux":
            success, _ = self.run_command("curl -fsSL https://ollama.ai/install.sh | sh")
            if success:
                # Iniciar servicio
                self.run_command("systemctl enable ollama")
                self.run_command("systemctl start ollama")
                self.print_step("Ollama instalado correctamente", "success")
                return True
        
        elif self.system == "darwin":
            success, _ = self.run_command("brew install ollama")
            if success:
                self.print_step("Ollama instalado correctamente", "success")
                return True
        
        self.print_step("Error instalando Ollama", "error")
        return False
    
    def install_python_dependencies(self) -> bool:
        """Instala dependencias de Python"""
        self.print_step("Instalando dependencias de Python...")
        
        # Actualizar pip
        success, _ = self.run_command(f"{sys.executable} -m pip install --upgrade pip")
        if not success:
            self.print_step("Error actualizando pip", "error")
            return False
        
        # Instalar dependencias del backend
        backend_deps = [
            "flask==2.3.3",
            "flask-cors==4.0.0",
            "flask-socketio==5.3.6",
            "supabase==2.0.0",
            "requests==2.31.0",
            "python-dotenv==1.0.0",
            "docker==6.1.3",
            "asyncio",
            "websockets==11.0.3",
            "pydantic==2.5.0",
            "python-multipart==0.0.6",
            "bcrypt==4.1.2",
            "pyjwt==2.8.0"
        ]
        
        for dep in backend_deps:
            success, output = self.run_command(f"{sys.executable} -m pip install {dep}")
            if not success:
                self.print_step(f"Error instalando {dep}: {output}", "error")
                return False
        
        self.print_step("Dependencias de Python instaladas", "success")
        return True
    
    def setup_project_structure(self) -> bool:
        """Configura la estructura del proyecto"""
        self.print_step("Configurando estructura del proyecto...")
        
        try:
            # Crear directorio principal
            self.install_dir.mkdir(exist_ok=True)
            
            # Crear subdirectorios
            dirs = [
                "backend",
                "frontend", 
                "data",
                "logs",
                "config",
                "docker",
                "scripts"
            ]
            
            for dir_name in dirs:
                (self.install_dir / dir_name).mkdir(exist_ok=True)
            
            self.print_step("Estructura del proyecto creada", "success")
            return True
            
        except Exception as e:
            self.print_step(f"Error creando estructura: {e}", "error")
            return False
    
    def copy_project_files(self) -> bool:
        """Copia los archivos del proyecto"""
        self.print_step("Copiando archivos del proyecto...")
        
        try:
            # Obtener directorio actual (donde está este script)
            current_dir = Path(__file__).parent
            
            # Copiar backend
            if (current_dir / "manus-backend").exists():
                shutil.copytree(
                    current_dir / "manus-backend",
                    self.install_dir / "backend",
                    dirs_exist_ok=True
                )
            
            # Copiar frontend
            if (current_dir / "manus-frontend").exists():
                shutil.copytree(
                    current_dir / "manus-frontend", 
                    self.install_dir / "frontend",
                    dirs_exist_ok=True
                )
            
            # Copiar archivos de configuración
            config_files = [
                "database_schema.md",
                "supabase_init.sql", 
                "initial_data.sql",
                "mcp_integration_plan.md"
            ]
            
            for file_name in config_files:
                if (current_dir / file_name).exists():
                    shutil.copy2(
                        current_dir / file_name,
                        self.install_dir / "config" / file_name
                    )
            
            self.print_step("Archivos del proyecto copiados", "success")
            return True
            
        except Exception as e:
            self.print_step(f"Error copiando archivos: {e}", "error")
            return False
    
    def create_docker_compose(self) -> bool:
        """Crea el archivo docker-compose.yml"""
        self.print_step("Creando configuración Docker...")
        
        docker_compose_content = """version: '3.8'

services:
  # Base de datos PostgreSQL
  postgres:
    image: postgres:15
    container_name: manus-postgres
    environment:
      POSTGRES_DB: manus_db
      POSTGRES_USER: manus_user
      POSTGRES_PASSWORD: manus_password_2024
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./config/supabase_init.sql:/docker-entrypoint-initdb.d/01-init.sql
      - ./config/initial_data.sql:/docker-entrypoint-initdb.d/02-data.sql
    networks:
      - manus-network
    restart: unless-stopped

  # Backend Flask
  backend:
    build: 
      context: ./backend
      dockerfile: Dockerfile
    container_name: manus-backend
    environment:
      - FLASK_ENV=production
      - DATABASE_URL=postgresql://manus_user:manus_password_2024@postgres:5432/manus_db
      - OLLAMA_HOST=host.docker.internal:11434
      - SECRET_KEY=manus_secret_key_2024_super_secure
      - CORS_ORIGINS=http://localhost:3000,http://localhost:5173
    ports:
      - "5000:5000"
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
      - /var/run/docker.sock:/var/run/docker.sock
    depends_on:
      - postgres
    networks:
      - manus-network
      - mcp-network
    restart: unless-stopped

  # Frontend React
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: manus-frontend
    environment:
      - REACT_APP_API_URL=http://localhost:5000
      - REACT_APP_WS_URL=ws://localhost:5000
    ports:
      - "3000:3000"
    depends_on:
      - backend
    networks:
      - manus-network
    restart: unless-stopped

  # Redis para cache y sesiones
  redis:
    image: redis:7-alpine
    container_name: manus-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    networks:
      - manus-network
    restart: unless-stopped

  # Nginx como proxy reverso
  nginx:
    image: nginx:alpine
    container_name: manus-nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./docker/nginx.conf:/etc/nginx/nginx.conf
      - ./docker/ssl:/etc/nginx/ssl
    depends_on:
      - frontend
      - backend
    networks:
      - manus-network
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:

networks:
  manus-network:
    driver: bridge
  mcp-network:
    driver: bridge
    external: true
"""
        
        try:
            docker_compose_path = self.install_dir / "docker-compose.yml"
            docker_compose_path.write_text(docker_compose_content)
            
            self.print_step("Docker Compose configurado", "success")
            return True
            
        except Exception as e:
            self.print_step(f"Error creando docker-compose.yml: {e}", "error")
            return False
    
    def create_dockerfiles(self) -> bool:
        """Crea los Dockerfiles necesarios"""
        self.print_step("Creando Dockerfiles...")
        
        # Dockerfile para backend
        backend_dockerfile = """FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \\
    curl \\
    docker.io \\
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements
COPY requirements.txt .

# Instalar dependencias Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código fuente
COPY . .

# Exponer puerto
EXPOSE 5000

# Comando de inicio
CMD ["python", "src/main.py"]
"""
        
        # Dockerfile para frontend
        frontend_dockerfile = """FROM node:20-alpine as builder

WORKDIR /app

# Copiar package files
COPY package*.json ./

# Instalar dependencias
RUN npm ci

# Copiar código fuente
COPY . .

# Build de producción
RUN npm run build

# Imagen de producción con nginx
FROM nginx:alpine

# Copiar build
COPY --from=builder /app/dist /usr/share/nginx/html

# Copiar configuración nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Exponer puerto
EXPOSE 3000

CMD ["nginx", "-g", "daemon off;"]
"""
        
        # Configuración nginx para frontend
        nginx_conf = """server {
    listen 3000;
    server_name localhost;
    
    location / {
        root /usr/share/nginx/html;
        index index.html index.htm;
        try_files $uri $uri/ /index.html;
    }
    
    location /api {
        proxy_pass http://backend:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
"""
        
        try:
            # Crear Dockerfile del backend
            (self.install_dir / "backend" / "Dockerfile").write_text(backend_dockerfile)
            
            # Crear Dockerfile del frontend
            (self.install_dir / "frontend" / "Dockerfile").write_text(frontend_dockerfile)
            (self.install_dir / "frontend" / "nginx.conf").write_text(nginx_conf)
            
            self.print_step("Dockerfiles creados", "success")
            return True
            
        except Exception as e:
            self.print_step(f"Error creando Dockerfiles: {e}", "error")
            return False
    
    def create_environment_files(self) -> bool:
        """Crea archivos de configuración de entorno"""
        self.print_step("Creando archivos de configuración...")
        
        # .env para backend
        backend_env = """# Configuración del Backend MANUS-like
FLASK_ENV=production
FLASK_DEBUG=False

# Base de datos
DATABASE_URL=postgresql://manus_user:manus_password_2024@localhost:5432/manus_db

# Ollama
OLLAMA_HOST=localhost:11434
OLLAMA_TIMEOUT=30

# Seguridad
SECRET_KEY=manus_secret_key_2024_super_secure
JWT_SECRET_KEY=jwt_secret_key_2024_super_secure

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# MCP
MCP_NETWORK=mcp-network
MCP_BASE_PORT=8000

# Logs
LOG_LEVEL=INFO
LOG_FILE=logs/manus.log

# Archivos
UPLOAD_FOLDER=data/uploads
MAX_CONTENT_LENGTH=100MB
"""
        
        # .env para frontend
        frontend_env = """# Configuración del Frontend MANUS-like
REACT_APP_API_URL=http://localhost:5000
REACT_APP_WS_URL=ws://localhost:5000
REACT_APP_NAME=MANUS-like System
REACT_APP_VERSION=1.0.0
"""
        
        try:
            # Crear archivos .env
            (self.install_dir / "backend" / ".env").write_text(backend_env)
            (self.install_dir / "frontend" / ".env").write_text(frontend_env)
            
            self.print_step("Archivos de configuración creados", "success")
            return True
            
        except Exception as e:
            self.print_step(f"Error creando archivos de configuración: {e}", "error")
            return False
    
    def create_startup_scripts(self) -> bool:
        """Crea scripts de inicio"""
        self.print_step("Creando scripts de inicio...")
        
        # Script de inicio para Windows
        windows_start = """@echo off
echo Iniciando MANUS-like System...

echo Verificando Docker...
docker --version >nul 2>&1
if errorlevel 1 (
    echo Error: Docker no está instalado o no está ejecutándose
    echo Por favor, inicia Docker Desktop
    pause
    exit /b 1
)

echo Verificando Ollama...
ollama --version >nul 2>&1
if errorlevel 1 (
    echo Error: Ollama no está instalado
    pause
    exit /b 1
)

echo Iniciando Ollama...
start /B ollama serve

echo Esperando a que Ollama esté listo...
timeout /t 5 /nobreak >nul

echo Descargando modelo por defecto...
ollama pull llama2

echo Creando red MCP...
docker network create mcp-network 2>nul

echo Iniciando servicios...
docker-compose up -d

echo Sistema iniciado correctamente!
echo Frontend: http://localhost:3000
echo Backend API: http://localhost:5000
echo.
echo Presiona cualquier tecla para abrir el navegador...
pause >nul
start http://localhost:3000
"""
        
        # Script de inicio para Linux/macOS
        unix_start = """#!/bin/bash

echo "Iniciando MANUS-like System..."

# Verificar Docker
if ! command -v docker &> /dev/null; then
    echo "Error: Docker no está instalado"
    exit 1
fi

# Verificar Ollama
if ! command -v ollama &> /dev/null; then
    echo "Error: Ollama no está instalado"
    exit 1
fi

# Iniciar Ollama
echo "Iniciando Ollama..."
ollama serve &
OLLAMA_PID=$!

# Esperar a que Ollama esté listo
echo "Esperando a que Ollama esté listo..."
sleep 5

# Descargar modelo por defecto
echo "Descargando modelo por defecto..."
ollama pull llama2

# Crear red MCP
echo "Creando red MCP..."
docker network create mcp-network 2>/dev/null || true

# Iniciar servicios
echo "Iniciando servicios..."
docker-compose up -d

echo "Sistema iniciado correctamente!"
echo "Frontend: http://localhost:3000"
echo "Backend API: http://localhost:5000"

# Abrir navegador
if command -v xdg-open &> /dev/null; then
    xdg-open http://localhost:3000
elif command -v open &> /dev/null; then
    open http://localhost:3000
fi
"""
        
        # Script de parada
        stop_script = """#!/bin/bash
echo "Deteniendo MANUS-like System..."
docker-compose down
echo "Sistema detenido."
"""
        
        try:
            # Crear scripts
            scripts_dir = self.install_dir / "scripts"
            
            if self.system == "windows":
                (scripts_dir / "start.bat").write_text(windows_start)
                (scripts_dir / "stop.bat").write_text("docker-compose down\npause")
            else:
                start_script_path = scripts_dir / "start.sh"
                stop_script_path = scripts_dir / "stop.sh"
                
                start_script_path.write_text(unix_start)
                stop_script_path.write_text(stop_script)
                
                # Hacer ejecutables
                os.chmod(start_script_path, 0o755)
                os.chmod(stop_script_path, 0o755)
            
            self.print_step("Scripts de inicio creados", "success")
            return True
            
        except Exception as e:
            self.print_step(f"Error creando scripts: {e}", "error")
            return False
    
    def install_ollama_models(self) -> bool:
        """Instala modelos básicos de Ollama"""
        self.print_step("Instalando modelos de Ollama...")
        
        # Iniciar Ollama si no está ejecutándose
        self.run_command("ollama serve", check=False)
        time.sleep(5)
        
        # Modelos básicos a instalar
        models = ["llama2", "codellama:7b", "mistral"]
        
        for model in models:
            self.print_step(f"Descargando modelo {model}...")
            success, output = self.run_command(f"ollama pull {model}")
            if success:
                self.print_step(f"Modelo {model} instalado", "success")
            else:
                self.print_step(f"Error instalando {model}: {output}", "warning")
        
        return True
    
    def setup_database(self) -> bool:
        """Configura la base de datos"""
        self.print_step("Configurando base de datos...")
        
        try:
            # Iniciar PostgreSQL con Docker
            success, _ = self.run_command("docker run -d --name manus-postgres-setup -e POSTGRES_DB=manus_db -e POSTGRES_USER=manus_user -e POSTGRES_PASSWORD=manus_password_2024 -p 5432:5432 postgres:15")
            
            if success:
                time.sleep(10)  # Esperar a que PostgreSQL se inicie
                
                # Ejecutar scripts de inicialización
                init_script = self.install_dir / "config" / "supabase_init.sql"
                data_script = self.install_dir / "config" / "initial_data.sql"
                
                if init_script.exists():
                    self.run_command(f"docker exec -i manus-postgres-setup psql -U manus_user -d manus_db < {init_script}")
                
                if data_script.exists():
                    self.run_command(f"docker exec -i manus-postgres-setup psql -U manus_user -d manus_db < {data_script}")
                
                # Detener contenedor temporal
                self.run_command("docker stop manus-postgres-setup")
                self.run_command("docker rm manus-postgres-setup")
                
                self.print_step("Base de datos configurada", "success")
                return True
            
        except Exception as e:
            self.print_step(f"Error configurando base de datos: {e}", "error")
        
        return False
    
    def install_frontend_dependencies(self) -> bool:
        """Instala dependencias del frontend"""
        self.print_step("Instalando dependencias del frontend...")
        
        try:
            frontend_dir = self.install_dir / "frontend"
            
            # Cambiar al directorio del frontend
            original_dir = os.getcwd()
            os.chdir(frontend_dir)
            
            # Instalar dependencias
            success, output = self.run_command("npm install")
            
            # Volver al directorio original
            os.chdir(original_dir)
            
            if success:
                self.print_step("Dependencias del frontend instaladas", "success")
                return True
            else:
                self.print_step(f"Error instalando dependencias: {output}", "error")
                return False
                
        except Exception as e:
            self.print_step(f"Error: {e}", "error")
            return False
    
    def create_desktop_shortcut(self) -> bool:
        """Crea acceso directo en el escritorio"""
        self.print_step("Creando acceso directo...")
        
        try:
            if self.system == "windows":
                # Crear acceso directo en Windows
                desktop = Path.home() / "Desktop"
                shortcut_path = desktop / "MANUS System.lnk"
                
                # Usar PowerShell para crear el acceso directo
                ps_script = f"""
$WshShell = New-Object -comObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("{shortcut_path}")
$Shortcut.TargetPath = "{self.install_dir / 'scripts' / 'start.bat'}"
$Shortcut.WorkingDirectory = "{self.install_dir}"
$Shortcut.IconLocation = "{self.install_dir / 'scripts' / 'start.bat'}"
$Shortcut.Description = "MANUS-like AI Agent System"
$Shortcut.Save()
"""
                
                with tempfile.NamedTemporaryFile(mode='w', suffix='.ps1', delete=False) as f:
                    f.write(ps_script)
                    ps_file = f.name
                
                self.run_command(f"powershell -ExecutionPolicy Bypass -File {ps_file}")
                os.unlink(ps_file)
            
            elif self.system == "linux":
                # Crear archivo .desktop en Linux
                desktop = Path.home() / "Desktop"
                desktop.mkdir(exist_ok=True)
                
                desktop_file = desktop / "manus-system.desktop"
                desktop_content = f"""[Desktop Entry]
Version=1.0
Type=Application
Name=MANUS System
Comment=MANUS-like AI Agent System
Exec={self.install_dir / 'scripts' / 'start.sh'}
Icon={self.install_dir / 'icon.png'}
Path={self.install_dir}
Terminal=true
StartupNotify=true
"""
                desktop_file.write_text(desktop_content)
                os.chmod(desktop_file, 0o755)
            
            self.print_step("Acceso directo creado", "success")
            return True
            
        except Exception as e:
            self.print_step(f"Error creando acceso directo: {e}", "warning")
            return True  # No es crítico
    
    def run_installation(self) -> bool:
        """Ejecuta la instalación completa"""
        self.print_step("=== INSTALADOR MANUS-LIKE SYSTEM ===", "header")
        self.print_step(f"Sistema detectado: {self.system} ({self.arch})", "info")
        self.print_step(f"Directorio de instalación: {self.install_dir}", "info")

        log_file_path = None
        if self.is_admin: # Ensure log_file_path is defined if admin
            log_file_path = Path(tempfile.gettempdir()) / "manus_setup_elevated.log"

        # Helper function for logging within this method
        def _log_admin_action(message: str):
            if self.is_admin and log_file_path:
                try:
                    with open(log_file_path, "a", encoding="utf-8") as log_f:
                        log_f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [run_installation] {message}\n")
                except Exception as e:
                    self.print_step(f"Warning: Could not write to elevated log file {log_file_path}: {e}", "warning")
        
        # Verificar permisos de administrador - This check is actually done in main() now before calling run_installation.
        # If not self.is_admin, main() would have handled re-launching.
        # So, by the time we are here, self.is_admin should be True if elevation was required.
        # However, if the script was initially launched as admin, this is the first point is_admin is effectively used by run_installation.
        if not self.is_admin:
            # This case should ideally not be hit if main() logic is correct.
            # If it is, it means the script was called in a way that bypassed main's admin check for run_installation.
            self.print_step("Error crítico: run_installation() llamada sin permisos de administrador.", "error")
            _log_admin_action("CRITICAL: run_installation() called without admin rights.")
            return False

        _log_admin_action("Admin permissions confirmed for installation steps.")
        
        steps = [
            ("Configurando estructura del proyecto", self.setup_project_structure),
            ("Copiando archivos del proyecto", self.copy_project_files),
            ("Instalando Docker", self.install_docker),
            ("Instalando Node.js", self.install_nodejs),
            ("Instalando Ollama", self.install_ollama),
            ("Instalando dependencias Python", self.install_python_dependencies),
            ("Instalando dependencias frontend", self.install_frontend_dependencies),
            ("Creando configuración Docker", self.create_docker_compose),
            ("Creando Dockerfiles", self.create_dockerfiles),
            ("Creando archivos de configuración", self.create_environment_files),
            ("Creando scripts de inicio", self.create_startup_scripts),
            ("Instalando modelos Ollama", self.install_ollama_models),
            ("Configurando base de datos", self.setup_database),
            ("Creando acceso directo", self.create_desktop_shortcut)
        ]
        
        total_steps = len(steps)
        
        for i, (description, step_function) in enumerate(steps, 1):
            self.print_step(f"[{i}/{total_steps}] {description}", "info")
            _log_admin_action(f"Starting step [{i}/{total_steps}]: {description}")

            step_success = step_function()
            
            if not step_success:
                self.print_step(f"Error en el paso: {description}", "error")
                _log_admin_action(f"FAILED step [{i}/{total_steps}]: {description}")
                return False
            
            _log_admin_action(f"COMPLETED step [{i}/{total_steps}]: {description}")
            # Mostrar progreso
            progress = (i / total_steps) * 100
            self.print_step(f"Progreso: {progress:.1f}%", "info")
        
        _log_admin_action("All installation steps completed successfully.")
        return True
    
    def show_completion_message(self):
        """Muestra mensaje de finalización"""
        self.print_step("=== INSTALACIÓN COMPLETADA ===", "header")
        self.print_step("", "info")
        self.print_step("¡El sistema MANUS-like ha sido instalado exitosamente!", "success")
        self.print_step("", "info")
        self.print_step("Para iniciar el sistema:", "info")
        
        if self.system == "windows":
            self.print_step(f"  - Ejecuta: {self.install_dir / 'scripts' / 'start.bat'}", "info")
            self.print_step("  - O usa el acceso directo del escritorio", "info")
        else:
            self.print_step(f"  - Ejecuta: {self.install_dir / 'scripts' / 'start.sh'}", "info")
        
        self.print_step("", "info")
        self.print_step("URLs de acceso:", "info")
        self.print_step("  - Frontend: http://localhost:3000", "info")
        self.print_step("  - Backend API: http://localhost:5000", "info")
        self.print_step("  - Documentación: http://localhost:3000/docs", "info")
        self.print_step("", "info")
        self.print_step("Credenciales por defecto:", "info")
        self.print_step("  - Usuario: admin@manus.local", "info")
        self.print_step("  - Contraseña: admin123", "info")
        self.print_step("", "info")
        self.print_step("¡Disfruta tu sistema MANUS-like!", "success")

def main():
    """Función principal"""
    installer = SystemInstaller() # Python check happens in __init__
    
    # Early log for elevated process
    if installer.is_admin:
        log_file_path = Path(tempfile.gettempdir()) / "manus_setup_elevated.log"
        try:
            with open(log_file_path, "a", encoding="utf-8") as log_file:
                log_file.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Elevated script instance started. Python: {sys.executable}\n")
        except Exception as e:
            installer.print_step(f"Warning: Could not write to elevated log file {log_file_path}: {e}", "warning")

    try:
        # Check for admin rights and re-launch if necessary
        if not installer.is_admin:
            installer.print_step("Se requieren permisos de administrador.", "warning")
            installer.print_step("Intentando re-lanzar con privilegios elevados...", "info")
            installer._run_as_admin() # This will exit if ShellExecuteW fails, or replace process on Unix
            # If _run_as_admin on Windows returns (because ShellExecuteW > 32), it means it *attempted* to start the new process.
            # The current non-admin script should now inform the user and exit.
            installer.print_step("Solicitud de elevación enviada. Por favor, observe la nueva ventana de la consola para ver el progreso.", "info")
            installer.print_step("Esta ventana se cerrará en unos segundos...", "info")
            time.sleep(5) # Give user time to read
            sys.exit(0) # Gracefully exit the non-elevated script

        # If we reach here, we are running with admin rights (either initially or after elevation)
        if installer.is_admin and 'log_file_path' in locals(): # Log before running installation
             with open(log_file_path, "a", encoding="utf-8") as log_file:
                log_file.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Admin rights confirmed. Calling run_installation().\n")

        if installer.run_installation(): # This is the main execution path for the admin instance
            installer.show_completion_message()
            if installer.is_admin and 'log_file_path' in locals():
                with open(log_file_path, "a", encoding="utf-8") as log_file:
                    log_file.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Installation successful.\n")
            
            if input("\n¿Deseas iniciar el sistema ahora? (s/n): ").lower() in ['s', 'y', 'yes', 'sí']:
                if installer.system == "windows":
                    os.system(f'"{installer.install_dir / "scripts" / "start.bat"}"')
                else:
                    os.system(f'"{installer.install_dir / "scripts" / "start.sh"}"')
        else:
            # This message is from the ELEVATED script if run_installation() returns False
            installer.print_step("La instalación falló (proceso elevado).", "error")
            if installer.is_admin and 'log_file_path' in locals():
                with open(log_file_path, "a", encoding="utf-8") as log_file:
                    log_file.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] run_installation() returned False.\n")
            sys.exit(1)
            
    except KeyboardInterrupt:
        installer.print_step("Instalación cancelada por el usuario.", "warning")
        if 'log_file_path' in locals() and installer.is_admin:
             with open(log_file_path, "a", encoding="utf-8") as log_file:
                log_file.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Installation cancelled by user.\n")
        if installer.is_admin: # Keep console open on error
            input("Presione Enter para salir...")
        sys.exit(1)
    except Exception as e:
        installer.print_step(f"Error inesperado: {e}", "error")
        if 'log_file_path' in locals() and installer.is_admin: # Redundant check for log_file_path, but safe
            with open(log_file_path, "a", encoding="utf-8") as log_file:
                log_file.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Unexpected error: {e}\n")
        if installer.is_admin: # Keep console open on error
            input("Presione Enter para salir...")
        sys.exit(1)

    # For successful completion, the input() prompt for starting the system already keeps the window open.
    # So, we only need the explicit input() pause in the error paths above for the admin instance.

if __name__ == "__main__":
    main()

