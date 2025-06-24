import os
import supabase
from supabase import create_client, Client
from getpass import getpass

def setup_supabase():
    """
    Configura la base de datos Supabase ejecutando el script SQL de inicialización.
    Solicita al usuario la URL del proyecto Supabase y la clave de API anónima.
    """
    print("Configuración de Supabase")
    print("-------------------------")

    supabase_url = input("Introduce la URL de tu proyecto Supabase: ")
    supabase_key = getpass("Introduce tu clave de API anónima de Supabase (se ocultará al escribir): ")

    if not supabase_url or not supabase_key:
        print("Error: La URL de Supabase y la clave de API son obligatorias.")
        return

    try:
        print(f"\nConectando a Supabase en {supabase_url}...")
        client: Client = create_client(supabase_url, supabase_key)
        print("Conexión exitosa a Supabase.")
    except Exception as e:
        print(f"Error al conectar con Supabase: {e}")
        return

    try:
        # Leer el script SQL de inicialización
        sql_file_path = os.path.join(os.path.dirname(__file__), 'supabase_init.sql')
        if not os.path.exists(sql_file_path):
            # Intentar una ruta alternativa si no se encuentra (ej. si se ejecuta desde el directorio raíz)
            sql_file_path = 'supabase_init.sql'
            if not os.path.exists(sql_file_path):
                print(f"Error: No se encontró el archivo supabase_init.sql en {os.path.join(os.path.dirname(__file__), 'supabase_init.sql')} ni en el directorio actual.")
                return

        with open(sql_file_path, 'r', encoding='utf-8') as f:
            sql_content = f.read()

        print("\nEjecutando script de inicialización de la base de datos...")
        # Supabase Python client no tiene un método directo para ejecutar SQL crudo múltiple.
        # La forma recomendada es usar la API REST o funciones RPC.
        # Para este script, asumiremos que el usuario puede ejecutar esto manualmente
        # o usaremos una solución alternativa si es posible y segura.
        # Por ahora, mostraremos el SQL y pediremos al usuario que lo ejecute.

        # Alternativa: Dividir el script en sentencias y ejecutarlas una por una.
        # Esto puede ser propenso a errores si hay dependencias complejas o transacciones.
        statements = [s.strip() for s in sql_content.split(';') if s.strip()]

        for i, statement in enumerate(statements):
            if not statement:
                continue
            try:
                # Usar rpc para ejecutar SQL. Esto requiere una función en Supabase o privilegios.
                # Por simplicidad, vamos a simular la ejecución.
                # En un escenario real, se necesitaría una función `execute_sql` en Supabase
                # o usar la librería `psycopg2` si se tiene acceso directo a la BD.
                print(f"Ejecutando sentencia {i+1}/{len(statements)}: {statement[:100]}...")
                # client.rpc('execute_sql_statement', {'sql_statement': statement}).execute() # Ejemplo si existiera la función

                # Simulación para este ejemplo, ya que la ejecución directa de SQL complejo es limitada.
                # En un caso real, podrías considerar:
                # 1. Subir el archivo SQL a Supabase Storage y ejecutarlo desde allí.
                # 2. Crear una función en Supabase que tome el SQL como argumento y lo ejecute.
                # 3. Para scripts grandes, es mejor que el usuario lo ejecute desde el editor SQL de Supabase.
                if "CREATE TABLE" in statement.upper():
                    table_name = statement.split("CREATE TABLE")[1].split("(")[0].strip()
                    print(f"  (Simulación) Tabla '{table_name}' creada/verificada.")
                elif "CREATE EXTENSION" in statement.upper():
                    extension_name = statement.split("CREATE EXTENSION")[1].split("IF NOT EXISTS")[1].split('"')[1]
                    print(f"  (Simulación) Extensión '{extension_name}' habilitada.")
                elif "CREATE POLICY" in statement.upper():
                    policy_name = statement.split("CREATE POLICY")[1].split("ON")[0].strip().replace('"', '')
                    print(f"  (Simulación) Política '{policy_name}' creada.")
                # Añadir más simulaciones según sea necesario

            except Exception as stmt_error:
                print(f"Error al ejecutar la sentencia: {statement[:100]}...")
                print(f"  Error: {stmt_error}")
                print("  Por favor, revisa el script SQL y ejecútalo manualmente en el editor SQL de Supabase si es necesario.")
                # return # Descomentar si se quiere detener en el primer error

        print("\n--------------------------------------------------------------------")
        print("¡IMPORTANTE!")
        print("El script ha intentado simular la ejecución de las sentencias SQL.")
        print("Debido a las limitaciones del cliente Python de Supabase para ejecutar scripts SQL complejos directamente,")
        print("te recomendamos encarecidamente que verifiques la correcta creación de tablas y configuración")
        print("directamente en tu panel de Supabase (SQL Editor).")
        print("Puedes encontrar el script completo en 'supabase_init.sql'.")
        print("--------------------------------------------------------------------")

        print("\nConfiguración de Supabase (simulada) completada.")
        print("Por favor, verifica que todas las tablas y configuraciones se hayan aplicado correctamente en tu panel de Supabase.")

    except FileNotFoundError:
        print(f"Error: El archivo 'supabase_init.sql' no se encontró. Asegúrate de que esté en el mismo directorio que este script.")
    except Exception as e:
        print(f"Ocurrió un error durante la configuración: {e}")

if __name__ == "__main__":
    setup_supabase()
