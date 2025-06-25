"""
Módulo de configuración de base de datos para el sistema MANUS-like
Maneja la conexión con Supabase PostgreSQL
"""

import os
import logging
from supabase import create_client, Client
from typing import Optional, Dict, Any, List
import psycopg2
from psycopg2.extras import RealDictCursor
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class Database:
    """Clase para manejar la conexión con Supabase"""
    
    def __init__(self):
        self.supabase: Optional[Client] = None
        self.pg_connection = None
        self._initialized = False
    
    def init_app(self, app):
        """Inicializar la conexión con Supabase"""
        try:
            supabase_url = app.config.get('SUPABASE_URL')
            supabase_key = app.config.get('SUPABASE_KEY')
            
            if not supabase_url or not supabase_key:
                raise ValueError("SUPABASE_URL and SUPABASE_KEY must be configured")
            
            self.supabase = create_client(supabase_url, supabase_key)
            
            # También configurar conexión directa a PostgreSQL para operaciones avanzadas
            self._setup_pg_connection(app)
            
            self._initialized = True
            logger.info("Database connection initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {str(e)}")
            raise
    
    def _setup_pg_connection(self, app):
        """Configurar conexión directa a PostgreSQL"""
        try:
            # Extraer información de conexión de la URL de Supabase
            supabase_url = app.config.get('SUPABASE_URL')
            service_key = app.config.get('SUPABASE_SERVICE_KEY')
            
            # Para desarrollo local, usar variables de entorno específicas
            pg_host = os.environ.get('POSTGRES_HOST', 'localhost')
            pg_port = os.environ.get('POSTGRES_PORT', '5432')
            pg_db = os.environ.get('POSTGRES_DB', 'postgres')
            pg_user = os.environ.get('POSTGRES_USER', 'postgres')
            pg_password = os.environ.get('POSTGRES_PASSWORD', 'postgres')
            
            self.pg_connection = psycopg2.connect(
                host=pg_host,
                port=pg_port,
                database=pg_db,
                user=pg_user,
                password=pg_password,
                cursor_factory=RealDictCursor
            )
            
            logger.info("PostgreSQL direct connection established")
            
        except Exception as e:
            logger.warning(f"Could not establish direct PostgreSQL connection: {str(e)}")
            self.pg_connection = None
    
    def execute_query(self, query: str, params: tuple = None) -> List[Dict[str, Any]]:
        """Ejecutar una consulta SQL directa"""
        if not self.pg_connection:
            raise RuntimeError("PostgreSQL connection not available")
        
        try:
            with self.pg_connection.cursor() as cursor:
                cursor.execute(query, params)
                if cursor.description:
                    return [dict(row) for row in cursor.fetchall()]
                return []
        except Exception as e:
            self.pg_connection.rollback()
            logger.error(f"Query execution failed: {str(e)}")
            raise
    
    def execute_transaction(self, queries: List[tuple]) -> bool:
        """Ejecutar múltiples consultas en una transacción"""
        if not self.pg_connection:
            raise RuntimeError("PostgreSQL connection not available")
        
        try:
            with self.pg_connection.cursor() as cursor:
                for query, params in queries:
                    cursor.execute(query, params)
                self.pg_connection.commit()
                return True
        except Exception as e:
            self.pg_connection.rollback()
            logger.error(f"Transaction failed: {str(e)}")
            raise
    
    def get_client(self) -> Client:
        """Obtener el cliente de Supabase"""
        if not self._initialized or not self.supabase:
            raise RuntimeError("Database not initialized")
        return self.supabase
    
    def close(self):
        """Cerrar conexiones"""
        if self.pg_connection:
            self.pg_connection.close()

# Instancia global de la base de datos
db = Database()

def init_db(app):
    """Función para inicializar la base de datos"""
    db.init_app(app)
    
    # Registrar función de limpieza al cerrar la app
    @app.teardown_appcontext
    def close_db(error):
        if error:
            logger.error(f"Application context error: {str(error)}")

class BaseModel:
    """Clase base para modelos de datos"""
    
    def __init__(self, table_name: str):
        self.table_name = table_name
        self.supabase = db.get_client()
    
    def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Crear un nuevo registro"""
        try:
            # Agregar timestamps
            now = datetime.utcnow().isoformat()
            data['created_at'] = now
            if 'updated_at' not in data:
                data['updated_at'] = now
            
            result = self.supabase.table(self.table_name).insert(data).execute()
            
            if result.data:
                return result.data[0]
            else:
                raise Exception("No data returned from insert operation")
                
        except Exception as e:
            logger.error(f"Error creating record in {self.table_name}: {str(e)}")
            raise
    
    def get_by_id(self, record_id: str) -> Optional[Dict[str, Any]]:
        """Obtener un registro por ID"""
        try:
            result = self.supabase.table(self.table_name).select("*").eq("id", record_id).execute()
            
            if result.data:
                return result.data[0]
            return None
            
        except Exception as e:
            logger.error(f"Error getting record from {self.table_name}: {str(e)}")
            raise
    
    def get_all(self, filters: Dict[str, Any] = None, limit: int = None, offset: int = None) -> List[Dict[str, Any]]:
        """Obtener múltiples registros"""
        try:
            query = self.supabase.table(self.table_name).select("*")
            
            if filters:
                for key, value in filters.items():
                    query = query.eq(key, value)
            
            if limit:
                query = query.limit(limit)
            
            if offset:
                query = query.offset(offset)
            
            result = query.execute()
            return result.data or []
            
        except Exception as e:
            logger.error(f"Error getting records from {self.table_name}: {str(e)}")
            raise
    
    def update(self, record_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Actualizar un registro"""
        try:
            # Agregar timestamp de actualización
            data['updated_at'] = datetime.utcnow().isoformat()
            
            result = self.supabase.table(self.table_name).update(data).eq("id", record_id).execute()
            
            if result.data:
                return result.data[0]
            else:
                raise Exception("No data returned from update operation")
                
        except Exception as e:
            logger.error(f"Error updating record in {self.table_name}: {str(e)}")
            raise
    
    def delete(self, record_id: str) -> bool:
        """Eliminar un registro"""
        try:
            result = self.supabase.table(self.table_name).delete().eq("id", record_id).execute()
            return True
            
        except Exception as e:
            logger.error(f"Error deleting record from {self.table_name}: {str(e)}")
            raise
    
    def count(self, filters: Dict[str, Any] = None) -> int:
        """Contar registros"""
        try:
            query = self.supabase.table(self.table_name).select("id", count="exact")
            
            if filters:
                for key, value in filters.items():
                    query = query.eq(key, value)
            
            result = query.execute()
            return result.count or 0
            
        except Exception as e:
            logger.error(f"Error counting records in {self.table_name}: {str(e)}")
            raise

class UserModel(BaseModel):
    """Modelo para usuarios"""
    
    def __init__(self):
        super().__init__("users")
    
    def get_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Obtener usuario por email"""
        try:
            result = self.supabase.table(self.table_name).select("*").eq("email", email).execute()
            
            if result.data:
                return result.data[0]
            return None
            
        except Exception as e:
            logger.error(f"Error getting user by email: {str(e)}")
            raise
    
    def get_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Obtener usuario por username"""
        try:
            result = self.supabase.table(self.table_name).select("*").eq("username", username).execute()
            
            if result.data:
                return result.data[0]
            return None
            
        except Exception as e:
            logger.error(f"Error getting user by username: {str(e)}")
            raise

class ConversationModel(BaseModel):
    """Modelo para conversaciones"""
    
    def __init__(self):
        super().__init__("conversations")
    
    def get_by_user(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Obtener conversaciones de un usuario"""
        try:
            result = (self.supabase.table(self.table_name)
                     .select("*, agents(name, description)")
                     .eq("user_id", user_id)
                     .order("created_at", desc=True)
                     .limit(limit)
                     .execute())
            
            return result.data or []
            
        except Exception as e:
            logger.error(f"Error getting conversations for user: {str(e)}")
            raise

class MessageModel(BaseModel):
    """Modelo para mensajes"""
    
    def __init__(self):
        super().__init__("messages")
    
    def get_by_conversation(self, conversation_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Obtener mensajes de una conversación"""
        try:
            result = (self.supabase.table(self.table_name)
                     .select("*")
                     .eq("conversation_id", conversation_id)
                     .order("created_at", desc=False)
                     .limit(limit)
                     .execute())
            
            return result.data or []
            
        except Exception as e:
            logger.error(f"Error getting messages for conversation: {str(e)}")
            raise

class TaskModel(BaseModel):
    """Modelo para tareas"""
    
    def __init__(self):
        super().__init__("tasks")
    
    def get_active_tasks(self, user_id: str = None) -> List[Dict[str, Any]]:
        """Obtener tareas activas"""
        try:
            query = (self.supabase.table(self.table_name)
                    .select("*, conversations(user_id, title)")
                    .in_("status", ["pending", "running"]))
            
            if user_id:
                query = query.eq("conversations.user_id", user_id)
            
            result = query.execute()
            return result.data or []
            
        except Exception as e:
            logger.error(f"Error getting active tasks: {str(e)}")
            raise

class ToolModel(BaseModel):
    """Modelo para herramientas"""
    
    def __init__(self):
        super().__init__("tools")
    
    def get_enabled_tools(self) -> List[Dict[str, Any]]:
        """Obtener herramientas habilitadas"""
        try:
            result = (self.supabase.table(self.table_name)
                     .select("*")
                     .eq("is_enabled", True)
                     .order("category", desc=False)
                     .execute())
            
            return result.data or []
            
        except Exception as e:
            logger.error(f"Error getting enabled tools: {str(e)}")
            raise
    
    def get_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Obtener herramienta por nombre"""
        try:
            result = self.supabase.table(self.table_name).select("*").eq("name", name).execute()
            
            if result.data:
                return result.data[0]
            return None
            
        except Exception as e:
            logger.error(f"Error getting tool by name: {str(e)}")
            raise

class AgentModel(BaseModel):
    """Modelo para agentes"""
    
    def __init__(self):
        super().__init__("agents")
    
    def get_public_agents(self) -> List[Dict[str, Any]]:
        """Obtener agentes públicos"""
        try:
            result = (self.supabase.table(self.table_name)
                     .select("*")
                     .eq("is_public", True)
                     .eq("is_active", True)
                     .order("name", desc=False)
                     .execute())
            
            return result.data or []
            
        except Exception as e:
            logger.error(f"Error getting public agents: {str(e)}")
            raise
    
    def get_by_user(self, user_id: str) -> List[Dict[str, Any]]:
        """Obtener agentes de un usuario"""
        try:
            result = (self.supabase.table(self.table_name)
                     .select("*")
                     .eq("created_by", user_id)
                     .eq("is_active", True)
                     .order("name", desc=False)
                     .execute())
            
            return result.data or []
            
        except Exception as e:
            logger.error(f"Error getting agents for user: {str(e)}")
            raise

