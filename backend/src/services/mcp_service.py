"""
Servicio MCP (Model Context Protocol) para integración con herramientas Docker
"""
import asyncio
import json
import logging
import docker
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class MCPTool:
    """Representa una herramienta MCP"""
    id: str
    name: str
    description: str
    docker_image: str
    status: str  # available, installed, running, error
    config_schema: Dict[str, Any]
    capabilities: List[str]
    container_id: Optional[str] = None
    port: Optional[int] = None

@dataclass
class MCPRequest:
    """Representa una solicitud a una herramienta MCP"""
    tool_id: str
    method: str
    params: Dict[str, Any]
    agent_id: str
    task_id: Optional[str] = None

@dataclass
class MCPResponse:
    """Representa una respuesta de una herramienta MCP"""
    success: bool
    result: Any = None
    error: Optional[str] = None
    execution_time: float = 0.0

class MCPService:
    """Servicio para gestionar herramientas MCP"""
    
    def __init__(self):
        self.docker_client = docker.from_env()
        self.tools: Dict[str, MCPTool] = {}
        self.running_containers: Dict[str, str] = {}  # tool_id -> container_id
        self.base_port = 8000
        self.network_name = "mcp-network"
        self._ensure_network()
        self._load_available_tools()
    
    def _ensure_network(self):
        """Asegura que la red Docker para MCP existe"""
        try:
            self.docker_client.networks.get(self.network_name)
        except docker.errors.NotFound:
            self.docker_client.networks.create(
                self.network_name,
                driver="bridge"
            )
            logger.info(f"Created Docker network: {self.network_name}")
    
    def _load_available_tools(self):
        """Carga las herramientas MCP disponibles"""
        # Herramientas MCP predefinidas del catálogo Docker
        predefined_tools = [
            {
                "id": "github",
                "name": "GitHub",
                "description": "Gestión de repositorios, operaciones de archivos y integración con GitHub API",
                "docker_image": "docker.io/mcp/github:latest",
                "config_schema": {
                    "github_token": {"type": "string", "required": True, "description": "GitHub Personal Access Token"},
                    "default_org": {"type": "string", "required": False, "description": "Organización por defecto"}
                },
                "capabilities": ["read_repos", "create_issues", "manage_files", "webhooks"]
            },
            {
                "id": "filesystem",
                "name": "Filesystem",
                "description": "Operaciones seguras de archivos con controles de acceso configurables",
                "docker_image": "docker.io/mcp/filesystem:latest",
                "config_schema": {
                    "allowed_paths": {"type": "array", "required": True, "description": "Rutas permitidas"},
                    "max_file_size": {"type": "number", "required": False, "description": "Tamaño máximo de archivo (MB)"}
                },
                "capabilities": ["read_files", "write_files", "list_directories", "file_search"]
            },
            {
                "id": "postgresql",
                "name": "PostgreSQL",
                "description": "Acceso de solo lectura a bases de datos con inspección de esquemas",
                "docker_image": "docker.io/mcp/postgresql:latest",
                "config_schema": {
                    "connection_string": {"type": "string", "required": True, "description": "Cadena de conexión PostgreSQL"},
                    "read_only": {"type": "boolean", "required": False, "description": "Modo solo lectura"}
                },
                "capabilities": ["query_data", "inspect_schema", "explain_queries"]
            },
            {
                "id": "puppeteer",
                "name": "Puppeteer",
                "description": "Automatización de navegador y web scraping",
                "docker_image": "docker.io/mcp/puppeteer:latest",
                "config_schema": {
                    "headless": {"type": "boolean", "required": False, "description": "Ejecutar en modo headless"},
                    "timeout": {"type": "number", "required": False, "description": "Timeout en segundos"}
                },
                "capabilities": ["navigate_pages", "extract_data", "take_screenshots", "fill_forms"]
            },
            {
                "id": "memory",
                "name": "Memory",
                "description": "Sistema de memoria persistente basado en grafos de conocimiento",
                "docker_image": "docker.io/mcp/memory:latest",
                "config_schema": {
                    "storage_path": {"type": "string", "required": True, "description": "Ruta de almacenamiento"},
                    "max_memories": {"type": "number", "required": False, "description": "Máximo número de memorias"}
                },
                "capabilities": ["store_memories", "retrieve_memories", "semantic_search", "knowledge_graph"]
            }
        ]
        
        for tool_data in predefined_tools:
            tool = MCPTool(
                id=tool_data["id"],
                name=tool_data["name"],
                description=tool_data["description"],
                docker_image=tool_data["docker_image"],
                status="available",
                config_schema=tool_data["config_schema"],
                capabilities=tool_data["capabilities"]
            )
            self.tools[tool.id] = tool
        
        logger.info(f"Loaded {len(self.tools)} MCP tools")
    
    async def install_tool(self, tool_id: str, config: Dict[str, Any] = None) -> bool:
        """Instala una herramienta MCP"""
        if tool_id not in self.tools:
            raise ValueError(f"Tool {tool_id} not found")
        
        tool = self.tools[tool_id]
        
        try:
            # Pull Docker image
            logger.info(f"Pulling Docker image: {tool.docker_image}")
            self.docker_client.images.pull(tool.docker_image)
            
            tool.status = "installed"
            logger.info(f"Successfully installed tool: {tool_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to install tool {tool_id}: {str(e)}")
            tool.status = "error"
            return False
    
    async def start_tool(self, tool_id: str, config: Dict[str, Any] = None) -> bool:
        """Inicia una herramienta MCP"""
        if tool_id not in self.tools:
            raise ValueError(f"Tool {tool_id} not found")
        
        tool = self.tools[tool_id]
        
        if tool.status not in ["installed", "stopped"]:
            raise ValueError(f"Tool {tool_id} cannot be started (status: {tool.status})")
        
        try:
            # Asignar puerto
            port = self._get_next_port()
            
            # Configurar variables de entorno
            environment = {}
            if config:
                for key, value in config.items():
                    environment[key.upper()] = str(value)
            
            # Crear y ejecutar contenedor
            container = self.docker_client.containers.run(
                tool.docker_image,
                detach=True,
                ports={f'{port}/tcp': port},
                environment=environment,
                network=self.network_name,
                name=f"mcp-{tool_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                restart_policy={"Name": "unless-stopped"}
            )
            
            tool.container_id = container.id
            tool.port = port
            tool.status = "running"
            self.running_containers[tool_id] = container.id
            
            logger.info(f"Started tool {tool_id} on port {port}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start tool {tool_id}: {str(e)}")
            tool.status = "error"
            return False
    
    async def stop_tool(self, tool_id: str) -> bool:
        """Detiene una herramienta MCP"""
        if tool_id not in self.tools:
            raise ValueError(f"Tool {tool_id} not found")
        
        tool = self.tools[tool_id]
        
        if tool.status != "running":
            return True
        
        try:
            if tool.container_id:
                container = self.docker_client.containers.get(tool.container_id)
                container.stop()
                container.remove()
            
            tool.container_id = None
            tool.port = None
            tool.status = "installed"
            
            if tool_id in self.running_containers:
                del self.running_containers[tool_id]
            
            logger.info(f"Stopped tool: {tool_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop tool {tool_id}: {str(e)}")
            return False
    
    async def execute_tool(self, request: MCPRequest) -> MCPResponse:
        """Ejecuta una herramienta MCP"""
        start_time = datetime.now()
        
        if request.tool_id not in self.tools:
            return MCPResponse(
                success=False,
                error=f"Tool {request.tool_id} not found"
            )
        
        tool = self.tools[request.tool_id]
        
        if tool.status != "running":
            return MCPResponse(
                success=False,
                error=f"Tool {request.tool_id} is not running"
            )
        
        try:
            # Simular ejecución de herramienta MCP
            # En una implementación real, esto haría una llamada HTTP al contenedor
            result = await self._simulate_tool_execution(tool, request)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return MCPResponse(
                success=True,
                result=result,
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"Tool execution failed: {str(e)}")
            
            return MCPResponse(
                success=False,
                error=str(e),
                execution_time=execution_time
            )
    
    async def _simulate_tool_execution(self, tool: MCPTool, request: MCPRequest) -> Any:
        """Simula la ejecución de una herramienta MCP"""
        # Simulación basada en el tipo de herramienta
        if tool.id == "github":
            if request.method == "list_repos":
                return {
                    "repositories": [
                        {"name": "manus-system", "url": "https://github.com/user/manus-system"},
                        {"name": "ai-tools", "url": "https://github.com/user/ai-tools"}
                    ]
                }
            elif request.method == "create_issue":
                return {
                    "issue_id": 123,
                    "url": "https://github.com/user/repo/issues/123",
                    "title": request.params.get("title", "New Issue")
                }
        
        elif tool.id == "filesystem":
            if request.method == "read_file":
                return {
                    "content": f"File content for {request.params.get('path', 'unknown')}",
                    "size": 1024,
                    "modified": datetime.now().isoformat()
                }
            elif request.method == "list_directory":
                return {
                    "files": [
                        {"name": "file1.txt", "type": "file", "size": 1024},
                        {"name": "folder1", "type": "directory", "size": 0}
                    ]
                }
        
        elif tool.id == "postgresql":
            if request.method == "query":
                return {
                    "rows": [
                        {"id": 1, "name": "John Doe", "email": "john@example.com"},
                        {"id": 2, "name": "Jane Smith", "email": "jane@example.com"}
                    ],
                    "count": 2
                }
        
        elif tool.id == "puppeteer":
            if request.method == "navigate":
                return {
                    "url": request.params.get("url"),
                    "title": "Page Title",
                    "status": 200
                }
            elif request.method == "screenshot":
                return {
                    "screenshot_path": "/tmp/screenshot.png",
                    "width": 1920,
                    "height": 1080
                }
        
        elif tool.id == "memory":
            if request.method == "store":
                return {
                    "memory_id": "mem_123",
                    "stored": True,
                    "timestamp": datetime.now().isoformat()
                }
            elif request.method == "search":
                return {
                    "memories": [
                        {"id": "mem_123", "content": "Relevant memory", "score": 0.95},
                        {"id": "mem_456", "content": "Another memory", "score": 0.87}
                    ]
                }
        
        # Respuesta por defecto
        return {
            "method": request.method,
            "params": request.params,
            "timestamp": datetime.now().isoformat(),
            "tool": tool.id
        }
    
    def _get_next_port(self) -> int:
        """Obtiene el siguiente puerto disponible"""
        used_ports = {tool.port for tool in self.tools.values() if tool.port}
        port = self.base_port
        while port in used_ports:
            port += 1
        return port
    
    def get_tool_status(self, tool_id: str) -> Dict[str, Any]:
        """Obtiene el estado de una herramienta"""
        if tool_id not in self.tools:
            raise ValueError(f"Tool {tool_id} not found")
        
        tool = self.tools[tool_id]
        
        status = {
            "id": tool.id,
            "name": tool.name,
            "status": tool.status,
            "capabilities": tool.capabilities,
            "port": tool.port,
            "container_id": tool.container_id
        }
        
        if tool.container_id:
            try:
                container = self.docker_client.containers.get(tool.container_id)
                status["container_status"] = container.status
                status["container_logs"] = container.logs(tail=10).decode('utf-8')
            except:
                status["container_status"] = "unknown"
        
        return status
    
    def list_tools(self) -> List[Dict[str, Any]]:
        """Lista todas las herramientas disponibles"""
        return [
            {
                "id": tool.id,
                "name": tool.name,
                "description": tool.description,
                "status": tool.status,
                "capabilities": tool.capabilities,
                "config_schema": tool.config_schema
            }
            for tool in self.tools.values()
        ]
    
    def get_tool_logs(self, tool_id: str, lines: int = 100) -> str:
        """Obtiene los logs de una herramienta"""
        if tool_id not in self.tools:
            raise ValueError(f"Tool {tool_id} not found")
        
        tool = self.tools[tool_id]
        
        if not tool.container_id:
            return "Tool is not running"
        
        try:
            container = self.docker_client.containers.get(tool.container_id)
            logs = container.logs(tail=lines).decode('utf-8')
            return logs
        except Exception as e:
            return f"Error retrieving logs: {str(e)}"
    
    async def cleanup(self):
        """Limpia recursos y detiene todos los contenedores"""
        for tool_id in list(self.running_containers.keys()):
            await self.stop_tool(tool_id)
        
        logger.info("MCP Service cleanup completed")

# Instancia global del servicio MCP
mcp_service = MCPService()

