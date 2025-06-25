"""
Servicio de herramientas para el sistema MANUS-like
Maneja la ejecución y gestión de herramientas disponibles para agentes
"""

import logging
import json
import subprocess
import requests
import importlib
import sys
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid
import traceback

from src.models.database import db, ToolModel

logger = logging.getLogger(__name__)

class ToolExecutionModel:
    """Modelo para ejecuciones de herramientas"""
    
    def __init__(self):
        self.table_name = "tool_executions"
    
    def create_execution(self, execution_data: Dict[str, Any]) -> Dict[str, Any]:
        """Crear registro de ejecución"""
        try:
            result = db.execute_query("""
                INSERT INTO tool_executions (
                    id, task_id, tool_id, parameters, status, started_at
                ) VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING *
            """, (
                execution_data['id'],
                execution_data.get('task_id'),
                execution_data['tool_id'],
                json.dumps(execution_data['parameters']),
                'pending',
                datetime.utcnow().isoformat()
            ))
            
            return result[0] if result else None
            
        except Exception as e:
            logger.error(f"Create execution failed: {str(e)}")
            raise
    
    def update_execution(self, execution_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Actualizar ejecución"""
        try:
            set_clauses = []
            values = []
            
            for key, value in update_data.items():
                if key in ['status', 'result', 'error_message', 'completed_at', 'execution_time_ms']:
                    set_clauses.append(f"{key} = %s")
                    if key == 'result' and isinstance(value, (dict, list)):
                        values.append(json.dumps(value))
                    else:
                        values.append(value)
            
            if not set_clauses:
                return None
            
            values.append(execution_id)
            
            result = db.execute_query(f"""
                UPDATE tool_executions 
                SET {', '.join(set_clauses)}
                WHERE id = %s
                RETURNING *
            """, values)
            
            return result[0] if result else None
            
        except Exception as e:
            logger.error(f"Update execution failed: {str(e)}")
            raise

class ToolService:
    """Servicio para gestión y ejecución de herramientas"""
    
    def __init__(self):
        self.tool_model = ToolModel()
        self.execution_model = ToolExecutionModel()
        self._builtin_tools = self._load_builtin_tools()
    
    def _load_builtin_tools(self) -> Dict[str, Any]:
        """Cargar herramientas integradas"""
        return {
            'shell_exec': {
                'function': self._execute_shell_command,
                'description': 'Execute shell command',
                'security_level': 'dangerous'
            },
            'file_read': {
                'function': self._read_file,
                'description': 'Read file content',
                'security_level': 'safe'
            },
            'file_write': {
                'function': self._write_file,
                'description': 'Write file content',
                'security_level': 'moderate'
            },
            'http_request': {
                'function': self._make_http_request,
                'description': 'Make HTTP request',
                'security_level': 'moderate'
            },
            'python_exec': {
                'function': self._execute_python_code,
                'description': 'Execute Python code',
                'security_level': 'dangerous'
            }
        }
    
    def get_available_tools(self, enabled_only: bool = True) -> List[Dict[str, Any]]:
        """Obtener herramientas disponibles"""
        try:
            filters = {}
            if enabled_only:
                filters['is_enabled'] = True
            
            tools = self.tool_model.get_all(filters)
            return tools
            
        except Exception as e:
            logger.error(f"Get available tools failed: {str(e)}")
            return []
    
    def get_tool_by_name(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Obtener herramienta por nombre"""
        try:
            return self.tool_model.get_by_name(tool_name)
        except Exception as e:
            logger.error(f"Get tool by name failed: {str(e)}")
            return None
    
    def execute_tool(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        task_id: str = None,
        test_mode: bool = False
    ) -> Dict[str, Any]:
        """Ejecutar una herramienta"""
        execution_id = str(uuid.uuid4())
        start_time = datetime.utcnow()
        
        try:
            # Obtener información de la herramienta
            tool = self.get_tool_by_name(tool_name)
            
            if not tool:
                return {
                    'success': False,
                    'error': f'Tool {tool_name} not found',
                    'execution_id': execution_id
                }
            
            if not tool.get('is_enabled', True) and not test_mode:
                return {
                    'success': False,
                    'error': f'Tool {tool_name} is disabled',
                    'execution_id': execution_id
                }
            
            # Crear registro de ejecución
            if not test_mode:
                execution_data = {
                    'id': execution_id,
                    'task_id': task_id,
                    'tool_id': tool['id'],
                    'parameters': parameters
                }
                self.execution_model.create_execution(execution_data)
            
            # Validar parámetros
            validation_result = self._validate_parameters(tool, parameters)
            if not validation_result['valid']:
                if not test_mode:
                    self.execution_model.update_execution(execution_id, {
                        'status': 'failed',
                        'error_message': validation_result['error'],
                        'completed_at': datetime.utcnow().isoformat()
                    })
                
                return {
                    'success': False,
                    'error': validation_result['error'],
                    'execution_id': execution_id
                }
            
            # Actualizar estado a ejecutándose
            if not test_mode:
                self.execution_model.update_execution(execution_id, {
                    'status': 'running'
                })
            
            # Ejecutar herramienta según su tipo
            implementation_type = tool.get('implementation_type', 'python')
            
            if implementation_type == 'builtin':
                result = self._execute_builtin_tool(tool_name, parameters)
            elif implementation_type == 'python':
                result = self._execute_python_tool(tool, parameters)
            elif implementation_type == 'shell':
                result = self._execute_shell_tool(tool, parameters)
            elif implementation_type == 'api':
                result = self._execute_api_tool(tool, parameters)
            else:
                result = {
                    'success': False,
                    'error': f'Unsupported implementation type: {implementation_type}'
                }
            
            # Calcular tiempo de ejecución
            end_time = datetime.utcnow()
            execution_time = (end_time - start_time).total_seconds() * 1000  # en milisegundos
            
            # Actualizar registro de ejecución
            if not test_mode:
                update_data = {
                    'status': 'completed' if result['success'] else 'failed',
                    'result': result.get('result'),
                    'error_message': result.get('error') if not result['success'] else None,
                    'completed_at': end_time.isoformat(),
                    'execution_time_ms': execution_time
                }
                self.execution_model.update_execution(execution_id, update_data)
            
            # Incrementar contador de uso
            if not test_mode and result['success']:
                try:
                    current_count = tool.get('usage_count', 0)
                    self.tool_model.update(tool['id'], {'usage_count': current_count + 1})
                except:
                    pass  # No es crítico si falla
            
            result['execution_id'] = execution_id
            result['execution_time_ms'] = execution_time
            
            return result
            
        except Exception as e:
            logger.error(f"Tool execution failed: {str(e)}")
            
            # Actualizar registro con error
            if not test_mode:
                try:
                    end_time = datetime.utcnow()
                    execution_time = (end_time - start_time).total_seconds() * 1000
                    
                    self.execution_model.update_execution(execution_id, {
                        'status': 'failed',
                        'error_message': str(e),
                        'completed_at': end_time.isoformat(),
                        'execution_time_ms': execution_time
                    })
                except:
                    pass
            
            return {
                'success': False,
                'error': str(e),
                'execution_id': execution_id
            }
    
    def _validate_parameters(self, tool: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validar parámetros de la herramienta"""
        try:
            function_schema = tool.get('function_schema', {})
            function_def = function_schema.get('function', {})
            param_schema = function_def.get('parameters', {})
            
            if not param_schema:
                return {'valid': True}
            
            required_params = param_schema.get('required', [])
            properties = param_schema.get('properties', {})
            
            # Verificar parámetros requeridos
            for param in required_params:
                if param not in parameters:
                    return {
                        'valid': False,
                        'error': f'Required parameter "{param}" is missing'
                    }
            
            # Validar tipos de parámetros
            for param_name, param_value in parameters.items():
                if param_name in properties:
                    prop_def = properties[param_name]
                    expected_type = prop_def.get('type')
                    
                    if expected_type == 'string' and not isinstance(param_value, str):
                        return {
                            'valid': False,
                            'error': f'Parameter "{param_name}" must be a string'
                        }
                    elif expected_type == 'integer' and not isinstance(param_value, int):
                        return {
                            'valid': False,
                            'error': f'Parameter "{param_name}" must be an integer'
                        }
                    elif expected_type == 'number' and not isinstance(param_value, (int, float)):
                        return {
                            'valid': False,
                            'error': f'Parameter "{param_name}" must be a number'
                        }
                    elif expected_type == 'boolean' and not isinstance(param_value, bool):
                        return {
                            'valid': False,
                            'error': f'Parameter "{param_name}" must be a boolean'
                        }
                    elif expected_type == 'array' and not isinstance(param_value, list):
                        return {
                            'valid': False,
                            'error': f'Parameter "{param_name}" must be an array'
                        }
                    elif expected_type == 'object' and not isinstance(param_value, dict):
                        return {
                            'valid': False,
                            'error': f'Parameter "{param_name}" must be an object'
                        }
            
            return {'valid': True}
            
        except Exception as e:
            return {
                'valid': False,
                'error': f'Parameter validation error: {str(e)}'
            }
    
    def _execute_builtin_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecutar herramienta integrada"""
        try:
            if tool_name not in self._builtin_tools:
                return {
                    'success': False,
                    'error': f'Builtin tool {tool_name} not found'
                }
            
            tool_func = self._builtin_tools[tool_name]['function']
            result = tool_func(parameters)
            
            return {
                'success': True,
                'result': result
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _execute_python_tool(self, tool: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecutar herramienta Python"""
        try:
            implementation_code = tool.get('implementation_code', '')
            
            if not implementation_code:
                return {
                    'success': False,
                    'error': 'No implementation code provided'
                }
            
            # Crear contexto de ejecución
            exec_globals = {
                '__builtins__': __builtins__,
                'parameters': parameters,
                'result': None,
                'requests': requests,
                'json': json,
                'datetime': datetime
            }
            
            # Ejecutar código
            exec(implementation_code, exec_globals)
            
            return {
                'success': True,
                'result': exec_globals.get('result')
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Python execution error: {str(e)}'
            }
    
    def _execute_shell_tool(self, tool: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecutar herramienta shell"""
        try:
            implementation_code = tool.get('implementation_code', '')
            
            if not implementation_code:
                return {
                    'success': False,
                    'error': 'No shell command provided'
                }
            
            # Reemplazar parámetros en el comando
            command = implementation_code
            for key, value in parameters.items():
                command = command.replace(f'{{{key}}}', str(value))
            
            # Ejecutar comando
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            return {
                'success': result.returncode == 0,
                'result': {
                    'stdout': result.stdout,
                    'stderr': result.stderr,
                    'returncode': result.returncode
                }
            }
            
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': 'Command execution timeout'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Shell execution error: {str(e)}'
            }
    
    def _execute_api_tool(self, tool: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecutar herramienta API"""
        try:
            implementation_code = tool.get('implementation_code', '')
            
            if not implementation_code:
                return {
                    'success': False,
                    'error': 'No API configuration provided'
                }
            
            # Parsear configuración de API
            api_config = json.loads(implementation_code)
            
            url = api_config.get('url', '')
            method = api_config.get('method', 'GET').upper()
            headers = api_config.get('headers', {})
            
            # Reemplazar parámetros en URL y headers
            for key, value in parameters.items():
                url = url.replace(f'{{{key}}}', str(value))
                for header_key, header_value in headers.items():
                    headers[header_key] = str(header_value).replace(f'{{{key}}}', str(value))
            
            # Realizar solicitud
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            elif method == 'POST':
                data = parameters.get('data', {})
                response = requests.post(url, headers=headers, json=data, timeout=30)
            elif method == 'PUT':
                data = parameters.get('data', {})
                response = requests.put(url, headers=headers, json=data, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=30)
            else:
                return {
                    'success': False,
                    'error': f'Unsupported HTTP method: {method}'
                }
            
            return {
                'success': response.status_code < 400,
                'result': {
                    'status_code': response.status_code,
                    'headers': dict(response.headers),
                    'content': response.text,
                    'json': response.json() if response.headers.get('content-type', '').startswith('application/json') else None
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'API execution error: {str(e)}'
            }
    
    # Herramientas integradas
    
    def _execute_shell_command(self, parameters: Dict[str, Any]) -> Any:
        """Ejecutar comando shell"""
        command = parameters.get('command', '')
        working_dir = parameters.get('working_dir', '/tmp')
        
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            cwd=working_dir,
            timeout=30
        )
        
        return {
            'stdout': result.stdout,
            'stderr': result.stderr,
            'returncode': result.returncode
        }
    
    def _read_file(self, parameters: Dict[str, Any]) -> Any:
        """Leer archivo"""
        file_path = parameters.get('file_path', '')
        encoding = parameters.get('encoding', 'utf-8')
        
        with open(file_path, 'r', encoding=encoding) as f:
            content = f.read()
        
        return {
            'content': content,
            'size': len(content)
        }
    
    def _write_file(self, parameters: Dict[str, Any]) -> Any:
        """Escribir archivo"""
        file_path = parameters.get('file_path', '')
        content = parameters.get('content', '')
        encoding = parameters.get('encoding', 'utf-8')
        
        with open(file_path, 'w', encoding=encoding) as f:
            f.write(content)
        
        return {
            'bytes_written': len(content.encode(encoding)),
            'file_path': file_path
        }
    
    def _make_http_request(self, parameters: Dict[str, Any]) -> Any:
        """Realizar solicitud HTTP"""
        url = parameters.get('url', '')
        method = parameters.get('method', 'GET').upper()
        headers = parameters.get('headers', {})
        data = parameters.get('data', {})
        
        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            json=data if data else None,
            timeout=30
        )
        
        return {
            'status_code': response.status_code,
            'headers': dict(response.headers),
            'content': response.text,
            'json': response.json() if response.headers.get('content-type', '').startswith('application/json') else None
        }
    
    def _execute_python_code(self, parameters: Dict[str, Any]) -> Any:
        """Ejecutar código Python"""
        code = parameters.get('code', '')
        
        exec_globals = {
            '__builtins__': __builtins__,
            'result': None
        }
        
        exec(code, exec_globals)
        
        return exec_globals.get('result')
    
    def get_execution_history(self, tool_id: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Obtener historial de ejecuciones"""
        try:
            query = "SELECT * FROM tool_executions"
            params = []
            
            if tool_id:
                query += " WHERE tool_id = %s"
                params.append(tool_id)
            
            query += " ORDER BY started_at DESC LIMIT %s"
            params.append(limit)
            
            executions = db.execute_query(query, params)
            return executions or []
            
        except Exception as e:
            logger.error(f"Get execution history failed: {str(e)}")
            return []

