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

# Constantes
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

def run_command(command_list, timeout=60, check=True, suppress_output=False):
    """Ejecuta un comando de subprocess de forma segura y devuelve (éxito, stdout, stderr)."""
    try:
        process = subprocess.run(
            command_list,
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

def check_supabase_cli():
    print_info("Verificando Supabase CLI...")
    success, initial_stdout, initial_stderr = run_command(["supabase", "--version"], suppress_output=True)
    if success:
        print_success("Supabase CLI ya está instalada.")
        return True

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
                        return True
                    else:
                        print_error("Supabase CLI no se encuentra después de la instalación con Winget (aunque Winget indicó éxito).")
                else:
                    print_error("Falló la instalación con Winget o no se confirmó el éxito en la salida.")
            else:
                print_warning(f"Winget no pudo encontrar/confirmar el paquete '{package_id}'. (Search stdout: '{search_stdout}', stderr: '{search_stderr_search}')")
        else:
            print_info("Winget no está disponible en este sistema.")

    # 2. SCOOP (Solo Windows, con intento de instalación de Scoop)
    if platform.system() == "Windows":
        print_header("Intentando instalación con Scoop")
        scoop_available, _, _ = run_command(["scoop", "--version"], suppress_output=True)
        if not scoop_available:
            print_info("Scoop no está disponible en este sistema.")
            install_scoop_choice = input("¿Deseas que el script intente instalar Scoop? (Esto cambiará tu política de ejecución de PowerShell y ejecutará un script de internet) (s/N): ").strip().lower()
            if install_scoop_choice == 's':
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
                        # Es crucial re-chequear la disponibilidad de scoop aquí ANTES de usarlo.
                        scoop_available, _, _ = run_command(["scoop", "--version"], suppress_output=True)
                        if scoop_available:
                            print_success("¡Scoop instalado exitosamente!")
                        else:
                            print_error(f"Scoop no se pudo verificar después de la instalación. Error: {scoop_install_err}")
                    else:
                        print_error(f"Falló la ejecución del script de instalación de Scoop. Error: {scoop_install_err}")
            else:
                print_info("Instalación de Scoop omitida por el usuario.")

        if scoop_available: # Si estaba disponible o se instaló y verificó
            print_info("Intentando instalar 'supabase' con Scoop...")
            install_success, _, _ = run_command(["scoop", "install", "supabase"], timeout=300, check=False)
            if install_success:
                print_success("Comando 'scoop install supabase' ejecutado. Verificando...")
                if run_command(["supabase", "--version"], suppress_output=True)[0]:
                    print_success("¡Supabase CLI instalada y verificada exitosamente vía Scoop!")
                    print_warning("Es posible que necesites REINICIAR TU TERMINAL (o VSCode) para que el PATH se actualice.")
                    return True
                else:
                    print_error("Supabase CLI no se encuentra después de la instalación con Scoop.")
            else:
                print_error("Falló la instalación de Supabase CLI con Scoop.")

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
                return True
            else:
                print_error("Supabase CLI no se encuentra después de la instalación con NPM.")
                print_info("Esto es común si el directorio global de paquetes de NPM no está en tu PATH o si la terminal necesita reiniciarse.")
        else:
            print_error("Falló la instalación con NPM.")
    else:
        print_info("NPM no está disponible en este sistema. Para usar este método, instala Node.js y NPM.")

    # 4. DESCARGA DIRECTA DESDE GITHUB RELEASES (Multiplataforma)
    # Esta sección se ejecuta si todos los métodos anteriores fallaron Y el usuario aceptó la instalación automática al principio.
    print_header("Intentando descarga directa de Supabase CLI desde GitHub")
    try:
        print_info("Obteniendo información de la última release de Supabase CLI...")
        api_url = "https://api.github.com/repos/supabase/cli/releases/latest"
        # Manejo de errores de red para la API de GitHub
        try:
            with urllib.request.urlopen(api_url, timeout=10) as response: # Timeout para la petición
                release_data = json.loads(response.read().decode())
        except urllib.error.URLError as e:
            print_error(f"Error de red al contactar la API de GitHub: {e.reason}")
            print_info("Por favor, verifica tu conexión a internet.")
            # No retornar False aquí, para que el mensaje final de error general se muestre
        except json.JSONDecodeError:
            print_error("No se pudo decodificar la respuesta de la API de GitHub (formato inesperado).")
        except Exception as e: # Otro error inesperado
            print_error(f"Error inesperado al obtener datos de release: {e}")
        else: # Si no hubo errores en la petición y decodificación JSON
            assets = release_data.get("assets", [])
            if not assets:
                print_error("No se encontraron assets en la última release de GitHub.")
            else:
                os_type = platform.system().lower()
                arch = platform.machine().lower()

                asset_filename_part = ""
                asset_ext = ""
                exe_name = "supabase"

                if os_type == "windows":
                    asset_ext = ".zip"
                    exe_name = "supabase.exe"
                    if arch in ["amd64", "x86_64"]: asset_filename_part = "windows-amd64"
                    elif arch in ["arm64", "aarch64"]: asset_filename_part = "windows-arm64"
                elif os_type == "linux":
                    asset_ext = ".tar.gz"
                    if arch in ["amd64", "x86_64"]: asset_filename_part = "linux-amd64"
                    elif arch in ["arm64", "aarch64"]: asset_filename_part = "linux-arm64"
                elif os_type == "darwin":
                    asset_ext = ".tar.gz"
                    if arch in ["amd64", "x86_64"]: asset_filename_part = "darwin-amd64"
                    elif arch in ["arm64", "aarch64"]: asset_filename_part = "darwin-arm64"

                if not asset_filename_part:
                    print_error(f"Combinación SO/arquitectura no soportada para descarga directa: {os_type}/{arch}")
                else:
                    download_url = None
                    found_asset_name = ""
                    for asset in assets:
                        name = asset.get("name", "").lower()
                        # Los nombres de assets son como: supabase_1.164.0_darwin_arm64.tar.gz
                        # o supabase_windows_amd64.zip (sin versión en el nombre a veces)
                        # Necesitamos un match flexible que contenga la parte os-arch y la extensión
                        if asset_filename_part in name and name.endswith(asset_ext):
                            download_url = asset.get("browser_download_url")
                            found_asset_name = name
                            print_success(f"Asset encontrado para descarga: {found_asset_name}")
                            break

                    if not download_url:
                        print_error(f"No se encontró un asset de descarga compatible para {asset_filename_part} en la última release.")
                    else:
                        print_info(f"Descargando Supabase CLI desde: {download_url}")
                        temp_dir = "temp_supabase_cli_download"
                        os.makedirs(temp_dir, exist_ok=True)
                        download_path = os.path.join(temp_dir, found_asset_name) # Usar el nombre encontrado

                        try:
                            urllib.request.urlretrieve(download_url, download_path)
                            print_success(f"Descargado en: {download_path}")

                            print_info("Extrayendo binario...")
                            extracted_bin_path = None
                            if asset_ext == ".zip":
                                with zipfile.ZipFile(download_path, 'r') as zip_ref:
                                    for member_info in zip_ref.infolist(): # Usar infolist para verificar si es un archivo
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
                                else: # Linux/macOS
                                    install_dir_path = os.path.join(os.path.expanduser("~"), ".supabase", "bin")

                                os.makedirs(install_dir_path, exist_ok=True)
                                final_bin_path = os.path.join(install_dir_path, exe_name)

                                try:
                                    shutil.move(extracted_bin_path, final_bin_path)
                                    print_success(f"Supabase CLI movida a: {final_bin_path}")
                                    if os_type != "windows":
                                        os.chmod(final_bin_path, os.stat(final_bin_path).st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH )
                                        print_info(f"Permisos de ejecución establecidos para {final_bin_path}")

                                    print_warning(f"Supabase CLI ha sido instalada en: {install_dir_path}")
                                    print_warning(f"DEBES AÑADIR ESTE DIRECTORIO A TU VARIABLE DE ENTORNO PATH MANUALMENTE.")
                                    print_warning("Después de añadirlo al PATH, reinicia tu terminal/PC para que los cambios surtan efecto.")

                                    print_info(f"Verificando la instalación en {final_bin_path}...")
                                    if run_command([final_bin_path, "--version"], suppress_output=False)[0]:
                                        print_success("¡Supabase CLI instalada y verificada exitosamente desde GitHub!")
                                        print_info(f"Recuerda añadir '{install_dir_path}' a tu PATH.")
                                        return True
                                    else:
                                        print_error("Falló la verificación de Supabase CLI después de la descarga directa.")
                                except Exception as move_err:
                                    print_error(f"No se pudo mover el binario a {final_bin_path}: {move_err}")
                        except urllib.error.URLError as e:
                             print_error(f"Error de red al descargar el asset: {e.reason}")
                        except Exception as e:
                             print_error(f"Error durante la descarga o extracción del asset: {e}")
                        finally:
                            if os.path.exists(temp_dir): shutil.rmtree(temp_dir)

    except Exception as e: # Captura errores de la lógica de descarga principal
        print_error(f"Ocurrió un error general durante el proceso de descarga directa: {e}")
        if 'temp_dir' in locals() and os.path.exists(temp_dir) and os.path.isdir(temp_dir):
            shutil.rmtree(temp_dir)

    # Mensaje final si todos los métodos, incluyendo descarga directa, fallaron
    print_error("Todos los métodos de instalación automática (incluyendo descarga directa) fallaron o fueron omitidos.")
    print_info("Por favor, instala Supabase CLI manualmente: https://supabase.com/docs/guides/cli/getting-started")
    return False

def check_supabase_login():
    print_info("Verificando estado de login en Supabase CLI...")
    success, _, stderr = run_command(["supabase", "projects", "list"], suppress_output=True)
    if success:
        print_success("Ya has iniciado sesión en Supabase CLI.")
        return True
    else:
        if "You are not logged in" in stderr or "Error: Unauthorized" in stderr or "Auth error" in stderr:
            print_warning("No has iniciado sesión en Supabase CLI.")
            print_info("Por favor, ejecuta 'supabase login' en tu terminal y luego vuelve a ejecutar este script.")
        else:
            print_error(f"Error desconocido al verificar el estado de login. Detalle: {stderr}")
        return False

def initialize_supabase_project_if_needed():
    print_info("Verificando inicialización del proyecto Supabase local...")
    if not os.path.isdir(SUPABASE_DIR):
        print_warning(f"El directorio '{SUPABASE_DIR}' no existe.")
        run_init = input(f"¿Deseas ejecutar 'supabase init' para inicializarlo ahora? (s/N): ").strip().lower()
        if run_init == 's':
            success, _, stderr = run_command(["supabase", "init"])
            if success:
                print_success(f"Proyecto Supabase inicializado localmente en el directorio '{SUPABASE_DIR}'.")
            else:
                print_error(f"Error al ejecutar 'supabase init'. Detalle: {stderr}")
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
    if os.path.exists(CONFIG_FILE_PATH):
        try:
            config = configparser.ConfigParser()
            if os.path.getsize(CONFIG_FILE_PATH) > 0:
                config.read(CONFIG_FILE_PATH)
                project_id = None
                if 'project_id' in config and 'id' in config['project_id']:
                    project_id = config['project_id']['id']
                if not project_id:
                    with open(CONFIG_FILE_PATH, 'r') as f_config:
                        for line in f_config:
                            line_strip = line.strip()
                            if line_strip.startswith('project_id'):
                                parts = line_strip.split('=', 1)
                                if len(parts) == 2:
                                    project_id = parts[1].strip().replace('"', '').replace("'", "")
                                    break
                if project_id:
                    print_success(f"PROJECT_REF encontrado en '{CONFIG_FILE_PATH}': {project_id}")
                    return project_id
                else:
                    print_warning(f"No se pudo extraer 'project_id' de '{CONFIG_FILE_PATH}' con los formatos esperados.")
            else:
                print_warning(f"El archivo '{CONFIG_FILE_PATH}' está vacío.")
        except Exception as e:
            print_warning(f"No se pudo leer el PROJECT_REF de '{CONFIG_FILE_PATH}': {e}")

    project_ref_input = input("Introduce tu PROJECT_REF de Supabase (lo encuentras en Configuración > General de tu dashboard): ").strip()
    if not project_ref_input:
        print_error("El PROJECT_REF es obligatorio.")
        return None
    return project_ref_input

def link_project(project_ref):
    print_info(f"Vinculando con el proyecto Supabase: {project_ref}...")
    success, stdout, stderr = run_command(["supabase", "link", "--project-ref", project_ref])
    if success:
        print_success(f"Proyecto vinculado exitosamente con {project_ref}.")
        return True
    else:
        if "already linked to project" in stderr.lower() and project_ref in stderr.lower():
            print_success(f"El proyecto ya está vinculado con {project_ref}. Continuando...")
            return True
        elif "config file differs" in stderr.lower():
             print_warning(f"El project ID en {CONFIG_FILE_PATH} difiere del proporcionado.")
             print_info("Por favor, resuelve esto manualmente o ejecuta 'supabase link --project-ref TU_PROJECT_ID --force' si es necesario.")
        return False

def create_migration_from_init_sql():
    print_info(f"Creando archivo de migración desde '{INIT_SQL_FILE}'...")
    if not os.path.exists(INIT_SQL_FILE):
        print_error(f"El archivo '{INIT_SQL_FILE}' no se encontró en el directorio actual.")
        return False

    if not os.path.isdir(MIGRATIONS_DIR):
        print_error(f"El directorio de migraciones '{MIGRATIONS_DIR}' no existe. Asegúrate de que 'supabase init' se haya ejecutado correctamente.")
        return False

    timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    migration_file_name = f"{timestamp}_initial_schema_from_script.sql"
    migration_file_path = os.path.join(MIGRATIONS_DIR, migration_file_name)

    try:
        shutil.copyfile(INIT_SQL_FILE, migration_file_path)
        print_success(f"Archivo de migración creado: '{migration_file_path}'")
        return True
    except Exception as e:
        print_error(f"No se pudo crear el archivo de migración: {e}")
        return False

def apply_migrations(project_ref):
    print_info("Aplicando migraciones a la base de datos Supabase remota...")
    print_warning("Esto puede tardar unos momentos y aplicará CUALQUIER migración pendiente.")

    command = ["supabase", "db", "push"]

    print_info(f"Ejecutando: {' '.join(command)} para el proyecto {project_ref}")
    success, _, stderr = run_command(command, timeout=180, suppress_output=False)

    if success:
        print_success("Migraciones aplicadas exitosamente (o no había cambios pendientes).")
        return True
    else:
        return False

def main():
    print_header("Script de Configuración de Supabase con CLI")

    if not check_supabase_cli():
        return

    if not initialize_supabase_project_if_needed():
        return

    if not check_supabase_login():
        return

    project_ref = get_project_ref()
    if not project_ref:
        return

    if not link_project(project_ref):
        print_error("No se pudo asegurar el vínculo con el proyecto Supabase. Saliendo.")
        return

    if not create_migration_from_init_sql():
        return

    confirm_apply = input(f"\n¿Estás listo para aplicar las migraciones (incluyendo '{INIT_SQL_FILE}') a tu proyecto Supabase '{project_ref}'? (s/N): ").strip().lower()
    if confirm_apply == 's':
        if apply_migrations(project_ref):
            print_success("¡Proceso de configuración de Supabase completado!")
            print_info("Recuerda verificar tu dashboard de Supabase para confirmar que todo está como esperas.")
        else:
            print_error("La configuración de Supabase falló durante la aplicación de migraciones.")
            print_info("Revisa los logs y el dashboard de Supabase.")
    else:
        print_info("Aplicación de migraciones cancelada por el usuario.")
        print_info(f"Puedes aplicar las migraciones manualmente ejecutando 'supabase db push' en la terminal, desde la raíz de tu proyecto.")

if __name__ == "__main__":
    main()

[end of supabase_setup.py]
