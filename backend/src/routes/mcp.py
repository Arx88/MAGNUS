"""
Rutas para gestión de herramientas MCP
"""
from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
import asyncio
from functools import wraps

from ..services.mcp_service import mcp_service
from ..services.auth_service import require_auth

mcp_bp = Blueprint('mcp', __name__, url_prefix='/api/mcp')

def async_route(f):
    """Decorador para rutas asíncronas"""
    @wraps(f)
    def wrapper(*args, **kwargs):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(f(*args, **kwargs))
        finally:
            loop.close()
    return wrapper

@mcp_bp.route('/tools', methods=['GET'])
@cross_origin()
@require_auth
def list_tools():
    """Lista todas las herramientas MCP disponibles"""
    try:
        tools = mcp_service.list_tools()
        return jsonify({
            'success': True,
            'tools': tools
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@mcp_bp.route('/tools/<tool_id>', methods=['GET'])
@cross_origin()
@require_auth
def get_tool_status(tool_id):
    """Obtiene el estado de una herramienta específica"""
    try:
        status = mcp_service.get_tool_status(tool_id)
        return jsonify({
            'success': True,
            'status': status
        })
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@mcp_bp.route('/tools/<tool_id>/install', methods=['POST'])
@cross_origin()
@require_auth
@async_route
async def install_tool(tool_id):
    """Instala una herramienta MCP"""
    try:
        data = request.get_json() or {}
        config = data.get('config', {})
        
        success = await mcp_service.install_tool(tool_id, config)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Tool {tool_id} installed successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Failed to install tool {tool_id}'
            }), 500
            
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@mcp_bp.route('/tools/<tool_id>/start', methods=['POST'])
@cross_origin()
@require_auth
@async_route
async def start_tool(tool_id):
    """Inicia una herramienta MCP"""
    try:
        data = request.get_json() or {}
        config = data.get('config', {})
        
        success = await mcp_service.start_tool(tool_id, config)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Tool {tool_id} started successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Failed to start tool {tool_id}'
            }), 500
            
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@mcp_bp.route('/tools/<tool_id>/stop', methods=['POST'])
@cross_origin()
@require_auth
@async_route
async def stop_tool(tool_id):
    """Detiene una herramienta MCP"""
    try:
        success = await mcp_service.stop_tool(tool_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Tool {tool_id} stopped successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Failed to stop tool {tool_id}'
            }), 500
            
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@mcp_bp.route('/tools/<tool_id>/execute', methods=['POST'])
@cross_origin()
@require_auth
@async_route
async def execute_tool(tool_id):
    """Ejecuta una herramienta MCP"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'Request body is required'
            }), 400
        
        method = data.get('method')
        params = data.get('params', {})
        agent_id = data.get('agent_id')
        task_id = data.get('task_id')
        
        if not method:
            return jsonify({
                'success': False,
                'error': 'Method is required'
            }), 400
        
        from ..services.mcp_service import MCPRequest
        request_obj = MCPRequest(
            tool_id=tool_id,
            method=method,
            params=params,
            agent_id=agent_id,
            task_id=task_id
        )
        
        response = await mcp_service.execute_tool(request_obj)
        
        return jsonify({
            'success': response.success,
            'result': response.result,
            'error': response.error,
            'execution_time': response.execution_time
        })
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@mcp_bp.route('/tools/<tool_id>/logs', methods=['GET'])
@cross_origin()
@require_auth
def get_tool_logs(tool_id):
    """Obtiene los logs de una herramienta"""
    try:
        lines = request.args.get('lines', 100, type=int)
        logs = mcp_service.get_tool_logs(tool_id, lines)
        
        return jsonify({
            'success': True,
            'logs': logs
        })
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@mcp_bp.route('/health', methods=['GET'])
@cross_origin()
def health_check():
    """Verifica el estado del servicio MCP"""
    try:
        # Verificar que Docker esté disponible
        tools = mcp_service.list_tools()
        running_tools = [tool for tool in tools if tool.get('status') == 'running']
        
        return jsonify({
            'success': True,
            'status': 'healthy',
            'total_tools': len(tools),
            'running_tools': len(running_tools),
            'docker_available': True
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'status': 'unhealthy',
            'error': str(e),
            'docker_available': False
        }), 500

