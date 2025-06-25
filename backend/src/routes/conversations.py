"""
Rutas para gestión de conversaciones en el sistema MANUS-like
Maneja CRUD de conversaciones, mensajes y comunicación en tiempo real
"""

from flask import Blueprint, request, jsonify, current_app
from flask_socketio import emit, join_room, leave_room
import logging
import uuid
from datetime import datetime

from src.models.database import ConversationModel, MessageModel, AgentModel
from src.routes.auth import token_required

logger = logging.getLogger(__name__)

conversations_bp = Blueprint('conversations', __name__)

@conversations_bp.route('/', methods=['GET'])
@token_required
def get_conversations():
    """Obtener lista de conversaciones del usuario"""
    try:
        user = request.current_user
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 20, type=int)
        
        # Validar límites
        if limit > 100:
            limit = 100
        
        offset = (page - 1) * limit
        
        conversation_model = ConversationModel()
        conversations = conversation_model.get_by_user(user['id'], limit)
        
        # Agregar información adicional a cada conversación
        for conversation in conversations:
            # Obtener último mensaje
            message_model = MessageModel()
            messages = message_model.get_by_conversation(conversation['id'], limit=1)
            conversation['last_message'] = messages[0] if messages else None
            
            # Contar mensajes totales
            conversation['message_count'] = message_model.count({'conversation_id': conversation['id']})
        
        return jsonify({
            'conversations': conversations,
            'page': page,
            'limit': limit,
            'total_count': len(conversations)
        }), 200
        
    except Exception as e:
        logger.error(f"Get conversations failed: {str(e)}")
        return jsonify({'error': 'Failed to get conversations'}), 500

@conversations_bp.route('/<conversation_id>', methods=['GET'])
@token_required
def get_conversation(conversation_id):
    """Obtener detalles de una conversación específica"""
    try:
        user = request.current_user
        
        conversation_model = ConversationModel()
        conversation = conversation_model.get_by_id(conversation_id)
        
        if not conversation:
            return jsonify({'error': 'Conversation not found'}), 404
        
        # Verificar permisos
        if conversation['user_id'] != user['id']:
            return jsonify({'error': 'Access denied'}), 403
        
        # Obtener información del agente
        agent_model = AgentModel()
        agent = agent_model.get_by_id(conversation['agent_id'])
        conversation['agent'] = agent
        
        # Obtener mensajes
        message_model = MessageModel()
        messages = message_model.get_by_conversation(conversation_id)
        conversation['messages'] = messages
        
        return jsonify({'conversation': conversation}), 200
        
    except Exception as e:
        logger.error(f"Get conversation failed: {str(e)}")
        return jsonify({'error': 'Failed to get conversation'}), 500

@conversations_bp.route('/', methods=['POST'])
@token_required
def create_conversation():
    """Crear una nueva conversación"""
    try:
        data = request.get_json()
        user = request.current_user
        
        agent_id = data.get('agent_id')
        title = data.get('title', 'Nueva Conversación')
        initial_message = data.get('initial_message')
        
        if not agent_id:
            return jsonify({'error': 'agent_id is required'}), 400
        
        # Verificar que el agente existe y es accesible
        agent_model = AgentModel()
        agent = agent_model.get_by_id(agent_id)
        
        if not agent:
            return jsonify({'error': 'Agent not found'}), 404
        
        if not agent.get('is_public', False) and agent.get('created_by') != user['id']:
            return jsonify({'error': 'Access denied to agent'}), 403
        
        if not agent.get('is_active', True):
            return jsonify({'error': 'Agent is not active'}), 400
        
        # Crear conversación
        conversation_data = {
            'title': title,
            'user_id': user['id'],
            'agent_id': agent_id,
            'status': 'active',
            'metadata': data.get('metadata', {})
        }
        
        conversation_model = ConversationModel()
        conversation = conversation_model.create(conversation_data)
        
        # Agregar mensaje inicial del sistema si el agente tiene system_prompt
        message_model = MessageModel()
        if agent.get('system_prompt'):
            system_message_data = {
                'conversation_id': conversation['id'],
                'role': 'system',
                'content': agent['system_prompt'],
                'metadata': {'type': 'system_prompt'}
            }
            message_model.create(system_message_data)
        
        # Agregar mensaje inicial del usuario si se proporciona
        if initial_message:
            user_message_data = {
                'conversation_id': conversation['id'],
                'role': 'user',
                'content': initial_message,
                'metadata': {'type': 'initial_message'}
            }
            message_model.create(user_message_data)
        
        # Agregar información del agente a la respuesta
        conversation['agent'] = agent
        
        return jsonify({
            'message': 'Conversation created successfully',
            'conversation': conversation
        }), 201
        
    except Exception as e:
        logger.error(f"Create conversation failed: {str(e)}")
        return jsonify({'error': 'Failed to create conversation'}), 500

@conversations_bp.route('/<conversation_id>', methods=['PUT'])
@token_required
def update_conversation(conversation_id):
    """Actualizar una conversación"""
    try:
        data = request.get_json()
        user = request.current_user
        
        conversation_model = ConversationModel()
        conversation = conversation_model.get_by_id(conversation_id)
        
        if not conversation:
            return jsonify({'error': 'Conversation not found'}), 404
        
        # Verificar permisos
        if conversation['user_id'] != user['id']:
            return jsonify({'error': 'Access denied'}), 403
        
        # Campos que se pueden actualizar
        updatable_fields = ['title', 'status', 'metadata']
        update_data = {}
        
        for field in updatable_fields:
            if field in data:
                update_data[field] = data[field]
        
        if not update_data:
            return jsonify({'error': 'No valid fields to update'}), 400
        
        # Validar status
        if 'status' in update_data:
            valid_statuses = ['active', 'completed', 'paused', 'error']
            if update_data['status'] not in valid_statuses:
                return jsonify({'error': f'Invalid status. Must be one of: {valid_statuses}'}), 400
        
        # Actualizar conversación
        updated_conversation = conversation_model.update(conversation_id, update_data)
        
        return jsonify({
            'message': 'Conversation updated successfully',
            'conversation': updated_conversation
        }), 200
        
    except Exception as e:
        logger.error(f"Update conversation failed: {str(e)}")
        return jsonify({'error': 'Failed to update conversation'}), 500

@conversations_bp.route('/<conversation_id>', methods=['DELETE'])
@token_required
def delete_conversation(conversation_id):
    """Eliminar una conversación"""
    try:
        user = request.current_user
        
        conversation_model = ConversationModel()
        conversation = conversation_model.get_by_id(conversation_id)
        
        if not conversation:
            return jsonify({'error': 'Conversation not found'}), 404
        
        # Verificar permisos
        if conversation['user_id'] != user['id']:
            return jsonify({'error': 'Access denied'}), 403
        
        # Eliminar conversación (esto también eliminará mensajes por CASCADE)
        conversation_model.delete(conversation_id)
        
        return jsonify({'message': 'Conversation deleted successfully'}), 200
        
    except Exception as e:
        logger.error(f"Delete conversation failed: {str(e)}")
        return jsonify({'error': 'Failed to delete conversation'}), 500

@conversations_bp.route('/<conversation_id>/messages', methods=['GET'])
@token_required
def get_messages(conversation_id):
    """Obtener mensajes de una conversación"""
    try:
        user = request.current_user
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 50, type=int)
        
        # Validar límites
        if limit > 200:
            limit = 200
        
        # Verificar acceso a la conversación
        conversation_model = ConversationModel()
        conversation = conversation_model.get_by_id(conversation_id)
        
        if not conversation:
            return jsonify({'error': 'Conversation not found'}), 404
        
        if conversation['user_id'] != user['id']:
            return jsonify({'error': 'Access denied'}), 403
        
        # Obtener mensajes
        message_model = MessageModel()
        messages = message_model.get_by_conversation(conversation_id, limit)
        
        return jsonify({
            'messages': messages,
            'conversation_id': conversation_id,
            'page': page,
            'limit': limit,
            'total_count': len(messages)
        }), 200
        
    except Exception as e:
        logger.error(f"Get messages failed: {str(e)}")
        return jsonify({'error': 'Failed to get messages'}), 500

@conversations_bp.route('/<conversation_id>/messages', methods=['POST'])
@token_required
def send_message(conversation_id):
    """Enviar un mensaje en una conversación"""
    try:
        data = request.get_json()
        user = request.current_user
        
        content = data.get('content')
        if not content:
            return jsonify({'error': 'content is required'}), 400
        
        # Verificar acceso a la conversación
        conversation_model = ConversationModel()
        conversation = conversation_model.get_by_id(conversation_id)
        
        if not conversation:
            return jsonify({'error': 'Conversation not found'}), 404
        
        if conversation['user_id'] != user['id']:
            return jsonify({'error': 'Access denied'}), 403
        
        if conversation['status'] != 'active':
            return jsonify({'error': 'Conversation is not active'}), 400
        
        # Crear mensaje del usuario
        message_model = MessageModel()
        user_message_data = {
            'conversation_id': conversation_id,
            'role': 'user',
            'content': content,
            'metadata': data.get('metadata', {})
        }
        
        user_message = message_model.create(user_message_data)
        
        # Emitir mensaje en tiempo real
        if hasattr(current_app, 'socketio'):
            current_app.socketio.emit('new_message', {
                'conversation_id': conversation_id,
                'message': user_message
            }, room=conversation_id)
        
        # Procesar respuesta del agente de forma asíncrona
        from src.services.agent_service import AgentService
        agent_service = AgentService()
        
        try:
            # Generar respuesta del agente
            response = agent_service.process_message(conversation_id, user_message)
            
            if response['success']:
                assistant_message = response['message']
                
                # Emitir respuesta del agente en tiempo real
                if hasattr(current_app, 'socketio'):
                    current_app.socketio.emit('new_message', {
                        'conversation_id': conversation_id,
                        'message': assistant_message
                    }, room=conversation_id)
                
                return jsonify({
                    'message': 'Message sent successfully',
                    'user_message': user_message,
                    'assistant_message': assistant_message
                }), 201
            else:
                # Si hay error en la respuesta del agente, crear mensaje de error
                error_message_data = {
                    'conversation_id': conversation_id,
                    'role': 'assistant',
                    'content': f"Lo siento, ocurrió un error al procesar tu mensaje: {response['error']}",
                    'metadata': {'type': 'error', 'error': response['error']}
                }
                
                error_message = message_model.create(error_message_data)
                
                return jsonify({
                    'message': 'Message sent but agent response failed',
                    'user_message': user_message,
                    'error_message': error_message,
                    'error': response['error']
                }), 201
                
        except Exception as agent_error:
            logger.error(f"Agent processing failed: {str(agent_error)}")
            
            # Crear mensaje de error
            error_message_data = {
                'conversation_id': conversation_id,
                'role': 'assistant',
                'content': "Lo siento, no pude procesar tu mensaje en este momento. Por favor, inténtalo de nuevo.",
                'metadata': {'type': 'error', 'error': str(agent_error)}
            }
            
            error_message = message_model.create(error_message_data)
            
            return jsonify({
                'message': 'Message sent but agent processing failed',
                'user_message': user_message,
                'error_message': error_message
            }), 201
        
    except Exception as e:
        logger.error(f"Send message failed: {str(e)}")
        return jsonify({'error': 'Failed to send message'}), 500

@conversations_bp.route('/<conversation_id>/messages/<message_id>', methods=['DELETE'])
@token_required
def delete_message(conversation_id, message_id):
    """Eliminar un mensaje específico"""
    try:
        user = request.current_user
        
        # Verificar acceso a la conversación
        conversation_model = ConversationModel()
        conversation = conversation_model.get_by_id(conversation_id)
        
        if not conversation:
            return jsonify({'error': 'Conversation not found'}), 404
        
        if conversation['user_id'] != user['id']:
            return jsonify({'error': 'Access denied'}), 403
        
        # Verificar que el mensaje existe y pertenece a la conversación
        message_model = MessageModel()
        message = message_model.get_by_id(message_id)
        
        if not message:
            return jsonify({'error': 'Message not found'}), 404
        
        if message['conversation_id'] != conversation_id:
            return jsonify({'error': 'Message does not belong to this conversation'}), 400
        
        # Eliminar mensaje
        message_model.delete(message_id)
        
        # Emitir evento de eliminación en tiempo real
        if hasattr(current_app, 'socketio'):
            current_app.socketio.emit('message_deleted', {
                'conversation_id': conversation_id,
                'message_id': message_id
            }, room=conversation_id)
        
        return jsonify({'message': 'Message deleted successfully'}), 200
        
    except Exception as e:
        logger.error(f"Delete message failed: {str(e)}")
        return jsonify({'error': 'Failed to delete message'}), 500

@conversations_bp.route('/<conversation_id>/clear', methods=['POST'])
@token_required
def clear_conversation(conversation_id):
    """Limpiar todos los mensajes de una conversación"""
    try:
        user = request.current_user
        
        # Verificar acceso a la conversación
        conversation_model = ConversationModel()
        conversation = conversation_model.get_by_id(conversation_id)
        
        if not conversation:
            return jsonify({'error': 'Conversation not found'}), 404
        
        if conversation['user_id'] != user['id']:
            return jsonify({'error': 'Access denied'}), 403
        
        # Obtener todos los mensajes y eliminarlos
        message_model = MessageModel()
        messages = message_model.get_by_conversation(conversation_id)
        
        for message in messages:
            message_model.delete(message['id'])
        
        # Emitir evento de limpieza en tiempo real
        if hasattr(current_app, 'socketio'):
            current_app.socketio.emit('conversation_cleared', {
                'conversation_id': conversation_id
            }, room=conversation_id)
        
        return jsonify({
            'message': 'Conversation cleared successfully',
            'deleted_messages': len(messages)
        }), 200
        
    except Exception as e:
        logger.error(f"Clear conversation failed: {str(e)}")
        return jsonify({'error': 'Failed to clear conversation'}), 500

@conversations_bp.route('/<conversation_id>/export', methods=['GET'])
@token_required
def export_conversation(conversation_id):
    """Exportar conversación en formato JSON"""
    try:
        user = request.current_user
        
        # Verificar acceso a la conversación
        conversation_model = ConversationModel()
        conversation = conversation_model.get_by_id(conversation_id)
        
        if not conversation:
            return jsonify({'error': 'Conversation not found'}), 404
        
        if conversation['user_id'] != user['id']:
            return jsonify({'error': 'Access denied'}), 403
        
        # Obtener información completa
        agent_model = AgentModel()
        agent = agent_model.get_by_id(conversation['agent_id'])
        
        message_model = MessageModel()
        messages = message_model.get_by_conversation(conversation_id)
        
        # Preparar datos de exportación
        export_data = {
            'conversation': {
                'id': conversation['id'],
                'title': conversation['title'],
                'status': conversation['status'],
                'created_at': conversation['created_at'],
                'updated_at': conversation['updated_at'],
                'metadata': conversation.get('metadata', {})
            },
            'agent': {
                'name': agent['name'] if agent else 'Unknown',
                'description': agent['description'] if agent else '',
                'model_name': agent['model_name'] if agent else ''
            },
            'user': {
                'username': user['username'],
                'full_name': user['full_name']
            },
            'messages': messages,
            'export_info': {
                'exported_at': datetime.utcnow().isoformat(),
                'total_messages': len(messages),
                'format_version': '1.0'
            }
        }
        
        return jsonify(export_data), 200
        
    except Exception as e:
        logger.error(f"Export conversation failed: {str(e)}")
        return jsonify({'error': 'Failed to export conversation'}), 500

