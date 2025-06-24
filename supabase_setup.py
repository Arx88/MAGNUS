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
            if process.stdout: print_info(f"Salida de {' '.join(command_list)}:\n{process.stdout.strip()}")
            if process.stderr: print_warning(f"Salida de error (puede ser informativa) de {' '.join(command_list)}:\n{process.stderr.strip()}")
        return True, process.stdout.strip(), process.stderr.strip()
    except subprocess.CalledProcessError as e:
        if not suppress_output:
            print_error(f"Error al ejecutar: {' '.join(command_list)}")
            if e.stdout: print_info(f"Salida (stdout) del error: {e.stdout.strip()}")
            if e.stderr: print_error(f"Salida (stderr) del error: {e.stderr.strip()}")
        return False, e.stdout.strip() if e.stdout else "", e.stderr.strip()
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

    # Si no está instalada, intentar instalar con Winget en Windows
    print_warning("Supabase CLI no está instalada o no se encuentra en el PATH.")
    if platform.system() == "Windows":
        print_info("Sistema operativo detectado: Windows.")
        install_choice = input("¿Deseas intentar instalar Supabase CLI usando Winget? (s/N): ").strip().lower()
        if install_choice == 's':
            print_info("Intentando instalar Supabase CLI con Winget...")
            # Winget puede requerir permisos de administrador, lo que podría fallar si el script no se ejecuta como tal.
            # Los argumentos --accept-package-agreements y --accept-source-agreements son para instalaciones no interactivas.
            winget_cmd = [
                "winget", "install", "supabase.cli",
                "--source", "winget",
                "--accept-package-agreements",
                "--accept-source-agreements"
            ]
            # Es importante no usar check=True aquí inicialmente para poder manejar el error de "winget no encontrado"
            install_success, install_stdout, install_stderr = run_command(winget_cmd, timeout=300, check=False) # 5 minutos de timeout

            if install_success:
                print_success("Winget ejecutado. Verificando la instalación de Supabase CLI nuevamente...")
                # Volver a verificar
                success_after_install, _, _ = run_command(["supabase", "--version"], suppress_output=True)
                if success_after_install:
                    print_success("Supabase CLI instalada y verificada exitosamente.")
                    return True
                else:
                    print_error("Supabase CLI aún no se encuentra después del intento de instalación con Winget.")
                    print_info(f"Salida de Winget (stdout): {install_stdout}")
                    print_info(f"Salida de Winget (stderr): {install_stderr}")
            elif "Comando no encontrado: winget" in install_stderr:
                print_error("Winget no está instalado o no se encuentra en el PATH.")
                print_info("Puedes instalar Winget (App Installer) desde la Microsoft Store: ms-windows-store://pdp/?productid=9NBLGGH4NNS1")
            else:
                print_error("Falló la instalación de Supabase CLI con Winget.")
                print_info(f"Salida de Winget (stdout): {install_stdout}")
                print_info(f"Salida de Winget (stderr): {install_stderr}")
        else:
            print_info("Instalación con Winget omitida por el usuario.")

    # Si no es Windows, o si la instalación con Winget falló o se omitió
    if "Comando no encontrado" not in stderr and platform.system() != "Windows": # Muestra el detalle solo si no es por no encontrar el comando
         print_info(f"Detalle del intento inicial: {stderr}")
    print_info("Por favor, instala Supabase CLI manualmente siguiendo las instrucciones en: https://supabase.com/docs/guides/cli/getting-started")
    return False

def check_supabase_login():
    print_info("Verificando estado de login en Supabase CLI...")
    # "supabase projects list" requiere autenticación.
    success, _, stderr = run_command(["supabase", "projects", "list"], suppress_output=True) # Suprimir salida normal, solo mostrar si hay error
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
    if not os.path.isdir(SUPABASE_DIR): # Verificar si es un directorio
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

    # Asegurar que el directorio de migraciones exista
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
            # Asegurarse de que el archivo no esté vacío
            if os.path.getsize(CONFIG_FILE_PATH) > 0:
                config.read(CONFIG_FILE_PATH)
                # Supabase CLI v1.110.1 en adelante usa [project_id] sin comillas
                # versiones anteriores podrían haberlo tenido como string literal.
                # Intentamos leerlo como sección y como valor simple si falla.
                project_id = None
                if 'project_id' in config: # Como sección [project_id]
                    project_id = config['project_id'].get('id', None) # Asumiendo [project_id]\nid = "xxx"

                if not project_id and 'PROJECT' in config: # Como sección [PROJECT] (observado en algunos configs)
                     project_id = config['PROJECT'].get('ref', None)


                if not project_id: # Intentar leerlo como un valor simple si no es una sección
                    # Esto es menos probable con configparser, pero por si acaso.
                    # La estructura real de config.toml es:
                    # project_id = "your-project-ref" (sin sección)
                    # O más recientemente:
                    # [project_id]
                    # id = "your-project-ref"
                    # Para el caso project_id = "xxx" sin sección, configparser lo leerá bajo DEFAULT si no hay secciones.
                    # O si hay una sección por defecto que lo contenga.
                    # Es más simple leer el archivo manualmente para este caso.
                    with open(CONFIG_FILE_PATH, 'r') as f_config:
                        for line in f_config:
                            if line.strip().startswith('project_id'):
                                project_id = line.split('=')[1].strip().replace('"', '')
                                break

                if project_id:
                    print_success(f"PROJECT_REF encontrado en '{CONFIG_FILE_PATH}': {project_id}")
                    return project_id
                else:
                    print_warning(f"No se pudo extraer 'project_id' de '{CONFIG_FILE_PATH}'. Formato inesperado.")
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
        # Supabase link puede fallar si ya está vinculado al mismo proyecto, lo cual no es un error crítico.
        if "already linked to project" in stderr.lower() and project_ref in stderr.lower():
            print_success(f"El proyecto ya está vinculado con {project_ref}. Continuando...")
            return True
        elif "config file differs" in stderr.lower():
             print_warning(f"El project ID en {CONFIG_FILE_PATH} difiere del proporcionado.")
             print_info("Por favor, resuelve esto manualmente o ejecuta 'supabase link --project-ref TU_PROJECT_ID --force' si es necesario.")
             # Consideramos esto un fallo para el script automático.
        print_error(f"Error al vincular el proyecto. Detalle: {stderr}")
        return False

def create_migration_from_init_sql():
    print_info(f"Creando archivo de migración desde '{INIT_SQL_FILE}'...")
    if not os.path.exists(INIT_SQL_FILE):
        print_error(f"El archivo '{INIT_SQL_FILE}' no se encontró en el directorio actual.")
        return False

    if not os.path.isdir(MIGRATIONS_DIR): # Doble check
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
    success, _, stderr = run_command(command, timeout=180) # Timeout de 3 minutos

    if success:
        print_success("Migraciones aplicadas exitosamente (o no había cambios pendientes).")
        return True
    else:
        print_error(f"Error al aplicar las migraciones. Detalle: {stderr}")
        return False

def main():
    print_header("Script de Configuración de Supabase con CLI")

    if not check_supabase_cli():
        return

    if not initialize_supabase_project_if_needed():
        return

    # El login es crucial antes de intentar obtener project_ref o linkear
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
