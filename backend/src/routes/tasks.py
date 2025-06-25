"""
Rutas para gestión de tareas en el sistema MANUS-like
Maneja CRUD de tareas, seguimiento de progreso y ejecución de agentes
"""

from flask import Blueprint, request, jsonify, current_app
import logging
import uuid
from datetime import datetime

from src.models.database import TaskModel, ConversationModel, ToolModel
from src.routes.auth import token_required

logger = logging.getLogger(__name__)

tasks_bp = Blueprint('tasks', __name__)

@tasks_bp.route('/', methods=['GET'])
@token_required
def get_tasks():
    """Obtener lista de tareas del usuario"""
    try:
        user = request.current_user
        status = request.args.get('status')  # pending, running, completed, failed, cancelled
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 20, type=int)
        
        # Validar límites
        if limit > 100:
            limit = 100
        
        task_model = TaskModel()
        
        # Filtros
        filters = {}
        if status:
            valid_statuses = ['pending', 'running', 'completed', 'failed', 'cancelled']
            if status in valid_statuses:
                filters['status'] = status
        
        # Obtener tareas del usuario a través de conversaciones
        if user.get('role') == 'admin':
            # Los admins pueden ver todas las tareas
            tasks = task_model.get_all(filters, limit=limit, offset=(page-1)*limit)
        else:
            # Los usuarios solo ven sus propias tareas
            tasks = task_model.get_active_tasks(user['id'])
            
            # Aplicar filtros manualmente para usuarios normales
            if status:
                tasks = [task for task in tasks if task.get('status') == status]
            
            # Aplicar paginación
            start_idx = (page - 1) * limit
            end_idx = start_idx + limit
            tasks = tasks[start_idx:end_idx]
        
        # Agregar información adicional
        for task in tasks:
            # Obtener información de la conversación
            conversation_model = ConversationModel()
            conversation = conversation_model.get_by_id(task['conversation_id'])
            task['conversation'] = conversation
            
            # Calcular duración si está completada
            if task['status'] in ['completed', 'failed'] and task.get('started_at') and task.get('completed_at'):
                started = datetime.fromisoformat(task['started_at'].replace('Z', '+00:00'))
                completed = datetime.fromisoformat(task['completed_at'].replace('Z', '+00:00'))
                task['duration_seconds'] = (completed - started).total_seconds()
        
        return jsonify({
            'tasks': tasks,
            'page': page,
            'limit': limit,
            'total_count': len(tasks),
            'filters': filters
        }), 200
        
    except Exception as e:
        logger.error(f"Get tasks failed: {str(e)}")
        return jsonify({'error': 'Failed to get tasks'}), 500

@tasks_bp.route('/<task_id>', methods=['GET'])
@token_required
def get_task(task_id):
    """Obtener detalles de una tarea específica"""
    try:
        user = request.current_user
        
        task_model = TaskModel()
        task = task_model.get_by_id(task_id)
        
        if not task:
            return jsonify({'error': 'Task not found'}), 404
        
        # Verificar permisos
        conversation_model = ConversationModel()
        conversation = conversation_model.get_by_id(task['conversation_id'])
        
        if not conversation:
            return jsonify({'error': 'Associated conversation not found'}), 404
        
        if conversation['user_id'] != user['id'] and user.get('role') != 'admin':
            return jsonify({'error': 'Access denied'}), 403
        
        # Agregar información adicional
        task['conversation'] = conversation
        
        # Obtener ejecuciones de herramientas asociadas
        from src.models.database import db
        try:
            tool_executions = db.execute_query(
                "SELECT * FROM tool_executions WHERE task_id = %s ORDER BY started_at",
                (task_id,)
            )
            task['tool_executions'] = tool_executions
        except:
            task['tool_executions'] = []
        
        # Calcular estadísticas
        if task['status'] in ['completed', 'failed'] and task.get('started_at') and task.get('completed_at'):
            started = datetime.fromisoformat(task['started_at'].replace('Z', '+00:00'))
            completed = datetime.fromisoformat(task['completed_at'].replace('Z', '+00:00'))
            task['duration_seconds'] = (completed - started).total_seconds()
        
        return jsonify({'task': task}), 200
        
    except Exception as e:
        logger.error(f"Get task failed: {str(e)}")
        return jsonify({'error': 'Failed to get task'}), 500

@tasks_bp.route('/', methods=['POST'])
@token_required
def create_task():
    """Crear una nueva tarea"""
    try:
        data = request.get_json()
        user = request.current_user
        
        # Validar datos requeridos
        required_fields = ['conversation_id', 'title', 'description']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        conversation_id = data['conversation_id']
        
        # Verificar acceso a la conversación
        conversation_model = ConversationModel()
        conversation = conversation_model.get_by_id(conversation_id)
        
        if not conversation:
            return jsonify({'error': 'Conversation not found'}), 404
        
        if conversation['user_id'] != user['id']:
            return jsonify({'error': 'Access denied'}), 403
        
        # Crear tarea
        task_data = {
            'conversation_id': conversation_id,
            'title': data['title'],
            'description': data['description'],
            'status': 'pending',
            'priority': data.get('priority', 1),
            'current_phase': 1,
            'total_phases': data.get('total_phases', 1),
            'progress_percentage': 0,
            'result': None,
            'error_message': None
        }
        
        task_model = TaskModel()
        task = task_model.create(task_data)
        
        # Emitir evento en tiempo real
        if hasattr(current_app, 'socketio'):
            current_app.socketio.emit('task_created', {
                'conversation_id': conversation_id,
                'task': task
            }, room=conversation_id)
        
        return jsonify({
            'message': 'Task created successfully',
            'task': task
        }), 201
        
    except Exception as e:
        logger.error(f"Create task failed: {str(e)}")
        return jsonify({'error': 'Failed to create task'}), 500

@tasks_bp.route('/<task_id>', methods=['PUT'])
@token_required
def update_task(task_id):
    """Actualizar una tarea existente"""
    try:
        data = request.get_json()
        user = request.current_user
        
        task_model = TaskModel()
        task = task_model.get_by_id(task_id)
        
        if not task:
            return jsonify({'error': 'Task not found'}), 404
        
        # Verificar permisos
        conversation_model = ConversationModel()
        conversation = conversation_model.get_by_id(task['conversation_id'])
        
        if not conversation:
            return jsonify({'error': 'Associated conversation not found'}), 404
        
        if conversation['user_id'] != user['id'] and user.get('role') != 'admin':
            return jsonify({'error': 'Access denied'}), 403
        
        # Campos que se pueden actualizar
        updatable_fields = [
            'title', 'description', 'status', 'priority', 'current_phase',
            'total_phases', 'progress_percentage', 'result', 'error_message'
        ]
        
        update_data = {}
        for field in updatable_fields:
            if field in data:
                update_data[field] = data[field]
        
        if not update_data:
            return jsonify({'error': 'No valid fields to update'}), 400
        
        # Validar status
        if 'status' in update_data:
            valid_statuses = ['pending', 'running', 'completed', 'failed', 'cancelled']
            if update_data['status'] not in valid_statuses:
                return jsonify({'error': f'Invalid status. Must be one of: {valid_statuses}'}), 400
            
            # Actualizar timestamps según el estado
            if update_data['status'] == 'running' and task['status'] == 'pending':
                update_data['started_at'] = datetime.utcnow().isoformat()
            elif update_data['status'] in ['completed', 'failed', 'cancelled'] and task['status'] == 'running':
                update_data['completed_at'] = datetime.utcnow().isoformat()
        
        # Validar prioridad
        if 'priority' in update_data:
            if not (1 <= update_data['priority'] <= 5):
                return jsonify({'error': 'Priority must be between 1 and 5'}), 400
        
        # Validar progreso
        if 'progress_percentage' in update_data:
            if not (0 <= update_data['progress_percentage'] <= 100):
                return jsonify({'error': 'Progress percentage must be between 0 and 100'}), 400
        
        # Actualizar tarea
        updated_task = task_model.update(task_id, update_data)
        
        # Emitir evento en tiempo real
        if hasattr(current_app, 'socketio'):
            current_app.socketio.emit('task_updated', {
                'conversation_id': task['conversation_id'],
                'task': updated_task
            }, room=task['conversation_id'])
        
        return jsonify({
            'message': 'Task updated successfully',
            'task': updated_task
        }), 200
        
    except Exception as e:
        logger.error(f"Update task failed: {str(e)}")
        return jsonify({'error': 'Failed to update task'}), 500

@tasks_bp.route('/<task_id>', methods=['DELETE'])
@token_required
def delete_task(task_id):
    """Eliminar una tarea"""
    try:
        user = request.current_user
        
        task_model = TaskModel()
        task = task_model.get_by_id(task_id)
        
        if not task:
            return jsonify({'error': 'Task not found'}), 404
        
        # Verificar permisos
        conversation_model = ConversationModel()
        conversation = conversation_model.get_by_id(task['conversation_id'])
        
        if not conversation:
            return jsonify({'error': 'Associated conversation not found'}), 404
        
        if conversation['user_id'] != user['id'] and user.get('role') != 'admin':
            return jsonify({'error': 'Access denied'}), 403
        
        # No permitir eliminar tareas en ejecución
        if task['status'] == 'running':
            return jsonify({'error': 'Cannot delete running task. Cancel it first.'}), 400
        
        # Eliminar tarea
        task_model.delete(task_id)
        
        # Emitir evento en tiempo real
        if hasattr(current_app, 'socketio'):
            current_app.socketio.emit('task_deleted', {
                'conversation_id': task['conversation_id'],
                'task_id': task_id
            }, room=task['conversation_id'])
        
        return jsonify({'message': 'Task deleted successfully'}), 200
        
    except Exception as e:
        logger.error(f"Delete task failed: {str(e)}")
        return jsonify({'error': 'Failed to delete task'}), 500

@tasks_bp.route('/<task_id>/cancel', methods=['POST'])
@token_required
def cancel_task(task_id):
    """Cancelar una tarea en ejecución"""
    try:
        user = request.current_user
        
        task_model = TaskModel()
        task = task_model.get_by_id(task_id)
        
        if not task:
            return jsonify({'error': 'Task not found'}), 404
        
        # Verificar permisos
        conversation_model = ConversationModel()
        conversation = conversation_model.get_by_id(task['conversation_id'])
        
        if not conversation:
            return jsonify({'error': 'Associated conversation not found'}), 404
        
        if conversation['user_id'] != user['id'] and user.get('role') != 'admin':
            return jsonify({'error': 'Access denied'}), 403
        
        # Solo se pueden cancelar tareas pendientes o en ejecución
        if task['status'] not in ['pending', 'running']:
            return jsonify({'error': 'Task cannot be cancelled in current status'}), 400
        
        # Actualizar estado a cancelado
        update_data = {
            'status': 'cancelled',
            'completed_at': datetime.utcnow().isoformat(),
            'error_message': 'Task cancelled by user'
        }
        
        updated_task = task_model.update(task_id, update_data)
        
        # Emitir evento en tiempo real
        if hasattr(current_app, 'socketio'):
            current_app.socketio.emit('task_cancelled', {
                'conversation_id': task['conversation_id'],
                'task': updated_task
            }, room=task['conversation_id'])
        
        return jsonify({
            'message': 'Task cancelled successfully',
            'task': updated_task
        }), 200
        
    except Exception as e:
        logger.error(f"Cancel task failed: {str(e)}")
        return jsonify({'error': 'Failed to cancel task'}), 500

@tasks_bp.route('/<task_id>/retry', methods=['POST'])
@token_required
def retry_task(task_id):
    """Reintentar una tarea fallida"""
    try:
        user = request.current_user
        
        task_model = TaskModel()
        task = task_model.get_by_id(task_id)
        
        if not task:
            return jsonify({'error': 'Task not found'}), 404
        
        # Verificar permisos
        conversation_model = ConversationModel()
        conversation = conversation_model.get_by_id(task['conversation_id'])
        
        if not conversation:
            return jsonify({'error': 'Associated conversation not found'}), 404
        
        if conversation['user_id'] != user['id'] and user.get('role') != 'admin':
            return jsonify({'error': 'Access denied'}), 403
        
        # Solo se pueden reintentar tareas fallidas o canceladas
        if task['status'] not in ['failed', 'cancelled']:
            return jsonify({'error': 'Task can only be retried if failed or cancelled'}), 400
        
        # Resetear estado de la tarea
        update_data = {
            'status': 'pending',
            'progress_percentage': 0,
            'current_phase': 1,
            'result': None,
            'error_message': None,
            'started_at': None,
            'completed_at': None
        }
        
        updated_task = task_model.update(task_id, update_data)
        
        # Emitir evento en tiempo real
        if hasattr(current_app, 'socketio'):
            current_app.socketio.emit('task_retried', {
                'conversation_id': task['conversation_id'],
                'task': updated_task
            }, room=task['conversation_id'])
        
        return jsonify({
            'message': 'Task queued for retry',
            'task': updated_task
        }), 200
        
    except Exception as e:
        logger.error(f"Retry task failed: {str(e)}")
        return jsonify({'error': 'Failed to retry task'}), 500

@tasks_bp.route('/statistics', methods=['GET'])
@token_required
def get_task_statistics():
    """Obtener estadísticas de tareas del usuario"""
    try:
        user = request.current_user
        
        # Obtener todas las tareas del usuario
        task_model = TaskModel()
        if user.get('role') == 'admin':
            all_tasks = task_model.get_all()
        else:
            all_tasks = task_model.get_active_tasks(user['id'])
        
        # Calcular estadísticas
        stats = {
            'total_tasks': len(all_tasks),
            'by_status': {
                'pending': 0,
                'running': 0,
                'completed': 0,
                'failed': 0,
                'cancelled': 0
            },
            'by_priority': {
                '1': 0, '2': 0, '3': 0, '4': 0, '5': 0
            },
            'completion_rate': 0,
            'average_duration': 0,
            'total_duration': 0
        }
        
        total_duration = 0
        completed_tasks = 0
        
        for task in all_tasks:
            # Contar por estado
            status = task.get('status', 'pending')
            if status in stats['by_status']:
                stats['by_status'][status] += 1
            
            # Contar por prioridad
            priority = str(task.get('priority', 1))
            if priority in stats['by_priority']:
                stats['by_priority'][priority] += 1
            
            # Calcular duración para tareas completadas
            if status in ['completed', 'failed'] and task.get('started_at') and task.get('completed_at'):
                try:
                    started = datetime.fromisoformat(task['started_at'].replace('Z', '+00:00'))
                    completed = datetime.fromisoformat(task['completed_at'].replace('Z', '+00:00'))
                    duration = (completed - started).total_seconds()
                    total_duration += duration
                    if status == 'completed':
                        completed_tasks += 1
                except:
                    pass
        
        # Calcular tasas
        if stats['total_tasks'] > 0:
            stats['completion_rate'] = (stats['by_status']['completed'] / stats['total_tasks']) * 100
        
        if completed_tasks > 0:
            stats['average_duration'] = total_duration / completed_tasks
        
        stats['total_duration'] = total_duration
        
        return jsonify({
            'statistics': stats,
            'user_id': user['id'],
            'generated_at': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Get task statistics failed: {str(e)}")
        return jsonify({'error': 'Failed to get task statistics'}), 500

@tasks_bp.route('/<task_id>/logs', methods=['GET'])
@token_required
def get_task_logs(task_id):
    """Obtener logs detallados de una tarea"""
    try:
        user = request.current_user
        
        task_model = TaskModel()
        task = task_model.get_by_id(task_id)
        
        if not task:
            return jsonify({'error': 'Task not found'}), 404
        
        # Verificar permisos
        conversation_model = ConversationModel()
        conversation = conversation_model.get_by_id(task['conversation_id'])
        
        if not conversation:
            return jsonify({'error': 'Associated conversation not found'}), 404
        
        if conversation['user_id'] != user['id'] and user.get('role') != 'admin':
            return jsonify({'error': 'Access denied'}), 403
        
        # Obtener logs de ejecuciones de herramientas
        from src.models.database import db
        try:
            tool_executions = db.execute_query("""
                SELECT te.*, t.name as tool_name, t.display_name as tool_display_name
                FROM tool_executions te
                JOIN tools t ON te.tool_id = t.id
                WHERE te.task_id = %s
                ORDER BY te.started_at
            """, (task_id,))
            
            # Obtener mensajes relacionados con la tarea
            messages = db.execute_query("""
                SELECT m.*
                FROM messages m
                WHERE m.conversation_id = %s
                AND m.created_at >= %s
                ORDER BY m.created_at
            """, (task['conversation_id'], task['created_at']))
            
        except Exception as db_error:
            logger.error(f"Database query failed: {str(db_error)}")
            tool_executions = []
            messages = []
        
        logs = {
            'task_id': task_id,
            'task_info': {
                'title': task['title'],
                'status': task['status'],
                'created_at': task['created_at'],
                'started_at': task.get('started_at'),
                'completed_at': task.get('completed_at')
            },
            'tool_executions': tool_executions,
            'related_messages': messages,
            'total_tool_executions': len(tool_executions),
            'total_messages': len(messages)
        }
        
        return jsonify({'logs': logs}), 200
        
    except Exception as e:
        logger.error(f"Get task logs failed: {str(e)}")
        return jsonify({'error': 'Failed to get task logs'}), 500

