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
            'python': {'min_version': '3.8', 'command': 'python --version', 'alt_command': None},
            'docker': {'min_version': '20.0', 'command': 'docker --version', 'alt_command': None},
            'docker-compose': {'min_version': '2.0', 'command': 'docker compose version', 'alt_command': 'docker-compose --version'}, # Try new command first
            'node': {'min_version': '18.0', 'command': 'node --version', 'alt_command': None},
            'npm': {'min_version': '8.0', 'command': 'npm --version', 'alt_command': None}, # Special handling for npm via node path is separate
            'git': {'min_version': '2.0', 'command': 'git --version', 'alt_command': None},
        }
    
    def _try_command(self, command_str: str, name: str) -> Tuple[Optional[str], Optional[subprocess.CompletedProcess]]:
        """Helper to run a command string and return version or None, and the process result."""
        try:
            command_parts = command_str.split()
            result = subprocess.run(
                command_parts,
                capture_output=True,
                text=True,
                timeout=10,
                env=os.environ.copy()
            )
            if result.returncode == 0:
                version = self._extract_version(result.stdout)
                if version != "unknown" and version.strip():
                    return version, result
            self.logger.debug(f"Comando '{command_str}' para {name} falló o no extrajo versión. RC: {result.returncode}. Stdout: {result.stdout.strip()}. Stderr: {result.stderr.strip()}")
            return None, result
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError) as e:
            self.logger.debug(f"Excepción para comando '{command_str}' verificando {name}: {e}")
            return None, None

    def check_dependency(self, name: str) -> Tuple[bool, str, str]:
        """Verifica una dependencia específica"""
        if name not in self.dependencies:
            return False, "unknown", "Dependencia desconocida"

        dep_config = self.dependencies[name]

        # Attempt primary command
        version, result_primary = self._try_command(dep_config['command'], name)
        if version:
            return True, version, "Instalado"

        # Attempt alternative command if specified and primary failed
        if dep_config.get('alt_command'):
            alt_version, result_alt = self._try_command(dep_config['alt_command'], name)
            if alt_version:
                return True, alt_version, f"Instalado (via {dep_config['alt_command'].split()[0]})"

        # Special handling for npm if direct/alt commands failed
        if name == 'npm':
            self.logger.debug(f"Comandos directos/alternativos para npm fallaron o no aplicables. Buscando npm via node.")
            node_executable_path = shutil.which("node") # Corrected indentation
            if node_executable_path:
                self.logger.debug(f"Node ejecutable encontrado en: {node_executable_path}")
                node_dir = Path(node_executable_path).parent
                npm_executable_name = "npm.cmd" if platform.system().lower() == "windows" else "npm"
                npm_path_via_node = node_dir / npm_executable_name

                if npm_path_via_node.exists() and npm_path_via_node.is_file():
                    self.logger.debug(f"Probando npm en: {npm_path_via_node}")
                    # Construct command string for _try_command helper
                    npm_via_node_cmd_str = f"{str(npm_path_via_node)} --version"
                    npm_via_node_version, _ = self._try_command(npm_via_node_cmd_str, "npm via node")

                    if npm_via_node_version:
                        self.logger.info(f"npm encontrado via node en {npm_path_via_node} con versión {npm_via_node_version}")
                        return True, npm_via_node_version, "Instalado (via node)"
                    else:
                        self.logger.warning(f"npm via node ({npm_path_via_node}) se ejecutó pero no se pudo extraer la versión.")
                else:
                    self.logger.debug(f"npm no encontrado en la ruta de node: {npm_path_via_node}")
            else:
                self.logger.debug("Node ejecutable no encontrado, no se puede buscar npm via node.")

        # If all attempts fail for any dependency (including special npm handling if it fails)
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
    
    def run_command(self, command: str, description: str = "", timeout: int = 300) -> Tuple[bool, str, str, Optional[int]]:
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
            
            return success, stdout, stderr, return_code
            
        except subprocess.TimeoutExpired:
            if process: process.kill()
            error_msg = f"Comando excedió timeout de {timeout}s"
            self.logger.error(f"{error_msg}: {command}")
            return False, "", error_msg, None # No return code available
            
        except Exception as e:
            error_msg = f"Error ejecutando comando: {str(e)}"
            self.logger.error(f"{error_msg}: {command}")
            return False, "", error_msg, None # No return code available
    
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
                    success, stdout, stderr, _ = self.run_command(
                        "winget install Docker.DockerDesktop --accept-package-agreements --accept-source-agreements",
                        "Instalando Docker Desktop con winget"
                    )
                elif package_manager == 'choco':
                    success, stdout, stderr, _ = self.run_command(
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
                        success, stdout, stderr, _ = self.run_command(
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
                    success, _, stderr, _ = self.run_command(
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
                        success, _, stderr, _ = self.run_command(
                            f"hdiutil attach {installer_path}",
                            "Montando imagen Docker"
                        )
                        if success:
                            success, _, stderr, _ = self.run_command(
                                "cp -R /Volumes/Docker/Docker.app /Applications/",
                                "Copiando Docker a Applications"
                            )
                            self.run_command("hdiutil detach /Volumes/Docker")
                    else:
                        return False
            
            else:  # Linux
                if package_manager in ['apt', 'yum', 'dnf']:
                    # Usar script oficial de Docker
                    success, _, stderr, _ = self.run_command(
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
                    success, _, stderr, _ = self.run_command(
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
                success, _, _, _ = self.run_command("docker --version", timeout=30)
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
        
        WINGET_NODE_ALREADY_INSTALLED_CODE = 2316632107 # From user log

        node_installed, _, _ = self.dep_checker.check_dependency('node')
        npm_installed, _, _ = self.dep_checker.check_dependency('npm')

        if node_installed and npm_installed:
            print(f"   {Colors.OKGREEN}✅ Node.js y npm ya están instalados.{Colors.ENDC}")
            return True

        command_executed = False
        installation_succeeded_or_skipped = False
        final_stderr = ""

        try:
            if system == 'windows':
                if package_manager == 'winget':
                    command_executed = True
                    # Always run winget if npm is missing, or if node is missing.
                    # If node is present but npm is not, winget *should* repair this.
                    print(f"   {Colors.OKBLUE}ℹ️ Intentando instalar/actualizar Node.js y npm con winget...{Colors.ENDC}")
                    success, stdout, stderr, return_code = self.run_command(
                        "winget install OpenJS.NodeJS --accept-package-agreements --accept-source-agreements",
                        "Instalando/Actualizando Node.js (OpenJS) con winget"
                    )
                    final_stderr = stderr
                    if success:
                        installation_succeeded_or_skipped = True
                        print(f"   {Colors.OKGREEN}✅ Winget: Comando para OpenJS.NodeJS ejecutado exitosamente.{Colors.ENDC}")
                    elif return_code == WINGET_NODE_ALREADY_INSTALLED_CODE:
                        installation_succeeded_or_skipped = True
                        print(f"   {Colors.OKBLUE}ℹ️ Winget: OpenJS.NodeJS ya está instalado y actualizado (código: {return_code}).{Colors.ENDC}")
                    else:
                        # Genuine error
                        print(f"   {Colors.FAIL}❌ Winget: Fallo al instalar OpenJS.NodeJS. Código: {return_code or 'N/A'}{Colors.ENDC}")
                        # stderr is already logged by run_command

                elif package_manager == 'choco':
                    command_executed = True
                    print(f"   {Colors.OKBLUE}ℹ️ Intentando instalar/actualizar Node.js y npm con Chocolatey...{Colors.ENDC}")
                    success, stdout, stderr, return_code = self.run_command(
                        "choco install nodejs -y", # nodejs package on choco usually includes npm
                        "Instalando/Actualizando Node.js con Chocolatey"
                    )
                    final_stderr = stderr
                    if success:
                        installation_succeeded_or_skipped = True
                        print(f"   {Colors.OKGREEN}✅ Chocolatey: Comando para Node.js ejecutado exitosamente.{Colors.ENDC}")
                    elif "already installed" in (stdout + stderr).lower(): # Choco's way of saying it's there
                        installation_succeeded_or_skipped = True
                        print(f"   {Colors.OKBLUE}ℹ️ Chocolatey: Node.js ya está instalado.{Colors.ENDC}")
                    else:
                        print(f"   {Colors.FAIL}❌ Chocolatey: Fallo al instalar Node.js. Código: {return_code or 'N/A'}{Colors.ENDC}")

                else: # Manual download path for Windows if no winget/choco
                    command_executed = True
                    print(f"   {Colors.OKBLUE}ℹ️ Winget/Choco no detectado. Intentando descarga manual de Node.js para Windows...{Colors.ENDC}")
                    url = "https://nodejs.org/dist/v20.10.0/node-v20.10.0-x64.msi" # Ensure this is the Windows URL
                    installer_path = self.temp_dir / "nodejs-installer.msi"
                    
                    if self.download_with_progress(url, installer_path, "Node.js MSI"):
                        success_manual, stdout_manual, stderr_manual, return_code_manual = self.run_command(
                            f'msiexec /i "{installer_path}" /quiet /norestart', # Common silent flags for MSI
                            "Instalando Node.js (descarga manual Windows)"
                        )
                        final_stderr = stderr_manual # Capture stderr from this path
                        if success_manual:
                            installation_succeeded_or_skipped = True
                            print(f"   {Colors.OKGREEN}✅ Node.js (MSI) instalado manualmente.{Colors.ENDC}")
                        else:
                            print(f"   {Colors.FAIL}❌ Fallo en la instalación manual de Node.js (MSI). Código: {return_code_manual or 'N/A'}{Colors.ENDC}")
                            # Logged by run_command
                    else:
                        self.logger.error("Fallo la descarga del MSI de Node.js para Windows.")
                        # installation_succeeded_or_skipped remains False
            
            elif system == 'darwin':  # macOS
                command_executed = True
                # Assuming node_installed and npm_installed checks at the start are sufficient for macOS too.
                if package_manager == 'brew':
                    success, stdout, stderr, return_code = self.run_command(
                        "brew install node", # Installs node and npm
                        "Instalando Node.js y npm con Homebrew"
                    )
                    final_stderr = stderr
                    if success:
                        installation_succeeded_or_skipped = True
                    # Brew usually exits 0 if already installed, or if successfully upgraded.
                    # If it fails for other reasons, it's a genuine error.
                    elif not success : # Genuine error
                         print(f"   {Colors.FAIL}❌ Homebrew: Fallo al instalar Node.js. Código: {return_code or 'N/A'}{Colors.ENDC}")
                else:
                    # Descarga manual para macOS
                    url = "https://nodejs.org/dist/v20.10.0/node-v20.10.0.pkg"
                    installer_path = self.temp_dir / "nodejs.pkg"
                    
                    if self.download_with_progress(url, installer_path, "Node.js"):
                        success, stdout, stderr, return_code = self.run_command(
                            f"installer -pkg {installer_path} -target /", # Installs node and npm
                            "Instalando Node.js y npm (descarga manual macOS)"
                        )
                        final_stderr = stderr
                        if success:
                            installation_succeeded_or_skipped = True
                        else:
                            print(f"   {Colors.FAIL}❌ Fallo en la instalación manual de Node.js en macOS. Código: {return_code or 'N/A'}{Colors.ENDC}")
                    else:
                        self.logger.error("Fallo la descarga manual de Node.js para macOS.")

            
            else:  # Linux
                command_executed = True
                # For Linux, package managers usually handle "already installed" gracefully (exit code 0)
                # or update if a new version is found.
                # The commands below typically install both node and npm.
                if package_manager == 'apt':
                    print(f"   {Colors.OKBLUE}ℹ️ Intentando instalar/actualizar Node.js y npm con apt...{Colors.ENDC}")
                    commands = [
                        "curl -fsSL https://deb.nodesource.com/setup_20.x | bash -", # Setup script for specific version
                        "apt-get install -y nodejs" # Installs nodejs and usually npm
                    ]
                    current_success = True
                    for cmd_idx, cmd_val in enumerate(commands):
                        success, stdout, stderr, return_code = self.run_command(cmd_val, f"Ejecutando: {cmd_val}")
                        final_stderr += f"\nCmd {cmd_idx} stderr: {stderr}"
                        if not success:
                            current_success = False
                            print(f"   {Colors.FAIL}❌ Fallo el comando apt: {cmd_val}. Código: {return_code or 'N/A'}{Colors.ENDC}")
                            break
                    if current_success: installation_succeeded_or_skipped = True
                
                elif package_manager in ['yum', 'dnf']:
                    print(f"   {Colors.OKBLUE}ℹ️ Intentando instalar/actualizar Node.js y npm con {package_manager}...{Colors.ENDC}")
                    commands = [
                        "curl -fsSL https://rpm.nodesource.com/setup_20.x | bash -",
                        f"{package_manager} install -y nodejs" # Installs nodejs and usually npm
                    ]
                    current_success = True
                    for cmd_idx, cmd_val in enumerate(commands):
                        success, stdout, stderr, return_code = self.run_command(cmd_val, f"Ejecutando: {cmd_val}")
                        final_stderr += f"\nCmd {cmd_idx} stderr: {stderr}"
                        if not success:
                            current_success = False
                            print(f"   {Colors.FAIL}❌ Fallo el comando {package_manager}: {cmd_val}. Código: {return_code or 'N/A'}{Colors.ENDC}")
                            break
                    if current_success: installation_succeeded_or_skipped = True
                
                elif package_manager == 'pacman':
                    print(f"   {Colors.OKBLUE}ℹ️ Intentando instalar/actualizar Node.js y npm con pacman...{Colors.ENDC}")
                    success, stdout, stderr, return_code = self.run_command(
                        "pacman -S nodejs npm --noconfirm", # Explicitly installs both
                        "Instalando Node.js y npm con pacman"
                    )
                    final_stderr = stderr
                    if success: installation_succeeded_or_skipped = True
                    else: print(f"   {Colors.FAIL}❌ Pacman: Fallo al instalar Node.js/npm. Código: {return_code or 'N/A'}{Colors.ENDC}")
                else:
                    self.logger.error(f"Gestor de paquetes Linux no soportado para Node.js: {package_manager}")
                    # This path will lead to overall failure if installation_succeeded_or_skipped is false
            
            if not command_executed and not (node_installed and npm_installed):
                 # This case should ideally not be reached if there's a package manager or manual download option.
                self.logger.error("No se ejecutó ningún comando de instalación para Node.js y no estaba preinstalado.")
                installation_succeeded_or_skipped = False


            # Post-installation verification for Node and especially NPM
            if installation_succeeded_or_skipped:
                self.logger.info("Iniciando verificación post-instalación para Node.js y npm.")
                print(f"   {Colors.OKBLUE}ℹ️ Verificando Node.js y npm después del intento de instalación/actualización...{Colors.ENDC}")

                # Force a re-check here, results are not cached in a way that helps if PATH just changed.
                node_installed_after, node_version_after, _ = self.dep_checker.check_dependency('node')
                npm_installed_after, npm_version_after, npm_status_after = self.dep_checker.check_dependency('npm')

                self.logger.info(f"Verificación post-instalación Node: {node_installed_after} ({node_version_after}). NPM: {npm_installed_after} ({npm_version_after}, Status: {npm_status_after})")


                if node_installed_after and npm_installed_after:
                    print(f"   {Colors.OKGREEN}✅ Node.js y npm verificados y funcionando.{Colors.ENDC}")
                    return True
                elif node_installed_after and not npm_installed_after:
                    print(f"   {Colors.WARNING}⚠️ Node.js está instalado, pero npm sigue sin encontrarse.{Colors.ENDC}")
                    self.logger.warning("npm no encontrado después del intento de instalación inicial de Node.js. Intentando reinstalación con MSI.")

                    # Attempt to fix missing npm by re-running MSI installer (Windows specific)
                    if system == 'windows':
                        print(f"   {Colors.OKBLUE}ℹ️ Intentando reinstalar Node.js desde MSI para asegurar npm...{Colors.ENDC}")
                        msi_url = "https://nodejs.org/dist/v20.10.0/node-v20.10.0-x64.msi" # Using a recent LTS version
                        msi_installer_path = self.temp_dir / "nodejs-lts-installer.msi"
                        msi_reinstall_succeeded = False
                        if self.download_with_progress(msi_url, msi_installer_path, "Node.js LTS MSI"):
                            # Using /faumus to force reinstall all files. /quiet for silent.
                            # May require admin rights.
                            # Note: The original script's manual download section didn't explicitly use admin for MSI.
                            # This might still be an issue if not run as admin.
                            msi_success, _, msi_stderr, _ = self.run_command(
                                f'msiexec /i "{msi_installer_path}" /quiet /norestart REINSTALL=ALL REINSTALLMODE=vomus',
                                "Reinstalando Node.js con MSI"
                            )
                            if msi_success:
                                print(f"   {Colors.OKGREEN}✅ Reinstalación con MSI completada.{Colors.ENDC}")
                                msi_reinstall_succeeded = True
                            else:
                                print(f"   {Colors.FAIL}❌ Fallo la reinstalación con MSI. Detalles: {msi_stderr or 'N/A'}{Colors.ENDC}")
                                self.logger.error(f"Fallo la reinstalación de Node.js con MSI. Stderr: {msi_stderr}")
                        else:
                            self.logger.error("Fallo la descarga del MSI de Node.js para reinstalación.")

                        if msi_reinstall_succeeded:
                            self.logger.info("Verificando npm después de la reinstalación con MSI.")
                            npm_installed_after_msi, _, _ = self.dep_checker.check_dependency('npm')
                            if npm_installed_after_msi:
                                print(f"   {Colors.OKGREEN}✅ npm encontrado después de la reinstalación con MSI.{Colors.ENDC}")
                                return True
                            else:
                                print(f"   {Colors.FAIL}❌ npm sigue sin encontrarse después de la reinstalación con MSI.{Colors.ENDC}")
                                self.logger.error("npm todavía no encontrado después de la reinstalación con MSI.")
                                return False
                        else: # MSI reinstall failed or download failed
                            return False
                    else: # Not windows, and npm is missing
                         print(f"   {Colors.FAIL}❌ Node.js está instalado, pero npm sigue sin encontrarse (sistema no Windows, no se intentó reinstalación con MSI).{Colors.ENDC}")
                         self.logger.error("npm no encontrado después de la instalación de Node.js (no Windows).")
                         return False

                elif not node_installed_after:
                    print(f"   {Colors.FAIL}❌ Node.js no se encuentra después del intento de instalación/actualización.{Colors.ENDC}")
                    self.logger.error("Node.js no encontrado después de un supuesto éxito de instalación/actualización.")
                    return False
                # No specific 'else' needed here, covered by subsequent failure path

            # If installation_succeeded_or_skipped is False (genuine failure from package manager/download)
            print(f"   {Colors.FAIL}❌ Error en la instalación de Node.js/npm.{Colors.ENDC}")
            if final_stderr: # This final_stderr is from the initial package manager attempt
                 print(f"      {Colors.FAIL}Detalles del error inicial: {final_stderr.strip()}{Colors.ENDC}")
            return False
                
        except Exception as e:
            self.logger.error(f"Excepción durante la instalación de Node.js: {e}")
            print(f"   {Colors.FAIL}❌ Error inesperado durante la instalación de Node.js: {e}{Colors.ENDC}")
            return False
    
    def install_ollama(self) -> bool:
        """Instala Ollama según el sistema operativo"""
        print(f"{Colors.OKBLUE}🧠 Instalando Ollama...{Colors.ENDC}")

        # 1. Pre-check if Ollama is already installed
        print(f"   {Colors.OKBLUE}ℹ️ Verificando si Ollama ya está instalado...{Colors.ENDC}")
        pre_check_success, pre_check_stdout, pre_check_stderr, _ = self.run_command("ollama --version", "Verificación previa de Ollama", timeout=20)
        
        if pre_check_success:
            ollama_version = self.dep_checker._extract_version(pre_check_stdout)
            if ollama_version != "unknown" and ollama_version.strip():
                print(f"   {Colors.OKGREEN}✅ Ollama ya está instalado y funcionando. Versión: {ollama_version}{Colors.ENDC}")
                self.logger.info(f"Ollama ya instalado (versión {ollama_version}). Saltando instalación.")
                return True
            else:
                # Command succeeded but version couldn't be extracted. Might be an issue.
                print(f"   {Colors.WARNING}⚠️  'ollama --version' se ejecutó pero no se pudo determinar la versión. Se procederá con el intento de instalación.{Colors.ENDC}")
                self.logger.warning(f"'ollama --version' (pre-check) exitoso pero no se extrajo versión. Stdout: {pre_check_stdout}")
        else:
            print(f"   {Colors.OKBLUE}ℹ️ Ollama no detectado o no responde. Se procederá con la instalación.{Colors.ENDC}")
            if pre_check_stderr:
                 self.logger.debug(f"Pre-check 'ollama --version' falló. Stderr: {pre_check_stderr.strip()}")

        system = self.system_info['system']
        inst_success = False # Ensure this is defined before the main try block in case download fails early for Windows
        inst_stdout = ""
        inst_stderr = ""
        inst_rc = None
        
        try:
            if system == 'windows':
                # Descarga e instalación para Windows
                url = "https://ollama.ai/download/windows"
                installer_path = self.temp_dir / "ollama-installer.exe"
                
                if self.download_with_progress(url, installer_path, "Ollama"):
                    # Correctly unpack 4 values
                    inst_success, inst_stdout, inst_stderr, inst_rc = self.run_command(
                        f'"{installer_path}" /S',
                        "Instalando Ollama (Windows)"
                    )
                else: # Download failed
                    self.logger.error("Fallo la descarga del instalador de Ollama para Windows.")
                    return False # Explicitly return False if download fails
            
            elif system == 'darwin':  # macOS
                if self.system_info['package_manager'] == 'brew':
                    # Correctly unpack 4 values
                    inst_success, inst_stdout, inst_stderr, inst_rc = self.run_command(
                        "brew install ollama",
                        "Instalando Ollama con Homebrew"
                    )
                else: # Manual script for macOS
                    # Correctly unpack 4 values
                    inst_success, inst_stdout, inst_stderr, inst_rc = self.run_command(
                        "curl -fsSL https://ollama.ai/install.sh | sh",
                        "Instalando Ollama con script oficial (macOS)"
                    )
            
            else:  # Assume Linux for other cases
                # Correctly unpack 4 values
                inst_success, inst_stdout, inst_stderr, inst_rc = self.run_command(
                    "curl -fsSL https://ollama.ai/install.sh | sh",
                    "Instalando Ollama con script oficial (Linux)"
                )
                
                if inst_success and system == 'linux':
                    # Best effort to enable/start service, ignore results for now
                    self.run_command("systemctl enable ollama", timeout=30)
                    self.run_command("systemctl start ollama", timeout=30)
            
            # Check if the installation command was successful
            if inst_success:
                print(f"   {Colors.OKGREEN}✅ Comando de instalación de Ollama ejecutado correctamente.{Colors.ENDC}")
                
                # Verification step
                print(f"   {Colors.OKBLUE}ℹ️ Verificando instalación de Ollama ejecutando 'ollama --version'...{Colors.ENDC}")
                time.sleep(3) # Give it a moment if it was just installed
                # Correctly unpack 4 values for verification
                verify_success, verify_stdout, verify_stderr, _ = self.run_command("ollama --version", timeout=20)

                if verify_success:
                    ollama_version = self.dep_checker._extract_version(verify_stdout)
                    print(f"   {Colors.OKGREEN}✅ Ollama verificado y funcionando. Versión: {ollama_version}{Colors.ENDC}")
                    return True
                else:
                    print(f"   {Colors.WARNING}⚠️  Ollama parece instalado (comando de instalación exitoso), pero 'ollama --version' falló o no respondió.{Colors.ENDC}")
                    self.logger.warning(f"Comando 'ollama --version' falló después de la instalación. stdout: {verify_stdout}, stderr: {verify_stderr}")
                    print(f"   {Colors.WARNING}   Puede que necesite iniciar Ollama manualmente o que haya un problema con la instalación.{Colors.ENDC}")
                    # Return True because the install command itself reported success.
                    # User might need to manually start Ollama service or troubleshoot.
                    return True
            else:
                # Installation command itself failed
                self.logger.error(f"Fallo el comando de instalación de Ollama. RC: {inst_rc}. Stderr: {inst_stderr}. Stdout: {inst_stdout}")
                print(f"   {Colors.FAIL}❌ Error durante el comando de instalación de Ollama.{Colors.ENDC}")

                # Specific check for Windows incompatibility error
                if system == 'windows' and inst_stderr and "no es compatible con la versi¢n de Windows" in inst_stderr:
                    print(f"      {Colors.FAIL}Detalles del error: {inst_stderr.strip()}{Colors.ENDC}")
                    print(f"   {Colors.FAIL}   El instalador de Ollama descargado no es compatible con su versión de Windows.{Colors.ENDC}")
                    print(f"   {Colors.FAIL}   Por favor, verifique los requisitos del sistema para Ollama o intente descargar manualmente una versión compatible desde el sitio web de Ollama.{Colors.ENDC}")
                elif inst_stderr: # Generic error message if stderr is present
                    print(f"      {Colors.FAIL}Detalles del error: {inst_stderr.strip()}{Colors.ENDC}")
                return False
                
        except Exception as e:
            self.logger.error(f"Excepción inesperada durante la instalación de Ollama: {str(e)}") # Log the string representation of e
            print(f"   {Colors.FAIL}❌ Error inesperado durante la instalación de Ollama: {e}{Colors.ENDC}")
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
            # Correctly unpack 4 values
            pip_success, pip_stdout, pip_stderr, pip_rc = self.run_command(
                f"{sys.executable} -m pip install --upgrade pip",
                "Actualizando pip"
            )
            
            if not pip_success: # Check pip_success
                # Use pip_stderr for the error message
                print(f"   {Colors.WARNING}⚠️  Error actualizando pip: {pip_stderr.strip() if pip_stderr else 'Unknown error'}{Colors.ENDC}")
            
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
                # Changed pydantic version to one likely to have pre-built wheels for Python 3.13
                # Supabase successfully installed pydantic 2.11.7 and its core wheel.
                "pydantic~=2.11.0",
                "python-multipart==0.0.6",
                "bcrypt==4.1.2",
                "pyjwt==2.8.0",
                "colorama"  # Para colores en Windows
            ]
            
            progress = ProgressBar(len(dependencies), "Instalando paquetes Python")
            
            for dep in dependencies:
                # Correctly unpack 4 values
                dep_success, dep_stdout, dep_stderr, dep_rc = self.run_command(
                    f"{sys.executable} -m pip install {dep}",
                    f"Instalando {dep}",
                    timeout=120
                )
                
                if dep_success: # Check dep_success
                    progress.update(1, f"✅ {dep}")
                else:
                    progress.update(1, f"❌ {dep}")
                    # Use dep_stderr for the error message
                    self.logger.error(f"Error instalando {dep}: {dep_stderr.strip() if dep_stderr else 'Unknown error'}")
                
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
                # Correctly unpack 4 values, even if return_code is not used here.
                success, stdout, stderr, _ = self.run_command(
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
                success, stdout, stderr, _ = self.run_command(
                    f"ollama pull {model}",
                    f"Descargando {model}",
                    timeout=600  # 10 minutos para descargas
                )
                
                if success:
                    progress.update(1, f"✅ {model}")
                    print(f"   {Colors.OKGREEN}✅ Modelo {model} descargado{Colors.ENDC}")
                else:
                    progress.update(1, f"❌ {model}")
                    print(f"   {Colors.WARNING}⚠️  Error descargando {model}: {stderr.strip() if stderr else 'Unknown error'}{Colors.ENDC}")
            
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

