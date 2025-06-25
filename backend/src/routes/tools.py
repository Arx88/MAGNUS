"""
Rutas para gestión de herramientas en el sistema MANUS-like
Maneja CRUD de herramientas, configuración y ejecución
"""

from flask import Blueprint, request, jsonify, current_app
import logging
import uuid
import json
from datetime import datetime

from src.models.database import ToolModel, db
from src.routes.auth import token_required, admin_required

logger = logging.getLogger(__name__)

tools_bp = Blueprint('tools', __name__)

@tools_bp.route('/', methods=['GET'])
@token_required
def get_tools():
    """Obtener lista de herramientas disponibles"""
    try:
        category = request.args.get('category')
        enabled_only = request.args.get('enabled_only', 'false').lower() == 'true'
        
        tool_model = ToolModel()
        
        if enabled_only:
            tools = tool_model.get_enabled_tools()
        else:
            filters = {}
            if category:
                filters['category'] = category
            tools = tool_model.get_all(filters)
        
        # Agregar estadísticas de uso
        for tool in tools:
            try:
                # Obtener estadísticas de ejecución
                stats = db.execute_query("""
                    SELECT 
                        COUNT(*) as total_executions,
                        COUNT(CASE WHEN status = 'completed' THEN 1 END) as successful_executions,
                        COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_executions,
                        AVG(execution_time_ms) as avg_execution_time
                    FROM tool_executions 
                    WHERE tool_id = %s
                """, (tool['id'],))
                
                if stats:
                    tool['statistics'] = stats[0]
                else:
                    tool['statistics'] = {
                        'total_executions': 0,
                        'successful_executions': 0,
                        'failed_executions': 0,
                        'avg_execution_time': 0
                    }
            except:
                tool['statistics'] = {
                    'total_executions': 0,
                    'successful_executions': 0,
                    'failed_executions': 0,
                    'avg_execution_time': 0
                }
        
        # Obtener categorías únicas
        categories = list(set(tool.get('category', 'uncategorized') for tool in tools))
        
        return jsonify({
            'tools': tools,
            'categories': sorted(categories),
            'total_count': len(tools),
            'filters': {
                'category': category,
                'enabled_only': enabled_only
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Get tools failed: {str(e)}")
        return jsonify({'error': 'Failed to get tools'}), 500

@tools_bp.route('/<tool_id>', methods=['GET'])
@token_required
def get_tool(tool_id):
    """Obtener detalles de una herramienta específica"""
    try:
        tool_model = ToolModel()
        tool = tool_model.get_by_id(tool_id)
        
        if not tool:
            return jsonify({'error': 'Tool not found'}), 404
        
        # Agregar estadísticas detalladas
        try:
            stats = db.execute_query("""
                SELECT 
                    COUNT(*) as total_executions,
                    COUNT(CASE WHEN status = 'completed' THEN 1 END) as successful_executions,
                    COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_executions,
                    COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending_executions,
                    COUNT(CASE WHEN status = 'running' THEN 1 END) as running_executions,
                    AVG(execution_time_ms) as avg_execution_time,
                    MIN(execution_time_ms) as min_execution_time,
                    MAX(execution_time_ms) as max_execution_time
                FROM tool_executions 
                WHERE tool_id = %s
            """, (tool_id,))
            
            if stats:
                tool['detailed_statistics'] = stats[0]
            
            # Obtener ejecuciones recientes
            recent_executions = db.execute_query("""
                SELECT te.*, t.title as task_title, c.title as conversation_title
                FROM tool_executions te
                LEFT JOIN tasks t ON te.task_id = t.id
                LEFT JOIN conversations c ON t.conversation_id = c.id
                WHERE te.tool_id = %s
                ORDER BY te.started_at DESC
                LIMIT 10
            """, (tool_id,))
            
            tool['recent_executions'] = recent_executions
            
        except Exception as stats_error:
            logger.warning(f"Could not get tool statistics: {str(stats_error)}")
            tool['detailed_statistics'] = {}
            tool['recent_executions'] = []
        
        return jsonify({'tool': tool}), 200
        
    except Exception as e:
        logger.error(f"Get tool failed: {str(e)}")
        return jsonify({'error': 'Failed to get tool'}), 500

@tools_bp.route('/', methods=['POST'])
@admin_required
def create_tool():
    """Crear una nueva herramienta (solo administradores)"""
    try:
        data = request.get_json()
        
        # Validar datos requeridos
        required_fields = ['name', 'display_name', 'description', 'category', 'function_schema']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        # Validar que el nombre sea único
        tool_model = ToolModel()
        existing_tool = tool_model.get_by_name(data['name'])
        if existing_tool:
            return jsonify({'error': 'Tool with this name already exists'}), 409
        
        # Validar esquema de función
        try:
            function_schema = data['function_schema']
            if isinstance(function_schema, str):
                function_schema = json.loads(function_schema)
            
            # Validar estructura básica del esquema
            if not isinstance(function_schema, dict):
                raise ValueError("Function schema must be a JSON object")
            
            if 'type' not in function_schema or function_schema['type'] != 'function':
                raise ValueError("Function schema must have type 'function'")
            
            if 'function' not in function_schema:
                raise ValueError("Function schema must contain 'function' object")
            
        except (json.JSONDecodeError, ValueError) as e:
            return jsonify({'error': f'Invalid function schema: {str(e)}'}), 400
        
        # Crear herramienta
        tool_data = {
            'name': data['name'],
            'display_name': data['display_name'],
            'description': data['description'],
            'category': data['category'],
            'function_schema': function_schema,
            'implementation_type': data.get('implementation_type', 'python'),
            'implementation_code': data.get('implementation_code', ''),
            'is_enabled': data.get('is_enabled', True),
            'requires_confirmation': data.get('requires_confirmation', False),
            'security_level': data.get('security_level', 'safe'),
            'usage_count': 0
        }
        
        # Validar security_level
        valid_security_levels = ['safe', 'moderate', 'dangerous']
        if tool_data['security_level'] not in valid_security_levels:
            return jsonify({'error': f'Invalid security level. Must be one of: {valid_security_levels}'}), 400
        
        # Validar implementation_type
        valid_implementation_types = ['python', 'shell', 'api', 'builtin']
        if tool_data['implementation_type'] not in valid_implementation_types:
            return jsonify({'error': f'Invalid implementation type. Must be one of: {valid_implementation_types}'}), 400
        
        created_tool = tool_model.create(tool_data)
        
        return jsonify({
            'message': 'Tool created successfully',
            'tool': created_tool
        }), 201
        
    except Exception as e:
        logger.error(f"Create tool failed: {str(e)}")
        return jsonify({'error': 'Failed to create tool'}), 500

@tools_bp.route('/<tool_id>', methods=['PUT'])
@admin_required
def update_tool(tool_id):
    """Actualizar una herramienta existente (solo administradores)"""
    try:
        data = request.get_json()
        
        tool_model = ToolModel()
        tool = tool_model.get_by_id(tool_id)
        
        if not tool:
            return jsonify({'error': 'Tool not found'}), 404
        
        # Campos que se pueden actualizar
        updatable_fields = [
            'display_name', 'description', 'category', 'function_schema',
            'implementation_type', 'implementation_code', 'is_enabled',
            'requires_confirmation', 'security_level'
        ]
        
        update_data = {}
        for field in updatable_fields:
            if field in data:
                update_data[field] = data[field]
        
        if not update_data:
            return jsonify({'error': 'No valid fields to update'}), 400
        
        # Validar nombre único si se está actualizando
        if 'name' in data and data['name'] != tool['name']:
            existing_tool = tool_model.get_by_name(data['name'])
            if existing_tool:
                return jsonify({'error': 'Tool with this name already exists'}), 409
            update_data['name'] = data['name']
        
        # Validar esquema de función si se está actualizando
        if 'function_schema' in update_data:
            try:
                function_schema = update_data['function_schema']
                if isinstance(function_schema, str):
                    function_schema = json.loads(function_schema)
                    update_data['function_schema'] = function_schema
                
                # Validar estructura básica del esquema
                if not isinstance(function_schema, dict):
                    raise ValueError("Function schema must be a JSON object")
                
            except (json.JSONDecodeError, ValueError) as e:
                return jsonify({'error': f'Invalid function schema: {str(e)}'}), 400
        
        # Validar security_level
        if 'security_level' in update_data:
            valid_security_levels = ['safe', 'moderate', 'dangerous']
            if update_data['security_level'] not in valid_security_levels:
                return jsonify({'error': f'Invalid security level. Must be one of: {valid_security_levels}'}), 400
        
        # Validar implementation_type
        if 'implementation_type' in update_data:
            valid_implementation_types = ['python', 'shell', 'api', 'builtin']
            if update_data['implementation_type'] not in valid_implementation_types:
                return jsonify({'error': f'Invalid implementation type. Must be one of: {valid_implementation_types}'}), 400
        
        # Actualizar herramienta
        updated_tool = tool_model.update(tool_id, update_data)
        
        return jsonify({
            'message': 'Tool updated successfully',
            'tool': updated_tool
        }), 200
        
    except Exception as e:
        logger.error(f"Update tool failed: {str(e)}")
        return jsonify({'error': 'Failed to update tool'}), 500

@tools_bp.route('/<tool_id>', methods=['DELETE'])
@admin_required
def delete_tool(tool_id):
    """Eliminar una herramienta (solo administradores)"""
    try:
        tool_model = ToolModel()
        tool = tool_model.get_by_id(tool_id)
        
        if not tool:
            return jsonify({'error': 'Tool not found'}), 404
        
        # Verificar si la herramienta está siendo usada
        try:
            usage_count = db.execute_query("""
                SELECT COUNT(*) as count
                FROM tool_executions 
                WHERE tool_id = %s AND status IN ('pending', 'running')
            """, (tool_id,))
            
            if usage_count and usage_count[0]['count'] > 0:
                return jsonify({'error': 'Cannot delete tool with pending or running executions'}), 400
                
        except Exception as usage_error:
            logger.warning(f"Could not check tool usage: {str(usage_error)}")
        
        # En lugar de eliminar físicamente, deshabilitar la herramienta
        tool_model.update(tool_id, {'is_enabled': False})
        
        return jsonify({'message': 'Tool disabled successfully'}), 200
        
    except Exception as e:
        logger.error(f"Delete tool failed: {str(e)}")
        return jsonify({'error': 'Failed to delete tool'}), 500

@tools_bp.route('/<tool_id>/test', methods=['POST'])
@admin_required
def test_tool(tool_id):
    """Probar una herramienta con parámetros de prueba"""
    try:
        data = request.get_json()
        
        tool_model = ToolModel()
        tool = tool_model.get_by_id(tool_id)
        
        if not tool:
            return jsonify({'error': 'Tool not found'}), 404
        
        if not tool.get('is_enabled', True):
            return jsonify({'error': 'Tool is disabled'}), 400
        
        test_parameters = data.get('parameters', {})
        
        # Importar servicio de ejecución de herramientas
        from src.services.tool_service import ToolService
        
        tool_service = ToolService()
        
        # Ejecutar herramienta en modo de prueba
        result = tool_service.execute_tool(
            tool_name=tool['name'],
            parameters=test_parameters,
            test_mode=True
        )
        
        return jsonify({
            'test_successful': result['success'],
            'tool_name': tool['name'],
            'parameters': test_parameters,
            'result': result
        }), 200
        
    except Exception as e:
        logger.error(f"Test tool failed: {str(e)}")
        return jsonify({'error': 'Failed to test tool'}), 500

@tools_bp.route('/<tool_id>/enable', methods=['POST'])
@admin_required
def enable_tool(tool_id):
    """Habilitar una herramienta"""
    try:
        tool_model = ToolModel()
        tool = tool_model.get_by_id(tool_id)
        
        if not tool:
            return jsonify({'error': 'Tool not found'}), 404
        
        updated_tool = tool_model.update(tool_id, {'is_enabled': True})
        
        return jsonify({
            'message': 'Tool enabled successfully',
            'tool': updated_tool
        }), 200
        
    except Exception as e:
        logger.error(f"Enable tool failed: {str(e)}")
        return jsonify({'error': 'Failed to enable tool'}), 500

@tools_bp.route('/<tool_id>/disable', methods=['POST'])
@admin_required
def disable_tool(tool_id):
    """Deshabilitar una herramienta"""
    try:
        tool_model = ToolModel()
        tool = tool_model.get_by_id(tool_id)
        
        if not tool:
            return jsonify({'error': 'Tool not found'}), 404
        
        updated_tool = tool_model.update(tool_id, {'is_enabled': False})
        
        return jsonify({
            'message': 'Tool disabled successfully',
            'tool': updated_tool
        }), 200
        
    except Exception as e:
        logger.error(f"Disable tool failed: {str(e)}")
        return jsonify({'error': 'Failed to disable tool'}), 500

@tools_bp.route('/categories', methods=['GET'])
@token_required
def get_tool_categories():
    """Obtener lista de categorías de herramientas"""
    try:
        tool_model = ToolModel()
        tools = tool_model.get_all()
        
        # Extraer categorías únicas
        categories = {}
        for tool in tools:
            category = tool.get('category', 'uncategorized')
            if category not in categories:
                categories[category] = {
                    'name': category,
                    'tool_count': 0,
                    'enabled_count': 0
                }
            
            categories[category]['tool_count'] += 1
            if tool.get('is_enabled', True):
                categories[category]['enabled_count'] += 1
        
        return jsonify({
            'categories': list(categories.values()),
            'total_categories': len(categories)
        }), 200
        
    except Exception as e:
        logger.error(f"Get tool categories failed: {str(e)}")
        return jsonify({'error': 'Failed to get tool categories'}), 500

@tools_bp.route('/statistics', methods=['GET'])
@admin_required
def get_tool_statistics():
    """Obtener estadísticas globales de herramientas"""
    try:
        tool_model = ToolModel()
        tools = tool_model.get_all()
        
        # Estadísticas básicas
        stats = {
            'total_tools': len(tools),
            'enabled_tools': len([t for t in tools if t.get('is_enabled', True)]),
            'disabled_tools': len([t for t in tools if not t.get('is_enabled', True)]),
            'by_category': {},
            'by_security_level': {
                'safe': 0,
                'moderate': 0,
                'dangerous': 0
            },
            'by_implementation_type': {
                'python': 0,
                'shell': 0,
                'api': 0,
                'builtin': 0
            },
            'total_executions': 0,
            'successful_executions': 0,
            'failed_executions': 0
        }
        
        # Contar por categorías, niveles de seguridad y tipos de implementación
        for tool in tools:
            # Categorías
            category = tool.get('category', 'uncategorized')
            if category not in stats['by_category']:
                stats['by_category'][category] = 0
            stats['by_category'][category] += 1
            
            # Niveles de seguridad
            security_level = tool.get('security_level', 'safe')
            if security_level in stats['by_security_level']:
                stats['by_security_level'][security_level] += 1
            
            # Tipos de implementación
            impl_type = tool.get('implementation_type', 'python')
            if impl_type in stats['by_implementation_type']:
                stats['by_implementation_type'][impl_type] += 1
        
        # Obtener estadísticas de ejecución
        try:
            execution_stats = db.execute_query("""
                SELECT 
                    COUNT(*) as total_executions,
                    COUNT(CASE WHEN status = 'completed' THEN 1 END) as successful_executions,
                    COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_executions,
                    AVG(execution_time_ms) as avg_execution_time
                FROM tool_executions
            """)
            
            if execution_stats:
                stats.update(execution_stats[0])
            
        except Exception as exec_error:
            logger.warning(f"Could not get execution statistics: {str(exec_error)}")
        
        return jsonify({
            'statistics': stats,
            'generated_at': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Get tool statistics failed: {str(e)}")
        return jsonify({'error': 'Failed to get tool statistics'}), 500

@tools_bp.route('/templates', methods=['GET'])
@admin_required
def get_tool_templates():
    """Obtener plantillas de herramientas predefinidas"""
    try:
        templates = [
            {
                'name': 'custom_shell_command',
                'display_name': 'Comando Shell Personalizado',
                'description': 'Ejecuta un comando shell personalizado',
                'category': 'system',
                'function_schema': {
                    "type": "function",
                    "function": {
                        "name": "custom_shell_command",
                        "description": "Execute custom shell command",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "command": {
                                    "type": "string",
                                    "description": "Shell command to execute"
                                },
                                "working_dir": {
                                    "type": "string",
                                    "description": "Working directory",
                                    "default": "/tmp"
                                }
                            },
                            "required": ["command"]
                        }
                    }
                },
                'implementation_type': 'python',
                'security_level': 'dangerous',
                'requires_confirmation': True
            },
            {
                'name': 'api_request',
                'display_name': 'Solicitud API',
                'description': 'Realiza una solicitud HTTP a una API externa',
                'category': 'web',
                'function_schema': {
                    "type": "function",
                    "function": {
                        "name": "api_request",
                        "description": "Make HTTP API request",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "url": {
                                    "type": "string",
                                    "description": "API endpoint URL"
                                },
                                "method": {
                                    "type": "string",
                                    "description": "HTTP method",
                                    "enum": ["GET", "POST", "PUT", "DELETE"],
                                    "default": "GET"
                                },
                                "headers": {
                                    "type": "object",
                                    "description": "HTTP headers"
                                },
                                "data": {
                                    "type": "object",
                                    "description": "Request body data"
                                }
                            },
                            "required": ["url"]
                        }
                    }
                },
                'implementation_type': 'python',
                'security_level': 'moderate',
                'requires_confirmation': False
            },
            {
                'name': 'data_processor',
                'display_name': 'Procesador de Datos',
                'description': 'Procesa y transforma datos estructurados',
                'category': 'data',
                'function_schema': {
                    "type": "function",
                    "function": {
                        "name": "data_processor",
                        "description": "Process and transform structured data",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "data": {
                                    "type": "array",
                                    "description": "Data to process"
                                },
                                "operation": {
                                    "type": "string",
                                    "description": "Processing operation",
                                    "enum": ["filter", "sort", "group", "aggregate", "transform"]
                                },
                                "criteria": {
                                    "type": "object",
                                    "description": "Operation criteria"
                                }
                            },
                            "required": ["data", "operation"]
                        }
                    }
                },
                'implementation_type': 'python',
                'security_level': 'safe',
                'requires_confirmation': False
            }
        ]
        
        return jsonify({
            'templates': templates,
            'total_count': len(templates)
        }), 200
        
    except Exception as e:
        logger.error(f"Get tool templates failed: {str(e)}")
        return jsonify({'error': 'Failed to get tool templates'}), 500

