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

# Log muy temprano
TEMP_DIR_PATH = Path(tempfile.gettempdir())
VERY_EARLY_LOG_FILE = TEMP_DIR_PATH / "manus_setup_very_early_log.txt"

def write_very_early_log(message: str):
    """Escribe un mensaje al log muy temprano."""
    try:
        with open(VERY_EARLY_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {message}\n")
    except Exception as e:
        # No hacer print aquí ya que podría ser demasiado temprano o causar problemas
        # Simplemente intentamos loguear, si falla, falla silenciosamente.
        pass

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
        write_very_early_log(f"SystemInstaller.__init__: system={self.system}, arch={self.arch}")

        # Initial Python check before anything else
        if not self._check_python_installation():
            write_very_early_log("SystemInstaller.__init__: Python check failed. Exiting.")
            self.print_step("Critical Python setup issue detected. Please see the messages above.", "error")
            sys.exit(1)
        write_very_early_log("SystemInstaller.__init__: Python check successful.")

        self.is_admin = self._check_admin()
        # Modificación para usar la ruta del script como base para install_dir
        self.install_dir = Path(__file__).resolve().parent
        write_very_early_log(f"SystemInstaller.__init__: self.install_dir set to script's parent directory: {self.install_dir}")
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
    
    def run_command(self, command: str, shell: bool = True, check: bool = True) -> Tuple[int, str]:
        """Ejecuta un comando y retorna el resultado (exit_code, output_message)"""
        is_winget_command = isinstance(command, str) and "winget" in command

        try:
            if isinstance(command, str):
                cmd_list = command if shell else command.split()
            else: # command is already a list
                cmd_list = command

            if is_winget_command:
                process = subprocess.run(
                    cmd_list,
                    shell=shell,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding='utf-8',
                    errors='replace',
                    check=False
                )
                # Check for specific winget "already installed" exit code
                # 2316632107 (0x8A15002B) observed for "already installed, no update"
                # WINGET_EXIT_CODE_ALREADY_INSTALLED is 0x8A15000F (2316632079)
                # We'll consider both for now, or more broadly any code that means "no action taken but not a failure for install intent"
                # For now, specifically handling the observed code.
                # Check if the original command string (if it was a string) contains " install "
                original_command_str = command if isinstance(command, str) else " ".join(command)
                if " install " in original_command_str.lower() and process.returncode == 2316632107:
                    self.print_step(f"Winget: Paquete '{original_command_str.split(' install ')[-1].split(' ')[0]}' ya instalado y actualizado (código: {process.returncode}). Considerado como éxito.", "info")
                    return 0, process.stdout.strip() # Treat as success
                return process.returncode, process.stdout.strip()
            else: # Non-winget commands
                if check: # If check=True, raise CalledProcessError on failure
                    process = subprocess.run(
                        cmd_list,
                        shell=shell,
                        capture_output=True,
                        text=True,
                        encoding='utf-8',
                        errors='replace',
                        check=True
                    )
                    return 0, process.stdout.strip() # Success is exit code 0
                else: # If check=False, manually check return code and capture output
                    process = subprocess.run(
                        cmd_list,
                        shell=shell,
                        capture_output=True,
                        text=True,
                        encoding='utf-8',
                        errors='replace',
                        check=False
                    )
                    output_msg = process.stdout.strip() if process.returncode == 0 else \
                                 (process.stderr.strip() if process.stderr else process.stdout.strip())
                    return process.returncode, output_msg

        except subprocess.CalledProcessError as e:
            # For non-winget commands with check=True that fail
            return e.returncode, e.stderr.strip() if e.stderr else str(e)
        except FileNotFoundError as e:
            # Command not found
            self.print_step(f"Comando no encontrado: {cmd_list[0] if isinstance(cmd_list, list) else cmd_list}. Error: {e}", "error")
            return -1, str(e) # Use a distinct error code like -1 for command not found
        except Exception as e:
            # General exceptions
            self.print_step(f"Excepción inesperada ejecutando comando: {cmd_list}. Error: {e}", "error")
            return -2, str(e) # Use a distinct error code like -2 for other exceptions
    
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
            command = f"winget install {package} --accept-package-agreements --accept-source-agreements"
            exit_code, combined_output = self.run_command(command)

            if exit_code != 0:
                self.print_step(f"Error instalando {package} con winget (código de salida: {exit_code}). Salida del comando:", "error")
                print(Colors.FAIL + combined_output + Colors.ENDC) # combined_output is already stripped by run_command

                if self.is_admin:
                    self.print_step(f"La instalación de {package} falló. La ventana se cerrará en 20 segundos...", "info")
                    time.sleep(20)
                return False
        return True
    
    def install_docker(self) -> bool:
        """Instala Docker"""
        self.print_step("Instalando Docker...")
        
        if self.system == "windows":
            self.print_step("Verificando si Docker ya está instalado y operativo en Windows...")
            docker_version_exit_code, docker_version_output = self.run_command("docker --version", check=False)

            if docker_version_exit_code == 0:
                self.print_step(f"Docker ya está instalado y respondiendo: {docker_version_output.splitlines()[0] if docker_version_output else 'OK'}", "success")
                self.print_step("Verificando si el servicio Docker está en ejecución...")
                docker_ps_exit_code, docker_ps_output = self.run_command("docker ps", check=False)
                if docker_ps_exit_code == 0:
                    self.print_step("El servicio Docker está en ejecución.", "success")
                    return True # Docker is installed and running
                else:
                    self.print_step(f"Docker CLI está presente (código de salida 'docker ps': {docker_ps_exit_code}), pero el servicio Docker no responde. Se intentará la instalación/reparación.", "warning")
                    self.print_step(f"Salida de 'docker ps': {docker_ps_output}", "info")
            else:
                self.print_step("Docker no parece estar instalado o no está en PATH. Se procederá con la instalación.", "info")

            # If Docker is not installed and responsive, proceed with winget installation.
            self.print_step("Intentando instalar Docker Desktop usando winget...", "info")
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
        
        # Verificar instalación (Este código es para Linux/Mac después de sus instalaciones específicas)
        # Para Windows, la verificación ya está integrada arriba o se maneja por winget.
        if self.system != "windows":
            time.sleep(10)  # Esperar a que Docker se inicie
            exit_code, _ = self.run_command("docker --version")
            if exit_code == 0:
                self.print_step("Docker instalado correctamente", "success")
                return True
            else:
                self.print_step("Error verificando Docker post-instalación", "error")
                return False
        return True # If windows, it would have returned earlier from pre-check or winget call.
    
    def install_nodejs(self) -> bool:
        """Instala Node.js"""
        self.print_step("Instalando Node.js...")
        
        install_success = False
        if self.system == "windows":
            install_success = self.install_winget_packages(["OpenJS.NodeJS"])
        
        elif self.system == "linux":
            commands = [
                "curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -",
                "apt-get install -y nodejs"
            ]
            all_succeeded = True
            for cmd in commands:
                exit_code, output = self.run_command(cmd)
                if exit_code != 0:
                    self.print_step(f"Error ejecutando: {cmd} (código: {exit_code}): {output}", "error")
                    all_succeeded = False
                    break
            install_success = all_succeeded
        
        elif self.system == "darwin":
            exit_code, _ = self.run_command("brew install node")
            install_success = (exit_code == 0)
            if not install_success:
                 self.print_step(f"Error instalando Node.js con Homebrew (código: {exit_code})", "error")

        if not install_success:
            self.print_step("Falló la instalación de Node.js.", "error")
            return False
        
        # Verificar instalación
        self.print_step("Verificando instalación de Node.js...")
        node_exit_code, node_version_output = self.run_command("node --version", check=False)
        if node_exit_code == 0:
            self.print_step(f"Node.js instalado correctamente: {node_version_output}", "success")
            return True
        else:
            self.print_step(f"Error verificando Node.js (código: {node_exit_code}): {node_version_output}", "error")
            return False
    
    def install_ollama(self) -> bool:
        """Instala Ollama"""
        self.print_step("Instalando Ollama...")

        # Pre-check if Ollama is already installed
        self.print_step("Verificando si Ollama ya está instalado...")
        ollama_check_exit_code, ollama_version_output = self.run_command("ollama --version", check=False)
        if ollama_check_exit_code == 0:
            self.print_step(f"Ollama ya está instalado y respondiendo: {ollama_version_output.splitlines()[0] if ollama_version_output else 'OK'}", "success")
            # Optionally, ensure the service is running, though 'ollama --version' might be sufficient
            # For simplicity, we'll assume if CLI works, it's usable or can be started.
            return True
        else:
            self.print_step("Ollama no parece estar instalado o no está en PATH. Se procederá con la instalación.", "info")

        if self.system == "windows":
            # Descargar e instalar Ollama para Windows
            temp_dir = Path(tempfile.gettempdir())
            installer_path = temp_dir / "ollama-installer.exe" # This is a Path object
            
            if self.download_file(self.urls["ollama"]["windows"], installer_path):
                resolved_installer_path = str(installer_path.resolve())
                self.print_step(f"Ejecutando instalador de Ollama desde: {resolved_installer_path}")

                # Try with shell=False first, which is generally safer for paths
                cmd_list = [resolved_installer_path, "/S"]
                exit_code, output = self.run_command(cmd_list, shell=False, check=False)

                if exit_code == 0:
                    self.print_step("Ollama instalado correctamente.", "success")
                    self.run_command("ollama serve", check=False)
                    # Verify after attempting install
                    ollama_verify_exit_code, _ = self.run_command("ollama --version", check=False)
                    if ollama_verify_exit_code == 0:
                        self.print_step("Verificación de Ollama post-instalación exitosa.", "success")
                        return True
                    else:
                        self.print_step("Ollama se instaló, pero la verificación post-instalación falló.", "warning")
                        return False # Or True if this state is acceptable
                else:
                    self.print_step(f"Falló el instalador de Ollama (código: {exit_code}). Salida: {output}", "error")
                    # As a fallback, try with shell=True if shell=False failed, though less likely to help with path issues like ??\\
                    # self.print_step("Intentando de nuevo con shell=True...", "info")
                    # exit_code_shell_true, output_shell_true = self.run_command(f'"{resolved_installer_path}" /S', shell=True, check=False)
                    # if exit_code_shell_true == 0: ...
                    # For now, we'll stick to the primary attempt.
            else: # Download failed
                self.print_step("Falló la descarga del instalador de Ollama.", "error")
                # No return False here, let it fall through to the general error at the end of the function.

        elif self.system == "linux":
            exit_code, output = self.run_command("curl -fsSL https://ollama.ai/install.sh | sh")
            if exit_code == 0:
                self.print_step("Script de instalación de Ollama ejecutado.", "info")
                # Iniciar servicio
                self.run_command("systemctl enable ollama", check=False) # Best effort
                self.run_command("systemctl start ollama", check=False)  # Best effort
                # Verify ollama
                ollama_check_exit_code, _ = self.run_command("ollama --version", check=False)
                if ollama_check_exit_code == 0:
                    self.print_step("Ollama instalado y verificado correctamente", "success")
                    return True
                else:
                    self.print_step("Ollama se instaló pero la verificación falló.", "warning")
                    return False # Or True if partial success is okay
            else:
                self.print_step(f"Falló la descarga/ejecución del script de Ollama (código: {exit_code}): {output}", "error")
        
        elif self.system == "darwin":
            exit_code, _ = self.run_command("brew install ollama")
            if exit_code == 0:
                self.print_step("Ollama instalado correctamente vía Homebrew", "success")
                self.run_command("ollama serve", check=False) # Non-critical if this fails to start immediately
                return True
            else:
                self.print_step(f"Falló la instalación de Ollama con Homebrew (código: {exit_code})", "error")
        
        self.print_step("Error general instalando Ollama", "error")
        return False
    
    def install_python_dependencies(self) -> bool:
        """Instala dependencias de Python"""
        self.print_step("Instalando dependencias de Python...")
        
        # Actualizar pip
        pip_upgrade_exit_code, pip_upgrade_output = self.run_command(f"{sys.executable} -m pip install --upgrade pip")
        if pip_upgrade_exit_code != 0:
            self.print_step(f"Error actualizando pip (código: {pip_upgrade_exit_code}): {pip_upgrade_output}", "error")
            if self.is_admin:
                self.print_step("La ventana se cerrará en 20 segundos...", "info")
                time.sleep(20)
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
            "pydantic==2.11.7", # Updating to latest stable to test Python 3.13 compatibility
            "python-multipart==0.0.6",
            "bcrypt==4.1.2",
            "pyjwt==2.8.0"
        ]
        
        # Set PYO3_USE_ABI3_FORWARD_COMPATIBILITY for Rust-based packages
        original_pyo3_env = os.environ.get("PYO3_USE_ABI3_FORWARD_COMPATIBILITY")
        os.environ["PYO3_USE_ABI3_FORWARD_COMPATIBILITY"] = "1"
        self.print_step("Establecido PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1 para la instalación de dependencias.", "info")

        any_error_occurred = False
        for dep in backend_deps:
            exit_code, output = self.run_command(f"{sys.executable} -m pip install {dep}")
            if exit_code != 0:
                self.print_step(f"Error instalando {dep} (código: {exit_code}): {output}", "error")
                # if self.is_admin: # Keep window open for debugging
                #     self.print_step(f"La instalación de {dep} falló. La ventana se cerrará en 20 segundos...", "info")
                #     time.sleep(20)
                any_error_occurred = True
                # Not breaking here to see all dependency errors, if any.

        # Restore original PYO3_USE_ABI3_FORWARD_COMPATIBILITY value
        if original_pyo3_env is None:
            if "PYO3_USE_ABI3_FORWARD_COMPATIBILITY" in os.environ: # Check before deleting
                del os.environ["PYO3_USE_ABI3_FORWARD_COMPATIBILITY"]
        else:
            os.environ["PYO3_USE_ABI3_FORWARD_COMPATIBILITY"] = original_pyo3_env
        self.print_step("Restaurado el valor original de PYO3_USE_ABI3_FORWARD_COMPATIBILITY.", "info")

        if any_error_occurred:
            self.print_step("Uno o más errores ocurrieron durante la instalación de dependencias de Python.", "error")
            # input("Presiona Enter para salir...") # Moved to main error handling
            return False
        
        self.print_step("Dependencias de Python instaladas", "success")
        return True

    def install_rust(self) -> bool:
        """Instala Rust y Cargo si no están presentes."""
        self.print_step("Verificando Rust (Cargo)...")
        exit_code, cargo_version_output = self.run_command("cargo --version", check=False)
        if exit_code == 0:
            self.print_step(f"Rust (Cargo) ya está instalado: {cargo_version_output.splitlines()[0] if cargo_version_output else 'OK'}", "success")
            return True

        self.print_step("Rust (Cargo) no encontrado. Intentando instalar Rustup...", "info")
        rustup_install_successful = False

        if self.system == "windows":
            self.print_step("Windows detectado: Se requieren MSVC Build Tools para Rust (MSVC target).")
            if not self.install_msvc_build_tools():
                self.print_step("Falló la instalación de MSVC Build Tools. La instalación de Rust (MSVC target) probablemente también fallará o tendrá problemas.", "warning")
                # We can choose to return False here, or let Rust installation attempt proceed and fail.
                # Let's proceed for now, as rustup might have its own checks or fallbacks, or user might fix MSVC manually.

            # Proceed with Rust installation
            temp_dir = Path(tempfile.gettempdir())
            rustup_installer_path = temp_dir / "rustup-init.exe"
            rustup_url = "https://static.rust-lang.org/rustup/dist/x86_64-pc-windows-msvc/rustup-init.exe"

            if self.download_file(rustup_url, rustup_installer_path):
                self.print_step("Ejecutando instalador de Rustup (rustup-init.exe)...")
                install_cmd = [str(rustup_installer_path.resolve()), "-y", "--default-toolchain", "stable", "--profile", "default", "--no-modify-path"]
                exit_code_install, output_install = self.run_command(install_cmd, shell=False, check=False)

                if exit_code_install == 0:
                    self.print_step("Rustup instalado correctamente.", "success")
                    rustup_install_successful = True
                else:
                    self.print_step(f"Falló la instalación de Rustup (código: {exit_code_install}). Salida: {output_install}", "error")

                try:
                    os.unlink(rustup_installer_path)
                except OSError as e:
                    self.print_step(f"Advertencia: no se pudo eliminar {rustup_installer_path}: {e}", "warning")
            else:
                self.print_step(f"Falló la descarga de rustup-init.exe desde {rustup_url}", "error")

        elif self.system in ["linux", "darwin"]:
            # Using the recommended curl | sh method
            # sh -s -- -y installs with default options non-interactively.
            # --no-modify-path to handle PATH update manually for current process.
            # Profile default for necessary components.
            rustup_script_cmd = "curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --default-toolchain stable --profile default --no-modify-path"
            self.print_step("Descargando y ejecutando script de Rustup...")
            exit_code_install, output_install = self.run_command(rustup_script_cmd, shell=True, check=False) # shell=True needed for pipes

            if exit_code_install == 0:
                self.print_step("Rustup instalado correctamente.", "success")
                rustup_install_successful = True
            else:
                self.print_step(f"Falló la instalación de Rustup (código: {exit_code_install}). Salida: {output_install}", "error")
        else:
            self.print_step(f"Instalación de Rust no soportada para el sistema: {self.system}", "warning")
            return False # Or True if Rust is optional and we can proceed without it. Assuming False for now.

        if rustup_install_successful:
            # Add $HOME/.cargo/bin or %USERPROFILE%/.cargo/bin to PATH for the current process
            cargo_bin_path = str(Path.home() / ".cargo" / "bin")
            self.print_step(f"Añadiendo {cargo_bin_path} al PATH para la sesión actual...")
            os.environ["PATH"] = cargo_bin_path + os.pathsep + os.environ["PATH"]

            # Verify installation again
            self.print_step("Verificando Cargo después de la instalación...")
            exit_code_verify, cargo_version_output_verify = self.run_command("cargo --version", check=False)
            if exit_code_verify == 0:
                self.print_step(f"Rust (Cargo) instalado y verificado: {cargo_version_output_verify.splitlines()[0] if cargo_version_output_verify else 'OK'}", "success")
                return True
            else:
                self.print_step(f"Cargo se instaló, pero la verificación falló (código: {exit_code_verify}). Es posible que necesite reiniciar la terminal/shell o el sistema. Salida: {cargo_version_output_verify}", "error")
                return False # Failed to verify after install

        self.print_step("La instalación de Rust falló.", "error")
        return False

    def install_msvc_build_tools(self) -> bool:
        """Instala MSVC Build Tools usando winget en Windows."""
        if self.system != "windows":
            return True # Not applicable for non-Windows

        self.print_step("Verificando/Instalando MSVC Build Tools (esto puede tardar mucho)...", "info")
        # Command to install Visual Studio Build Tools with the C++ workload
        # Using --force to ensure it runs even if winget thinks it might be there, to trigger repair/verify
        # However, --force with winget can sometimes be problematic if not used carefully.
        # Let's try without --force first.
        # The ID for VS Build Tools is typically Microsoft.VisualStudio.BuildTools or Microsoft.VisualStudio.2022.BuildTools
        # Using Microsoft.VisualStudio.2022.BuildTools for better specificity with newer systems.
        # The workload for C++ is Microsoft.VisualStudio.Workload.VCTools
        # Using --override to pass installer-specific arguments.
        # --quiet should make the VS installer less interactive.
        # --wait ensures winget waits for the (potentially very long) installation.
        package_id = "Microsoft.VisualStudio.2022.BuildTools"
        installer_args = "--add Microsoft.VisualStudio.Workload.VCTools --includeRecommended --quiet --wait"

        # We need to ensure the installer_args are passed correctly through winget's --override
        # Winget's --override needs a single string argument. Quotes within that string need care.
        # Example: winget install vscode --override "/silent /mergetasks=!runcode"
        # So, for VS, it might be: --override "--add Workload1 --quiet"
        # The arguments themselves don't need to be quoted if they don't have spaces, but the whole string for --override does.
        # Let's ensure the arguments for VS installer are correctly formatted for the --override.
        # The args like --add don't need their own quotes if they are single tokens.

        # Simpler approach for override: winget expects the arguments to the installer *after* --override as a single string.
        # However, current `run_command` might split them if not careful with shell=True/False.
        # Let's form the command string carefully.
        # `winget install <package> --override "--arg1 --arg2"`
        # The `install_winget_packages` method is more suited for simple package names.
        # We'll call `run_command` directly here for more control.

        # Command structure: winget install <ID> [options for winget] --override "args for installer"
        # Our run_command passes the command as a string if shell=True.
        # Shell=True is default for winget commands in run_command.
        msvc_command = f'winget install {package_id} --accept-package-agreements --accept-source-agreements --override "{installer_args}"'

        self.print_step(f"Ejecutando: {msvc_command}", "info")
        exit_code, output = self.run_command(msvc_command) # run_command handles winget's "already installed" code 2316632107 as success (0)

        if exit_code == 0:
            self.print_step("MSVC Build Tools instalados/verificados correctamente.", "success")
            return True
        else:
            # If it was the "already installed" code that run_command didn't specifically handle for *this package*
            # (because run_command's special handling is for " install " in general, not specific package results),
            # we might need to check output too.
            # For now, trust that if run_command returns non-zero, it's a genuine failure for this context.
            self.print_step(f"Falló la instalación/verificación de MSVC Build Tools (código: {exit_code}).", "error")
            self.print_step(f"Salida: {output}", "info")
            # No time.sleep here as this is a sub-step of Rust install; Rust install itself may pause.
            return False

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
ollama pull llama3.1:8b

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
        # We use check=False as it might already be running or fail gracefully if not yet fully installed.
        self.run_command("ollama serve", check=False)
        time.sleep(5)
        
        # Modelos básicos a instalar
        models = ["magistral:24b", "qwen3:32b", "llama3.1:8b"]
        
        for model in models:
            self.print_step(f"Descargando modelo {model}...")
            # Using check=True here as 'ollama pull' should ideally succeed.
            # If it fails, we print a warning but continue with other models.
            exit_code, output = self.run_command(f"ollama pull {model}", check=True)
            if exit_code == 0:
                self.print_step(f"Modelo {model} instalado", "success")
            else:
                self.print_step(f"Error instalando {model} (código: {exit_code}): {output}", "warning")
        
        return True # This step is best-effort for models.
    
    def setup_database(self) -> bool:
        """Configura la base de datos"""
        self.print_step("Configurando base de datos...")
        
        # Start PostgreSQL with Docker for setup
        # Using check=True as these Docker operations are critical for DB setup.
        pg_setup_cmd = "docker run -d --name manus-postgres-setup -e POSTGRES_DB=manus_db -e POSTGRES_USER=manus_user -e POSTGRES_PASSWORD=manus_password_2024 -p 5432:5432 postgres:15"
        exit_code_run, output_run = self.run_command(pg_setup_cmd, check=True)

        if exit_code_run != 0:
            self.print_step(f"Error iniciando contenedor PostgreSQL para setup (código: {exit_code_run}): {output_run}", "error")
            return False
            
        self.print_step("Contenedor PostgreSQL para setup iniciado. Esperando 10s...", "info")
        time.sleep(10)  # Esperar a que PostgreSQL se inicie
            
        init_script = self.install_dir / "config" / "supabase_init.sql"
        data_script = self.install_dir / "config" / "initial_data.sql"
        
        db_setup_ok = True
        if init_script.exists():
            self.print_step(f"Ejecutando script de inicialización: {init_script}")
            # Note: Input redirection might be tricky with run_command's current shell handling.
            # Consider using Popen directly for commands with input redirection if issues arise.
            # For now, assuming simple exec commands.
            # This command structure is problematic for self.run_command as it involves redirection.
            # Let's use a more direct approach or adjust run_command if this specific pattern is frequent.
            # Simplified for now:
            # exit_code_init, out_init = self.run_command(f"docker exec -i manus-postgres-setup psql -U manus_user -d manus_db < \"{init_script}\"", check=True)
            # This type of command with redirection is better handled by shell=True and as a single string.
            cmd_init = f"docker exec -i manus-postgres-setup psql -U manus_user -d manus_db < \"{init_script.resolve()}\""
            exit_code_init, out_init = self.run_command(cmd_init, shell=True, check=True) # Explicitly shell=True
            if exit_code_init != 0:
                self.print_step(f"Error ejecutando script de inicialización DB (código: {exit_code_init}): {out_init}", "error")
                db_setup_ok = False

        if db_setup_ok and data_script.exists():
            self.print_step(f"Ejecutando script de datos iniciales: {data_script}")
            cmd_data = f"docker exec -i manus-postgres-setup psql -U manus_user -d manus_db < \"{data_script.resolve()}\""
            exit_code_data, out_data = self.run_command(cmd_data, shell=True, check=True) # Explicitly shell=True
            if exit_code_data != 0:
                self.print_step(f"Error ejecutando script de datos DB (código: {exit_code_data}): {out_data}", "error")
                db_setup_ok = False

        # Stop and remove temporary container
        self.print_step("Deteniendo contenedor PostgreSQL de setup...")
        exit_code_stop, out_stop = self.run_command("docker stop manus-postgres-setup", check=True)
        if exit_code_stop != 0:
            self.print_step(f"Advertencia: No se pudo detener el contenedor manus-postgres-setup (código: {exit_code_stop}): {out_stop}", "warning")
            # Not returning False here, as DB scripts might have run.

        exit_code_rm, out_rm = self.run_command("docker rm manus-postgres-setup", check=True)
        if exit_code_rm != 0:
            self.print_step(f"Advertencia: No se pudo remover el contenedor manus-postgres-setup (código: {exit_code_rm}): {out_rm}", "warning")

        if db_setup_ok:
            self.print_step("Base de datos configurada", "success")
            return True
        else:
            self.print_step("Falló la configuración de la base de datos.", "error")
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
            self.print_step(f"Ejecutando 'npm install' en {frontend_dir}...")
            exit_code, output = self.run_command("npm install") # Defaults to shell=True, check=True
            
            # Volver al directorio original
            os.chdir(original_dir)
            
            if exit_code == 0:
                self.print_step("Dependencias del frontend instaladas", "success")
                return True
            else:
                self.print_step(f"Error instalando dependencias del frontend (código: {exit_code}): {output}", "error")
                return False
                
        except Exception as e: # Catches errors like os.chdir failing
            self.print_step(f"Error excepcional durante instalación de dependencias frontend: {e}", "error")
            # Ensure we change back to original_dir if an exception occurred after os.chdir but before the second os.chdir
            if 'original_dir' in locals() and Path.cwd() != Path(original_dir):
                 os.chdir(original_dir)
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
                
                # This command is primarily for its side effect; output isn't critical.
                # Using check=False as failure here is not fatal for the whole setup.
                exit_code, ps_output = self.run_command(f"powershell -ExecutionPolicy Bypass -File \"{ps_file}\"", check=False)
                if exit_code != 0:
                    self.print_step(f"Advertencia: Falló la creación del acceso directo con PowerShell (código: {exit_code}): {ps_output}", "warning")
                os.unlink(ps_file) # Clean up temp file
            
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
            ("Instalando Rust (si es necesario)", self.install_rust), # Added Rust installation step
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
    write_very_early_log("main(): Script started.")
    try:
        installer = SystemInstaller() # Python check happens in __init__
        write_very_early_log("main(): SystemInstaller instance created.")
    except Exception as e:
        write_very_early_log(f"main(): EXCEPTION during SystemInstaller instantiation: {e}")
        # Attempt to print to console as a last resort, though it might not be visible
        print(f"Critical error during SystemInstaller instantiation: {e}")
        sys.exit(1) # Exit if installer can't even be created

    # Early log for elevated process (using the new very_early_log)
    if installer.is_admin:
        write_very_early_log(f"main(): Running as admin. Python: {sys.executable}")
    else:
        write_very_early_log(f"main(): Not running as admin. Python: {sys.executable}")

    # The old log_file_path for manus_setup_elevated.log can be removed or kept.
    # For now, let's keep it to see if it also works, but our primary focus is VERY_EARLY_LOG_FILE.
    log_file_path = None # Initialize
    if installer.is_admin:
        log_file_path = Path(tempfile.gettempdir()) / "manus_setup_elevated.log" # Original elevated log
        try:
            with open(log_file_path, "a", encoding="utf-8") as log_f: # Changed variable name
                log_f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Elevated script instance started (old log). Python: {sys.executable}\n")
        except Exception as e:
            write_very_early_log(f"main(): Warning - Could not write to old elevated log file {log_file_path}: {e}")
            # installer.print_step might not be safe if installer instance failed, but we check instance creation above.
            # For safety, using write_very_early_log for this warning.

    try:
        write_very_early_log("main(): Entering main try block.")
        # Check for admin rights and re-launch if necessary
        if not installer.is_admin:
            write_very_early_log("main(): Admin rights not detected. Attempting elevation.")
            installer.print_step("Se requieren permisos de administrador.", "warning")
            installer.print_step("Se requieren permisos de administrador para continuar.", "warning")
            installer.print_step("El script intentará solicitar estos permisos.", "info")
            installer.print_step("Si aparece una ventana de Control de Cuentas de Usuario (UAC), por favor acepte.", "info")
            installer.print_step("Se abrirá una NUEVA VENTANA de consola donde continuará la instalación.", "info")
            installer.print_step("Por favor, siga las instrucciones en la NUEVA ventana.", "info")
            input("Presione Enter para intentar la elevación de privilegios...") # Pause for user to read

            installer.print_step("Intentando re-lanzar con privilegios elevados...", "info")
            installer._run_as_admin() # This will exit if ShellExecuteW fails, or replace process on Unix
            # If _run_as_admin on Windows returns (because ShellExecuteW > 32), it means it *attempted* to start the new process.
            # The current non-admin script should now inform the user and exit.
            # The previous messages already informed the user about the new window.
            installer.print_step("Si la elevación fue exitosa, la instalación continuará en una nueva ventana.", "info")
            installer.print_step("Esta ventana actual se cerrará en 10 segundos...", "info")
            time.sleep(10) # Give user time to read
            sys.exit(0) # Gracefully exit the non-elevated script

        # If we reach here, we are running with admin rights (either initially or after elevation)
        if installer.is_admin and 'log_file_path' in locals(): # Log before running installation
             with open(log_file_path, "a", encoding="utf-8") as log_file:
                log_file.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Admin rights confirmed. Calling run_installation().\n")

        if installer.run_installation(): # This is the main execution path for the admin instance
            write_very_early_log("main(): run_installation() completed successfully.")
            installer.show_completion_message()
            if installer.is_admin and 'log_file_path' in locals() and log_file_path is not None: # Check log_file_path not None
                try: # Add try-except for old log
                    with open(log_file_path, "a", encoding="utf-8") as log_f: # Changed variable
                        log_f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Installation successful (old log).\n")
                except Exception as e:
                    write_very_early_log(f"main(): Warning - Could not write to old elevated log {log_file_path} on success: {e}")
            
            write_very_early_log("main(): Before asking to start the system.")
            if input("\n¿Deseas iniciar el sistema ahora? (s/n): ").lower() in ['s', 'y', 'yes', 'sí']:
                write_very_early_log("main(): User chose to start the system.")
                script_to_run = ""
                if installer.system == "windows":
                    write_very_early_log("main(): System is Windows. Preparing to run start.bat.")
                    script_to_run = installer.install_dir / "scripts" / "start.bat" # Necesario para el print_step más adelante

                    # INTENTO DE LOGGING AISLADO Y TEMPRANO para setup_debug_trace.log
                    early_trace_path_debug = None # Para registrar en caso de error aquí
                    try:
                        write_very_early_log("main(): Windows: Attempting to create logs directory and setup_debug_trace.log (isolated test).")
                        log_dir_test = installer.install_dir / "logs"
                        write_very_early_log(f"main(): Windows (isolated test): log_dir_test path is {log_dir_test}")

                        log_dir_test.mkdir(exist_ok=True)
                        write_very_early_log(f"main(): Windows (isolated test): mkdir for {log_dir_test} attempted (exist_ok=True).")

                        early_trace_path_debug = log_dir_test / "setup_debug_trace.log"
                        with open(early_trace_path_debug, "a", encoding='utf-8') as etf:
                            etf.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Test log entry from isolated block. If you see this, directory creation and initial file write worked.\n")
                        write_very_early_log(f"main(): Windows (isolated test): Successfully wrote test entry to {early_trace_path_debug}.")
                    except Exception as e_test:
                        write_very_early_log(f"main(): Windows (isolated test): EXCEPTION in isolated logging attempt for setup_debug_trace.log. Error: {e_test}. Path was: {early_trace_path_debug if early_trace_path_debug else str(installer.install_dir / 'logs' / 'setup_debug_trace.log')}")

                    installer.print_step(f"Ejecutando script de inicio: {script_to_run}...", "info") # Mantener para flujo visual si no crashea antes

                    # try original (ahora con el logging detallado que ya teníamos)
                    try:
                        # El NUEVO LOGGING DETALLADO (que ahora usa trace_log_file_path)
                        # La definición de trace_log_file_path se mueve aquí para que coincida con el original.
                        trace_log_file_path = installer.install_dir / "logs" / "setup_debug_trace.log" # Esta es la misma ruta que early_trace_path_debug
                        log_dir_for_trace = installer.install_dir / "logs"
                        log_dir_for_trace.mkdir(exist_ok=True) # Asegurar que el directorio de logs existe para el trace log

                        with open(trace_log_file_path, "a", encoding='utf-8') as trace_f:
                            trace_f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] --- Iniciando intento de ejecución de start.bat ---\n")
                            trace_f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Script a ejecutar: {script_to_run.name}\n")
                            trace_f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] CWD para subprocess: {str(script_to_run.parent)}\n")
                            trace_f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Antes de llamar a subprocess.run.\n")

                        process_result = None # Inicializar por si subprocess.run falla catastróficamente

                        try: # Bloque try interno para la ejecución de subprocess y el logging principal
                            with open(trace_log_file_path, "a", encoding='utf-8') as trace_f:
                                trace_f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Intentando lanzar start.bat con Popen y DETACHED_PROCESS/CREATE_NEW_CONSOLE.\n")

                            # Usar Popen para más control sobre la creación del proceso
                            # Intentar con la ruta completa al script
                            full_script_path = str(script_to_run.resolve())
                            with open(trace_log_file_path, "a", encoding='utf-8') as trace_f:
                                trace_f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Usando ruta completa para Popen: {full_script_path}.\n")

                            process = subprocess.Popen(
                                ['cmd', '/c', full_script_path], # Usar ruta completa
                                cwd=str(script_to_run.parent), # Mantener CWD por si start.bat depende de él para otros archivos
                                shell=False,
                                creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_CONSOLE
                            )

                            with open(trace_log_file_path, "a", encoding='utf-8') as trace_f:
                                trace_f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] start.bat lanzado con Popen (ruta completa, sin captura stdout/stderr directa). PID (si está disponible): {process.pid}.\n")
                                trace_f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] setup.py continuará y finalizará. Revisa si apareció una nueva ventana para start.bat.\n")

                            # stdout, stderr = process.communicate(timeout=10) # Podríamos intentar un communicate con timeout
                                                                            # pero con detached process esto podría no funcionar como se espera.
                                                                            # Por ahora, solo lo lanzamos.

                            # No podemos obtener process_result.returncode directamente de Popen sin esperar.
                            # El objetivo aquí es ver si start.bat se ejecuta y si su ventana muestra algo.
                            # El logging de la salida de start.bat (stdout/stderr) a setup_start_bat_output.log
                            # probablemente no funcionará como antes con DETACHED_PROCESS si no usamos communicate().

                            # Eliminamos la escritura a setup_start_bat_output.log por ahora,
                            # ya que el foco es ver si start.bat se ejecuta visiblemente.
                            # El log de start.bat (debug_start_bat.log y docker_compose_output.log si start.bat está modificado)
                            # sería la fuente de información de lo que hace start.bat.

                            installer.print_step(f"Script de inicio ({script_to_run.name}) invocado en una nueva ventana (esperado).", "info")
                            installer.print_step("Revisa si apareció una nueva ventana de consola para start.bat y si muestra errores.", "warning")
                            installer.print_step("setup.py ahora esperará 15 segundos antes de salir para dar tiempo a observar.", "info")
                            time.sleep(15) # Dar tiempo a observar la nueva ventana

                        except Exception as sub_e: # Captura error de Popen
                            with open(trace_log_file_path, "a", encoding='utf-8') as trace_f:
                                trace_f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] EXCEPCIÓN durante subprocess.Popen: {sub_e}\n")
                            installer.print_step(f"Excepción al intentar lanzar {script_to_run.name} con Popen: {sub_e}", "error")

                        # El bloque finally original ya no es tan relevante aquí porque no estamos esperando a process_result
                        # pero lo dejamos por si acaso, o lo podemos eliminar/ajustar.
                        # Por ahora, lo comentaré para simplificar, ya que su propósito original
                        # estaba ligado a la finalización de subprocess.run.
                        # finally: # Finally para el try interno de subprocess
                        #     with open(trace_log_file_path, "a", encoding='utf-8') as trace_f:
                        #         trace_f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Bloque finally del try interno de Popen (ajustado) alcanzado.\n")

                    # except originales del script
                    except subprocess.CalledProcessError as e:
                        with open(trace_log_file_path, "a", encoding='utf-8') as trace_f:
                            trace_f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] EXCEPCIÓN (CalledProcessError): {e}. stdout: {e.stdout}, stderr: {e.stderr}\n")
                        installer.print_step(f"El script de inicio ({script_to_run.name}) encontró un error (CalledProcessError): {e}. stdout: {e.stdout}, stderr: {e.stderr}", "error")
                    except FileNotFoundError:
                        with open(trace_log_file_path, "a", encoding='utf-8') as trace_f:
                            trace_f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] EXCEPCIÓN (FileNotFoundError): No se encontró {script_to_run}\n")
                        installer.print_step(f"Error: No se encontró el script de inicio en {script_to_run}", "error")
                    except Exception as e:
                        # Este es el catch-all más externo para esta sección
                        # Asegurémonos de que trace_log_file_path esté definido incluso si el error ocurre antes de su primera asignación
                        # (aunque en este flujo, se asigna justo al entrar al 'try' original)
                        current_time_for_log = time.strftime('%Y-%m-%d %H:%M:%S')
                        if 'trace_log_file_path' not in locals():
                             # Definir una ruta de emergencia si es necesario, aunque no debería ser el caso aquí.
                             # Esto es más por robustez extrema.
                             emergency_log_dir = Path.home() / "manus_system_emergency_logs"
                             emergency_log_dir.mkdir(exist_ok=True)
                             trace_log_file_path_emergency = emergency_log_dir / "setup_debug_trace_emergency.log"
                             with open(trace_log_file_path_emergency, "a", encoding='utf-8') as trace_f_emergency:
                                trace_f_emergency.write(f"[{current_time_for_log}] EXCEPCIÓN GENERAL (trace_log_file_path no definido): {e}\n")
                        else: # Ruta normal del log de trace
                             with open(trace_log_file_path, "a", encoding='utf-8') as trace_f:
                                trace_f.write(f"[{current_time_for_log}] EXCEPCIÓN GENERAL en bloque de ejecución de start.bat: {e}\n")
                        installer.print_step(f"Error inesperado al ejecutar {script_to_run.name if 'script_to_run' in locals() else 'script desconocido'}: {e}", "error")
                else:
                    script_to_run = installer.install_dir / "scripts" / "start.sh"
                    installer.print_step(f"Ejecutando script de inicio: {script_to_run}...", "info")
                    # For Linux/macOS, os.system is generally fine as it often inherits the console
                    os.system(f'sh "{script_to_run}"') # Ensure sh is used for .sh
        else:
            # This message is from the ELEVATED script if run_installation() returns False
            installer.print_step("La instalación falló (proceso elevado).", "error")
            if installer.is_admin and 'log_file_path' in locals():
                with open(log_file_path, "a", encoding="utf-8") as log_file:
                    log_file.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] run_installation() returned False.\n")
            input("Presiona Enter para salir...")
            sys.exit(1)
            
    except KeyboardInterrupt:
        installer.print_step("Instalación cancelada por el usuario.", "warning")
        if 'log_file_path' in locals() and installer.is_admin:
             with open(log_file_path, "a", encoding="utf-8") as log_file:
                log_file.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Installation cancelled by user.\n")
        input("Presiona Enter para salir...")
        sys.exit(1)
    except Exception as e:
        installer.print_step(f"Error inesperado: {e}", "error")
        if 'log_file_path' in locals() and installer.is_admin: # Redundant check for log_file_path, but safe
            with open(log_file_path, "a", encoding="utf-8") as log_file:
                log_file.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Unexpected error: {e}\n")
        input("Presiona Enter para salir...")
        sys.exit(1)

    # For successful completion, the input() prompt for starting the system already keeps the window open.
    # So, we only need the explicit input() pause in the error paths above for the admin instance.

if __name__ == "__main__":
    main()
