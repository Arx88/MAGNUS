"""
Servicio para integración con Ollama
Maneja la comunicación con modelos de lenguaje locales
"""

import requests
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import time

logger = logging.getLogger(__name__)

class OllamaService:
    """Servicio para interactuar con Ollama"""
    
    def __init__(self, base_url: str = None, timeout: int = 30):
        self.base_url = base_url or "http://localhost:11434"
        self.timeout = timeout
        self.session = requests.Session()
        
        # Headers por defecto
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'MANUS-Backend/1.0'
        })
    
    def health_check(self) -> Dict[str, Any]:
        """Verificar si Ollama está disponible"""
        try:
            response = self.session.get(
                f"{self.base_url}/api/version",
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                version_info = response.json()
                return {
                    'success': True,
                    'version': version_info.get('version', 'unknown'),
                    'status': 'online'
                }
            else:
                return {
                    'success': False,
                    'error': f"HTTP {response.status_code}: {response.text}",
                    'status': 'offline'
                }
                
        except requests.exceptions.ConnectionError:
            return {
                'success': False,
                'error': 'Connection refused - Ollama service not available',
                'status': 'offline'
            }
        except requests.exceptions.Timeout:
            return {
                'success': False,
                'error': 'Request timeout - Ollama service not responding',
                'status': 'timeout'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f"Unexpected error: {str(e)}",
                'status': 'error'
            }
    
    def get_available_models(self) -> Dict[str, Any]:
        """Obtener lista de modelos disponibles"""
        try:
            response = self.session.get(
                f"{self.base_url}/api/tags",
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                models = []
                
                for model in data.get('models', []):
                    model_info = {
                        'name': model.get('name', ''),
                        'size': model.get('size', 0),
                        'digest': model.get('digest', ''),
                        'modified_at': model.get('modified_at', ''),
                        'details': model.get('details', {})
                    }
                    models.append(model_info)
                
                return {
                    'success': True,
                    'models': models,
                    'total_count': len(models)
                }
            else:
                return {
                    'success': False,
                    'error': f"HTTP {response.status_code}: {response.text}",
                    'models': []
                }
                
        except Exception as e:
            logger.error(f"Get available models failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'models': []
            }
    
    def get_model_info(self, model_name: str) -> Dict[str, Any]:
        """Obtener información detallada de un modelo"""
        try:
            payload = {
                'name': model_name
            }
            
            response = self.session.post(
                f"{self.base_url}/api/show",
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                model_info = response.json()
                return {
                    'success': True,
                    'model': model_info
                }
            else:
                return {
                    'success': False,
                    'error': f"HTTP {response.status_code}: {response.text}"
                }
                
        except Exception as e:
            logger.error(f"Get model info failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def pull_model(self, model_name: str) -> Dict[str, Any]:
        """Descargar un modelo"""
        try:
            payload = {
                'name': model_name
            }
            
            response = self.session.post(
                f"{self.base_url}/api/pull",
                json=payload,
                timeout=300  # 5 minutos para descarga
            )
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'status': 'completed',
                    'model': model_name
                }
            else:
                return {
                    'success': False,
                    'error': f"HTTP {response.status_code}: {response.text}"
                }
                
        except Exception as e:
            logger.error(f"Pull model failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def delete_model(self, model_name: str) -> Dict[str, Any]:
        """Eliminar un modelo"""
        try:
            payload = {
                'name': model_name
            }
            
            response = self.session.delete(
                f"{self.base_url}/api/delete",
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'model': model_name
                }
            else:
                return {
                    'success': False,
                    'error': f"HTTP {response.status_code}: {response.text}"
                }
                
        except Exception as e:
            logger.error(f"Delete model failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def generate_response(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        stream: bool = False
    ) -> Dict[str, Any]:
        """Generar respuesta usando un modelo"""
        try:
            start_time = time.time()
            
            # Convertir mensajes al formato de Ollama
            prompt = self._convert_messages_to_prompt(messages)
            
            payload = {
                'model': model,
                'prompt': prompt,
                'stream': stream,
                'options': {
                    'temperature': temperature,
                    'num_predict': max_tokens
                }
            }
            
            response = self.session.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=120  # 2 minutos para generación
            )
            
            end_time = time.time()
            response_time = end_time - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                return {
                    'success': True,
                    'content': data.get('response', ''),
                    'model': model,
                    'response_time': response_time,
                    'usage': {
                        'prompt_tokens': data.get('prompt_eval_count', 0),
                        'completion_tokens': data.get('eval_count', 0),
                        'total_tokens': data.get('prompt_eval_count', 0) + data.get('eval_count', 0)
                    },
                    'done': data.get('done', True)
                }
            else:
                return {
                    'success': False,
                    'error': f"HTTP {response.status_code}: {response.text}",
                    'response_time': response_time
                }
                
        except Exception as e:
            logger.error(f"Generate response failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'response_time': 0
            }
    
    def chat_completion(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096
    ) -> Dict[str, Any]:
        """Completar chat usando la API de chat de Ollama"""
        try:
            start_time = time.time()
            
            payload = {
                'model': model,
                'messages': messages,
                'stream': False,
                'options': {
                    'temperature': temperature,
                    'num_predict': max_tokens
                }
            }
            
            response = self.session.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=120
            )
            
            end_time = time.time()
            response_time = end_time - start_time
            
            if response.status_code == 200:
                data = response.json()
                message = data.get('message', {})
                
                return {
                    'success': True,
                    'content': message.get('content', ''),
                    'role': message.get('role', 'assistant'),
                    'model': model,
                    'response_time': response_time,
                    'usage': {
                        'prompt_tokens': data.get('prompt_eval_count', 0),
                        'completion_tokens': data.get('eval_count', 0),
                        'total_tokens': data.get('prompt_eval_count', 0) + data.get('eval_count', 0)
                    },
                    'done': data.get('done', True)
                }
            else:
                return {
                    'success': False,
                    'error': f"HTTP {response.status_code}: {response.text}",
                    'response_time': response_time
                }
                
        except Exception as e:
            logger.error(f"Chat completion failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'response_time': 0
            }
    
    def generate_embeddings(self, model: str, text: str) -> Dict[str, Any]:
        """Generar embeddings para un texto"""
        try:
            payload = {
                'model': model,
                'prompt': text
            }
            
            response = self.session.post(
                f"{self.base_url}/api/embeddings",
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'success': True,
                    'embeddings': data.get('embedding', []),
                    'model': model
                }
            else:
                return {
                    'success': False,
                    'error': f"HTTP {response.status_code}: {response.text}"
                }
                
        except Exception as e:
            logger.error(f"Generate embeddings failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _convert_messages_to_prompt(self, messages: List[Dict[str, str]]) -> str:
        """Convertir lista de mensajes a un prompt único"""
        prompt_parts = []
        
        for message in messages:
            role = message.get('role', 'user')
            content = message.get('content', '')
            
            if role == 'system':
                prompt_parts.append(f"System: {content}")
            elif role == 'user':
                prompt_parts.append(f"Human: {content}")
            elif role == 'assistant':
                prompt_parts.append(f"Assistant: {content}")
        
        # Agregar prompt para la respuesta del asistente
        prompt_parts.append("Assistant:")
        
        return "\n\n".join(prompt_parts)
    
    def validate_model_name(self, model_name: str) -> bool:
        """Validar si un modelo está disponible"""
        try:
            models_result = self.get_available_models()
            if not models_result['success']:
                return False
            
            available_models = [model['name'] for model in models_result['models']]
            return model_name in available_models
            
        except Exception as e:
            logger.error(f"Validate model name failed: {str(e)}")
            return False
    
    def get_model_capabilities(self, model_name: str) -> Dict[str, Any]:
        """Obtener capacidades de un modelo"""
        try:
            model_info = self.get_model_info(model_name)
            
            if not model_info['success']:
                return {
                    'success': False,
                    'error': model_info['error']
                }
            
            model_data = model_info['model']
            details = model_data.get('details', {})
            
            capabilities = {
                'success': True,
                'model_name': model_name,
                'family': details.get('family', 'unknown'),
                'format': details.get('format', 'unknown'),
                'parameter_size': details.get('parameter_size', 'unknown'),
                'quantization_level': details.get('quantization_level', 'unknown'),
                'supports_chat': True,  # Asumimos que todos los modelos soportan chat
                'supports_embeddings': True,  # Asumimos que todos los modelos soportan embeddings
                'context_length': 4096,  # Valor por defecto
                'max_tokens': 4096
            }
            
            return capabilities
            
        except Exception as e:
            logger.error(f"Get model capabilities failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def estimate_tokens(self, text: str) -> int:
        """Estimar número de tokens en un texto"""
        # Estimación simple: ~4 caracteres por token
        return len(text) // 4
    
    def truncate_messages(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int
    ) -> List[Dict[str, str]]:
        """Truncar mensajes para que no excedan el límite de tokens"""
        total_tokens = 0
        truncated_messages = []
        
        # Procesar mensajes en orden inverso para mantener los más recientes
        for message in reversed(messages):
            content = message.get('content', '')
            message_tokens = self.estimate_tokens(content)
            
            if total_tokens + message_tokens <= max_tokens:
                truncated_messages.insert(0, message)
                total_tokens += message_tokens
            else:
                # Si es el primer mensaje y es muy largo, truncarlo
                if not truncated_messages and message.get('role') == 'system':
                    remaining_tokens = max_tokens - total_tokens
                    if remaining_tokens > 100:  # Mínimo 100 tokens para el sistema
                        truncated_content = content[:remaining_tokens * 4]
                        truncated_message = {
                            'role': message['role'],
                            'content': truncated_content + "... [truncated]"
                        }
                        truncated_messages.insert(0, truncated_message)
                break
        
        return truncated_messages

