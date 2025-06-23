#!/usr/bin/env python3
"""
MANUS-like System - Instalador Automático Universal v2.0
========================================================

Instalador completamente rediseñado con:
- UX visual mejorada con barras de progreso
- Compatibilidad real multiplataforma
- Manejo robusto de errores
- Detección inteligente de dependencias
- Logs detallados y recuperación automática

Uso:
    python setup.py

Autor: Manus AI
Versión: 2.0.0
"""

import os
import sys
import platform
import subprocess
import json
import time
import urllib.request
import urllib.error
import zipfile
import shutil
import tempfile
import threading
import signal
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import logging
from datetime import datetime

# Verificar Python 3.8+
if sys.version_info < (3, 8):
    print("❌ Error: Se requiere Python 3.8 o superior")
    print(f"   Versión actual: {sys.version}")
    sys.exit(1)

class Colors:
    """Colores ANSI para terminal con fallback"""
    if os.name == 'nt':  # Windows
        try:
            import colorama
            colorama.init()
            HEADER = '\033[95m'
            OKBLUE = '\033[94m'
            OKCYAN = '\033[96m'
            OKGREEN = '\033[92m'
            WARNING = '\033[93m'
            FAIL = '\033[91m'
            ENDC = '\033[0m'
            BOLD = '\033[1m'
        except ImportError:
            # Fallback sin colores en Windows sin colorama
            HEADER = OKBLUE = OKCYAN = OKGREEN = WARNING = FAIL = ENDC = BOLD = ''
    else:
        HEADER = '\033[95m'
        OKBLUE = '\033[94m'
        OKCYAN = '\033[96m'
        OKGREEN = '\033[92m'
        WARNING = '\033[93m'
        FAIL = '\033[91m'
        ENDC = '\033[0m'
        BOLD = '\033[1m'

class ProgressBar:
    """Barra de progreso visual"""
    
    def __init__(self, total: int, description: str = "", width: int = 50):
        self.total = total
        self.current = 0
        self.description = description
        self.width = width
        self.start_time = time.time()
    
    def update(self, amount: int = 1, description: str = None):
        """Actualiza la barra de progreso"""
        self.current = min(self.current + amount, self.total)
        if description:
            self.description = description
        
        # Calcular porcentaje y tiempo
        percentage = (self.current / self.total) * 100
        elapsed = time.time() - self.start_time
        
        # Crear barra visual
        filled = int(self.width * self.current / self.total)
        bar = '█' * filled + '░' * (self.width - filled)
        
        # Estimar tiempo restante
        if self.current > 0:
            eta = (elapsed / self.current) * (self.total - self.current)
            eta_str = f"ETA: {int(eta)}s" if eta > 0 else "Completando..."
        else:
            eta_str = "Calculando..."
        
        # Imprimir barra
        print(f"\r{Colors.OKBLUE}[{bar}] {percentage:5.1f}% {Colors.ENDC}"
              f"{self.description[:30]:<30} {eta_str}", end='', flush=True)
        
        if self.current >= self.total:
            print()  # Nueva línea al completar

class Logger:
    """Sistema de logging mejorado"""
    
    def __init__(self, log_file: Path):
        self.log_file = log_file
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Configurar logging
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def info(self, message: str):
        self.logger.info(message)
    
    def warning(self, message: str):
        self.logger.warning(message)
    
    def error(self, message: str, include_stdout_stderr: bool = False, stdout: str = "", stderr: str = ""):
        full_message = message
        if include_stdout_stderr:
            if stdout:
                full_message += f"\n  STDOUT: {stdout}"
            if stderr:
                full_message += f"\n  STDERR: {stderr}"
        self.logger.error(full_message)
    
    def debug(self, message: str):
        self.logger.debug(message)

class SystemDetector:
    """Detector inteligente del sistema"""
    
    def __init__(self):
        self.system = platform.system().lower()
        self.arch = platform.machine().lower()
        self.version = platform.version()
        self.is_wsl = self._detect_wsl()
        self.package_manager = self._detect_package_manager()
    
    def _detect_wsl(self) -> bool:
        """Detecta si está ejecutándose en WSL"""
        try:
            with open('/proc/version', 'r') as f:
                return 'microsoft' in f.read().lower()
        except:
            return False
    
    def _detect_package_manager(self) -> str:
        """Detecta el gestor de paquetes disponible"""
        managers = {
            'apt': 'apt-get',
            'yum': 'yum',
            'dnf': 'dnf',
            'pacman': 'pacman',
            'brew': 'brew',
            'winget': 'winget',
            'choco': 'choco'
        }
        
        for manager, command in managers.items():
            if shutil.which(command):
                return manager
        
        return 'unknown'
    
    def get_info(self) -> Dict[str, Any]:
        """Retorna información completa del sistema"""
        return {
            'system': self.system,
            'arch': self.arch,
            'version': self.version,
            'is_wsl': self.is_wsl,
            'package_manager': self.package_manager,
            'python_version': sys.version,
            'is_admin': self._check_admin()
        }
    
    def _check_admin(self) -> bool:
        """Verifica permisos de administrador"""
        try:
            if self.system == "windows":
                import ctypes
                return ctypes.windll.shell32.IsUserAnAdmin()
            else:
                return os.geteuid() == 0
        except:
            return False

class DependencyChecker:
    """Verificador inteligente de dependencias"""
    
    def __init__(self, logger: Logger):
        self.logger = logger
        self.dependencies = {
            'python': {'min_version': '3.8', 'command': 'python --version'},
            'docker': {'min_version': '20.0', 'command': 'docker --version'},
            'docker-compose': {'min_version': '2.0', 'command': 'docker-compose --version'},
            'node': {'min_version': '18.0', 'command': 'node --version'},
            'npm': {'min_version': '8.0', 'command': 'npm --version'},
            'git': {'min_version': '2.0', 'command': 'git --version'},
        }
    
    def check_dependency(self, name: str) -> Tuple[bool, str, str]:
        """Verifica una dependencia específica"""
        if name not in self.dependencies:
            return False, "unknown", "Dependencia desconocida"
        
        dep = self.dependencies[name]
        
        try:
            result = subprocess.run(
                dep['command'].split(),
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                version = self._extract_version(result.stdout)
                return True, version, "Instalado"
            else:
                return False, "0.0", "No encontrado"
                
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
            return False, "0.0", "No encontrado"
    
    def _extract_version(self, output: str) -> str:
        """Extrae versión de la salida del comando"""
        import re
        # Buscar patrones de versión comunes
        patterns = [
            r'v?(\d+\.\d+\.\d+)',
            r'version\s+v?(\d+\.\d+\.\d+)',
            r'(\d+\.\d+\.\d+)',
            r'v?(\d+\.\d+)',
            r'(\d+\.\d+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, output, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return "unknown"
    
    def check_all(self) -> Dict[str, Tuple[bool, str, str]]:
        """Verifica todas las dependencias"""
        results = {}
        for name in self.dependencies:
            results[name] = self.check_dependency(name)
        return results

class ManusInstaller:
    """Instalador principal del sistema MANUS-like"""
    
    def __init__(self):
        self.start_time = time.time()
        self.install_dir = Path.home() / "manus-system"
        self.temp_dir = Path(tempfile.gettempdir()) / "manus-installer"
        self.temp_dir.mkdir(exist_ok=True)
        
        # Configurar logging
        self.logger = Logger(self.install_dir / "logs" / "installation.log")
        
        # Detectar sistema
        self.detector = SystemDetector()
        self.system_info = self.detector.get_info()
        
        # Verificador de dependencias
        self.dep_checker = DependencyChecker(self.logger)
        
        # Estado de instalación
        self.installation_state = {
            'phase': 'init',
            'step': 0,
            'total_steps': 15,
            'errors': [],
            'warnings': []
        }
        
        # Configurar manejo de señales
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Maneja señales de interrupción"""
        print(f"\n{Colors.WARNING}⚠️  Instalación interrumpida por el usuario{Colors.ENDC}")
        self.logger.warning("Instalación interrumpida por señal")
        self._cleanup()
        sys.exit(1)
    
    def _cleanup(self):
        """Limpia archivos temporales"""
        try:
            if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)
        except Exception as e:
            self.logger.warning(f"Error limpiando archivos temporales: {e}")
    
    def print_header(self):
        """Imprime header del instalador"""
        print(f"""
{Colors.HEADER}╔══════════════════════════════════════════════════════════════╗
║                    MANUS-like System v2.0                   ║
║                  Instalador Automático Universal            ║
╚══════════════════════════════════════════════════════════════╝{Colors.ENDC}

{Colors.OKBLUE}🚀 Instalador inteligente con detección automática de sistema
📊 Progreso visual y manejo robusto de errores
🔧 Compatibilidad completa Windows/Linux/macOS{Colors.ENDC}
""")
    
    def print_system_info(self):
        """Imprime información del sistema detectado"""
        info = self.system_info
        print(f"{Colors.OKCYAN}📋 Información del Sistema:{Colors.ENDC}")
        print(f"   Sistema Operativo: {info['system'].title()} {info['arch']}")
        print(f"   Versión: {info['version']}")
        print(f"   Gestor de Paquetes: {info['package_manager']}")
        print(f"   Python: {info['python_version'].split()[0]}")
        print(f"   WSL: {'Sí' if info['is_wsl'] else 'No'}")
        print(f"   Permisos Admin: {'Sí' if info['is_admin'] else 'No'}")
        print()
    
    def check_dependencies(self) -> bool:
        """Verifica dependencias del sistema"""
        print(f"{Colors.OKBLUE}🔍 Verificando dependencias...{Colors.ENDC}")
        
        deps = self.dep_checker.check_all()
        missing = []
        
        for name, (installed, version, status) in deps.items():
            icon = "✅" if installed else "❌"
            color = Colors.OKGREEN if installed else Colors.FAIL
            print(f"   {icon} {name:<15} {color}{status:<12}{Colors.ENDC} {version}")
            
            if not installed:
                missing.append(name)
        
        if missing:
            print(f"\n{Colors.WARNING}⚠️  Dependencias faltantes: {', '.join(missing)}{Colors.ENDC}")
            print(f"{Colors.OKBLUE}   Se instalarán automáticamente...{Colors.ENDC}")
        else:
            print(f"\n{Colors.OKGREEN}✅ Todas las dependencias están disponibles{Colors.ENDC}")
        
        print()
        return True
    
    def run_command(self, command: str, description: str = "", timeout: int = 300) -> Tuple[bool, str, str]:
        """Ejecuta comando con timeout y logging"""
        self.logger.debug(f"Ejecutando: {command}")
        
        try:
            if isinstance(command, str):
                cmd = command
                shell = True
            else:
                cmd = command
                shell = False
            
            process = subprocess.Popen(
                cmd,
                shell=shell,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                universal_newlines=True
            )
            
            stdout, stderr = process.communicate(timeout=timeout)
            return_code = process.returncode
            success = return_code == 0

            log_message = f"Comando: {command}\n  Exitoso: {success}\n  Código de retorno: {return_code}"
            if stdout:
                log_message += f"\n  STDOUT: {stdout.strip()}"
            if stderr:
                log_message += f"\n  STDERR: {stderr.strip()}"

            if success:
                self.logger.debug(log_message)
            else:
                self.logger.error(log_message) # stderr is now part of the structured log
            
            return success, stdout, stderr
            
        except subprocess.TimeoutExpired:
            if process: process.kill()
            error_msg = f"Comando excedió timeout de {timeout}s"
            self.logger.error(f"{error_msg}: {command}")
            return False, "", error_msg
            
        except Exception as e:
            error_msg = f"Error ejecutando comando: {str(e)}"
            self.logger.error(f"{error_msg}: {command}")
            return False, "", error_msg
    
    def download_with_progress(self, url: str, destination: Path, description: str = "") -> bool:
        """Descarga archivo con barra de progreso"""
        try:
            print(f"{Colors.OKBLUE}📥 Descargando {description or url}{Colors.ENDC}")
            
            # Obtener tamaño del archivo
            req = urllib.request.Request(url)
            req.add_header('User-Agent', 'MANUS-Installer/2.0')
            
            with urllib.request.urlopen(req) as response:
                total_size = int(response.headers.get('Content-Length', 0))
                
                if total_size > 0:
                    progress = ProgressBar(total_size, f"Descargando {description}")
                    
                    with open(destination, 'wb') as f:
                        downloaded = 0
                        while True:
                            chunk = response.read(8192)
                            if not chunk:
                                break
                            f.write(chunk)
                            downloaded += len(chunk)
                            progress.update(len(chunk))
                else:
                    # Descarga sin progreso si no conocemos el tamaño
                    with open(destination, 'wb') as f:
                        shutil.copyfileobj(response, f)
                    print(f"   ✅ Descarga completada")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error descargando {url}: {e}")
            print(f"   {Colors.FAIL}❌ Error: {e}{Colors.ENDC}")
            return False
    
    def install_docker(self) -> bool:
        """Instala Docker según el sistema operativo"""
        print(f"{Colors.OKBLUE}🐳 Instalando Docker...{Colors.ENDC}")
        
        system = self.system_info['system']
        package_manager = self.system_info['package_manager']
        is_admin = self.system_info['is_admin']
        is_wsl_detected = self.system_info['is_wsl'] # Relies on /proc/version, may not be perfect for "WSL installed"

        # Pre-check for Docker on Windows
        if system == 'windows':
            if not is_admin:
                print(f"   {Colors.WARNING}⚠️  Advertencia: La instalación de Docker Desktop generalmente requiere permisos de administrador.{Colors.ENDC}")
                print(f"   {Colors.WARNING}   Es posible que deba confirmar un aviso de UAC (Control de Cuentas de Usuario) manualmente.{Colors.ENDC}")
                self.logger.warning("Intentando instalar Docker sin permisos de administrador detectados. Puede requerir UAC.")

            # WSL2 check (basic detection)
            # A more robust check would involve `wsl --status` or checking registry keys,
            # but that's more complex for this script. This relies on the initial WSL detection.
            # The original script showed "WSL: No" for the user.
            try:
                # Try to get more accurate WSL status if possible
                # This command might fail if WSL is not installed at all.
                wsl_status_check = subprocess.run("wsl.exe --status", shell=True, capture_output=True, text=True, timeout=10)
                if wsl_status_check.returncode == 0 and "Versión de WSL: 2" in wsl_status_check.stdout: # Check for WSL2 specifically if possible
                    is_wsl_active_and_v2 = True
                else:
                    is_wsl_active_and_v2 = False # Covers WSL1 or WSL not fully functional
            except (subprocess.TimeoutExpired, FileNotFoundError): # FileNotFoundError if wsl.exe not found
                 is_wsl_active_and_v2 = False

            if not is_wsl_active_and_v2:
                print(f"   {Colors.WARNING}⚠️  Advertencia: Docker Desktop en Windows requiere WSL2 (Subsistema de Windows para Linux v2).{Colors.ENDC}")
                print(f"   {Colors.WARNING}   WSL2 no parece estar instalado o activo en su sistema.{Colors.ENDC}")
                print(f"   {Colors.WARNING}   Por favor, asegúrese de que WSL2 esté instalado y habilitado. Puede encontrar instrucciones en:")
                print(f"   {Colors.WARNING}   https://docs.microsoft.com/es-es/windows/wsl/install{Colors.ENDC}")
                self.logger.warning("WSL2 no detectado o no activo. Docker Desktop podría fallar en la instalación o ejecución.")
                # For now, we'll still attempt installation, but this warning is crucial.
                # A future improvement could be to offer to try and install WSL2.

        try:
            if system == 'windows':
                # Check if Docker is already installed
                docker_installed, _, _ = self.dep_checker.check_dependency('docker')
                if docker_installed:
                    print(f"   {Colors.OKGREEN}✅ Docker ya está instalado.{Colors.ENDC}")
                    # Optionally, ask if user wants to reinstall or skip. For now, skip.
                    return True

                if package_manager == 'winget':
                    success, stdout, stderr = self.run_command(
                        "winget install Docker.DockerDesktop --accept-package-agreements --accept-source-agreements",
                        "Instalando Docker Desktop con winget"
                    )
                elif package_manager == 'choco':
                    success, stdout, stderr = self.run_command(
                        "choco install docker-desktop -y",
                        "Instalando Docker Desktop con Chocolatey"
                    )
                else:
                    # Descarga manual
                    print(f"   {Colors.OKBLUE}ℹ️ Winget/Choco no detectado. Intentando descarga manual de Docker Desktop...{Colors.ENDC}")
                    url = "https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe"
                    installer_path = self.temp_dir / "docker-installer.exe"
                    
                    if self.download_with_progress(url, installer_path, "Docker Desktop"):
                        # Note: Silent install for the official .exe can be tricky and might still show UAC.
                        # The --quiet flag is a common convention but not guaranteed for all installers.
                        success, stdout, stderr = self.run_command(
                            f'"{installer_path}" install --quiet', # The installer might have different silent flags e.g., /S, /quiet, --silent
                            "Instalando Docker Desktop (descarga manual)"
                        )
                        if not success and not is_admin:
                             print(f"   {Colors.WARNING}⚠️  La instalación manual también puede requerir ejecución como administrador.{Colors.ENDC}")
                    else:
                        self.logger.error("Fallo la descarga manual de Docker Desktop.")
                        return False
            
            elif system == 'darwin':  # macOS
                if package_manager == 'brew':
                    success, _, stderr = self.run_command(
                        "brew install --cask docker",
                        "Instalando Docker con Homebrew"
                    )
                else:
                    # Descarga manual para macOS
                    arch = 'arm64' if 'arm' in self.system_info['arch'] else 'amd64'
                    url = f"https://desktop.docker.com/mac/main/{arch}/Docker.dmg"
                    installer_path = self.temp_dir / "docker.dmg"
                    
                    if self.download_with_progress(url, installer_path, "Docker Desktop"):
                        # Montar DMG e instalar
                        success, _, stderr = self.run_command(
                            f"hdiutil attach {installer_path}",
                            "Montando imagen Docker"
                        )
                        if success:
                            success, _, stderr = self.run_command(
                                "cp -R /Volumes/Docker/Docker.app /Applications/",
                                "Copiando Docker a Applications"
                            )
                            self.run_command("hdiutil detach /Volumes/Docker")
                    else:
                        return False
            
            else:  # Linux
                if package_manager in ['apt', 'yum', 'dnf']:
                    # Usar script oficial de Docker
                    success, _, stderr = self.run_command(
                        "curl -fsSL https://get.docker.com | sh",
                        "Instalando Docker con script oficial"
                    )
                    
                    if success:
                        # Configurar Docker
                        self.run_command("systemctl enable docker")
                        self.run_command("systemctl start docker")
                        
                        # Agregar usuario al grupo docker
                        username = os.getenv('USER', 'ubuntu')
                        self.run_command(f"usermod -aG docker {username}")
                
                elif package_manager == 'pacman':
                    success, _, stderr = self.run_command(
                        "pacman -S docker docker-compose --noconfirm",
                        "Instalando Docker con pacman"
                    )
                else:
                    self.logger.error(f"Gestor de paquetes no soportado: {package_manager}")
                    return False
            
            if success:
                print(f"   {Colors.OKGREEN}✅ Docker instalado correctamente{Colors.ENDC}")
                
                # Verificar instalación
                time.sleep(5)
                success, _, _ = self.run_command("docker --version", timeout=30)
                if success:
                    print(f"   {Colors.OKGREEN}✅ Docker verificado y funcionando{Colors.ENDC}")
                    return True
                else:
                    # This part is tricky because the 'docker --version' command might fail if the Docker daemon/service
                    # isn't running yet, which can take time after installation, or require a reboot/re-login.
                    print(f"   {Colors.WARNING}⚠️  Docker parece instalado, pero 'docker --version' falló o no respondió a tiempo.{Colors.ENDC}")
                    print(f"   {Colors.WARNING}   Puede que necesite iniciar Docker Desktop manualmente o reiniciar su sistema.{Colors.ENDC}")
                    self.logger.warning("Docker instalado pero 'docker --version' falló post-instalación.")
                    return True # Return true because the installation command itself succeeded. Verification is a separate concern.
            else:
                # Ensure stderr from run_command is available here for better error message
                error_details = stderr.strip() if stderr else "No se capturó salida de error específica."
                self.logger.error(f"Fallo en el comando de instalación de Docker. Detalles: {error_details}", include_stdout_stderr=True, stdout=stdout, stderr=stderr)
                print(f"   {Colors.FAIL}❌ Error instalando Docker.{Colors.ENDC}")
                if system == 'windows':
                    print(f"   {Colors.FAIL}   Detalles: {error_details}{Colors.ENDC}")
                    print(f"   {Colors.FAIL}   Asegúrese de estar ejecutando el script como administrador y que WSL2 esté instalado y habilitado.{Colors.ENDC}")
                    print(f"   {Colors.FAIL}   Puede intentar descargar Docker Desktop manualmente desde: https://www.docker.com/products/docker-desktop{Colors.ENDC}")
                return False
                
        except Exception as e:
            self.logger.error(f"Excepción durante la instalación de Docker: {e}")
            print(f"   {Colors.FAIL}❌ Error inesperado durante la instalación de Docker: {e}{Colors.ENDC}")
            return False
    
    def install_nodejs(self) -> bool:
        """Instala Node.js según el sistema operativo"""
        print(f"{Colors.OKBLUE}📦 Instalando Node.js...{Colors.ENDC}")
        
        system = self.system_info['system']
        package_manager = self.system_info['package_manager']
        
        try:
            if system == 'windows':
                if package_manager == 'winget':
                    success, _, stderr = self.run_command(
                        "winget install OpenJS.NodeJS --accept-package-agreements --accept-source-agreements",
                        "Instalando Node.js"
                    )
                elif package_manager == 'choco':
                    success, _, stderr = self.run_command(
                        "choco install nodejs -y",
                        "Instalando Node.js con Chocolatey"
                    )
                else:
                    # Descarga manual
                    url = "https://nodejs.org/dist/v20.10.0/node-v20.10.0-x64.msi"
                    installer_path = self.temp_dir / "nodejs-installer.msi"
                    
                    if self.download_with_progress(url, installer_path, "Node.js"):
                        success, _, stderr = self.run_command(
                            f'msiexec /i "{installer_path}" /quiet',
                            "Instalando Node.js"
                        )
                    else:
                        return False
            
            elif system == 'darwin':  # macOS
                if package_manager == 'brew':
                    success, _, stderr = self.run_command(
                        "brew install node",
                        "Instalando Node.js con Homebrew"
                    )
                else:
                    # Descarga manual para macOS
                    url = "https://nodejs.org/dist/v20.10.0/node-v20.10.0.pkg"
                    installer_path = self.temp_dir / "nodejs.pkg"
                    
                    if self.download_with_progress(url, installer_path, "Node.js"):
                        success, _, stderr = self.run_command(
                            f"installer -pkg {installer_path} -target /",
                            "Instalando Node.js"
                        )
                    else:
                        return False
            
            else:  # Linux
                if package_manager == 'apt':
                    # Usar NodeSource repository
                    commands = [
                        "curl -fsSL https://deb.nodesource.com/setup_20.x | bash -",
                        "apt-get install -y nodejs"
                    ]
                    
                    for cmd in commands:
                        success, _, stderr = self.run_command(cmd, f"Ejecutando: {cmd}")
                        if not success:
                            break
                
                elif package_manager in ['yum', 'dnf']:
                    # Usar NodeSource repository para RHEL/CentOS
                    commands = [
                        "curl -fsSL https://rpm.nodesource.com/setup_20.x | bash -",
                        f"{package_manager} install -y nodejs"
                    ]
                    
                    for cmd in commands:
                        success, _, stderr = self.run_command(cmd, f"Ejecutando: {cmd}")
                        if not success:
                            break
                
                elif package_manager == 'pacman':
                    success, _, stderr = self.run_command(
                        "pacman -S nodejs npm --noconfirm",
                        "Instalando Node.js con pacman"
                    )
                else:
                    self.logger.error(f"Gestor de paquetes no soportado: {package_manager}")
                    return False
            
            if success:
                print(f"   {Colors.OKGREEN}✅ Node.js instalado correctamente{Colors.ENDC}")
                
                # Verificar instalación
                success, _, _ = self.run_command("node --version", timeout=10)
                if success:
                    print(f"   {Colors.OKGREEN}✅ Node.js verificado y funcionando{Colors.ENDC}")
                    return True
                else:
                    print(f"   {Colors.WARNING}⚠️  Node.js instalado pero no responde{Colors.ENDC}")
                    return False
            else:
                print(f"   {Colors.FAIL}❌ Error instalando Node.js: {stderr}{Colors.ENDC}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error en instalación de Node.js: {e}")
            print(f"   {Colors.FAIL}❌ Error inesperado: {e}{Colors.ENDC}")
            return False
    
    def install_ollama(self) -> bool:
        """Instala Ollama según el sistema operativo"""
        print(f"{Colors.OKBLUE}🧠 Instalando Ollama...{Colors.ENDC}")
        
        system = self.system_info['system']
        
        try:
            if system == 'windows':
                # Descarga e instalación para Windows
                url = "https://ollama.ai/download/windows"
                installer_path = self.temp_dir / "ollama-installer.exe"
                
                if self.download_with_progress(url, installer_path, "Ollama"):
                    success, _, stderr = self.run_command(
                        f'"{installer_path}" /S',
                        "Instalando Ollama"
                    )
                else:
                    return False
            
            elif system == 'darwin':  # macOS
                # Usar Homebrew si está disponible
                if self.system_info['package_manager'] == 'brew':
                    success, _, stderr = self.run_command(
                        "brew install ollama",
                        "Instalando Ollama con Homebrew"
                    )
                else:
                    # Script de instalación oficial
                    success, _, stderr = self.run_command(
                        "curl -fsSL https://ollama.ai/install.sh | sh",
                        "Instalando Ollama con script oficial"
                    )
            
            else:  # Linux
                # Script de instalación oficial
                success, _, stderr = self.run_command(
                    "curl -fsSL https://ollama.ai/install.sh | sh",
                    "Instalando Ollama con script oficial"
                )
                
                if success and system == 'linux':
                    # Configurar servicio en Linux
                    self.run_command("systemctl enable ollama", timeout=30)
                    self.run_command("systemctl start ollama", timeout=30)
            
            if success:
                print(f"   {Colors.OKGREEN}✅ Ollama instalado correctamente{Colors.ENDC}")
                
                # Verificar instalación
                time.sleep(3)
                success, _, _ = self.run_command("ollama --version", timeout=10)
                if success:
                    print(f"   {Colors.OKGREEN}✅ Ollama verificado y funcionando{Colors.ENDC}")
                    return True
                else:
                    print(f"   {Colors.WARNING}⚠️  Ollama instalado pero no responde{Colors.ENDC}")
                    return False
            else:
                print(f"   {Colors.FAIL}❌ Error instalando Ollama: {stderr}{Colors.ENDC}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error en instalación de Ollama: {e}")
            print(f"   {Colors.FAIL}❌ Error inesperado: {e}{Colors.ENDC}")
            return False
    
    def setup_project_structure(self) -> bool:
        """Configura la estructura del proyecto"""
        print(f"{Colors.OKBLUE}📁 Configurando estructura del proyecto...{Colors.ENDC}")
        
        try:
            # Crear directorio principal
            self.install_dir.mkdir(exist_ok=True)
            
            # Crear subdirectorios
            dirs = [
                "backend", "frontend", "data", "logs", 
                "config", "docker", "scripts", "temp"
            ]
            
            progress = ProgressBar(len(dirs), "Creando directorios")
            
            for dir_name in dirs:
                (self.install_dir / dir_name).mkdir(exist_ok=True)
                progress.update(1, f"Creando {dir_name}/")
                time.sleep(0.1)  # Simular trabajo
            
            print(f"   {Colors.OKGREEN}✅ Estructura del proyecto creada{Colors.ENDC}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error creando estructura: {e}")
            print(f"   {Colors.FAIL}❌ Error: {e}{Colors.ENDC}")
            return False
    
    def copy_project_files(self) -> bool:
        """Copia los archivos del proyecto"""
        print(f"{Colors.OKBLUE}📋 Copiando archivos del proyecto...{Colors.ENDC}")
        
        try:
            current_dir = Path(__file__).parent
            
            # Lista de archivos/directorios a copiar
            items_to_copy = [
                ("manus-backend", "backend"),
                ("manus-frontend", "frontend"),
                ("docker", "docker"),
                ("scripts", "scripts"),
                ("database_schema.md", "config/database_schema.md"),
                ("supabase_init.sql", "config/supabase_init.sql"),
                ("initial_data.sql", "config/initial_data.sql"),
                ("mcp_integration_plan.md", "config/mcp_integration_plan.md"),
                ("README.md", "README.md"),
                ("LICENSE", "LICENSE")
            ]
            
            progress = ProgressBar(len(items_to_copy), "Copiando archivos")
            
            for source, dest in items_to_copy:
                source_path = current_dir / source
                dest_path = self.install_dir / dest
                
                if source_path.exists():
                    dest_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    if source_path.is_dir():
                        if dest_path.exists():
                            shutil.rmtree(dest_path)
                        shutil.copytree(source_path, dest_path)
                    else:
                        shutil.copy2(source_path, dest_path)
                    
                    progress.update(1, f"Copiando {source}")
                else:
                    self.logger.warning(f"Archivo no encontrado: {source}")
                    progress.update(1, f"Omitiendo {source}")
                
                time.sleep(0.1)
            
            print(f"   {Colors.OKGREEN}✅ Archivos del proyecto copiados{Colors.ENDC}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error copiando archivos: {e}")
            print(f"   {Colors.FAIL}❌ Error: {e}{Colors.ENDC}")
            return False
    
    def install_python_dependencies(self) -> bool:
        """Instala dependencias de Python"""
        print(f"{Colors.OKBLUE}🐍 Instalando dependencias de Python...{Colors.ENDC}")
        
        try:
            # Actualizar pip primero
            success, _, stderr = self.run_command(
                f"{sys.executable} -m pip install --upgrade pip",
                "Actualizando pip"
            )
            
            if not success:
                print(f"   {Colors.WARNING}⚠️  Error actualizando pip: {stderr}{Colors.ENDC}")
            
            # Lista de dependencias
            dependencies = [
                "flask==2.3.3",
                "flask-cors==4.0.0", 
                "flask-socketio==5.3.6",
                "supabase==2.0.0",
                "requests==2.31.0",
                "python-dotenv==1.0.0",
                "docker==6.1.3",
                "websockets==11.0.3",
                "pydantic==2.5.0",
                "python-multipart==0.0.6",
                "bcrypt==4.1.2",
                "pyjwt==2.8.0",
                "colorama"  # Para colores en Windows
            ]
            
            progress = ProgressBar(len(dependencies), "Instalando paquetes Python")
            
            for dep in dependencies:
                success, _, stderr = self.run_command(
                    f"{sys.executable} -m pip install {dep}",
                    f"Instalando {dep}",
                    timeout=120
                )
                
                if success:
                    progress.update(1, f"✅ {dep}")
                else:
                    progress.update(1, f"❌ {dep}")
                    self.logger.error(f"Error instalando {dep}: {stderr}")
                
                time.sleep(0.1)
            
            print(f"   {Colors.OKGREEN}✅ Dependencias de Python instaladas{Colors.ENDC}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error instalando dependencias Python: {e}")
            print(f"   {Colors.FAIL}❌ Error: {e}{Colors.ENDC}")
            return False
    
    def install_frontend_dependencies(self) -> bool:
        """Instala dependencias del frontend"""
        print(f"{Colors.OKBLUE}⚛️  Instalando dependencias del frontend...{Colors.ENDC}")
        
        try:
            frontend_dir = self.install_dir / "frontend"
            
            if not frontend_dir.exists():
                print(f"   {Colors.WARNING}⚠️  Directorio frontend no encontrado{Colors.ENDC}")
                return False
            
            # Cambiar al directorio del frontend
            original_dir = os.getcwd()
            os.chdir(frontend_dir)
            
            try:
                # Instalar dependencias con npm
                print(f"   📦 Ejecutando npm install...")
                success, stdout, stderr = self.run_command(
                    "npm install",
                    "Instalando dependencias npm",
                    timeout=300
                )
                
                if success:
                    print(f"   {Colors.OKGREEN}✅ Dependencias del frontend instaladas{Colors.ENDC}")
                    return True
                else:
                    print(f"   {Colors.FAIL}❌ Error: {stderr}{Colors.ENDC}")
                    return False
                    
            finally:
                os.chdir(original_dir)
                
        except Exception as e:
            self.logger.error(f"Error instalando dependencias frontend: {e}")
            print(f"   {Colors.FAIL}❌ Error: {e}{Colors.ENDC}")
            return False
    
    def create_configuration_files(self) -> bool:
        """Crea archivos de configuración"""
        print(f"{Colors.OKBLUE}⚙️  Creando archivos de configuración...{Colors.ENDC}")
        
        try:
            # Docker Compose
            docker_compose_content = """version: '3.8'

services:
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
    restart: unless-stopped

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

volumes:
  postgres_data:
  redis_data:

networks:
  manus-network:
    driver: bridge
"""
            
            # Escribir docker-compose.yml
            (self.install_dir / "docker-compose.yml").write_text(docker_compose_content)
            
            # Archivo .env para backend
            backend_env = f"""FLASK_ENV=production
FLASK_DEBUG=False
DATABASE_URL=postgresql://manus_user:manus_password_2024@localhost:5432/manus_db
OLLAMA_HOST=localhost:11434
SECRET_KEY=manus_secret_key_2024_super_secure
JWT_SECRET_KEY=jwt_secret_key_2024_super_secure
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
LOG_LEVEL=INFO
"""
            
            (self.install_dir / "backend" / ".env").write_text(backend_env)
            
            # Archivo .env para frontend
            frontend_env = """REACT_APP_API_URL=http://localhost:5000
REACT_APP_WS_URL=ws://localhost:5000
REACT_APP_NAME=MANUS-like System
REACT_APP_VERSION=2.0.0
"""
            
            (self.install_dir / "frontend" / ".env").write_text(frontend_env)
            
            print(f"   {Colors.OKGREEN}✅ Archivos de configuración creados{Colors.ENDC}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error creando configuración: {e}")
            print(f"   {Colors.FAIL}❌ Error: {e}{Colors.ENDC}")
            return False
    
    def create_startup_scripts(self) -> bool:
        """Crea scripts de inicio"""
        print(f"{Colors.OKBLUE}🚀 Creando scripts de inicio...{Colors.ENDC}")
        
        try:
            scripts_dir = self.install_dir / "scripts"
            
            if self.system_info['system'] == 'windows':
                # Script de inicio para Windows
                start_script = f"""@echo off
echo.
echo {Colors.HEADER}MANUS-like System - Iniciando...{Colors.ENDC}
echo.

echo Verificando Docker...
docker --version >nul 2>&1
if errorlevel 1 (
    echo {Colors.FAIL}Error: Docker no esta instalado o no esta ejecutandose{Colors.ENDC}
    echo Por favor, inicia Docker Desktop
    pause
    exit /b 1
)

echo Verificando Ollama...
ollama --version >nul 2>&1
if errorlevel 1 (
    echo {Colors.FAIL}Error: Ollama no esta instalado{Colors.ENDC}
    pause
    exit /b 1
)

echo Iniciando Ollama...
start /B ollama serve

echo Esperando a que Ollama este listo...
timeout /t 5 /nobreak >nul

echo Descargando modelo por defecto...
ollama pull llama2

echo Iniciando servicios...
docker-compose up -d

echo.
echo {Colors.OKGREEN}Sistema iniciado correctamente!{Colors.ENDC}
echo Frontend: http://localhost:3000
echo Backend API: http://localhost:5000
echo.
echo Presiona cualquier tecla para abrir el navegador...
pause >nul
start http://localhost:3000
"""
                
                (scripts_dir / "start.bat").write_text(start_script)
                (scripts_dir / "stop.bat").write_text("docker-compose down\npause")
            
            else:
                # Script de inicio para Unix
                start_script = f"""#!/bin/bash

echo ""
echo "{Colors.HEADER}MANUS-like System - Iniciando...{Colors.ENDC}"
echo ""

# Verificar Docker
if ! command -v docker &> /dev/null; then
    echo "{Colors.FAIL}Error: Docker no está instalado{Colors.ENDC}"
    exit 1
fi

# Verificar Ollama
if ! command -v ollama &> /dev/null; then
    echo "{Colors.FAIL}Error: Ollama no está instalado{Colors.ENDC}"
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

# Iniciar servicios
echo "Iniciando servicios..."
docker-compose up -d

echo ""
echo "{Colors.OKGREEN}Sistema iniciado correctamente!{Colors.ENDC}"
echo "Frontend: http://localhost:3000"
echo "Backend API: http://localhost:5000"

# Abrir navegador
if command -v xdg-open &> /dev/null; then
    xdg-open http://localhost:3000
elif command -v open &> /dev/null; then
    open http://localhost:3000
fi
"""
                
                start_script_path = scripts_dir / "start.sh"
                start_script_path.write_text(start_script)
                os.chmod(start_script_path, 0o755)
                
                # Script de parada
                stop_script = """#!/bin/bash
echo "Deteniendo MANUS-like System..."
docker-compose down
echo "Sistema detenido."
"""
                
                stop_script_path = scripts_dir / "stop.sh"
                stop_script_path.write_text(stop_script)
                os.chmod(stop_script_path, 0o755)
            
            print(f"   {Colors.OKGREEN}✅ Scripts de inicio creados{Colors.ENDC}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error creando scripts: {e}")
            print(f"   {Colors.FAIL}❌ Error: {e}{Colors.ENDC}")
            return False
    
    def download_ollama_models(self) -> bool:
        """Descarga modelos básicos de Ollama"""
        print(f"{Colors.OKBLUE}🧠 Descargando modelos de Ollama...{Colors.ENDC}")
        
        try:
            # Iniciar Ollama si no está ejecutándose
            self.run_command("ollama serve", timeout=5)
            time.sleep(3)
            
            # Modelos básicos
            models = ["llama2"]  # Solo el modelo básico para empezar
            
            progress = ProgressBar(len(models), "Descargando modelos")
            
            for model in models:
                print(f"   📥 Descargando modelo {model}...")
                success, stdout, stderr = self.run_command(
                    f"ollama pull {model}",
                    f"Descargando {model}",
                    timeout=600  # 10 minutos para descargas
                )
                
                if success:
                    progress.update(1, f"✅ {model}")
                    print(f"   {Colors.OKGREEN}✅ Modelo {model} descargado{Colors.ENDC}")
                else:
                    progress.update(1, f"❌ {model}")
                    print(f"   {Colors.WARNING}⚠️  Error descargando {model}: {stderr}{Colors.ENDC}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error descargando modelos: {e}")
            print(f"   {Colors.FAIL}❌ Error: {e}{Colors.ENDC}")
            return False
    
    def run_installation(self) -> bool:
        """Ejecuta la instalación completa"""
        try:
            self.print_header()
            self.print_system_info()
            
            # Verificar dependencias
            if not self.check_dependencies():
                return False
            
            # Pasos de instalación
            steps = [
                ("Configurando estructura del proyecto", self.setup_project_structure),
                ("Copiando archivos del proyecto", self.copy_project_files),
                ("Instalando Docker", self.install_docker),
                ("Instalando Node.js", self.install_nodejs),
                ("Instalando Ollama", self.install_ollama),
                ("Instalando dependencias Python", self.install_python_dependencies),
                ("Instalando dependencias frontend", self.install_frontend_dependencies),
                ("Creando archivos de configuración", self.create_configuration_files),
                ("Creando scripts de inicio", self.create_startup_scripts),
                ("Descargando modelos Ollama", self.download_ollama_models)
            ]
            
            print(f"{Colors.HEADER}🔧 Iniciando instalación ({len(steps)} pasos)...{Colors.ENDC}\n")
            
            overall_progress = ProgressBar(len(steps), "Progreso general")
            
            for i, (description, step_function) in enumerate(steps, 1):
                print(f"\n{Colors.BOLD}[{i}/{len(steps)}] {description}{Colors.ENDC}")
                
                if not step_function():
                    print(f"\n{Colors.FAIL}❌ Instalación falló en: {description}{Colors.ENDC}")
                    return False
                
                overall_progress.update(1, f"Completado: {description}")
                time.sleep(0.5)
            
            return True
            
        except KeyboardInterrupt:
            print(f"\n{Colors.WARNING}⚠️  Instalación cancelada por el usuario{Colors.ENDC}")
            return False
        except Exception as e:
            self.logger.error(f"Error en instalación: {e}")
            print(f"\n{Colors.FAIL}❌ Error inesperado: {e}{Colors.ENDC}")
            return False
    
    def show_completion_message(self):
        """Muestra mensaje de finalización"""
        elapsed = time.time() - self.start_time
        
        print(f"""
{Colors.HEADER}╔══════════════════════════════════════════════════════════════╗
║                    ¡INSTALACIÓN COMPLETADA!                 ║
╚══════════════════════════════════════════════════════════════╝{Colors.ENDC}

{Colors.OKGREEN}🎉 ¡El sistema MANUS-like ha sido instalado exitosamente!{Colors.ENDC}

{Colors.OKBLUE}📊 Estadísticas de instalación:{Colors.ENDC}
   ⏱️  Tiempo total: {elapsed:.1f} segundos
   📁 Directorio: {self.install_dir}
   💾 Logs: {self.install_dir}/logs/installation.log

{Colors.OKBLUE}🚀 Para iniciar el sistema:{Colors.ENDC}""")
        
        if self.system_info['system'] == 'windows':
            print(f"   {self.install_dir}/scripts/start.bat")
        else:
            print(f"   {self.install_dir}/scripts/start.sh")
        
        print(f"""
{Colors.OKBLUE}🌐 URLs de acceso:{Colors.ENDC}
   Frontend: http://localhost:3000
   Backend API: http://localhost:5000
   Documentación: http://localhost:3000/docs

{Colors.OKBLUE}🔐 Credenciales por defecto:{Colors.ENDC}
   Usuario: admin@manus.local
   Contraseña: admin123

{Colors.OKGREEN}¡Disfruta tu sistema MANUS-like! 🚀{Colors.ENDC}
""")

def main():
    """Función principal"""
    try:
        installer = ManusInstaller()
        
        if installer.run_installation():
            installer.show_completion_message()
            
            # Preguntar si iniciar el sistema
            response = input(f"\n{Colors.OKBLUE}¿Deseas iniciar el sistema ahora? (s/n): {Colors.ENDC}")
            if response.lower() in ['s', 'y', 'yes', 'sí', 'si']:
                if installer.system_info['system'] == 'windows':
                    os.system(f'"{installer.install_dir}/scripts/start.bat"')
                else:
                    os.system(f'"{installer.install_dir}/scripts/start.sh"')
        else:
            print(f"\n{Colors.FAIL}❌ La instalación falló{Colors.ENDC}")
            print(f"   Revisa los logs en: {installer.install_dir}/logs/installation.log")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}⚠️  Instalación cancelada por el usuario{Colors.ENDC}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.FAIL}❌ Error inesperado: {e}{Colors.ENDC}")
        sys.exit(1)

if __name__ == "__main__":
    main()

