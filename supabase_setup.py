import os
import shutil
import subprocess
import datetime
import configparser # Para leer el project_id de config.toml
import platform # Para detectar el sistema operativo

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

# Nueva función run_command proporcionada por el usuario
def run_command(command_list, timeout=60, check=True, suppress_output=False):
    """Ejecuta un comando de subprocess de forma segura y devuelve (éxito, stdout, stderr)."""
    try:
        # Añadir encoding y errors='replace' para sistemas Windows
        process = subprocess.run(
            command_list,
            capture_output=True,
            text=True,
            check=check,
            timeout=timeout,
            encoding='utf-8', # Especificar utf-8
            errors='replace'  # Reemplazar caracteres que no se puedan decodificar
        )
        if not suppress_output:
            if process.stdout and process.stdout.strip():
                print_info(f"Salida de {' '.join(command_list)}:\n{process.stdout.strip()}")
            if process.stderr and process.stderr.strip():
                print_warning(f"Salida de error (puede ser informativa) de {' '.join(command_list)}:\n{process.stderr.strip()}")
        return True, process.stdout.strip(), process.stderr.strip()
    except subprocess.CalledProcessError as e:
        if not suppress_output: # Solo imprimir si no se suprime la salida
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
    except Exception as e: # Captura otras excepciones de subprocess o generales
        if not suppress_output:
            print_error(f"Error inesperado al ejecutar {' '.join(command_list)}: {e}")
        return False, "", str(e)

# Nueva función check_supabase_cli con lógica secuencial de instalación
def check_supabase_cli():
    print_info("Verificando Supabase CLI...")
    success, initial_stdout, initial_stderr = run_command(["supabase", "--version"], suppress_output=True)
    if success:
        print_success("Supabase CLI ya está instalada.")
        return True

    print_warning("Supabase CLI no está instalada o no se encuentra en el PATH.")

    # Preguntar una sola vez si se desea intentar la instalación automática
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
            run_command(["winget", "source", "update"], timeout=180, check=False) # Salida manejada por run_command
            print_info("Intento de actualización de fuentes de Winget completado.")

            package_id = "Supabase.SupabaseCLI"
            print_info(f"Buscando el paquete '{package_id}' con Winget...")
            search_cmd = ["winget", "search", package_id, "--source", "winget", "--accept-source-agreements"]
            search_success, search_stdout, search_stderr = run_command(search_cmd, timeout=120, check=False)

            if search_success and package_id.lower() in search_stdout.lower() and "No se encontró ningún paquete" not in search_stdout :
                print_success(f"Paquete '{package_id}' encontrado vía Winget.")
                print_info(f"Intentando instalar '{package_id}' con Winget...")
                winget_cmd = ["winget", "install", package_id, "--source", "winget", "--accept-package-agreements", "--accept-source-agreements"]
                install_success, install_stdout, _ = run_command(winget_cmd, timeout=300, check=False)

                if install_success and ("instalado correctamente" in install_stdout.lower() or "successfully installed" in install_stdout.lower()):
                    print_success("Winget reportó instalación exitosa. Verificando...")
                    if run_command(["supabase", "--version"], suppress_output=True)[0]:
                        print_success("¡Supabase CLI instalada y verificada exitosamente vía Winget!")
                        print_warning("Es posible que necesites REINICIAR TU TERMINAL (o VSCode) para que el PATH se actualice.")
                        return True
                    else:
                        print_error("Supabase CLI no se encuentra después de la instalación con Winget, aunque Winget indicó éxito.")
                else:
                    print_error("Falló la instalación con Winget o no se confirmó el éxito.")
            else:
                print_warning(f"Winget no pudo encontrar/confirmar el paquete '{package_id}'. (Search stdout: '{search_stdout}', stderr: '{search_stderr}')")
        else:
            print_info("Winget no está disponible en este sistema.")

    # 2. SCOOP (Principalmente Windows, pero puede estar en otros SO si el usuario lo instaló)
    # No preguntaremos de nuevo, si el usuario aceptó la instalación automática, probamos todos los métodos.
    print_header("Intentando instalación con Scoop")
    scoop_available, _, _ = run_command(["scoop", "--version"], suppress_output=True)
    if scoop_available:
        print_info("Scoop detectado. Intentando instalar 'supabase'...")
        # Scoop puede necesitar que el bucket 'extras' esté añadido para algunos paquetes.
        # Por simplicidad, no intentaremos añadir buckets aquí.
        install_success, _, _ = run_command(["scoop", "install", "supabase"], timeout=300, check=False)
        if install_success: # Scoop suele ser más directo; si el comando tiene éxito, usualmente está instalado.
            print_success("Comando 'scoop install supabase' ejecutado. Verificando...")
            if run_command(["supabase", "--version"], suppress_output=True)[0]:
                print_success("¡Supabase CLI instalada y verificada exitosamente vía Scoop!")
                print_warning("Es posible que necesites REINICIAR TU TERMINAL (o VSCode) para que el PATH se actualice.")
                return True
            else:
                print_error("Supabase CLI no se encuentra después de la instalación con Scoop.")
        else:
            print_error("Falló la instalación con Scoop.")
    else:
        print_info("Scoop no está disponible en este sistema.")

    # 3. NPM (Multiplataforma)
    print_header("Intentando instalación con NPM")
    npm_available, _, _ = run_command(["npm", "--version"], suppress_output=True)
    if npm_available:
        print_info("NPM detectado. Intentando instalar 'supabase' globalmente...")
        # npm install -g puede requerir permisos de administrador en algunos sistemas.
        install_success, _, _ = run_command(["npm", "install", "supabase", "--global"], timeout=300, check=False)
        if install_success: # Similar a scoop, si npm -g tiene éxito, suele funcionar.
            print_success("Comando 'npm install supabase --global' ejecutado. Verificando...")
            # La verificación de `supabase --version` puede fallar inmediatamente si el PATH global de npm no está en la sesión actual.
            if run_command(["supabase", "--version"], suppress_output=True)[0]:
                print_success("¡Supabase CLI instalada y verificada exitosamente vía NPM!")
                print_warning("Es posible que necesites REINICIAR TU TERMINAL (o VSCode) para que el PATH se actualice.")
                return True
            else:
                print_error("Supabase CLI no se encuentra después de la instalación con NPM.")
                print_info("Esto es común si el directorio global de paquetes de NPM no está en tu PATH o si la terminal necesita reiniciarse.")
                print_info("Intenta reiniciar tu terminal o verifica la configuración de tu PATH para los módulos globales de NPM.")
        else:
            print_error("Falló la instalación con NPM.")
    else:
        print_info("NPM no está disponible en este sistema.")

    # Si todos los métodos fallaron
    print_error("Todos los métodos de instalación automática fallaron o no estaban disponibles.")
    print_info("Por favor, instala Supabase CLI manualmente: https://supabase.com/docs/guides/cli/getting-started")
    return False

# El resto del archivo supabase_setup.py (desde check_supabase_login hasta el final) permanece igual
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
                # Caso 1: [project_id]\nid = "xxx"
                if 'project_id' in config and 'id' in config['project_id']:
                    project_id = config['project_id']['id']
                # Caso 2: project_id = "xxx" (sin sección, leído por configparser bajo DEFAULT si no hay otras secciones)
                # O si está en una sección por defecto. Es más fiable leerlo manualmente si no está en [project_id].
                if not project_id:
                    with open(CONFIG_FILE_PATH, 'r') as f_config:
                        for line in f_config:
                            line_strip = line.strip()
                            if line_strip.startswith('project_id'): # Cubre project_id = "xxx" y project_id="xxx"
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
