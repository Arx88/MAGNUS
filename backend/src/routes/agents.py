"""
Rutas para gestión de agentes en el sistema MANUS-like
Maneja CRUD de agentes, configuración y asignación de herramientas
"""

from flask import Blueprint, request, jsonify, current_app
import logging
import uuid
from datetime import datetime

from src.models.database import AgentModel, ToolModel
from src.routes.auth import token_required, admin_required

logger = logging.getLogger(__name__)

agents_bp = Blueprint('agents', __name__)

@agents_bp.route('/', methods=['GET'])
@token_required
def get_agents():
    """Obtener lista de agentes disponibles para el usuario"""
    try:
        user = request.current_user
        agent_model = AgentModel()
        
        # Obtener agentes públicos
        public_agents = agent_model.get_public_agents()
        
        # Obtener agentes del usuario
        user_agents = agent_model.get_by_user(user['id'])
        
        # Combinar y marcar origen
        all_agents = []
        
        for agent in public_agents:
            agent['is_owner'] = False
            agent['is_public'] = True
            all_agents.append(agent)
        
        for agent in user_agents:
            agent['is_owner'] = True
            all_agents.append(agent)
        
        # Remover duplicados (en caso de que un usuario sea dueño de un agente público)
        seen_ids = set()
        unique_agents = []
        for agent in all_agents:
            if agent['id'] not in seen_ids:
                seen_ids.add(agent['id'])
                unique_agents.append(agent)
        
        return jsonify({
            'agents': unique_agents,
            'total_count': len(unique_agents)
        }), 200
        
    except Exception as e:
        logger.error(f"Get agents failed: {str(e)}")
        return jsonify({'error': 'Failed to get agents'}), 500

@agents_bp.route('/<agent_id>', methods=['GET'])
@token_required
def get_agent(agent_id):
    """Obtener detalles de un agente específico"""
    try:
        user = request.current_user
        agent_model = AgentModel()
        
        agent = agent_model.get_by_id(agent_id)
        
        if not agent:
            return jsonify({'error': 'Agent not found'}), 404
        
        # Verificar permisos
        if not agent.get('is_public', False) and agent.get('created_by') != user['id']:
            return jsonify({'error': 'Access denied'}), 403
        
        # Agregar información de herramientas disponibles
        tool_model = ToolModel()
        available_tools = tool_model.get_enabled_tools()
        
        agent['available_tools'] = available_tools
        agent['is_owner'] = agent.get('created_by') == user['id']
        
        return jsonify({'agent': agent}), 200
        
    except Exception as e:
        logger.error(f"Get agent failed: {str(e)}")
        return jsonify({'error': 'Failed to get agent'}), 500

@agents_bp.route('/', methods=['POST'])
@token_required
def create_agent():
    """Crear un nuevo agente"""
    try:
        data = request.get_json()
        user = request.current_user
        
        # Validar datos requeridos
        required_fields = ['name', 'description', 'system_prompt', 'model_name']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        # Validar herramientas
        tools_enabled = data.get('tools_enabled', [])
        if tools_enabled:
            tool_model = ToolModel()
            available_tools = tool_model.get_enabled_tools()
            available_tool_names = [tool['name'] for tool in available_tools]
            
            for tool_name in tools_enabled:
                if tool_name not in available_tool_names:
                    return jsonify({'error': f'Tool {tool_name} is not available'}), 400
        
        # Validar parámetros del modelo
        temperature = data.get('temperature', 0.7)
        if not (0 <= temperature <= 2):
            return jsonify({'error': 'Temperature must be between 0 and 2'}), 400
        
        max_tokens = data.get('max_tokens', 4096)
        if not (1 <= max_tokens <= 32000):
            return jsonify({'error': 'Max tokens must be between 1 and 32000'}), 400
        
        # Crear agente
        agent_data = {
            'name': data['name'],
            'description': data['description'],
            'system_prompt': data['system_prompt'],
            'model_name': data['model_name'],
            'temperature': temperature,
            'max_tokens': max_tokens,
            'tools_enabled': tools_enabled,
            'memory_enabled': data.get('memory_enabled', True),
            'memory_limit': data.get('memory_limit', 10000),
            'created_by': user['id'],
            'is_public': data.get('is_public', False),
            'is_active': True,
            'configuration': data.get('configuration', {})
        }
        
        agent_model = AgentModel()
        created_agent = agent_model.create(agent_data)
        
        return jsonify({
            'message': 'Agent created successfully',
            'agent': created_agent
        }), 201
        
    except Exception as e:
        logger.error(f"Create agent failed: {str(e)}")
        return jsonify({'error': 'Failed to create agent'}), 500

@agents_bp.route('/<agent_id>', methods=['PUT'])
@token_required
def update_agent(agent_id):
    """Actualizar un agente existente"""
    try:
        data = request.get_json()
        user = request.current_user
        
        agent_model = AgentModel()
        agent = agent_model.get_by_id(agent_id)
        
        if not agent:
            return jsonify({'error': 'Agent not found'}), 404
        
        # Verificar permisos (solo el creador o admin puede modificar)
        if agent.get('created_by') != user['id'] and user.get('role') != 'admin':
            return jsonify({'error': 'Access denied'}), 403
        
        # Campos que se pueden actualizar
        updatable_fields = [
            'name', 'description', 'system_prompt', 'model_name',
            'temperature', 'max_tokens', 'tools_enabled', 'memory_enabled',
            'memory_limit', 'is_public', 'is_active', 'configuration'
        ]
        
        update_data = {}
        for field in updatable_fields:
            if field in data:
                update_data[field] = data[field]
        
        if not update_data:
            return jsonify({'error': 'No valid fields to update'}), 400
        
        # Validar herramientas si se están actualizando
        if 'tools_enabled' in update_data:
            tool_model = ToolModel()
            available_tools = tool_model.get_enabled_tools()
            available_tool_names = [tool['name'] for tool in available_tools]
            
            for tool_name in update_data['tools_enabled']:
                if tool_name not in available_tool_names:
                    return jsonify({'error': f'Tool {tool_name} is not available'}), 400
        
        # Validar parámetros del modelo
        if 'temperature' in update_data:
            if not (0 <= update_data['temperature'] <= 2):
                return jsonify({'error': 'Temperature must be between 0 and 2'}), 400
        
        if 'max_tokens' in update_data:
            if not (1 <= update_data['max_tokens'] <= 32000):
                return jsonify({'error': 'Max tokens must be between 1 and 32000'}), 400
        
        # Actualizar agente
        updated_agent = agent_model.update(agent_id, update_data)
        
        return jsonify({
            'message': 'Agent updated successfully',
            'agent': updated_agent
        }), 200
        
    except Exception as e:
        logger.error(f"Update agent failed: {str(e)}")
        return jsonify({'error': 'Failed to update agent'}), 500

@agents_bp.route('/<agent_id>', methods=['DELETE'])
@token_required
def delete_agent(agent_id):
    """Eliminar un agente"""
    try:
        user = request.current_user
        
        agent_model = AgentModel()
        agent = agent_model.get_by_id(agent_id)
        
        if not agent:
            return jsonify({'error': 'Agent not found'}), 404
        
        # Verificar permisos (solo el creador o admin puede eliminar)
        if agent.get('created_by') != user['id'] and user.get('role') != 'admin':
            return jsonify({'error': 'Access denied'}), 403
        
        # En lugar de eliminar físicamente, marcar como inactivo
        agent_model.update(agent_id, {'is_active': False})
        
        return jsonify({'message': 'Agent deleted successfully'}), 200
        
    except Exception as e:
        logger.error(f"Delete agent failed: {str(e)}")
        return jsonify({'error': 'Failed to delete agent'}), 500

@agents_bp.route('/<agent_id>/clone', methods=['POST'])
@token_required
def clone_agent(agent_id):
    """Clonar un agente existente"""
    try:
        user = request.current_user
        
        agent_model = AgentModel()
        original_agent = agent_model.get_by_id(agent_id)
        
        if not original_agent:
            return jsonify({'error': 'Agent not found'}), 404
        
        # Verificar permisos (debe ser público o del usuario)
        if not original_agent.get('is_public', False) and original_agent.get('created_by') != user['id']:
            return jsonify({'error': 'Access denied'}), 403
        
        # Crear copia del agente
        clone_data = {
            'name': f"{original_agent['name']} (Copy)",
            'description': original_agent['description'],
            'system_prompt': original_agent['system_prompt'],
            'model_name': original_agent['model_name'],
            'temperature': original_agent['temperature'],
            'max_tokens': original_agent['max_tokens'],
            'tools_enabled': original_agent['tools_enabled'],
            'memory_enabled': original_agent['memory_enabled'],
            'memory_limit': original_agent['memory_limit'],
            'created_by': user['id'],
            'is_public': False,  # Las copias son privadas por defecto
            'is_active': True,
            'configuration': original_agent.get('configuration', {})
        }
        
        cloned_agent = agent_model.create(clone_data)
        
        return jsonify({
            'message': 'Agent cloned successfully',
            'agent': cloned_agent
        }), 201
        
    except Exception as e:
        logger.error(f"Clone agent failed: {str(e)}")
        return jsonify({'error': 'Failed to clone agent'}), 500

@agents_bp.route('/<agent_id>/test', methods=['POST'])
@token_required
def test_agent(agent_id):
    """Probar un agente con un mensaje de prueba"""
    try:
        data = request.get_json()
        user = request.current_user
        
        test_message = data.get('message', 'Hello, please introduce yourself.')
        
        agent_model = AgentModel()
        agent = agent_model.get_by_id(agent_id)
        
        if not agent:
            return jsonify({'error': 'Agent not found'}), 404
        
        # Verificar permisos
        if not agent.get('is_public', False) and agent.get('created_by') != user['id']:
            return jsonify({'error': 'Access denied'}), 403
        
        # Importar servicio de Ollama
        from src.services.ollama_service import OllamaService
        
        ollama_service = OllamaService()
        
        # Preparar contexto para el agente
        messages = [
            {
                "role": "system",
                "content": agent['system_prompt']
            },
            {
                "role": "user",
                "content": test_message
            }
        ]
        
        # Generar respuesta
        response = ollama_service.generate_response(
            model=agent['model_name'],
            messages=messages,
            temperature=agent['temperature'],
            max_tokens=agent['max_tokens']
        )
        
        if not response['success']:
            return jsonify({'error': response['error']}), 500
        
        return jsonify({
            'test_successful': True,
            'request': {
                'message': test_message,
                'agent_name': agent['name'],
                'model': agent['model_name']
            },
            'response': {
                'content': response['content'],
                'usage': response.get('usage', {}),
                'response_time': response.get('response_time', 0)
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Test agent failed: {str(e)}")
        return jsonify({'error': 'Failed to test agent'}), 500

@agents_bp.route('/templates', methods=['GET'])
@token_required
def get_agent_templates():
    """Obtener plantillas de agentes predefinidas"""
    try:
        templates = [
            {
                'id': 'general_assistant',
                'name': 'Asistente General',
                'description': 'Agente de propósito general capaz de realizar múltiples tareas',
                'system_prompt': 'Eres un asistente de IA útil y capaz llamado MANUS. Puedes ayudar con una amplia variedad de tareas utilizando las herramientas disponibles. Siempre explica lo que estás haciendo y por qué.',
                'model_name': 'llama2',
                'temperature': 0.7,
                'max_tokens': 4096,
                'tools_enabled': ['shell_exec', 'file_read', 'file_write', 'web_search', 'browser_navigate'],
                'memory_enabled': True,
                'memory_limit': 10000
            },
            {
                'id': 'developer',
                'name': 'Desarrollador',
                'description': 'Agente especializado en tareas de desarrollo de software',
                'system_prompt': 'Eres un desarrollador de software experto. Tu especialidad es ayudar con tareas de programación, análisis de código, debugging y desarrollo de aplicaciones.',
                'model_name': 'llama2',
                'temperature': 0.3,
                'max_tokens': 8192,
                'tools_enabled': ['shell_exec', 'file_read', 'file_write', 'text_analyze'],
                'memory_enabled': True,
                'memory_limit': 15000
            },
            {
                'id': 'researcher',
                'name': 'Investigador Web',
                'description': 'Agente especializado en investigación web y análisis de contenido',
                'system_prompt': 'Eres un investigador especializado en búsqueda y análisis de información web. Tu objetivo es encontrar, analizar y sintetizar información de manera eficiente y precisa.',
                'model_name': 'llama2',
                'temperature': 0.5,
                'max_tokens': 6144,
                'tools_enabled': ['web_search', 'browser_navigate', 'text_analyze', 'file_write'],
                'memory_enabled': True,
                'memory_limit': 12000
            },
            {
                'id': 'creative_writer',
                'name': 'Escritor Creativo',
                'description': 'Agente especializado en escritura creativa y generación de contenido',
                'system_prompt': 'Eres un escritor creativo experto. Tu especialidad es crear contenido original, historias, artículos y material creativo de alta calidad.',
                'model_name': 'llama2',
                'temperature': 0.9,
                'max_tokens': 8192,
                'tools_enabled': ['file_write', 'text_analyze', 'web_search'],
                'memory_enabled': True,
                'memory_limit': 8000
            },
            {
                'id': 'data_analyst',
                'name': 'Analista de Datos',
                'description': 'Agente especializado en análisis de datos y generación de insights',
                'system_prompt': 'Eres un analista de datos experto. Tu especialidad es analizar datos, generar insights y crear visualizaciones útiles.',
                'model_name': 'llama2',
                'temperature': 0.2,
                'max_tokens': 6144,
                'tools_enabled': ['file_read', 'file_write', 'text_analyze', 'json_parse'],
                'memory_enabled': True,
                'memory_limit': 10000
            }
        ]
        
        return jsonify({
            'templates': templates,
            'total_count': len(templates)
        }), 200
        
    except Exception as e:
        logger.error(f"Get agent templates failed: {str(e)}")
        return jsonify({'error': 'Failed to get agent templates'}), 500

@agents_bp.route('/models', methods=['GET'])
@token_required
def get_available_models():
    """Obtener lista de modelos disponibles en Ollama"""
    try:
        from src.services.ollama_service import OllamaService
        
        ollama_service = OllamaService()
        models = ollama_service.get_available_models()
        
        if not models['success']:
            return jsonify({'error': models['error']}), 500
        
        return jsonify({
            'models': models['models'],
            'total_count': len(models['models'])
        }), 200
        
    except Exception as e:
        logger.error(f"Get available models failed: {str(e)}")
        return jsonify({'error': 'Failed to get available models'}), 500

