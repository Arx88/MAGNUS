import os
import shutil
import subprocess
import datetime
import configparser # Para leer el project_id de config.toml
import platform # Para detectar el sistema operativo
import json
import urllib.request
import zipfile
import tarfile
import stat # Para os.chmod
import ctypes # Para verificar privilegios de administrador en Windows
import sys # Para sys.exit()
import getpass # Para solicitar contraseñas de forma segura

# Constantes
SUPABASE_IN_PATH = "supabase_found_in_path" # Constante para indicar que se usa la CLI del PATH
SUPABASE_DIR = "supabase"
MIGRATIONS_DIR = os.path.join(SUPABASE_DIR, "migrations")
CONFIG_FILE_PATH = os.path.join(SUPABASE_DIR, "config.toml") # supabase/config.toml
INIT_SQL_FILE = "supabase_init.sql"

def print_header(title):
    print("\n" + "=" * 40)
    print(title)
    print("=" * 40)

def print_success(message):
    print(f"\n✅ SUCCESS: {message}")

def print_error(message):
    print(f"\n❌ ERROR: {message}")

def print_info(message):
    print(f"\nℹ️ INFO: {message}")

def print_warning(message):
    print(f"\n⚠️ WARNING: {message}")

def run_command(command_list, timeout=60, check=True, suppress_output=False, supabase_executable_path=None):
    """Ejecuta un comando de subprocess de forma segura y devuelve (éxito, stdout, stderr)."""
    actual_command_list = list(command_list) # Copiar para poder modificarla

    if supabase_executable_path and actual_command_list[0] == "supabase":
        # Si se proporciona una ruta ejecutable y el comando es "supabase", usar la ruta.
        # Esto es útil si supabase_executable_path es una ruta completa y command_list[0] es solo "supabase".
        actual_command_list[0] = supabase_executable_path
    elif supabase_executable_path and actual_command_list[0] != "supabase" and os.path.basename(actual_command_list[0]) == "supabase.exe":
        # Si supabase_executable_path se pasó como el primer elemento de command_list directamente.
        # No es necesario hacer nada, actual_command_list[0] ya es la ruta completa.
        pass


    # Asegurarse de que si el comando es una ruta directa (ej. resultado de check_supabase_cli),
    # y los argumentos se pasaron por separado, se reconstruya correctamente.
    # Esta situación se maneja mejor en el código que llama a run_command, asegurando
    # que command_list[0] sea el ejecutable correcto.

    # La lógica anterior es un poco redundante si las funciones que llaman a run_command
    # ya construyen command_list con [ruta_completa_o_comando, arg1, arg2].
    # Simplifiquemos: si supabase_executable_path se pasa Y el primer comando es "supabase",
    # entonces reemplazamos "supabase" con supabase_executable_path.
    # Si command_list[0] ya es una ruta completa, entonces supabase_executable_path no debería
    # ser necesario o debería coincidir.

    # Lógica simplificada:
    # La función que llama a run_command es responsable de construir el inicio de command_list
    # correctamente (sea "supabase" o "/path/to/supabase").
    # supabase_executable_path en run_command es una conveniencia para el caso de que
    # el código más antiguo siga llamando con ["supabase", "arg"] pero necesitemos sobreescribir "supabase".

    # Re-simplificación de la lógica de `actual_command_list`
    # Si el primer elemento de command_list es "supabase" Y supabase_executable_path está definido (y no es "supabase")
    # entonces usamos supabase_executable_path como el comando.
    # Sino, usamos command_list[0] como está.

    cmd_to_run = list(command_list) # Copia de la lista original

    if cmd_to_run[0] == "supabase" and supabase_executable_path and supabase_executable_path != "supabase":
        cmd_to_run[0] = supabase_executable_path
    # Si cmd_to_run[0] ya es una ruta completa (porque supabase_executable_path se usó para construirlo fuera),
    # y supabase_executable_path también se pasa (y es igual), está bien.
    # Si cmd_to_run[0] es una ruta completa y supabase_executable_path es None o "supabase", también está bien.

    try:
        process = subprocess.run(
            cmd_to_run, # Usar la lista procesada
            capture_output=True,
            text=True,
            check=check,
            timeout=timeout,
            encoding='utf-8',
            errors='replace'
        )
        if not suppress_output:
            if process.stdout and process.stdout.strip():
                print_info(f"Salida de {' '.join(command_list)}:\n{process.stdout.strip()}")
            if process.stderr and process.stderr.strip():
                print_warning(f"Salida de error (puede ser informativa) de {' '.join(command_list)}:\n{process.stderr.strip()}")
        return True, process.stdout.strip(), process.stderr.strip()
    except subprocess.CalledProcessError as e:
        if not suppress_output:
            print_error(f"Error al ejecutar: {' '.join(command_list)}")
            if e.stdout and e.stdout.strip(): print_info(f"Salida (stdout) del error: {e.stdout.strip()}")
            if e.stderr and e.stderr.strip(): print_error(f"Salida (stderr) del error: {e.stderr.strip()}")
        return False, e.stdout.strip() if e.stdout else "", e.stderr.strip() if e.stderr else ""
    except FileNotFoundError:
        if not suppress_output:
            print_error(f"Comando no encontrado: {command_list[0]}. Asegúrate de que esté instalado y en el PATH.")
        return False, "", f"Comando no encontrado: {command_list[0]}"
    except subprocess.TimeoutExpired:
        if not suppress_output:
            print_error(f"El comando '{' '.join(command_list)}' tardó demasiado en responder (timeout: {timeout}s).")
        return False, "", f"Timeout ({timeout}s) para el comando: {' '.join(command_list)}"
    except Exception as e:
        if not suppress_output:
            print_error(f"Error inesperado al ejecutar {' '.join(command_list)}: {e}")
        return False, "", str(e)

def check_supabase_cli(): # Modificado para devolver ruta, SUPABASE_IN_PATH o False
    print_info("Verificando Supabase CLI...")
    # Usar run_command directamente, ya que supabase_executable_path no está definido aún en este punto.
    success, initial_stdout, initial_stderr = run_command(["supabase", "--version"], suppress_output=True)
    if success:
        print_success("Supabase CLI ya está instalada y en el PATH.")
        return SUPABASE_IN_PATH

    print_warning("Supabase CLI no está instalada o no se encuentra en el PATH.")

    attempt_auto_install = input("¿Deseas que el script intente instalar Supabase CLI automáticamente? (s/N): ").strip().lower()
    if attempt_auto_install != 's':
        print_info("Instalación automática omitida por el usuario.")
        print_info("Por favor, instala Supabase CLI manualmente: https://supabase.com/docs/guides/cli/getting-started")
        return False

    # --- Secuencia de intentos de instalación ---
    # 1. WINGET (Solo Windows)
    if platform.system() == "Windows":
        print_header("Intentando instalación con Winget (Windows)")
        winget_available, _, _ = run_command(["winget", "--version"], suppress_output=True)
        if winget_available:
            print_info("Winget detectado. Intentando actualizar fuentes...")
            run_command(["winget", "source", "update"], timeout=180, check=False)
            print_info("Intento de actualización de fuentes de Winget completado.")

            package_id = "Supabase.SupabaseCLI"
            print_info(f"Buscando el paquete '{package_id}' con Winget...")
            search_cmd = ["winget", "search", package_id, "--source", "winget", "--accept-source-agreements"]
            search_success, search_stdout, search_stderr_search = run_command(search_cmd, timeout=120, check=False)

            if search_success and package_id.lower() in search_stdout.lower() and "No se encontró ningún paquete" not in search_stdout :
                print_success(f"Paquete '{package_id}' encontrado vía Winget.")
                print_info(f"Intentando instalar '{package_id}' con Winget...")
                winget_cmd = ["winget", "install", package_id, "--source", "winget", "--accept-package-agreements", "--accept-source-agreements"]
                install_success, install_stdout, install_stderr_install = run_command(winget_cmd, timeout=300, check=False)

                if install_success and \
                   ("instalado correctamente" in install_stdout.lower() or "successfully installed" in install_stdout.lower()) and \
                   "No se encontró ningún paquete" not in install_stdout and \
                   "No se encontró ningún paquete" not in install_stderr_install:
                    print_success("Winget reportó instalación exitosa. Verificando...")
                    if run_command(["supabase", "--version"], suppress_output=True)[0]:
                        print_success("¡Supabase CLI instalada y verificada exitosamente vía Winget!")
                        print_warning("Es posible que necesites REINICIAR TU TERMINAL (o VSCode) para que el PATH se actualice.")
                        return SUPABASE_IN_PATH
                    else:
                        print_error("Supabase CLI no se encuentra después de la instalación con Winget (aunque Winget indicó éxito).")
                        return False # Fallo explícito
                else:
                    print_error("Falló la instalación con Winget o no se confirmó el éxito en la salida.")
                    return False # Fallo explícito
            else:
                print_warning(f"Winget no pudo encontrar/confirmar el paquete '{package_id}'. (Search stdout: '{search_stdout}', stderr: '{search_stderr_search}')")
                # No retornar False aquí, permite que otros métodos continúen
        else:
            print_info("Winget no está disponible en este sistema.")

    # 2. SCOOP (Solo Windows, con intento de instalación de Scoop)
    if platform.system() == "Windows":
        print_header("Intentando instalación con Scoop")
        scoop_available, _, _ = run_command(["scoop", "--version"], suppress_output=True)
        if not scoop_available:
            print_info("Scoop no está disponible. Intentando instalar Scoop automáticamente...")
            # No más preguntas aquí, procedemos si attempt_auto_install fue 's'
            # El siguiente bloque se ejecuta si scoop no está disponible y el usuario aceptó la instalación automática general.
            print_info("Intentando instalar Scoop...")
            ps_command_policy = "Set-ExecutionPolicy RemoteSigned -Scope CurrentUser -Force"
            ps_command_install = "iex (new-object net.webclient).downloadstring('https://get.scoop.sh')"

            print_warning("Cambiando política de ejecución de PowerShell para CurrentUser a RemoteSigned...")
            policy_success, _, policy_err = run_command(["powershell", "-Command", ps_command_policy], timeout=60, check=False)
            if not policy_success:
                print_error(f"No se pudo cambiar la política de ejecución de PowerShell. Detalle: {policy_err}")
            else:
                print_success("Política de ejecución de PowerShell actualizada para CurrentUser.")
                print_info("Descargando y ejecutando script de instalación de Scoop...")
                install_scoop_success, _, scoop_install_err = run_command(["powershell", "-Command", ps_command_install], timeout=300, check=False)
                if install_scoop_success:
                    print_success("Script de instalación de Scoop ejecutado. Verificando Scoop...")
                    scoop_available, _, _ = run_command(["scoop", "--version"], suppress_output=True)
                    if scoop_available:
                        print_success("¡Scoop instalado exitosamente!")
                    else:
                        print_error(f"Scoop no se pudo verificar después de la instalación. Error: {scoop_install_err}")
                else:
                    scoop_install_err_lower = scoop_install_err.lower()
                    if "running the installer as administrator is disabled" in scoop_install_err_lower or "abort." in scoop_install_err_lower:
                        print_error("La instalación de Scoop falló porque requiere privilegios de administrador.")
                        print_warning("Por favor, re-ejecuta este script (supabase_setup.py) como Administrador.")
                    else:
                        print_error(f"Falló la ejecución del script de instalación de Scoop. Error: {scoop_install_err}")

        if scoop_available: # Si estaba disponible o se instaló y verificó
            print_info("Intentando instalar 'supabase' con Scoop...")
            install_success, _, _ = run_command(["scoop", "install", "supabase"], timeout=300, check=False)
            if install_success:
                print_success("Comando 'scoop install supabase' ejecutado. Verificando...")
                if run_command(["supabase", "--version"], suppress_output=True)[0]:
                    print_success("¡Supabase CLI instalada y verificada exitosamente vía Scoop!")
                    print_warning("Es posible que necesites REINICIAR TU TERMINAL (o VSCode) para que el PATH se actualice.")
                    return SUPABASE_IN_PATH
                else:
                    print_error("Supabase CLI no se encuentra después de la instalación con Scoop.")
                    return False # Fallo explícito
            else:
                print_error("Falló la instalación de Supabase CLI con Scoop.")
                return False # Fallo explícito

    # 3. NPM (Multiplataforma)
    print_header("Intentando instalación con NPM")
    npm_available, _, _ = run_command(["npm", "--version"], suppress_output=True)
    if npm_available:
        print_info("NPM detectado. Intentando instalar 'supabase' globalmente...")
        install_success, _, _ = run_command(["npm", "install", "supabase", "--global"], timeout=300, check=False)
        if install_success:
            print_success("Comando 'npm install supabase --global' ejecutado. Verificando...")
            if run_command(["supabase", "--version"], suppress_output=True)[0]:
                print_success("¡Supabase CLI instalada y verificada exitosamente vía NPM!")
                print_warning("Es posible que necesites REINICIAR TU TERMINAL (o VSCode) para que el PATH se actualice.")
                return SUPABASE_IN_PATH
            else:
                print_error("Supabase CLI no se encuentra después de la instalación con NPM.")
                print_info("Esto es común si el directorio global de paquetes de NPM no está en tu PATH o si la terminal necesita reiniciarse.")
                return False # Fallo explícito
        else:
            print_error("Falló la instalación con NPM.")
            return False # Fallo explícito
    else:
        print_info("NPM no está disponible en este sistema. Para usar este método, instala Node.js y NPM.")

    # 4. DESCARGA DIRECTA DESDE GITHUB RELEASES (Multiplataforma)
    print_header("Intentando descarga directa de Supabase CLI desde GitHub")
    try:
        print_info("Obteniendo información de la última release de Supabase CLI...")
        api_url = "https://api.github.com/repos/supabase/cli/releases/latest"
        release_data = {} # Inicializar en caso de error de red/API
        try:
            with urllib.request.urlopen(api_url, timeout=10) as response:
                release_data = json.loads(response.read().decode())
        except urllib.error.URLError as e:
            print_error(f"Error de red al contactar la API de GitHub: {e.reason}")
            print_info("Por favor, verifica tu conexión a internet.")
        except json.JSONDecodeError:
            print_error("No se pudo decodificar la respuesta de la API de GitHub (formato inesperado).")
        except Exception as e:
            print_error(f"Error inesperado al obtener datos de release: {e}")

        assets = release_data.get("assets", [])
        if not assets:
            print_error("No se encontraron assets en la última release de GitHub (o hubo un error previo al obtenerlos).")
        else:
            os_type = platform.system().lower()
            arch = platform.machine().lower()

            asset_identifier = None
            asset_ext = ""
            exe_name = "supabase" # Nombre por defecto para Linux/macOS

            if os_type == "windows":
                exe_name = "supabase.exe"
                asset_ext = ".tar.gz" # Cambiado de .zip a .tar.gz
                if arch in ["amd64", "x86_64"]: asset_identifier = "windows_amd64" # Cambiado de windows-amd64
                elif arch in ["arm64", "aarch64"]: asset_identifier = "windows_arm64" # Cambiado de windows-arm64
            elif os_type == "linux":
                asset_ext = ".tar.gz"
                if arch in ["amd64", "x86_64"]: asset_identifier = "linux_amd64" # _ en lugar de -
                elif arch in ["arm64", "aarch64"]: asset_identifier = "linux_arm64" # _ en lugar de -
            elif os_type == "darwin": # macOS
                asset_ext = ".tar.gz"
                if arch in ["amd64", "x86_64"]: asset_identifier = "darwin_amd64" # _ en lugar de -
                elif arch in ["arm64", "aarch64"]: asset_identifier = "darwin_arm64" # _ en lugar de -

            if not asset_identifier:
                print_error(f"Combinación SO/arquitectura no soportada para descarga directa: {os_type}/{arch}")
            else:
                # El nombre del asset suele ser supabase_{version}_{os}_{arch}{ext} o supabase_{os}_{arch}{ext}
                # Ejemplo: supabase_2.26.9_windows_amd64.tar.gz o supabase_windows_amd64.tar.gz
                # La clave es buscar "supabase_" seguido por el asset_identifier y la extensión.
                # También puede haber una "v" antes de la versión.
                print_info(f"Buscando asset que contenga 'supabase_' y '{asset_identifier}' y termine con '{asset_ext}'")
                download_url = None
                found_asset_name = ""

                for asset in assets:
                    name_lower = asset.get("name", "").lower()
                    # Criterios de búsqueda:
                    # 1. Debe contener "supabase_"
                    # 2. Debe contener el asset_identifier (ej. "windows_amd64")
                    # 3. Debe terminar con la asset_ext (ej. ".tar.gz")
                    if "supabase_" in name_lower and \
                       asset_identifier in name_lower and \
                       name_lower.endswith(asset_ext):

                        # Podría haber múltiples coincidencias si hay formatos antiguos o alternativos.
                        # Damos preferencia a los que no tienen "checksum" o extensiones adicionales raras.
                        if "checksums.txt" in name_lower or ".sig" in name_lower or ".pem" in name_lower:
                            continue

                        download_url = asset.get("browser_download_url")
                        found_asset_name = asset.get("name")
                        print_success(f"Asset encontrado para descarga: {found_asset_name}")
                        break # Tomar el primero que coincida con los criterios principales

                if not download_url:
                    print_error(f"No se encontró un asset de descarga compatible para '{asset_identifier}' con extensión '{asset_ext}' en la última release.")
                else:
                    print_info(f"Descargando Supabase CLI desde: {download_url}")
                    temp_dir = "temp_supabase_cli_download" # Nombre diferente para evitar colisiones
                    os.makedirs(temp_dir, exist_ok=True)
                    download_path = os.path.join(temp_dir, found_asset_name)

                    try:
                        urllib.request.urlretrieve(download_url, download_path)
                        print_success(f"Descargado en: {download_path}")

                        print_info("Extrayendo binario...")
                        extracted_bin_path = None
                        if asset_ext == ".zip":
                            with zipfile.ZipFile(download_path, 'r') as zip_ref:
                                for member_info in zip_ref.infolist():
                                    if member_info.filename.lower().endswith(exe_name.lower()) and not member_info.is_dir():
                                        zip_ref.extract(member_info, temp_dir)
                                        extracted_bin_path = os.path.join(temp_dir, member_info.filename)
                                        break
                        elif asset_ext == ".tar.gz":
                            with tarfile.open(download_path, "r:gz") as tar_ref:
                                for member_info in tar_ref.getmembers():
                                    if member_info.name.lower().endswith(exe_name.lower()) and member_info.isfile():
                                        tar_ref.extract(member_info, temp_dir)
                                        extracted_bin_path = os.path.join(temp_dir, member_info.name)
                                        break

                        if not extracted_bin_path or not os.path.exists(extracted_bin_path):
                            print_error("No se pudo extraer o encontrar el binario de Supabase CLI del archivo descargado.")
                        else:
                            print_success(f"Binario extraído en: {extracted_bin_path}")

                            if platform.system() == "Windows":
                                install_dir_base = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
                                install_dir_path = os.path.join(install_dir_base, "Supabase", "CLI")
                            else:
                                install_dir_path = os.path.join(os.path.expanduser("~"), ".supabase", "bin")

                            os.makedirs(install_dir_path, exist_ok=True)
                            final_bin_path = os.path.join(install_dir_path, exe_name)

                            try:
                                # shutil.move puede fallar si el destino existe y es un directorio en algunas plataformas
                                # o si los permisos son un problema. Copiar y luego borrar es más seguro.
                                if os.path.exists(final_bin_path):
                                    print_warning(f"El archivo existente {final_bin_path} será reemplazado.")
                                    os.remove(final_bin_path)
                                shutil.copy(extracted_bin_path, final_bin_path)
                                print_success(f"Supabase CLI copiada a: {final_bin_path}")
                                if os_type != "windows":
                                    os.chmod(final_bin_path, os.stat(final_bin_path).st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH )
                                    print_info(f"Permisos de ejecución establecidos para {final_bin_path}")

                                print_warning(f"Supabase CLI ha sido instalada en: {install_dir_path}")
                                print_warning(f"DEBES AÑADIR ESTE DIRECTORIO A TU VARIABLE DE ENTORNO PATH MANUALMENTE.")
                                print_warning("Después de añadirlo al PATH, reinicia tu terminal/PC para que los cambios surtan efecto.")

                                print_info(f"Verificando la instalación en {final_bin_path}...")
                                verify_success, _, _ = run_command([final_bin_path, "--version"], suppress_output=False)
                                if verify_success:
                                    print_success("¡Supabase CLI instalada y verificada exitosamente desde GitHub!")
                                    print_info(f"Recuerda añadir '{install_dir_path}' a tu PATH.")
                                    return final_bin_path # Devolver la ruta al binario
                                else:
                                    print_error("Falló la verificación de Supabase CLI después de la descarga directa.")
                                    return False # Fallo explícito
                            except Exception as move_err:
                                print_error(f"No se pudo mover/copiar el binario a {final_bin_path}: {move_err}")
                                return False # Fallo explícito
                    except urllib.error.URLError as e:
                         print_error(f"Error de red al descargar el asset: {e.reason}")
                         return False # Fallo explícito
                    except Exception as e:
                         print_error(f"Error durante la descarga o extracción del asset: {e}")
                         return False # Fallo explícito
                    finally:
                        if 'temp_dir' in locals() and os.path.exists(temp_dir): shutil.rmtree(temp_dir)
                # Si no hay download_url o falla antes de la descarga
                if not download_url: # Asegurarse de que si no hay URL, también es un fallo de este método.
                    return False


    except Exception as e:
        print_error(f"Ocurrió un error general durante el proceso de descarga directa: {e}")
        if 'temp_dir' in locals() and os.path.exists(temp_dir) and os.path.isdir(temp_dir):
            shutil.rmtree(temp_dir)
        return False # Fallo explícito

    # Mensaje final si todos los métodos fueron probados y fallaron (o se omitieron).
    # Este return False es el último recurso si ninguna instalación tuvo éxito.
    print_error("Todos los métodos de instalación automática probados fallaron o fueron omitidos.")
    print_info("Por favor, instala Supabase CLI manualmente: https://supabase.com/docs/guides/cli/getting-started")
    return False

def check_supabase_login(supabase_cmd="supabase"): # Añadir supabase_cmd
    print_info("Verificando estado de login en Supabase CLI...")
    # Intento 1: Verificar si ya está logueado
    print_info("Verificando estado de login en Supabase CLI (intento 1)...")
    success, _, stderr = run_command(
        [supabase_cmd, "projects", "list"],
        suppress_output=True,
        supabase_executable_path=supabase_cmd if supabase_cmd != "supabase" else None
    )

    if success:
        print_success("Ya has iniciado sesión en Supabase CLI.")
        return True # O SUPABASE_IN_PATH si es la convención para "listo y en path"

    # Si falla el primer intento, determinar si es por falta de login
    stderr_lower = stderr.lower()
    needs_login = "you are not logged in" in stderr_lower or \
                  "error: unauthorized" in stderr_lower or \
                  "auth error" in stderr_lower or \
                  "access token not provided" in stderr_lower

    if needs_login:
        print_warning("No has iniciado sesión en Supabase CLI.")
        login_command_display = os.path.basename(supabase_cmd)
        print_info(f"Intentando ejecutar '{login_command_display} login' interactivamente...")
        print_info("Por favor, sigue las instrucciones en tu navegador para completar el login.")

        # Intentar ejecutar 'supabase login --no-browser' con salida directa a la consola
        login_command_to_run = [supabase_cmd, "login", "--no-browser"]
        print_info(f"Ejecutando: {' '.join(login_command_to_run)}")
        print_info("Se espera que este comando imprima una URL. Copia esa URL en tu navegador, completa el login, y luego pega el token de acceso que te proporcione la web de Supabase aquí en la consola si el comando lo solicita.")

        login_success = False
        try:
            # Llamada directa a subprocess.run para permitir salida directa a la consola
            # No se usa capture_output=True, por lo que stdout/stderr van a la consola.
            process = subprocess.run(
                login_command_to_run,
                check=False, # El script manejará el código de retorno
                timeout=300 # Timeout generoso para interacción del usuario
            )
            if process.returncode == 0:
                login_success = True
                print_success(f"'{' '.join(login_command_to_run)}' finalizó con código de salida 0.")
            else:
                print_error(f"'{' '.join(login_command_to_run)}' finalizó con código de salida {process.returncode}.")
        except subprocess.TimeoutExpired:
            print_error(f"El comando '{' '.join(login_command_to_run)}' tardó demasiado en responder (timeout: 300s).")
            login_success = False
        except Exception as e:
            print_error(f"Error inesperado al ejecutar '{' '.join(login_command_to_run)}': {e}")
            login_success = False

        if login_success:
            print_info("Verificando estado de login en Supabase CLI (intento 2)...")
            retry_success, _, retry_stderr = run_command(
                [supabase_cmd, "projects", "list"],
                suppress_output=True,
                supabase_executable_path=supabase_cmd if supabase_cmd != "supabase" else None
            )
            if retry_success:
                print_success("¡Login verificado exitosamente después del intento interactivo!")
                return True
            else:
                print_error(f"Falló la verificación del login después de ejecutar '{' '.join(login_command_to_run)}'.")
                if retry_stderr: print_info(f"Detalle del reintento: {retry_stderr}")
                print_info(f"Asegúrate de haber completado el proceso de login (copiar URL, autenticar, pegar token si es necesario). Si el problema persiste, intenta '{login_command_display} login' manualmente.")
                return False
        else:
            # login_success es False
            print_error(f"El proceso para '{' '.join(login_command_to_run)}' no fue exitoso o fue cancelado/falló.")
            print_info(f"Por favor, intenta ejecutar '{login_command_display} login --no-browser' manualmente en tu terminal, completa el proceso, y luego vuelve a ejecutar este script.")
            return False
    else:
        # El error original al listar proyectos no era por falta de login conocido
        print_error(f"Error desconocido al verificar el estado de login (no parece ser un problema de autenticación). Detalle: {stderr}")
        return False

def initialize_supabase_project_if_needed(supabase_cmd="supabase"):
    print_info("Verificando inicialización del proyecto Supabase local...")
    if not os.path.isdir(SUPABASE_DIR):
        print_warning(f"El directorio '{SUPABASE_DIR}' no existe.")
        # Usar supabase_cmd en el mensaje al usuario también
        run_init_prompt = f"¿Deseas ejecutar '{os.path.basename(supabase_cmd)} init' para inicializarlo ahora? (s/N): "
        run_init = input(run_init_prompt).strip().lower()
        if run_init == 's':
            # Aumentar timeout a 180s y añadir --force
            success, _, stderr = run_command(
                [supabase_cmd, "init", "--force"],
                timeout=180,
                supabase_executable_path=supabase_cmd if supabase_cmd != "supabase" else None
            )
            if success:
                print_success(f"Proyecto Supabase inicializado localmente en el directorio '{SUPABASE_DIR}'.")
            else:
                print_error(f"Error al ejecutar '{os.path.basename(supabase_cmd)} init --force'. Detalle: {stderr}")
                return False
        else:
            print_error(f"El script no puede continuar sin un proyecto Supabase inicializado localmente (directorio '{SUPABASE_DIR}').")
            return False
    else:
        print_success(f"El directorio '{SUPABASE_DIR}' ya existe.")

    if not os.path.isdir(MIGRATIONS_DIR):
        try:
            os.makedirs(MIGRATIONS_DIR, exist_ok=True)
            print_info(f"Directorio de migraciones '{MIGRATIONS_DIR}' creado/verificado.")
        except OSError as e:
            print_error(f"No se pudo crear el directorio de migraciones '{MIGRATIONS_DIR}': {e}")
            return False
    return True

def get_project_ref():
    print_info("Obteniendo referencia del proyecto Supabase (PROJECT_REF)...")
    project_id = None
    if os.path.exists(CONFIG_FILE_PATH):
        if os.path.getsize(CONFIG_FILE_PATH) > 0:
            # Intento 1: Usar ConfigParser
            try:
                config = configparser.ConfigParser()
                config.read(CONFIG_FILE_PATH)
                if config.has_section('project_id') and config.has_option('project_id', 'id'):
                    project_id = config.get('project_id', 'id')
                elif config.has_option(config.default_section, 'project_id'):
                    project_id = config.get(config.default_section, 'project_id')

                if project_id:
                    # Quitar comillas si configparser las incluyó (a veces pasa con get)
                    if (project_id.startswith('"') and project_id.endswith('"')) or \
                       (project_id.startswith("'") and project_id.endswith("'")):
                        project_id = project_id[1:-1]
                    print_success(f"PROJECT_REF encontrado en '{CONFIG_FILE_PATH}' (via configparser): {project_id}")
                    return project_id
            except configparser.Error as e_cfg:
                print_info(f"Lectura con configparser de '{CONFIG_FILE_PATH}' falló o no encontró project_id ({e_cfg}). Intentando lectura manual.")

            # Intento 2: Lectura manual (fallback si configparser falló o no encontró)
            if not project_id:
                try:
                    with open(CONFIG_FILE_PATH, 'r') as f_config:
                        for line in f_config:
                            line = line.strip()
                            if line.startswith('#') or '=' not in line: # Ignorar comentarios y líneas sin '='
                                continue

                            key, value_str = line.split('=', 1)
                            key = key.strip()
                            value_str = value_str.strip()

                            if key == 'project_id' or key == 'project-id':
                                # Quitar comillas
                                if (value_str.startswith('"') and value_str.endswith('"')) or \
                                   (value_str.startswith("'") and value_str.endswith("'")):
                                    project_id = value_str[1:-1]
                                else:
                                    project_id = value_str

                                if project_id:
                                    print_success(f"PROJECT_REF encontrado en '{CONFIG_FILE_PATH}' (lectura manual): {project_id}")
                                    return project_id
                    if not project_id:
                        print_warning(f"No se pudo extraer 'project_id' de '{CONFIG_FILE_PATH}' mediante lectura manual (línea no encontrada o formato incorrecto).")
                except Exception as e_manual:
                    print_warning(f"Error durante la lectura manual de '{CONFIG_FILE_PATH}': {e_manual}")
        else:
            print_warning(f"El archivo '{CONFIG_FILE_PATH}' está vacío.")
    else:
        print_info(f"El archivo de configuración '{CONFIG_FILE_PATH}' no existe. No se intentará leer de él.")

    # Si no se encontró el ID por ningún método automático o el archivo no existe
    if not project_id:
        print_info("No se pudo obtener el PROJECT_REF del archivo de configuración.")

    project_ref_input = input("Introduce tu PROJECT_REF de Supabase (lo encuentras en Configuración > General de tu dashboard): ").strip()
    if not project_ref_input:
        print_error("El PROJECT_REF es obligatorio.")
        return None
    return project_ref_input

def link_project(project_ref, supabase_cmd="supabase"):
    print_info(f"Vinculando con el proyecto Supabase: {project_ref}...")
    link_command_list = [supabase_cmd, "link", "--project-ref", project_ref]

    db_password_env = os.environ.get("SUPABASE_DB_PASSWORD")
    password_source = ""
    password_entered_by_user = None # Variable to store password if user types it

    if db_password_env:
        print_info("Usando contraseña de la base de datos desde la variable de entorno SUPABASE_DB_PASSWORD.")
        password_source = "variable de entorno"
        # password_entered_by_user remains None because db_push can also check env var
    else:
        print_info("La variable de entorno SUPABASE_DB_PASSWORD no está configurada.")
        try:
            print_info("Por favor, introduce la contraseña de tu base de datos Supabase. Deja en blanco para omitir.")
            db_password_input_user = getpass.getpass("Contraseña de la base de datos (se ocultará la entrada): ")
            if db_password_input_user:
                link_command_list.extend(["--password", db_password_input_user])
                password_source = "entrada del usuario"
                password_entered_by_user = db_password_input_user # Store for returning
                print_info("Contraseña proporcionada por el usuario.")
            else:
                # password_entered_by_user remains None
                print_info("No se proporcionó contraseña. El comando 'link' intentará continuar sin ella (puede omitir la validación de la BD o fallar si es obligatoria).")
        except Exception as e:
            # password_entered_by_user remains None
            print_warning(f"No se pudo leer la contraseña de forma segura ({e}). El comando 'link' se ejecutará sin pasar una contraseña explícita.")
            print_info("Puedes configurar la variable de entorno SUPABASE_DB_PASSWORD para evitar este prompt.")

    # Mantenemos el timeout de 180s para link
    success, stdout, stderr = run_command(
        link_command_list,
        timeout=180, # Mantenemos el timeout de 180s
        supabase_executable_path=supabase_cmd if supabase_cmd != "supabase" else None,
        check=False # Permitir que analicemos el error nosotros mismos
    )

    link_command_str_display = list(link_command_list)
    # Ocultar la contraseña en el mensaje de log si se proporcionó
    try:
        idx = link_command_str_display.index("--password")
        if idx + 1 < len(link_command_str_display):
            link_command_str_display[idx+1] = "*******"
    except ValueError:
        pass # --password no estaba en la lista
    final_link_command_str = ' '.join(link_command_str_display)


    if success:
        print_success(f"Proyecto vinculado exitosamente con {project_ref}.")
        # Actualizar/crear config.toml con el project_id correcto
        try:
            os.makedirs(SUPABASE_DIR, exist_ok=True)
            new_project_id_line = f'project_id = "{project_ref}"\n'
            lines_to_write = []
            existed_before = os.path.exists(CONFIG_FILE_PATH)

            if existed_before:
                print_info(f"Actualizando '{CONFIG_FILE_PATH}' para asegurar que project_id = \"{project_ref}\".")
                with open(CONFIG_FILE_PATH, 'r') as f_cfg_read:
                    for line in f_cfg_read:
                        # Keep lines that are not project_id definitions
                        if not (line.strip().startswith("project_id") and "=" in line):
                            lines_to_write.append(line)
            else:
                print_info(f"Creando '{CONFIG_FILE_PATH}' con project_id = \"{project_ref}\".")

            with open(CONFIG_FILE_PATH, 'w') as f_cfg_write:
                f_cfg_write.write(new_project_id_line) # Write the new/correct project_id first
                for line in lines_to_write:
                    f_cfg_write.write(line)

            if existed_before:
                print_success(f"'{CONFIG_FILE_PATH}' actualizado para reflejar project_id = \"{project_ref}\".")
            else:
                print_success(f"'{CONFIG_FILE_PATH}' creado con project_id = \"{project_ref}\".")

        except Exception as e_cfg_update:
            print_warning(f"No se pudo actualizar/crear '{CONFIG_FILE_PATH}' con el project_ref: {e_cfg_update}")
        return True, password_entered_by_user # Return password if link was successful
    else:
        # Analizar stderr para dar mejores mensajes
        stderr_lower = stderr.lower()

        if "already linked to project" in stderr_lower and project_ref in stderr_lower:
            print_success(f"El proyecto ya está vinculado con {project_ref}. Continuando...")
            # Si ya está vinculado, no tenemos una contraseña "recién introducida" para propagar,
            # pero la operación de "asegurar el vínculo" es exitosa.
            return True, None
        elif "config file differs" in stderr_lower:
            print_warning(f"El project ID en {CONFIG_FILE_PATH} difiere del proporcionado para el comando '{final_link_command_str}'.")
            print_info("Esto puede ocurrir si el archivo local ya está vinculado a otro proyecto.")
            print_info(f"El script intentó vincular con '{project_ref}'.")
            print_info(f"Puedes intentar '{supabase_cmd} unlink' y luego re-ejecutar este script,")
            print_info(f"o ejecutar '{supabase_cmd} link --project-ref {project_ref} --force' manualmente si estás seguro.")
            return False, None

        is_timeout_error = "timeout (" in stderr_lower and "para el comando" in stderr_lower
        is_generic_timeout_message_from_cli = "operation timed out" in stderr_lower # Mensaje directo de la CLI

        # Si se proporcionó contraseña y aún así hay timeout, el problema es otro (red, servicio, etc.)
        if (is_timeout_error or is_generic_timeout_message_from_cli) and password_source:
            print_error(f"El comando '{final_link_command_str}' (con contraseña de {password_source}) falló por timeout.")
            print_info("Recomendaciones:")
            print_info(f"  1. Verifica tu conexión a internet y que el proyecto Supabase '{project_ref}' esté accesible y operativo.")
            print_info(f"  2. Intenta ejecutar el comando '{final_link_command_str}' manualmente en tu terminal para ver si hay más detalles.")
            if stderr.strip(): print_warning(f"  Detalle del error (stderr): {stderr.strip()}")
            if stdout.strip(): print_info(f"  Salida (stdout): {stdout.strip()}")
            return False, None
        # Si NO se proporcionó contraseña (o falló getpass) Y hay timeout, es probable que sea el prompt.
        elif (is_timeout_error or is_generic_timeout_message_from_cli) and not password_source:
            print_error(f"El comando '{final_link_command_str}' (sin contraseña explícita) falló, muy probablemente por timeout esperando un input interactivo (como la contraseña de la base de datos).")
            print_info("\nRecomendaciones:")
            print_info(f"  1. Intenta ejecutar el comando '{final_link_command_str}' manualmente en tu terminal. Esto te permitirá ver si aparece algún prompt y responderlo.")
            print_info(f"  2. Para automatizar, configura la variable de entorno SUPABASE_DB_PASSWORD con la contraseña de tu base de datos antes de ejecutar este script.")
            print_info(f"     El script intentará leerla o te la solicitará de forma segura si no está configurada.")
            print_info(f"  3. Verifica tu conexión a internet y que el proyecto Supabase '{project_ref}' esté accesible.")
            if stderr.strip(): print_warning(f"  Detalle del error (stderr): {stderr.strip()}")
            if stdout.strip(): print_info(f"  Salida (stdout): {stdout.strip()}")
            return False, None
        else: # Otro tipo de error
            print_error(f"Error al ejecutar '{final_link_command_str}'.")
            if "authentication failed" in stderr_lower or "password authentication failed" in stderr_lower:
                print_error("Falló la autenticación de la base de datos. Verifica la contraseña proporcionada.")
                if password_source == "variable de entorno":
                    print_info("La contraseña se tomó de SUPABASE_DB_PASSWORD. Verifica que sea correcta.")
                elif password_source == "entrada del usuario":
                    print_info("La contraseña fue la que introdujiste en el prompt.")
            elif "project not found" in stderr_lower:
                print_error(f"El proyecto con ref '{project_ref}' no fue encontrado en Supabase.")
                print_info("Verifica que el PROJECT_REF sea correcto y que el proyecto exista.")

            if stdout.strip(): print_info(f"  Salida (stdout): {stdout.strip()}")
            if stderr.strip(): print_warning(f"  Salida (stderr): {stderr.strip()}")
            return False, None

def create_migration_from_init_sql():
    print_info(f"Creando archivo de migración desde '{INIT_SQL_FILE}'...")
    if not os.path.exists(INIT_SQL_FILE):
        print_error(f"El archivo '{INIT_SQL_FILE}' no se encontró en el directorio actual.")
        return False

    if not os.path.isdir(MIGRATIONS_DIR):
        print_error(f"El directorio de migraciones '{MIGRATIONS_DIR}' no existe. Asegúrate de que 'supabase init' se haya ejecutado correctamente.")
        return False

    # Check if an initial schema migration from today already exists
    today_str = datetime.datetime.now().strftime('%Y%m%d')
    suffix_to_check = "_initial_schema_from_script.sql"
    try:
        for existing_file in os.listdir(MIGRATIONS_DIR):
            if existing_file.startswith(today_str) and existing_file.endswith(suffix_to_check):
                print_info(f"Ya existe un archivo de migración inicial para hoy: '{existing_file}'. No se creará uno nuevo.")
                print_warning("Se reintentará aplicar las migraciones existentes. Si la ejecución anterior falló a la mitad, la base de datos podría estar en un estado inconsistente.")
                print_warning("Para un inicio limpio, considera resetear la base de datos remota y borrar los archivos de migración locales si es necesario.")
                return True # Proceed assuming this existing migration will be picked up by `db push`
    except FileNotFoundError:
        # MIGRATIONS_DIR might not exist if init didn't run or was partial, though checked above.
        # This specific check is for os.listdir, so if MIGRATIONS_DIR was created *after* the top check but before listdir.
        pass # Fall through to creating the migration.
    except Exception as e:
        print_warning(f"Error al verificar migraciones existentes: {e}. Se intentará crear una nueva.")
        # Fall through to creating the migration.

    timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    migration_file_name = f"{timestamp}{suffix_to_check}" # Use the defined suffix
    migration_file_path = os.path.join(MIGRATIONS_DIR, migration_file_name)

    try:
        shutil.copyfile(INIT_SQL_FILE, migration_file_path)
        print_success(f"Archivo de migración creado: '{migration_file_path}'")
        return True
    except Exception as e:
        print_error(f"No se pudo crear el archivo de migración: {e}")
        return False

def apply_migrations(project_ref, supabase_cmd="supabase", db_password_from_link=None):
    print_info("Aplicando migraciones a la base de datos Supabase remota...")
    print_warning("Esto puede tardar unos momentos y aplicará CUALQUIER migración pendiente.")

    # Add --debug for more verbose output from the CLI
    command_list = [supabase_cmd, "db", "push", "--debug"]
    password_source_for_push = None

    if db_password_from_link:
        print_info("Usando contraseña proporcionada durante el 'link' para 'db push'.")
        command_list.extend(["--password", db_password_from_link])
        password_source_for_push = "link step"
    else:
        # db_password_from_link was None or empty, try environment variable
        db_password_env = os.environ.get("SUPABASE_DB_PASSWORD")
        if db_password_env:
            print_info("Usando contraseña de la variable de entorno SUPABASE_DB_PASSWORD para 'db push'.")
            command_list.extend(["--password", db_password_env])
            password_source_for_push = "environment variable"
        else:
            print_info("No se proporcionó contraseña desde 'link' ni se encontró SUPABASE_DB_PASSWORD. 'db push' se ejecutará sin pasar una contraseña explícita (confiando en la sesión de 'link' o credenciales almacenadas).")

    # Usar os.path.basename(supabase_cmd) para mensajes si es una ruta larga
    # Ocultar la contraseña en el mensaje de log si se proporcionó
    command_list_display = list(command_list)
    try:
        idx = command_list_display.index("--password")
        if idx + 1 < len(command_list_display):
            command_list_display[idx+1] = "*******"
    except ValueError:
        pass # --password no estaba en la lista
    final_db_push_command_str = ' '.join(command_list_display)

    print_info(f"Ejecutando: {final_db_push_command_str} para el proyecto {project_ref}")

    new_timeout = 1200  # 20 minutes
    print_info(f"Timeout para 'db push' configurado a {new_timeout} segundos con --debug habilitado.")
    success, stdout, stderr = run_command(
        command_list,
        timeout=new_timeout,
        suppress_output=False,
        supabase_executable_path=supabase_cmd if supabase_cmd != "supabase" else None
    )

    if success:
        print_success("Migraciones aplicadas exitosamente (o no había cambios pendientes).")
        return True
    else:
        return False

def is_admin():
    """Verifica si el script se está ejecutando con privilegios de administrador en Windows."""
    if platform.system() == "Windows":
        try:
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except:
            return False
    return True # No es Windows, asumir que no se necesita o se maneja de otra forma

def main():
    print_header("Script de Configuración de Supabase con CLI")

    if platform.system() == "Windows" and not is_admin():
        print_error("Este script necesita privilegios de administrador para intentar instalar algunas herramientas como Scoop.")
        print_warning("Por favor, cierra esta ventana y vuelve a ejecutar el script como Administrador.")
        sys.exit(1) # Salir con código de error

    cli_status_or_path = check_supabase_cli() # Puede devolver SUPABASE_IN_PATH, False, o una ruta de string

    supabase_executable_to_use = "supabase" # Por defecto, usa el comando del PATH

    if isinstance(cli_status_or_path, str):
        if cli_status_or_path == SUPABASE_IN_PATH:
            print_info("Usando Supabase CLI del PATH.")
            supabase_executable_to_use = "supabase"
        else: # Es una ruta directa al ejecutable
            print_info(f"Usando Supabase CLI desde la ruta: {cli_status_or_path}")
            supabase_executable_to_use = cli_status_or_path
    elif not cli_status_or_path: # Es False o None
        print_info("Saliendo del script porque Supabase CLI no está disponible o no se pudo instalar.")
        return # Salir si la CLI no está lista

    if not initialize_supabase_project_if_needed(supabase_executable_to_use):
        return

    if not check_supabase_login(supabase_executable_to_use):
        return

    project_ref = get_project_ref() # Esta función no ejecuta comandos de supabase
    if not project_ref:
        return

    link_success, session_db_password = link_project(project_ref, supabase_executable_to_use)
    if not link_success:
        print_error("No se pudo asegurar el vínculo con el proyecto Supabase. Saliendo.")
        return

    # This was called too early before, now it's correctly placed before asking to apply migrations,
    # but after link and other essential checks.
    # However, the actual creation of migration file from SQL should only happen if the user confirms
    # they want to apply migrations, and potentially after a reset.
    # So, the call to `create_migration_from_init_sql` is moved further down.

    confirm_apply = input(f"\n¿Estás listo para aplicar las migraciones (basadas en '{INIT_SQL_FILE}') a tu proyecto Supabase '{project_ref}'? (s/N): ").strip().lower()
    if confirm_apply == 's':
        # --- Preguntar por reseteo de base de datos ---
        confirm_reset = input(f"\n⚠️ ADVERTENCIA: ¿Quieres resetear la base de datos remota para el proyecto '{project_ref}' ANTES de aplicar las migraciones? \nESTO BORRARÁ TODOS LOS DATOS EN LA BASE DE DATOS REMOTA. Esta acción es irreversible. (yes/NO): ").strip().lower()

        if confirm_reset == 'yes':
            print_info(f"Intentando resetear la base de datos remota para el proyecto {project_ref}...")

            reset_command_list = [supabase_executable_to_use, "db", "reset", "--debug"]
            print_info(f"Ejecutando: {' '.join(reset_command_list)}")

            reset_success, _, reset_stderr = run_command(
                reset_command_list,
                timeout=300,
                suppress_output=False,
                supabase_executable_path=supabase_executable_to_use if supabase_executable_to_use != "supabase" else None,
                check=False
            )

            if reset_success:
                print_success(f"Base de datos remota para el proyecto '{project_ref}' reseteada exitosamente.")
                if os.path.isdir(MIGRATIONS_DIR):
                    try:
                        shutil.rmtree(MIGRATIONS_DIR)
                        print_info(f"Directorio de migraciones local '{MIGRATIONS_DIR}' eliminado para asegurar un inicio limpio.")
                        os.makedirs(MIGRATIONS_DIR, exist_ok=True)
                        print_info(f"Directorio de migraciones local '{MIGRATIONS_DIR}' recreado vacío.")
                    except Exception as e_rm:
                        print_error(f"No se pudo eliminar o recrear el directorio de migraciones local '{MIGRATIONS_DIR}': {e_rm}")
                        print_warning("Continuando de todas formas, pero podrían surgir problemas con migraciones antiguas.")
            else:
                print_error(f"Falló el reseteo de la base de datos remota para '{project_ref}'. Detalle: {reset_stderr}")
                print_warning("Las migraciones NO se aplicarán debido al fallo en el reseteo.")
                return
        else:
            print_info("Reseteo de la base de datos remota omitido por el usuario.")
        # --- Fin de la lógica de reseteo ---

        # Crear la migración DESPUÉS del posible reseteo y limpieza de migraciones locales
        # y solo si el usuario confirmó que quiere aplicar migraciones.
        print_info("Preparando archivo de migración...")
        if not create_migration_from_init_sql():
            print_error("Falló la creación del archivo de migración inicial. No se puede continuar con 'db push'.")
            return

        print_info("Procediendo a aplicar migraciones...")
        if apply_migrations(project_ref, supabase_executable_to_use, db_password_from_link=session_db_password):
            print_success("¡Proceso de configuración de Supabase completado!")
            print_info("Recuerda verificar tu dashboard de Supabase para confirmar que todo está como esperas.")
        else:
            print_error("La configuración de Supabase falló durante la aplicación de migraciones.")
            print_info("Revisa los logs y el dashboard de Supabase.")
    else:
        print_info("Aplicación de migraciones cancelada por el usuario.")
        print_info(f"Puedes aplicar las migraciones manualmente ejecutando '{os.path.basename(supabase_executable_to_use)} db push' en tu terminal, desde la raíz de tu proyecto.")

if __name__ == "__main__":
    main()
