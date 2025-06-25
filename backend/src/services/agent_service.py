"""
Servicio de agentes para el sistema MANUS-like
Maneja la lógica de agentes autónomos, razonamiento y ejecución de tareas
"""

import logging
import json
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio
import re

from src.models.database import AgentModel, ConversationModel, MessageModel, TaskModel
from src.services.ollama_service import OllamaService
from src.services.tool_service import ToolService
from src.services.config_service import ConfigService

logger = logging.getLogger(__name__)

class AgentService:
    """Servicio para gestión y ejecución de agentes"""
    
    def __init__(self):
        self.agent_model = AgentModel()
        self.conversation_model = ConversationModel()
        self.message_model = MessageModel()
        self.task_model = TaskModel()
        self.ollama_service = OllamaService()
        self.tool_service = ToolService()
        self.config_service = ConfigService()
        
        # Plantilla de sistema para agentes
        self.system_template = """You are {agent_name}, {agent_description}

Your capabilities include:
{capabilities}

Available tools:
{available_tools}

Guidelines:
- Always think step by step before taking actions
- Use tools when necessary to complete tasks
- Provide clear and helpful responses
- Ask for clarification when needed
- Be proactive in solving problems

Current conversation context:
- User: {user_name}
- Conversation ID: {conversation_id}
- Task: {current_task}

Remember to be helpful, accurate, and efficient in your responses."""
    
    def create_agent(self, agent_data: Dict[str, Any], created_by: str) -> Dict[str, Any]:
        """Crear un nuevo agente"""
        try:
            # Validar datos del agente
            required_fields = ['name', 'description', 'model', 'system_prompt']
            for field in required_fields:
                if not agent_data.get(field):
                    raise ValueError(f'{field} is required')
            
            # Verificar que el modelo existe en Ollama
            if not self.ollama_service.validate_model_name(agent_data['model']):
                raise ValueError(f"Model {agent_data['model']} is not available in Ollama")
            
            # Preparar datos del agente
            agent_data['created_by'] = created_by
            agent_data['is_active'] = agent_data.get('is_active', True)
            agent_data['is_public'] = agent_data.get('is_public', False)
            
            # Configuración por defecto
            default_config = self.config_service.get_agent_config()
            agent_data['temperature'] = agent_data.get('temperature', default_config['default_temperature'])
            agent_data['max_tokens'] = agent_data.get('max_tokens', default_config['max_tokens'])
            agent_data['memory_enabled'] = agent_data.get('memory_enabled', default_config['memory_enabled'])
            
            # Crear agente
            agent = self.agent_model.create(agent_data)
            
            logger.info(f"Agent created: {agent['name']} (ID: {agent['id']})")
            return agent
            
        except Exception as e:
            logger.error(f"Create agent failed: {str(e)}")
            raise
    
    def get_agent_by_id(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Obtener agente por ID"""
        try:
            return self.agent_model.get_by_id(agent_id)
        except Exception as e:
            logger.error(f"Get agent by ID failed: {str(e)}")
            return None
    
    def start_conversation(
        self,
        agent_id: str,
        user_id: str,
        initial_message: str = None,
        conversation_title: str = None
    ) -> Dict[str, Any]:
        """Iniciar una nueva conversación con un agente"""
        try:
            # Verificar que el agente existe y está activo
            agent = self.get_agent_by_id(agent_id)
            if not agent:
                raise ValueError(f"Agent {agent_id} not found")
            
            if not agent.get('is_active', True):
                raise ValueError(f"Agent {agent['name']} is not active")
            
            # Crear conversación
            conversation_data = {
                'user_id': user_id,
                'agent_id': agent_id,
                'title': conversation_title or f"Chat with {agent['name']}",
                'status': 'active'
            }
            
            conversation = self.conversation_model.create(conversation_data)
            
            # Agregar mensaje inicial del sistema
            system_message = self._build_system_message(agent, conversation, user_id)
            self.message_model.create({
                'conversation_id': conversation['id'],
                'role': 'system',
                'content': system_message,
                'agent_id': agent_id
            })
            
            # Agregar mensaje inicial del usuario si se proporciona
            if initial_message:
                user_message = self.message_model.create({
                    'conversation_id': conversation['id'],
                    'role': 'user',
                    'content': initial_message,
                    'user_id': user_id
                })
                
                # Generar respuesta del agente
                agent_response = self.generate_agent_response(
                    conversation['id'],
                    agent_id,
                    user_id
                )
                
                return {
                    'conversation': conversation,
                    'user_message': user_message,
                    'agent_response': agent_response
                }
            
            return {
                'conversation': conversation,
                'user_message': None,
                'agent_response': None
            }
            
        except Exception as e:
            logger.error(f"Start conversation failed: {str(e)}")
            raise
    
    def send_message(
        self,
        conversation_id: str,
        user_id: str,
        message_content: str
    ) -> Dict[str, Any]:
        """Enviar mensaje en una conversación"""
        try:
            # Verificar que la conversación existe
            conversation = self.conversation_model.get_by_id(conversation_id)
            if not conversation:
                raise ValueError(f"Conversation {conversation_id} not found")
            
            if conversation['user_id'] != user_id:
                raise ValueError("Access denied to this conversation")
            
            if conversation['status'] != 'active':
                raise ValueError("Conversation is not active")
            
            # Crear mensaje del usuario
            user_message = self.message_model.create({
                'conversation_id': conversation_id,
                'role': 'user',
                'content': message_content,
                'user_id': user_id
            })
            
            # Generar respuesta del agente
            agent_response = self.generate_agent_response(
                conversation_id,
                conversation['agent_id'],
                user_id
            )
            
            return {
                'user_message': user_message,
                'agent_response': agent_response
            }
            
        except Exception as e:
            logger.error(f"Send message failed: {str(e)}")
            raise
    
    def generate_agent_response(
        self,
        conversation_id: str,
        agent_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """Generar respuesta del agente"""
        try:
            # Obtener agente
            agent = self.get_agent_by_id(agent_id)
            if not agent:
                raise ValueError(f"Agent {agent_id} not found")
            
            # Obtener historial de mensajes
            messages = self.message_model.get_conversation_messages(conversation_id)
            
            # Preparar mensajes para Ollama
            ollama_messages = self._prepare_messages_for_ollama(messages, agent)
            
            # Detectar si el usuario solicita usar herramientas
            tool_requests = self._detect_tool_requests(messages[-1]['content'] if messages else "")
            
            # Generar respuesta
            if tool_requests:
                # El agente necesita usar herramientas
                response = self._generate_response_with_tools(
                    agent, ollama_messages, tool_requests, conversation_id
                )
            else:
                # Respuesta normal sin herramientas
                response = self._generate_normal_response(agent, ollama_messages)
            
            # Crear mensaje del agente
            agent_message = self.message_model.create({
                'conversation_id': conversation_id,
                'role': 'assistant',
                'content': response['content'],
                'agent_id': agent_id,
                'metadata': response.get('metadata', {})
            })
            
            return agent_message
            
        except Exception as e:
            logger.error(f"Generate agent response failed: {str(e)}")
            raise
    
    def _build_system_message(
        self,
        agent: Dict[str, Any],
        conversation: Dict[str, Any],
        user_id: str
    ) -> str:
        """Construir mensaje del sistema para el agente"""
        try:
            # Obtener herramientas disponibles
            available_tools = self.tool_service.get_available_tools()
            tools_description = "\n".join([
                f"- {tool['name']}: {tool['description']}"
                for tool in available_tools
            ])
            
            # Obtener información del usuario
            user_name = "User"  # Se podría obtener de la base de datos
            
            # Construir mensaje del sistema
            system_message = self.system_template.format(
                agent_name=agent['name'],
                agent_description=agent['description'],
                capabilities=agent.get('capabilities', 'General assistance and task completion'),
                available_tools=tools_description,
                user_name=user_name,
                conversation_id=conversation['id'],
                current_task="General conversation"
            )
            
            # Agregar prompt personalizado del agente
            if agent.get('system_prompt'):
                system_message += f"\n\nAdditional instructions:\n{agent['system_prompt']}"
            
            return system_message
            
        except Exception as e:
            logger.error(f"Build system message failed: {str(e)}")
            return f"You are {agent['name']}, an AI assistant."
    
    def _prepare_messages_for_ollama(
        self,
        messages: List[Dict[str, Any]],
        agent: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """Preparar mensajes para enviar a Ollama"""
        try:
            ollama_messages = []
            
            # Limitar historial según configuración
            max_history = self.config_service.get_config('max_conversation_history', 100)
            recent_messages = messages[-max_history:] if len(messages) > max_history else messages
            
            for message in recent_messages:
                ollama_message = {
                    'role': message['role'],
                    'content': message['content']
                }
                ollama_messages.append(ollama_message)
            
            # Truncar si es necesario para no exceder límites de tokens
            max_tokens = agent.get('max_tokens', 4096)
            context_limit = max_tokens // 2  # Reservar la mitad para la respuesta
            
            truncated_messages = self.ollama_service.truncate_messages(
                ollama_messages, context_limit
            )
            
            return truncated_messages
            
        except Exception as e:
            logger.error(f"Prepare messages for Ollama failed: {str(e)}")
            return []
    
    def _detect_tool_requests(self, user_message: str) -> List[str]:
        """Detectar si el usuario solicita usar herramientas específicas"""
        tool_keywords = {
            'file': ['archivo', 'file', 'leer', 'read', 'escribir', 'write'],
            'shell': ['comando', 'command', 'ejecutar', 'execute', 'terminal'],
            'web': ['web', 'http', 'api', 'request', 'solicitud'],
            'python': ['python', 'código', 'code', 'script', 'programar']
        }
        
        detected_tools = []
        user_message_lower = user_message.lower()
        
        for tool_type, keywords in tool_keywords.items():
            if any(keyword in user_message_lower for keyword in keywords):
                detected_tools.append(tool_type)
        
        return detected_tools
    
    def _generate_response_with_tools(
        self,
        agent: Dict[str, Any],
        messages: List[Dict[str, str]],
        tool_requests: List[str],
        conversation_id: str
    ) -> Dict[str, Any]:
        """Generar respuesta usando herramientas"""
        try:
            # Agregar instrucciones sobre herramientas al contexto
            tool_instruction = f"""
The user's request seems to require using tools. Available tool types: {', '.join(tool_requests)}

Please analyze the request and determine if you need to use any tools. If so, describe what you would do step by step.
"""
            
            # Agregar instrucción al final de los mensajes
            enhanced_messages = messages + [{
                'role': 'system',
                'content': tool_instruction
            }]
            
            # Generar respuesta
            result = self.ollama_service.chat_completion(
                model=agent['model'],
                messages=enhanced_messages,
                temperature=agent.get('temperature', 0.7),
                max_tokens=agent.get('max_tokens', 4096)
            )
            
            if not result['success']:
                raise Exception(f"Ollama generation failed: {result['error']}")
            
            response_content = result['content']
            
            # Analizar si la respuesta indica que se necesitan herramientas
            # En una implementación completa, aquí se ejecutarían las herramientas
            
            return {
                'content': response_content,
                'metadata': {
                    'tool_requests': tool_requests,
                    'model_used': agent['model'],
                    'response_time': result.get('response_time', 0)
                }
            }
            
        except Exception as e:
            logger.error(f"Generate response with tools failed: {str(e)}")
            return {
                'content': f"I apologize, but I encountered an error while processing your request: {str(e)}",
                'metadata': {'error': str(e)}
            }
    
    def _generate_normal_response(
        self,
        agent: Dict[str, Any],
        messages: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """Generar respuesta normal sin herramientas"""
        try:
            result = self.ollama_service.chat_completion(
                model=agent['model'],
                messages=messages,
                temperature=agent.get('temperature', 0.7),
                max_tokens=agent.get('max_tokens', 4096)
            )
            
            if not result['success']:
                raise Exception(f"Ollama generation failed: {result['error']}")
            
            return {
                'content': result['content'],
                'metadata': {
                    'model_used': agent['model'],
                    'response_time': result.get('response_time', 0),
                    'usage': result.get('usage', {})
                }
            }
            
        except Exception as e:
            logger.error(f"Generate normal response failed: {str(e)}")
            return {
                'content': f"I apologize, but I encountered an error: {str(e)}",
                'metadata': {'error': str(e)}
            }
    
    def execute_task(
        self,
        agent_id: str,
        task_description: str,
        conversation_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """Ejecutar una tarea específica con un agente"""
        try:
            # Crear tarea
            task_data = {
                'conversation_id': conversation_id,
                'title': f"Task: {task_description[:50]}...",
                'description': task_description,
                'status': 'pending'
            }
            
            task = self.task_model.create(task_data)
            
            # Obtener agente
            agent = self.get_agent_by_id(agent_id)
            if not agent:
                raise ValueError(f"Agent {agent_id} not found")
            
            # Actualizar estado de la tarea
            self.task_model.update(task['id'], {
                'status': 'running',
                'started_at': datetime.utcnow().isoformat()
            })
            
            # Preparar contexto para la tarea
            task_context = f"""
Task: {task_description}

Please break down this task into steps and execute them systematically.
Use available tools when necessary and provide detailed progress updates.
"""
            
            # Crear mensaje de tarea
            task_message = self.message_model.create({
                'conversation_id': conversation_id,
                'role': 'user',
                'content': task_context,
                'user_id': user_id,
                'metadata': {'task_id': task['id']}
            })
            
            # Generar respuesta del agente para la tarea
            agent_response = self.generate_agent_response(
                conversation_id,
                agent_id,
                user_id
            )
            
            # Actualizar estado de la tarea
            self.task_model.update(task['id'], {
                'status': 'completed',
                'completed_at': datetime.utcnow().isoformat(),
                'result': agent_response['content']
            })
            
            return {
                'task': task,
                'task_message': task_message,
                'agent_response': agent_response
            }
            
        except Exception as e:
            logger.error(f"Execute task failed: {str(e)}")
            
            # Actualizar tarea como fallida
            if 'task' in locals():
                self.task_model.update(task['id'], {
                    'status': 'failed',
                    'completed_at': datetime.utcnow().isoformat(),
                    'error_message': str(e)
                })
            
            raise
    
    def get_agent_statistics(self, agent_id: str) -> Dict[str, Any]:
        """Obtener estadísticas de un agente"""
        try:
            agent = self.get_agent_by_id(agent_id)
            if not agent:
                return {}
            
            # Contar conversaciones
            conversation_count = self.conversation_model.count({'agent_id': agent_id})
            
            # Contar mensajes
            from src.models.database import db
            message_stats = db.execute_query("""
                SELECT COUNT(*) as total_messages
                FROM messages m
                JOIN conversations c ON m.conversation_id = c.id
                WHERE c.agent_id = %s AND m.role = 'assistant'
            """, (agent_id,))
            
            total_messages = message_stats[0]['total_messages'] if message_stats else 0
            
            # Contar tareas
            task_stats = db.execute_query("""
                SELECT 
                    COUNT(*) as total_tasks,
                    COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_tasks,
                    COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_tasks
                FROM tasks t
                JOIN conversations c ON t.conversation_id = c.id
                WHERE c.agent_id = %s
            """, (agent_id,))
            
            task_data = task_stats[0] if task_stats else {
                'total_tasks': 0,
                'completed_tasks': 0,
                'failed_tasks': 0
            }
            
            return {
                'agent_id': agent_id,
                'agent_name': agent['name'],
                'total_conversations': conversation_count,
                'total_messages': total_messages,
                'total_tasks': task_data['total_tasks'],
                'completed_tasks': task_data['completed_tasks'],
                'failed_tasks': task_data['failed_tasks'],
                'success_rate': (
                    (task_data['completed_tasks'] / task_data['total_tasks'] * 100)
                    if task_data['total_tasks'] > 0 else 0
                ),
                'created_at': agent['created_at'],
                'is_active': agent.get('is_active', True)
            }
            
        except Exception as e:
            logger.error(f"Get agent statistics failed: {str(e)}")
            return {}
    
    def update_agent_config(
        self,
        agent_id: str,
        config_updates: Dict[str, Any],
        updated_by: str
    ) -> Dict[str, Any]:
        """Actualizar configuración de un agente"""
        try:
            agent = self.get_agent_by_id(agent_id)
            if not agent:
                raise ValueError(f"Agent {agent_id} not found")
            
            # Validar configuración
            valid_fields = [
                'name', 'description', 'system_prompt', 'model',
                'temperature', 'max_tokens', 'is_active', 'is_public',
                'capabilities', 'memory_enabled'
            ]
            
            update_data = {}
            for field, value in config_updates.items():
                if field in valid_fields:
                    update_data[field] = value
            
            if not update_data:
                raise ValueError("No valid fields to update")
            
            # Validar modelo si se está actualizando
            if 'model' in update_data:
                if not self.ollama_service.validate_model_name(update_data['model']):
                    raise ValueError(f"Model {update_data['model']} is not available")
            
            # Validar temperatura
            if 'temperature' in update_data:
                if not (0 <= update_data['temperature'] <= 2):
                    raise ValueError("Temperature must be between 0 and 2")
            
            # Actualizar agente
            updated_agent = self.agent_model.update(agent_id, update_data)
            
            logger.info(f"Agent {agent_id} updated by {updated_by}")
            return updated_agent
            
        except Exception as e:
            logger.error(f"Update agent config failed: {str(e)}")
            raise

