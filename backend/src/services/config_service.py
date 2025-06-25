"""
Servicio de configuración del sistema MANUS-like
Maneja la configuración global del sistema y preferencias
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from src.models.database import db, BaseModel

logger = logging.getLogger(__name__)

class ConfigModel(BaseModel):
    """Modelo para configuración del sistema"""
    
    def __init__(self):
        super().__init__("system_config")
    
    def get_by_key(self, key: str) -> Optional[Dict[str, Any]]:
        """Obtener configuración por clave"""
        try:
            result = self.supabase.table(self.table_name).select("*").eq("config_key", key).execute()
            
            if result.data:
                return result.data[0]
            return None
            
        except Exception as e:
            logger.error(f"Error getting config by key: {str(e)}")
            raise

class ConfigService:
    """Servicio para gestión de configuración del sistema"""
    
    def __init__(self):
        self.config_model = ConfigModel()
        self._cache = {}
        self._cache_timestamp = None
    
    def get_config(self, key: str, default_value: Any = None) -> Any:
        """Obtener valor de configuración"""
        try:
            config = self.config_model.get_by_key(key)
            
            if config:
                return config['config_value']
            else:
                return default_value
                
        except Exception as e:
            logger.error(f"Get config failed for key {key}: {str(e)}")
            return default_value
    
    def set_config(self, key: str, value: Any, updated_by: str = None) -> bool:
        """Establecer valor de configuración"""
        try:
            existing_config = self.config_model.get_by_key(key)
            
            config_data = {
                'config_key': key,
                'config_value': value,
                'updated_by': updated_by
            }
            
            if existing_config:
                # Actualizar configuración existente
                self.config_model.update(existing_config['id'], {
                    'config_value': value,
                    'updated_by': updated_by
                })
            else:
                # Crear nueva configuración
                self.config_model.create(config_data)
            
            # Limpiar cache
            self._cache.pop(key, None)
            
            return True
            
        except Exception as e:
            logger.error(f"Set config failed for key {key}: {str(e)}")
            return False
    
    def get_all_config(self, include_sensitive: bool = False) -> Dict[str, Any]:
        """Obtener toda la configuración"""
        try:
            filters = {}
            if not include_sensitive:
                filters['is_sensitive'] = False
            
            configs = self.config_model.get_all(filters)
            
            config_dict = {}
            for config in configs:
                config_dict[config['config_key']] = config['config_value']
            
            return config_dict
            
        except Exception as e:
            logger.error(f"Get all config failed: {str(e)}")
            return {}
    
    def delete_config(self, key: str) -> bool:
        """Eliminar configuración"""
        try:
            config = self.config_model.get_by_key(key)
            
            if config:
                self.config_model.delete(config['id'])
                self._cache.pop(key, None)
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Delete config failed for key {key}: {str(e)}")
            return False
    
    def initialize_default_config(self) -> None:
        """Inicializar configuración por defecto"""
        default_configs = {
            # Configuración de Ollama
            'ollama_base_url': 'http://localhost:11434',
            'default_model': 'llama2',
            'ollama_timeout': 30,
            'ollama_max_retries': 3,
            
            # Configuración de agentes
            'default_agent_temperature': 0.7,
            'max_tokens_per_request': 4096,
            'max_conversation_history': 100,
            'enable_memory_persistence': True,
            'default_memory_limit': 10000,
            
            # Configuración de archivos
            'file_upload_max_size': 104857600,  # 100MB
            'allowed_file_extensions': [
                'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx',
                'xls', 'xlsx', 'ppt', 'pptx', 'csv', 'json', 'xml', 'md',
                'py', 'js', 'html', 'css', 'zip', 'tar', 'gz'
            ],
            'temp_file_retention_hours': 24,
            
            # Configuración de tareas
            'max_concurrent_tasks': 10,
            'task_timeout_minutes': 60,
            'enable_task_queue': True,
            'task_retry_attempts': 3,
            
            # Configuración de seguridad
            'session_timeout': 3600,  # 1 hora
            'enable_audit_logging': True,
            'require_tool_confirmation': False,
            'max_login_attempts': 5,
            'login_lockout_minutes': 15,
            
            # Configuración del sistema
            'system_name': 'MANUS-like System',
            'system_version': '1.0.0',
            'maintenance_mode': False,
            'debug_mode': False,
            'log_level': 'INFO',
            
            # Configuración de notificaciones
            'enable_email_notifications': False,
            'enable_realtime_updates': True,
            'notification_retention_days': 7,
            
            # Configuración de backup
            'auto_backup_enabled': True,
            'backup_retention_days': 30,
            'backup_schedule': '0 2 * * *',  # Diario a las 2 AM
            
            # Configuración de rendimiento
            'cache_enabled': True,
            'cache_ttl_seconds': 300,  # 5 minutos
            'rate_limit_requests_per_minute': 60,
            'enable_compression': True,
            
            # Configuración de Docker
            'docker_network': 'manus_network',
            'docker_restart_policy': 'unless-stopped',
            'docker_log_driver': 'json-file',
            'docker_log_max_size': '10m',
            'docker_log_max_file': '3'
        }
        
        for key, value in default_configs.items():
            try:
                existing = self.config_model.get_by_key(key)
                if not existing:
                    self.set_config(key, value)
                    logger.info(f"Initialized default config: {key}")
            except Exception as e:
                logger.error(f"Failed to initialize config {key}: {str(e)}")
    
    def get_ollama_config(self) -> Dict[str, Any]:
        """Obtener configuración específica de Ollama"""
        return {
            'base_url': self.get_config('ollama_base_url', 'http://localhost:11434'),
            'default_model': self.get_config('default_model', 'llama2'),
            'timeout': self.get_config('ollama_timeout', 30),
            'max_retries': self.get_config('ollama_max_retries', 3)
        }
    
    def get_agent_config(self) -> Dict[str, Any]:
        """Obtener configuración específica de agentes"""
        return {
            'default_temperature': self.get_config('default_agent_temperature', 0.7),
            'max_tokens': self.get_config('max_tokens_per_request', 4096),
            'max_history': self.get_config('max_conversation_history', 100),
            'memory_enabled': self.get_config('enable_memory_persistence', True),
            'memory_limit': self.get_config('default_memory_limit', 10000)
        }
    
    def get_file_config(self) -> Dict[str, Any]:
        """Obtener configuración específica de archivos"""
        return {
            'max_size': self.get_config('file_upload_max_size', 104857600),
            'allowed_extensions': self.get_config('allowed_file_extensions', []),
            'temp_retention_hours': self.get_config('temp_file_retention_hours', 24)
        }
    
    def get_security_config(self) -> Dict[str, Any]:
        """Obtener configuración específica de seguridad"""
        return {
            'session_timeout': self.get_config('session_timeout', 3600),
            'audit_logging': self.get_config('enable_audit_logging', True),
            'tool_confirmation': self.get_config('require_tool_confirmation', False),
            'max_login_attempts': self.get_config('max_login_attempts', 5),
            'lockout_minutes': self.get_config('login_lockout_minutes', 15)
        }
    
    def get_system_config(self) -> Dict[str, Any]:
        """Obtener configuración específica del sistema"""
        return {
            'name': self.get_config('system_name', 'MANUS-like System'),
            'version': self.get_config('system_version', '1.0.0'),
            'maintenance_mode': self.get_config('maintenance_mode', False),
            'debug_mode': self.get_config('debug_mode', False),
            'log_level': self.get_config('log_level', 'INFO')
        }
    
    def update_ollama_config(self, config: Dict[str, Any], updated_by: str = None) -> bool:
        """Actualizar configuración de Ollama"""
        try:
            success = True
            
            if 'base_url' in config:
                success &= self.set_config('ollama_base_url', config['base_url'], updated_by)
            
            if 'default_model' in config:
                success &= self.set_config('default_model', config['default_model'], updated_by)
            
            if 'timeout' in config:
                success &= self.set_config('ollama_timeout', config['timeout'], updated_by)
            
            if 'max_retries' in config:
                success &= self.set_config('ollama_max_retries', config['max_retries'], updated_by)
            
            return success
            
        except Exception as e:
            logger.error(f"Update Ollama config failed: {str(e)}")
            return False
    
    def is_maintenance_mode(self) -> bool:
        """Verificar si el sistema está en modo mantenimiento"""
        return self.get_config('maintenance_mode', False)
    
    def enable_maintenance_mode(self, updated_by: str = None) -> bool:
        """Habilitar modo mantenimiento"""
        return self.set_config('maintenance_mode', True, updated_by)
    
    def disable_maintenance_mode(self, updated_by: str = None) -> bool:
        """Deshabilitar modo mantenimiento"""
        return self.set_config('maintenance_mode', False, updated_by)
    
    def validate_config_value(self, key: str, value: Any) -> tuple[bool, str]:
        """Validar valor de configuración"""
        try:
            # Validaciones específicas por tipo de configuración
            if key == 'ollama_base_url':
                if not isinstance(value, str) or not value.startswith(('http://', 'https://')):
                    return False, "URL must start with http:// or https://"
            
            elif key in ['ollama_timeout', 'session_timeout', 'max_tokens_per_request']:
                if not isinstance(value, int) or value <= 0:
                    return False, "Value must be a positive integer"
            
            elif key == 'default_agent_temperature':
                if not isinstance(value, (int, float)) or not (0 <= value <= 2):
                    return False, "Temperature must be between 0 and 2"
            
            elif key == 'file_upload_max_size':
                if not isinstance(value, int) or value <= 0:
                    return False, "File size must be a positive integer"
            
            elif key in ['enable_audit_logging', 'maintenance_mode', 'debug_mode']:
                if not isinstance(value, bool):
                    return False, "Value must be boolean (true/false)"
            
            elif key == 'allowed_file_extensions':
                if not isinstance(value, list):
                    return False, "Value must be a list of file extensions"
                
                for ext in value:
                    if not isinstance(ext, str) or not ext.isalnum():
                        return False, "File extensions must be alphanumeric strings"
            
            return True, "Valid"
            
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    def export_config(self, include_sensitive: bool = False) -> Dict[str, Any]:
        """Exportar configuración para backup"""
        try:
            config = self.get_all_config(include_sensitive)
            
            export_data = {
                'config': config,
                'exported_at': datetime.utcnow().isoformat(),
                'version': self.get_config('system_version', '1.0.0'),
                'include_sensitive': include_sensitive
            }
            
            return export_data
            
        except Exception as e:
            logger.error(f"Export config failed: {str(e)}")
            return {}
    
    def import_config(self, config_data: Dict[str, Any], updated_by: str = None) -> Dict[str, Any]:
        """Importar configuración desde backup"""
        try:
            imported_count = 0
            errors = []
            
            config = config_data.get('config', {})
            
            for key, value in config.items():
                try:
                    # Validar valor
                    is_valid, error_msg = self.validate_config_value(key, value)
                    
                    if is_valid:
                        if self.set_config(key, value, updated_by):
                            imported_count += 1
                        else:
                            errors.append(f"Failed to set {key}")
                    else:
                        errors.append(f"Invalid value for {key}: {error_msg}")
                        
                except Exception as e:
                    errors.append(f"Error importing {key}: {str(e)}")
            
            return {
                'success': True,
                'imported_count': imported_count,
                'total_configs': len(config),
                'errors': errors
            }
            
        except Exception as e:
            logger.error(f"Import config failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'imported_count': 0,
                'errors': []
            }

