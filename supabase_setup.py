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

def run_command(command_list, timeout=60, check=True, suppress_output=False):
    """Ejecuta un comando de subprocess de forma segura y devuelve (éxito, stdout, stderr)."""
    try:
        process = subprocess.run(
            command_list,
            capture_output=True,
            text=True,
            check=check, # Lanza CalledProcessError si el comando devuelve un código de error
            timeout=timeout
        )
        if not suppress_output:
            # Imprimir stdout solo si no está vacío
            if process.stdout and process.stdout.strip():
                 print_info(f"Salida de {' '.join(command_list)}:\n{process.stdout.strip()}")
            # Imprimir stderr solo si no está vacío
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

def check_supabase_cli():
    print_info("Verificando Supabase CLI...")
    success, _, stderr = run_command(["supabase", "--version"], suppress_output=True)
    if success:
        print_success("Supabase CLI está instalada.")
        return True

    print_warning("Supabase CLI no está instalada o no se encuentra en el PATH.")
    if platform.system() == "Windows":
        print_info("Sistema operativo detectado: Windows.")
        install_choice = input("¿Deseas intentar instalar Supabase CLI usando Winget? (s/N): ").strip().lower()
        if install_choice == 's':
            print_info("Intentando instalar Supabase CLI con Winget...")

            print_info("Intentando actualizar las fuentes de Winget...")
            # No es crítico si esto falla, podría ser por permisos o estar actualizado.
            # run_command ya imprime la salida si no se suprime.
            _, _, update_stderr = run_command(["winget", "source", "update"], timeout=120, check=False)
            if "No se reconoció el nombre del argumento" in update_stderr and "update" in update_stderr:
                 print_warning(f"Tu versión de 'winget source update' podría tener argumentos diferentes o no ser reconocida. Continuando de todas formas...")
            else:
                 print_info("Intento de actualización de fuentes de Winget completado.")


            # --- CAMBIO 1: Usar el ID de paquete correcto ---
            package_id_to_install = "Supabase.SupabaseCLI"

            print_info(f"Buscando el paquete '{package_id_to_install}' con Winget...")
            search_cmd = ["winget", "search", package_id_to_install, "--source", "winget", "--accept-source-agreements"]
            search_success, search_stdout, search_stderr = run_command(search_cmd, timeout=120, check=False)

            if not search_success or "No se encontró ningún paquete" in search_stdout or "No se encontró ningún paquete" in search_stderr:
                 print_warning(f"Winget search no pudo confirmar el paquete '{package_id_to_install}'. (stdout: '{search_stdout}', stderr: '{search_stderr}'). Se intentará la instalación de todas formas con este ID.")
            else:
                 print_success(f"Paquete '{package_id_to_install}' encontrado en los repositorios de Winget.")


            print_info(f"Intentando instalar '{package_id_to_install}' con Winget...")
            # --- CAMBIO 2: Corregir el error tipográfico ---
            winget_cmd = [
                "winget", "install", package_id_to_install,
                "--source", "winget",
                "--accept-package-agreements",
                "--accept-source-agreements"  # Corregido
            ]
            install_success, install_stdout, install_stderr = run_command(winget_cmd, timeout=300, check=False)

            # --- CAMBIO 3: Mejorar la comprobación de éxito ---
            # Winget puede devolver código 0 aunque no instale nada.
            # Hay que verificar la salida de texto para estar seguros.
            if install_success and "No se encontró ningún paquete" not in install_stdout and "No se encontró ningún paquete" not in install_stderr:
                print_success("Comando de instalación de Winget parece haberse ejecutado. Verificando la instalación...")
                success_after_install, _, _ = run_command(["supabase", "--version"], suppress_output=True)
                if success_after_install:
                    print_success("Supabase CLI instalada y verificada exitosamente.")
                    return True
                else:
                    print_error("Supabase CLI aún no se encuentra después del intento de instalación con Winget.")
                    print_info("Es posible que necesites reiniciar tu terminal (o VSCode) para que el PATH se actualice.")
            else:
                print_error(f"Falló la instalación de Supabase CLI con Winget.")
                # El error ya se imprime desde run_command si no es suppress_output=False en la llamada.
                # Aquí podemos añadir contexto específico si es necesario.
                if not install_success:
                     print_info(f"El comando 'winget install' devolvió un código de error.")
                if "No se encontró ningún paquete" in install_stdout or "No se encontró ningún paquete" in install_stderr:
                     print_info(f"Winget reportó explícitamente: 'No se encontró ningún paquete'.")

        else:
            print_info("Instalación con Winget omitida por el usuario.")

    # Mensaje final si todo lo anterior falla
    # stderr aquí es del primer `supabase --version`
    # Solo mostrar si no es Windows o si la instalación de Winget no se intentó.
    initial_check_stderr = stderr
    if not (platform.system() == "Windows" and 'install_choice' in locals() and install_choice == 's'):
        if "Comando no encontrado" not in initial_check_stderr and initial_check_stderr:
            print_info(f"Detalle del intento inicial de 'supabase --version': {initial_check_stderr}")
    print_info("Por favor, instala Supabase CLI manualmente siguiendo las instrucciones en: https://supabase.com/docs/guides/cli/getting-started")
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
