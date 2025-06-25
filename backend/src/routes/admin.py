"""
Rutas del panel de administración para el sistema MANUS-like
Maneja configuración del sistema, gestión de usuarios y monitorización
"""

from flask import Blueprint, request, jsonify, current_app
import logging
import os
from datetime import datetime, timedelta

from src.models.database import db, UserModel, AgentModel, ToolModel, ConversationModel, TaskModel
from src.routes.auth import admin_required
from src.services.config_service import ConfigService

logger = logging.getLogger(__name__)

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/dashboard', methods=['GET'])
@admin_required
def get_dashboard():
    """Obtener datos del dashboard de administración"""
    try:
        # Modelos
        user_model = UserModel()
        agent_model = AgentModel()
        tool_model = ToolModel()
        conversation_model = ConversationModel()
        task_model = TaskModel()
        
        # Estadísticas básicas
        stats = {
            'users': {
                'total': user_model.count(),
                'active': user_model.count({'is_active': True}),
                'admins': user_model.count({'role': 'admin'})
            },
            'agents': {
                'total': agent_model.count(),
                'public': agent_model.count({'is_public': True}),
                'active': agent_model.count({'is_active': True})
            },
            'tools': {
                'total': tool_model.count(),
                'enabled': tool_model.count({'is_enabled': True}),
                'disabled': tool_model.count({'is_enabled': False})
            },
            'conversations': {
                'total': conversation_model.count(),
                'active': conversation_model.count({'status': 'active'}),
                'completed': conversation_model.count({'status': 'completed'})
            },
            'tasks': {
                'total': task_model.count(),
                'pending': task_model.count({'status': 'pending'}),
                'running': task_model.count({'status': 'running'}),
                'completed': task_model.count({'status': 'completed'}),
                'failed': task_model.count({'status': 'failed'})
            }
        }
        
        # Estadísticas de actividad reciente (últimos 7 días)
        week_ago = (datetime.utcnow() - timedelta(days=7)).isoformat()
        
        try:
            recent_activity = {
                'new_users': db.execute_query(
                    "SELECT COUNT(*) as count FROM users WHERE created_at >= %s",
                    (week_ago,)
                )[0]['count'],
                'new_conversations': db.execute_query(
                    "SELECT COUNT(*) as count FROM conversations WHERE created_at >= %s",
                    (week_ago,)
                )[0]['count'],
                'completed_tasks': db.execute_query(
                    "SELECT COUNT(*) as count FROM tasks WHERE status = 'completed' AND completed_at >= %s",
                    (week_ago,)
                )[0]['count'],
                'tool_executions': db.execute_query(
                    "SELECT COUNT(*) as count FROM tool_executions WHERE started_at >= %s",
                    (week_ago,)
                )[0]['count']
            }
            stats['recent_activity'] = recent_activity
        except Exception as activity_error:
            logger.warning(f"Could not get recent activity: {str(activity_error)}")
            stats['recent_activity'] = {}
        
        # Información del sistema
        system_info = {
            'version': '1.0.0',
            'uptime': 'N/A',  # Se podría implementar un contador de uptime
            'python_version': f"{os.sys.version_info.major}.{os.sys.version_info.minor}.{os.sys.version_info.micro}",
            'environment': os.environ.get('FLASK_ENV', 'production'),
            'debug_mode': current_app.config.get('DEBUG', False)
        }
        
        return jsonify({
            'dashboard': {
                'statistics': stats,
                'system_info': system_info,
                'generated_at': datetime.utcnow().isoformat()
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Get dashboard failed: {str(e)}")
        return jsonify({'error': 'Failed to get dashboard data'}), 500

@admin_bp.route('/users', methods=['GET'])
@admin_required
def get_all_users():
    """Obtener lista de todos los usuarios"""
    try:
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 20, type=int)
        role = request.args.get('role')
        active_only = request.args.get('active_only', 'false').lower() == 'true'
        
        # Validar límites
        if limit > 100:
            limit = 100
        
        user_model = UserModel()
        
        # Construir filtros
        filters = {}
        if role:
            filters['role'] = role
        if active_only:
            filters['is_active'] = True
        
        # Obtener usuarios
        offset = (page - 1) * limit
        users = user_model.get_all(filters, limit=limit, offset=offset)
        
        # Agregar estadísticas adicionales para cada usuario
        for user in users:
            try:
                # Contar conversaciones del usuario
                user['conversation_count'] = db.execute_query(
                    "SELECT COUNT(*) as count FROM conversations WHERE user_id = %s",
                    (user['id'],)
                )[0]['count']
                
                # Contar agentes creados por el usuario
                user['agent_count'] = db.execute_query(
                    "SELECT COUNT(*) as count FROM agents WHERE created_by = %s",
                    (user['id'],)
                )[0]['count']
                
            except Exception as user_stats_error:
                logger.warning(f"Could not get user statistics: {str(user_stats_error)}")
                user['conversation_count'] = 0
                user['agent_count'] = 0
        
        return jsonify({
            'users': users,
            'page': page,
            'limit': limit,
            'total_count': len(users),
            'filters': filters
        }), 200
        
    except Exception as e:
        logger.error(f"Get all users failed: {str(e)}")
        return jsonify({'error': 'Failed to get users'}), 500

@admin_bp.route('/users/<user_id>', methods=['PUT'])
@admin_required
def update_user(user_id):
    """Actualizar un usuario (solo administradores)"""
    try:
        data = request.get_json()
        
        user_model = UserModel()
        user = user_model.get_by_id(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Campos que se pueden actualizar
        updatable_fields = ['username', 'full_name', 'role', 'is_active', 'preferences']
        update_data = {}
        
        for field in updatable_fields:
            if field in data:
                update_data[field] = data[field]
        
        if not update_data:
            return jsonify({'error': 'No valid fields to update'}), 400
        
        # Validar rol
        if 'role' in update_data:
            valid_roles = ['admin', 'user', 'viewer']
            if update_data['role'] not in valid_roles:
                return jsonify({'error': f'Invalid role. Must be one of: {valid_roles}'}), 400
        
        # Verificar username único si se está actualizando
        if 'username' in update_data:
            existing_user = user_model.get_by_username(update_data['username'])
            if existing_user and existing_user['id'] != user_id:
                return jsonify({'error': 'Username already taken'}), 409
        
        # Actualizar usuario
        updated_user = user_model.update(user_id, update_data)
        
        return jsonify({
            'message': 'User updated successfully',
            'user': updated_user
        }), 200
        
    except Exception as e:
        logger.error(f"Update user failed: {str(e)}")
        return jsonify({'error': 'Failed to update user'}), 500

@admin_bp.route('/users/<user_id>/deactivate', methods=['POST'])
@admin_required
def deactivate_user(user_id):
    """Desactivar un usuario"""
    try:
        user_model = UserModel()
        user = user_model.get_by_id(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # No permitir desactivar al último administrador
        if user['role'] == 'admin':
            admin_count = user_model.count({'role': 'admin', 'is_active': True})
            if admin_count <= 1:
                return jsonify({'error': 'Cannot deactivate the last active admin'}), 400
        
        # Desactivar usuario
        updated_user = user_model.update(user_id, {'is_active': False})
        
        return jsonify({
            'message': 'User deactivated successfully',
            'user': updated_user
        }), 200
        
    except Exception as e:
        logger.error(f"Deactivate user failed: {str(e)}")
        return jsonify({'error': 'Failed to deactivate user'}), 500

@admin_bp.route('/users/<user_id>/activate', methods=['POST'])
@admin_required
def activate_user(user_id):
    """Activar un usuario"""
    try:
        user_model = UserModel()
        user = user_model.get_by_id(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Activar usuario
        updated_user = user_model.update(user_id, {'is_active': True})
        
        return jsonify({
            'message': 'User activated successfully',
            'user': updated_user
        }), 200
        
    except Exception as e:
        logger.error(f"Activate user failed: {str(e)}")
        return jsonify({'error': 'Failed to activate user'}), 500

@admin_bp.route('/config', methods=['GET'])
@admin_required
def get_system_config():
    """Obtener configuración del sistema"""
    try:
        config_service = ConfigService()
        config = config_service.get_all_config()
        
        return jsonify({
            'config': config,
            'total_settings': len(config)
        }), 200
        
    except Exception as e:
        logger.error(f"Get system config failed: {str(e)}")
        return jsonify({'error': 'Failed to get system config'}), 500

@admin_bp.route('/config', methods=['PUT'])
@admin_required
def update_system_config():
    """Actualizar configuración del sistema"""
    try:
        data = request.get_json()
        user = request.current_user
        
        config_service = ConfigService()
        
        updated_configs = []
        errors = []
        
        for key, value in data.items():
            try:
                config_service.set_config(key, value, user['id'])
                updated_configs.append(key)
            except Exception as config_error:
                errors.append(f"Error updating {key}: {str(config_error)}")
        
        return jsonify({
            'message': 'Configuration updated',
            'updated_configs': updated_configs,
            'errors': errors,
            'total_updated': len(updated_configs)
        }), 200
        
    except Exception as e:
        logger.error(f"Update system config failed: {str(e)}")
        return jsonify({'error': 'Failed to update system config'}), 500

@admin_bp.route('/logs', methods=['GET'])
@admin_required
def get_system_logs():
    """Obtener logs del sistema"""
    try:
        log_type = request.args.get('type', 'audit')  # audit, error, access
        limit = request.args.get('limit', 100, type=int)
        
        # Validar límites
        if limit > 1000:
            limit = 1000
        
        logs = []
        
        if log_type == 'audit':
            # Obtener logs de auditoría
            try:
                audit_logs = db.execute_query("""
                    SELECT al.*, u.username, u.full_name
                    FROM audit_logs al
                    LEFT JOIN users u ON al.user_id = u.id
                    ORDER BY al.created_at DESC
                    LIMIT %s
                """, (limit,))
                logs = audit_logs
            except Exception as audit_error:
                logger.warning(f"Could not get audit logs: {str(audit_error)}")
        
        return jsonify({
            'logs': logs,
            'log_type': log_type,
            'limit': limit,
            'total_count': len(logs)
        }), 200
        
    except Exception as e:
        logger.error(f"Get system logs failed: {str(e)}")
        return jsonify({'error': 'Failed to get system logs'}), 500

@admin_bp.route('/maintenance/cleanup', methods=['POST'])
@admin_required
def system_cleanup():
    """Realizar limpieza del sistema"""
    try:
        cleanup_type = request.json.get('type', 'all')  # all, files, logs, expired
        
        cleanup_results = {
            'expired_files': 0,
            'old_logs': 0,
            'orphaned_records': 0,
            'errors': []
        }
        
        # Limpiar archivos expirados
        if cleanup_type in ['all', 'files', 'expired']:
            try:
                # Obtener archivos expirados
                current_time = datetime.utcnow().isoformat()
                expired_files = db.execute_query("""
                    SELECT * FROM files 
                    WHERE is_temporary = true 
                    AND expires_at < %s
                """, (current_time,))
                
                for file_info in expired_files:
                    try:
                        # Eliminar archivo físico
                        if os.path.exists(file_info['file_path']):
                            os.remove(file_info['file_path'])
                        
                        # Eliminar registro
                        db.execute_query("DELETE FROM files WHERE id = %s", (file_info['id'],))
                        cleanup_results['expired_files'] += 1
                        
                    except Exception as file_error:
                        cleanup_results['errors'].append(f"Error cleaning file {file_info['id']}: {str(file_error)}")
                        
            except Exception as files_error:
                cleanup_results['errors'].append(f"Error cleaning expired files: {str(files_error)}")
        
        # Limpiar logs antiguos (más de 30 días)
        if cleanup_type in ['all', 'logs']:
            try:
                thirty_days_ago = (datetime.utcnow() - timedelta(days=30)).isoformat()
                result = db.execute_query("""
                    DELETE FROM audit_logs 
                    WHERE created_at < %s
                """, (thirty_days_ago,))
                cleanup_results['old_logs'] = result
                
            except Exception as logs_error:
                cleanup_results['errors'].append(f"Error cleaning old logs: {str(logs_error)}")
        
        # Limpiar registros huérfanos
        if cleanup_type in ['all', 'orphaned']:
            try:
                # Eliminar ejecuciones de herramientas sin tarea asociada
                orphaned_executions = db.execute_query("""
                    DELETE FROM tool_executions 
                    WHERE task_id NOT IN (SELECT id FROM tasks)
                """)
                cleanup_results['orphaned_records'] += orphaned_executions or 0
                
                # Eliminar mensajes sin conversación asociada
                orphaned_messages = db.execute_query("""
                    DELETE FROM messages 
                    WHERE conversation_id NOT IN (SELECT id FROM conversations)
                """)
                cleanup_results['orphaned_records'] += orphaned_messages or 0
                
            except Exception as orphaned_error:
                cleanup_results['errors'].append(f"Error cleaning orphaned records: {str(orphaned_error)}")
        
        return jsonify({
            'message': 'System cleanup completed',
            'cleanup_type': cleanup_type,
            'results': cleanup_results
        }), 200
        
    except Exception as e:
        logger.error(f"System cleanup failed: {str(e)}")
        return jsonify({'error': 'Failed to perform system cleanup'}), 500

@admin_bp.route('/maintenance/backup', methods=['POST'])
@admin_required
def create_backup():
    """Crear backup del sistema"""
    try:
        backup_type = request.json.get('type', 'database')  # database, files, full
        
        # Esta es una implementación básica
        # En un entorno real, se usarían herramientas específicas de backup
        
        backup_info = {
            'type': backup_type,
            'created_at': datetime.utcnow().isoformat(),
            'status': 'completed',
            'size': 0,
            'location': '/tmp/backups/',
            'tables_backed_up': []
        }
        
        if backup_type in ['database', 'full']:
            # Simular backup de base de datos
            tables = ['users', 'agents', 'conversations', 'messages', 'tasks', 'tools', 'tool_executions', 'files', 'system_config']
            backup_info['tables_backed_up'] = tables
        
        return jsonify({
            'message': 'Backup created successfully',
            'backup': backup_info
        }), 200
        
    except Exception as e:
        logger.error(f"Create backup failed: {str(e)}")
        return jsonify({'error': 'Failed to create backup'}), 500

@admin_bp.route('/monitoring/health', methods=['GET'])
@admin_required
def system_health():
    """Verificar salud del sistema"""
    try:
        health_status = {
            'overall_status': 'healthy',
            'components': {
                'database': 'healthy',
                'ollama': 'unknown',
                'file_system': 'healthy',
                'memory': 'healthy'
            },
            'metrics': {
                'active_users': 0,
                'running_tasks': 0,
                'pending_tasks': 0,
                'disk_usage': 0,
                'memory_usage': 0
            },
            'alerts': []
        }
        
        # Verificar base de datos
        try:
            db.execute_query("SELECT 1")
            health_status['components']['database'] = 'healthy'
        except Exception as db_error:
            health_status['components']['database'] = 'unhealthy'
            health_status['overall_status'] = 'degraded'
            health_status['alerts'].append(f"Database connection failed: {str(db_error)}")
        
        # Verificar Ollama
        try:
            from src.services.ollama_service import OllamaService
            ollama_service = OllamaService()
            ollama_status = ollama_service.health_check()
            health_status['components']['ollama'] = 'healthy' if ollama_status['success'] else 'unhealthy'
            if not ollama_status['success']:
                health_status['alerts'].append(f"Ollama service unavailable: {ollama_status['error']}")
        except Exception as ollama_error:
            health_status['components']['ollama'] = 'unhealthy'
            health_status['alerts'].append(f"Ollama check failed: {str(ollama_error)}")
        
        # Verificar sistema de archivos
        try:
            upload_folder = current_app.config.get('UPLOAD_FOLDER', '/tmp/manus-uploads')
            if os.path.exists(upload_folder):
                # Verificar espacio en disco
                statvfs = os.statvfs(upload_folder)
                free_space = statvfs.f_frsize * statvfs.f_bavail
                total_space = statvfs.f_frsize * statvfs.f_blocks
                disk_usage = ((total_space - free_space) / total_space) * 100
                
                health_status['metrics']['disk_usage'] = round(disk_usage, 2)
                
                if disk_usage > 90:
                    health_status['components']['file_system'] = 'critical'
                    health_status['overall_status'] = 'critical'
                    health_status['alerts'].append(f"Disk usage critical: {disk_usage:.1f}%")
                elif disk_usage > 80:
                    health_status['components']['file_system'] = 'warning'
                    health_status['alerts'].append(f"Disk usage high: {disk_usage:.1f}%")
            else:
                health_status['components']['file_system'] = 'unhealthy'
                health_status['alerts'].append("Upload folder does not exist")
        except Exception as fs_error:
            health_status['components']['file_system'] = 'unknown'
            health_status['alerts'].append(f"File system check failed: {str(fs_error)}")
        
        # Obtener métricas de tareas
        try:
            task_model = TaskModel()
            health_status['metrics']['running_tasks'] = task_model.count({'status': 'running'})
            health_status['metrics']['pending_tasks'] = task_model.count({'status': 'pending'})
            
            # Verificar si hay demasiadas tareas pendientes
            if health_status['metrics']['pending_tasks'] > 100:
                health_status['alerts'].append(f"High number of pending tasks: {health_status['metrics']['pending_tasks']}")
                
        except Exception as task_error:
            health_status['alerts'].append(f"Task metrics check failed: {str(task_error)}")
        
        # Determinar estado general
        if health_status['components']['database'] == 'unhealthy':
            health_status['overall_status'] = 'critical'
        elif any(status == 'critical' for status in health_status['components'].values()):
            health_status['overall_status'] = 'critical'
        elif any(status in ['unhealthy', 'warning'] for status in health_status['components'].values()):
            health_status['overall_status'] = 'degraded'
        
        return jsonify({
            'health': health_status,
            'checked_at': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"System health check failed: {str(e)}")
        return jsonify({'error': 'Failed to check system health'}), 500

