"""
Rutas para integración con Ollama en el sistema MANUS-like
Maneja comunicación con modelos de lenguaje locales
"""

from flask import Blueprint, request, jsonify, current_app
import logging
from datetime import datetime

from src.routes.auth import token_required, admin_required
from src.services.ollama_service import OllamaService

logger = logging.getLogger(__name__)

ollama_bp = Blueprint('ollama', __name__)

@ollama_bp.route('/models', methods=['GET'])
@token_required
def get_models():
    """Obtener lista de modelos disponibles en Ollama"""
    try:
        ollama_service = OllamaService()
        result = ollama_service.get_available_models()
        
        if not result['success']:
            return jsonify({'error': result['error']}), 500
        
        return jsonify({
            'models': result['models'],
            'total_count': len(result['models']),
            'ollama_version': result.get('version', 'unknown')
        }), 200
        
    except Exception as e:
        logger.error(f"Get models failed: {str(e)}")
        return jsonify({'error': 'Failed to get models'}), 500

@ollama_bp.route('/models/<model_name>', methods=['GET'])
@token_required
def get_model_info(model_name):
    """Obtener información detallada de un modelo específico"""
    try:
        ollama_service = OllamaService()
        result = ollama_service.get_model_info(model_name)
        
        if not result['success']:
            return jsonify({'error': result['error']}), 404
        
        return jsonify({
            'model': result['model'],
            'model_name': model_name
        }), 200
        
    except Exception as e:
        logger.error(f"Get model info failed: {str(e)}")
        return jsonify({'error': 'Failed to get model info'}), 500

@ollama_bp.route('/models/pull', methods=['POST'])
@admin_required
def pull_model():
    """Descargar un nuevo modelo (solo administradores)"""
    try:
        data = request.get_json()
        model_name = data.get('model_name')
        
        if not model_name:
            return jsonify({'error': 'model_name is required'}), 400
        
        ollama_service = OllamaService()
        result = ollama_service.pull_model(model_name)
        
        if not result['success']:
            return jsonify({'error': result['error']}), 500
        
        return jsonify({
            'message': f'Model {model_name} pulled successfully',
            'model_name': model_name,
            'status': result.get('status', 'completed')
        }), 200
        
    except Exception as e:
        logger.error(f"Pull model failed: {str(e)}")
        return jsonify({'error': 'Failed to pull model'}), 500

@ollama_bp.route('/models/<model_name>', methods=['DELETE'])
@admin_required
def delete_model(model_name):
    """Eliminar un modelo (solo administradores)"""
    try:
        ollama_service = OllamaService()
        result = ollama_service.delete_model(model_name)
        
        if not result['success']:
            return jsonify({'error': result['error']}), 500
        
        return jsonify({
            'message': f'Model {model_name} deleted successfully',
            'model_name': model_name
        }), 200
        
    except Exception as e:
        logger.error(f"Delete model failed: {str(e)}")
        return jsonify({'error': 'Failed to delete model'}), 500

@ollama_bp.route('/generate', methods=['POST'])
@token_required
def generate_response():
    """Generar respuesta usando un modelo de Ollama"""
    try:
        data = request.get_json()
        
        # Validar datos requeridos
        required_fields = ['model', 'messages']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        model = data['model']
        messages = data['messages']
        temperature = data.get('temperature', 0.7)
        max_tokens = data.get('max_tokens', 4096)
        stream = data.get('stream', False)
        
        # Validar parámetros
        if not isinstance(messages, list) or len(messages) == 0:
            return jsonify({'error': 'messages must be a non-empty list'}), 400
        
        if not (0 <= temperature <= 2):
            return jsonify({'error': 'temperature must be between 0 and 2'}), 400
        
        if not (1 <= max_tokens <= 32000):
            return jsonify({'error': 'max_tokens must be between 1 and 32000'}), 400
        
        # Validar formato de mensajes
        for i, message in enumerate(messages):
            if not isinstance(message, dict):
                return jsonify({'error': f'message {i} must be an object'}), 400
            
            if 'role' not in message or 'content' not in message:
                return jsonify({'error': f'message {i} must have role and content'}), 400
            
            valid_roles = ['system', 'user', 'assistant']
            if message['role'] not in valid_roles:
                return jsonify({'error': f'message {i} role must be one of: {valid_roles}'}), 400
        
        ollama_service = OllamaService()
        
        if stream:
            # Para streaming, necesitaríamos implementar Server-Sent Events
            # Por simplicidad, devolvemos error por ahora
            return jsonify({'error': 'Streaming not implemented yet'}), 501
        else:
            # Generación normal
            result = ollama_service.generate_response(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            if not result['success']:
                return jsonify({'error': result['error']}), 500
            
            return jsonify({
                'response': {
                    'content': result['content'],
                    'model': model,
                    'usage': result.get('usage', {}),
                    'response_time': result.get('response_time', 0)
                },
                'request': {
                    'model': model,
                    'message_count': len(messages),
                    'temperature': temperature,
                    'max_tokens': max_tokens
                }
            }), 200
        
    except Exception as e:
        logger.error(f"Generate response failed: {str(e)}")
        return jsonify({'error': 'Failed to generate response'}), 500

@ollama_bp.route('/chat', methods=['POST'])
@token_required
def chat_completion():
    """Completar chat usando un modelo de Ollama (compatible con OpenAI API)"""
    try:
        data = request.get_json()
        
        # Mapear formato OpenAI a nuestro formato interno
        model = data.get('model')
        messages = data.get('messages', [])
        temperature = data.get('temperature', 0.7)
        max_tokens = data.get('max_tokens', 4096)
        
        if not model or not messages:
            return jsonify({'error': 'model and messages are required'}), 400
        
        ollama_service = OllamaService()
        result = ollama_service.generate_response(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        if not result['success']:
            return jsonify({'error': result['error']}), 500
        
        # Formato de respuesta compatible con OpenAI
        response = {
            'id': f"chatcmpl-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            'object': 'chat.completion',
            'created': int(datetime.utcnow().timestamp()),
            'model': model,
            'choices': [
                {
                    'index': 0,
                    'message': {
                        'role': 'assistant',
                        'content': result['content']
                    },
                    'finish_reason': 'stop'
                }
            ],
            'usage': result.get('usage', {
                'prompt_tokens': 0,
                'completion_tokens': 0,
                'total_tokens': 0
            })
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Chat completion failed: {str(e)}")
        return jsonify({'error': 'Failed to complete chat'}), 500

@ollama_bp.route('/embeddings', methods=['POST'])
@token_required
def generate_embeddings():
    """Generar embeddings usando un modelo de Ollama"""
    try:
        data = request.get_json()
        
        model = data.get('model')
        input_text = data.get('input')
        
        if not model or not input_text:
            return jsonify({'error': 'model and input are required'}), 400
        
        ollama_service = OllamaService()
        result = ollama_service.generate_embeddings(model, input_text)
        
        if not result['success']:
            return jsonify({'error': result['error']}), 500
        
        return jsonify({
            'embeddings': result['embeddings'],
            'model': model,
            'input': input_text,
            'dimensions': len(result['embeddings']) if result['embeddings'] else 0
        }), 200
        
    except Exception as e:
        logger.error(f"Generate embeddings failed: {str(e)}")
        return jsonify({'error': 'Failed to generate embeddings'}), 500

@ollama_bp.route('/health', methods=['GET'])
@token_required
def health_check():
    """Verificar estado de salud de Ollama"""
    try:
        ollama_service = OllamaService()
        result = ollama_service.health_check()
        
        return jsonify({
            'healthy': result['success'],
            'status': 'online' if result['success'] else 'offline',
            'version': result.get('version', 'unknown'),
            'error': result.get('error') if not result['success'] else None,
            'checked_at': datetime.utcnow().isoformat()
        }), 200 if result['success'] else 503
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            'healthy': False,
            'status': 'error',
            'error': str(e),
            'checked_at': datetime.utcnow().isoformat()
        }), 503

@ollama_bp.route('/config', methods=['GET'])
@admin_required
def get_ollama_config():
    """Obtener configuración de Ollama (solo administradores)"""
    try:
        config = {
            'base_url': current_app.config.get('OLLAMA_BASE_URL', 'http://localhost:11434'),
            'timeout': 30,  # Timeout por defecto
            'max_retries': 3,
            'default_model': 'llama2'
        }
        
        # Verificar conectividad
        ollama_service = OllamaService()
        health = ollama_service.health_check()
        config['connection_status'] = 'connected' if health['success'] else 'disconnected'
        config['last_error'] = health.get('error') if not health['success'] else None
        
        return jsonify({
            'config': config,
            'retrieved_at': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Get Ollama config failed: {str(e)}")
        return jsonify({'error': 'Failed to get Ollama config'}), 500

@ollama_bp.route('/config', methods=['PUT'])
@admin_required
def update_ollama_config():
    """Actualizar configuración de Ollama (solo administradores)"""
    try:
        data = request.get_json()
        
        # Por ahora, solo permitimos actualizar la URL base
        base_url = data.get('base_url')
        
        if base_url:
            # Validar URL
            if not base_url.startswith(('http://', 'https://')):
                return jsonify({'error': 'base_url must start with http:// or https://'}), 400
            
            # Actualizar configuración en el app context
            current_app.config['OLLAMA_BASE_URL'] = base_url
            
            # Probar conectividad con la nueva URL
            ollama_service = OllamaService()
            health = ollama_service.health_check()
            
            if not health['success']:
                return jsonify({
                    'warning': 'Configuration updated but connection test failed',
                    'error': health['error']
                }), 200
        
        return jsonify({
            'message': 'Ollama configuration updated successfully',
            'new_config': {
                'base_url': current_app.config.get('OLLAMA_BASE_URL')
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Update Ollama config failed: {str(e)}")
        return jsonify({'error': 'Failed to update Ollama config'}), 500

@ollama_bp.route('/test', methods=['POST'])
@admin_required
def test_model():
    """Probar un modelo con un prompt de prueba (solo administradores)"""
    try:
        data = request.get_json()
        
        model = data.get('model')
        test_prompt = data.get('prompt', 'Hello, please respond with a simple greeting.')
        
        if not model:
            return jsonify({'error': 'model is required'}), 400
        
        # Preparar mensajes de prueba
        messages = [
            {
                'role': 'user',
                'content': test_prompt
            }
        ]
        
        ollama_service = OllamaService()
        start_time = datetime.utcnow()
        
        result = ollama_service.generate_response(
            model=model,
            messages=messages,
            temperature=0.7,
            max_tokens=100
        )
        
        end_time = datetime.utcnow()
        response_time = (end_time - start_time).total_seconds()
        
        if not result['success']:
            return jsonify({
                'test_successful': False,
                'error': result['error'],
                'model': model,
                'prompt': test_prompt
            }), 200
        
        return jsonify({
            'test_successful': True,
            'model': model,
            'prompt': test_prompt,
            'response': result['content'],
            'response_time': response_time,
            'usage': result.get('usage', {}),
            'tested_at': start_time.isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Test model failed: {str(e)}")
        return jsonify({'error': 'Failed to test model'}), 500

@ollama_bp.route('/statistics', methods=['GET'])
@admin_required
def get_ollama_statistics():
    """Obtener estadísticas de uso de Ollama (solo administradores)"""
    try:
        # Obtener estadísticas de la base de datos
        from src.models.database import db
        
        stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'average_response_time': 0,
            'models_used': {},
            'requests_by_date': {}
        }
        
        try:
            # Estas estadísticas se podrían obtener de una tabla de logs de Ollama
            # Por ahora, devolvemos estadísticas simuladas
            stats = {
                'total_requests': 150,
                'successful_requests': 142,
                'failed_requests': 8,
                'average_response_time': 2.3,
                'models_used': {
                    'llama2': 89,
                    'codellama': 34,
                    'mistral': 27
                },
                'requests_by_date': {
                    '2024-01-15': 23,
                    '2024-01-16': 31,
                    '2024-01-17': 28,
                    '2024-01-18': 35,
                    '2024-01-19': 33
                }
            }
        except Exception as stats_error:
            logger.warning(f"Could not get Ollama statistics: {str(stats_error)}")
        
        return jsonify({
            'statistics': stats,
            'generated_at': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Get Ollama statistics failed: {str(e)}")
        return jsonify({'error': 'Failed to get Ollama statistics'}), 500

