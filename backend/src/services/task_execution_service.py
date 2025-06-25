"""
Servicio de ejecución de tareas para agentes autónomos
"""
import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum

from .ollama_service import ollama_service
from .mcp_service import mcp_service, MCPRequest
from .config_service import config_service

logger = logging.getLogger(__name__)

class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class StepStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class TaskStep:
    """Representa un paso en la ejecución de una tarea"""
    id: str
    name: str
    description: str
    status: StepStatus
    tool_id: Optional[str] = None
    tool_method: Optional[str] = None
    tool_params: Optional[Dict[str, Any]] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration: Optional[float] = None

@dataclass
class Task:
    """Representa una tarea ejecutada por un agente"""
    id: str
    title: str
    description: str
    agent_id: str
    conversation_id: str
    user_id: str
    status: TaskStatus
    progress: float = 0.0
    steps: List[TaskStep] = None
    result: Optional[Any] = None
    error_message: Optional[str] = None
    files_generated: List[str] = None
    tools_used: List[str] = None
    created_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.steps is None:
            self.steps = []
        if self.files_generated is None:
            self.files_generated = []
        if self.tools_used is None:
            self.tools_used = []
        if self.created_at is None:
            self.created_at = datetime.now()

class TaskExecutionService:
    """Servicio para ejecutar tareas de agentes de forma autónoma"""
    
    def __init__(self):
        self.running_tasks: Dict[str, Task] = {}
        self.task_history: Dict[str, Task] = {}
        self.progress_callbacks: Dict[str, List[Callable]] = {}
        self.max_concurrent_tasks = 10
        self.task_timeout = 3600  # 1 hora
    
    async def create_task(
        self,
        title: str,
        description: str,
        agent_id: str,
        conversation_id: str,
        user_id: str,
        initial_steps: List[Dict[str, Any]] = None
    ) -> str:
        """Crea una nueva tarea"""
        task_id = str(uuid.uuid4())
        
        task = Task(
            id=task_id,
            title=title,
            description=description,
            agent_id=agent_id,
            conversation_id=conversation_id,
            user_id=user_id,
            status=TaskStatus.PENDING
        )
        
        # Agregar pasos iniciales si se proporcionan
        if initial_steps:
            for i, step_data in enumerate(initial_steps):
                step = TaskStep(
                    id=f"{task_id}_step_{i+1}",
                    name=step_data.get("name", f"Paso {i+1}"),
                    description=step_data.get("description", ""),
                    status=StepStatus.PENDING,
                    tool_id=step_data.get("tool_id"),
                    tool_method=step_data.get("tool_method"),
                    tool_params=step_data.get("tool_params")
                )
                task.steps.append(step)
        
        self.running_tasks[task_id] = task
        logger.info(f"Created task {task_id}: {title}")
        
        return task_id
    
    async def execute_task(self, task_id: str) -> bool:
        """Ejecuta una tarea de forma autónoma"""
        if task_id not in self.running_tasks:
            raise ValueError(f"Task {task_id} not found")
        
        task = self.running_tasks[task_id]
        
        if task.status != TaskStatus.PENDING:
            raise ValueError(f"Task {task_id} is not in pending status")
        
        try:
            task.status = TaskStatus.RUNNING
            task.started_at = datetime.now()
            
            await self._notify_progress(task_id, 0, "Iniciando tarea...")
            
            # Si no hay pasos definidos, generar plan de ejecución
            if not task.steps:
                await self._generate_execution_plan(task)
            
            # Ejecutar pasos secuencialmente
            total_steps = len(task.steps)
            for i, step in enumerate(task.steps):
                if task.status == TaskStatus.CANCELLED:
                    break
                
                await self._execute_step(task, step)
                
                # Actualizar progreso
                progress = ((i + 1) / total_steps) * 100
                task.progress = progress
                
                current_step = step.name if step.status == StepStatus.RUNNING else None
                await self._notify_progress(task_id, progress, current_step)
            
            # Finalizar tarea
            if task.status != TaskStatus.CANCELLED:
                if all(step.status == StepStatus.COMPLETED for step in task.steps):
                    task.status = TaskStatus.COMPLETED
                    task.progress = 100.0
                    await self._generate_task_summary(task)
                else:
                    task.status = TaskStatus.FAILED
                    task.error_message = "Algunos pasos fallaron en la ejecución"
            
            task.completed_at = datetime.now()
            
            # Mover a historial
            self.task_history[task_id] = task
            if task_id in self.running_tasks:
                del self.running_tasks[task_id]
            
            logger.info(f"Task {task_id} completed with status: {task.status}")
            return task.status == TaskStatus.COMPLETED
            
        except Exception as e:
            logger.error(f"Task execution failed: {str(e)}")
            task.status = TaskStatus.FAILED
            task.error_message = str(e)
            task.completed_at = datetime.now()
            
            # Mover a historial
            self.task_history[task_id] = task
            if task_id in self.running_tasks:
                del self.running_tasks[task_id]
            
            return False
    
    async def _generate_execution_plan(self, task: Task):
        """Genera un plan de ejecución usando el agente"""
        try:
            # Obtener información del agente
            agent_info = await self._get_agent_info(task.agent_id)
            
            # Prompt para generar plan de ejecución
            planning_prompt = f"""
            Eres un agente autónomo que debe crear un plan de ejecución para la siguiente tarea:
            
            Título: {task.title}
            Descripción: {task.description}
            
            Herramientas disponibles: {await self._get_available_tools()}
            
            Genera un plan de ejecución detallado con pasos específicos. 
            Cada paso debe incluir:
            - Nombre del paso
            - Descripción detallada
            - Herramienta a usar (si aplica)
            - Método de la herramienta
            - Parámetros necesarios
            
            Responde en formato JSON con la estructura:
            {{
                "steps": [
                    {{
                        "name": "Nombre del paso",
                        "description": "Descripción detallada",
                        "tool_id": "id_herramienta",
                        "tool_method": "metodo",
                        "tool_params": {{"param": "valor"}}
                    }}
                ]
            }}
            """
            
            response = await ollama_service.generate_response(
                model=agent_info.get("model", "llama2"),
                prompt=planning_prompt,
                system_prompt=agent_info.get("system_prompt", ""),
                temperature=0.3
            )
            
            # Parsear respuesta JSON
            try:
                plan_data = json.loads(response)
                steps_data = plan_data.get("steps", [])
                
                for i, step_data in enumerate(steps_data):
                    step = TaskStep(
                        id=f"{task.id}_step_{i+1}",
                        name=step_data.get("name", f"Paso {i+1}"),
                        description=step_data.get("description", ""),
                        status=StepStatus.PENDING,
                        tool_id=step_data.get("tool_id"),
                        tool_method=step_data.get("tool_method"),
                        tool_params=step_data.get("tool_params")
                    )
                    task.steps.append(step)
                
                logger.info(f"Generated execution plan with {len(task.steps)} steps for task {task.id}")
                
            except json.JSONDecodeError:
                # Plan de respaldo si no se puede parsear JSON
                task.steps = [
                    TaskStep(
                        id=f"{task.id}_step_1",
                        name="Análisis de la tarea",
                        description="Analizar los requisitos y planificar la ejecución",
                        status=StepStatus.PENDING
                    ),
                    TaskStep(
                        id=f"{task.id}_step_2",
                        name="Ejecución principal",
                        description="Ejecutar la tarea principal",
                        status=StepStatus.PENDING
                    ),
                    TaskStep(
                        id=f"{task.id}_step_3",
                        name="Finalización",
                        description="Revisar resultados y generar entregables",
                        status=StepStatus.PENDING
                    )
                ]
                
        except Exception as e:
            logger.error(f"Failed to generate execution plan: {str(e)}")
            # Plan de respaldo básico
            task.steps = [
                TaskStep(
                    id=f"{task.id}_step_1",
                    name="Ejecución de tarea",
                    description=task.description,
                    status=StepStatus.PENDING
                )
            ]
    
    async def _execute_step(self, task: Task, step: TaskStep):
        """Ejecuta un paso individual de la tarea"""
        try:
            step.status = StepStatus.RUNNING
            step.started_at = datetime.now()
            
            logger.info(f"Executing step {step.id}: {step.name}")
            
            if step.tool_id and step.tool_method:
                # Ejecutar usando herramienta MCP
                await self._execute_tool_step(task, step)
            else:
                # Ejecutar usando el agente LLM
                await self._execute_llm_step(task, step)
            
            step.status = StepStatus.COMPLETED
            step.completed_at = datetime.now()
            step.duration = (step.completed_at - step.started_at).total_seconds()
            
            # Agregar herramienta a la lista de herramientas usadas
            if step.tool_id and step.tool_id not in task.tools_used:
                task.tools_used.append(step.tool_id)
            
        except Exception as e:
            logger.error(f"Step execution failed: {str(e)}")
            step.status = StepStatus.FAILED
            step.error = str(e)
            step.completed_at = datetime.now()
            if step.started_at:
                step.duration = (step.completed_at - step.started_at).total_seconds()
    
    async def _execute_tool_step(self, task: Task, step: TaskStep):
        """Ejecuta un paso usando una herramienta MCP"""
        request = MCPRequest(
            tool_id=step.tool_id,
            method=step.tool_method,
            params=step.tool_params or {},
            agent_id=task.agent_id,
            task_id=task.id
        )
        
        response = await mcp_service.execute_tool(request)
        
        if response.success:
            step.result = response.result
            logger.info(f"Tool execution successful for step {step.id}")
        else:
            raise Exception(f"Tool execution failed: {response.error}")
    
    async def _execute_llm_step(self, task: Task, step: TaskStep):
        """Ejecuta un paso usando el agente LLM"""
        try:
            # Obtener información del agente
            agent_info = await self._get_agent_info(task.agent_id)
            
            # Construir contexto de la tarea
            context = f"""
            Tarea: {task.title}
            Descripción: {task.description}
            
            Paso actual: {step.name}
            Descripción del paso: {step.description}
            
            Pasos anteriores completados:
            {self._get_previous_steps_context(task, step)}
            
            Ejecuta este paso y proporciona un resultado detallado.
            """
            
            response = await ollama_service.generate_response(
                model=agent_info.get("model", "llama2"),
                prompt=context,
                system_prompt=agent_info.get("system_prompt", ""),
                temperature=agent_info.get("temperature", 0.7)
            )
            
            step.result = {
                "response": response,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            raise Exception(f"LLM execution failed: {str(e)}")
    
    async def _generate_task_summary(self, task: Task):
        """Genera un resumen de la tarea completada"""
        try:
            # Obtener información del agente
            agent_info = await self._get_agent_info(task.agent_id)
            
            # Construir contexto para el resumen
            steps_summary = []
            for step in task.steps:
                steps_summary.append(f"- {step.name}: {step.status.value}")
                if step.result:
                    steps_summary.append(f"  Resultado: {str(step.result)[:200]}...")
            
            summary_prompt = f"""
            Genera un resumen ejecutivo de la tarea completada:
            
            Título: {task.title}
            Descripción: {task.description}
            
            Pasos ejecutados:
            {chr(10).join(steps_summary)}
            
            Herramientas utilizadas: {', '.join(task.tools_used)}
            
            Proporciona un resumen conciso de lo que se logró y los resultados principales.
            """
            
            summary = await ollama_service.generate_response(
                model=agent_info.get("model", "llama2"),
                prompt=summary_prompt,
                system_prompt=agent_info.get("system_prompt", ""),
                temperature=0.3
            )
            
            task.result = {
                "summary": summary,
                "steps_completed": len([s for s in task.steps if s.status == StepStatus.COMPLETED]),
                "total_steps": len(task.steps),
                "tools_used": task.tools_used,
                "files_generated": task.files_generated,
                "execution_time": (task.completed_at - task.started_at).total_seconds() if task.started_at and task.completed_at else 0
            }
            
        except Exception as e:
            logger.error(f"Failed to generate task summary: {str(e)}")
            task.result = {
                "summary": "Tarea completada exitosamente",
                "error": "No se pudo generar resumen detallado"
            }
    
    def _get_previous_steps_context(self, task: Task, current_step: TaskStep) -> str:
        """Obtiene el contexto de pasos anteriores"""
        context_lines = []
        for step in task.steps:
            if step.id == current_step.id:
                break
            if step.status == StepStatus.COMPLETED:
                context_lines.append(f"- {step.name}: Completado")
                if step.result:
                    result_str = str(step.result)[:100]
                    context_lines.append(f"  Resultado: {result_str}...")
        
        return "\n".join(context_lines) if context_lines else "Ningún paso anterior completado"
    
    async def _get_agent_info(self, agent_id: str) -> Dict[str, Any]:
        """Obtiene información del agente"""
        # En una implementación real, esto consultaría la base de datos
        return {
            "id": agent_id,
            "model": "llama2",
            "system_prompt": "Eres un asistente útil y eficiente.",
            "temperature": 0.7,
            "max_tokens": 4096
        }
    
    async def _get_available_tools(self) -> List[str]:
        """Obtiene lista de herramientas disponibles"""
        tools = mcp_service.list_tools()
        return [f"{tool['id']}: {tool['description']}" for tool in tools]
    
    async def _notify_progress(self, task_id: str, progress: float, current_step: str = None):
        """Notifica el progreso de la tarea"""
        if task_id in self.progress_callbacks:
            for callback in self.progress_callbacks[task_id]:
                try:
                    await callback(task_id, progress, current_step)
                except Exception as e:
                    logger.error(f"Progress callback failed: {str(e)}")
    
    def subscribe_to_progress(self, task_id: str, callback: Callable):
        """Suscribe a actualizaciones de progreso de una tarea"""
        if task_id not in self.progress_callbacks:
            self.progress_callbacks[task_id] = []
        self.progress_callbacks[task_id].append(callback)
    
    def unsubscribe_from_progress(self, task_id: str, callback: Callable):
        """Desuscribe de actualizaciones de progreso"""
        if task_id in self.progress_callbacks:
            try:
                self.progress_callbacks[task_id].remove(callback)
                if not self.progress_callbacks[task_id]:
                    del self.progress_callbacks[task_id]
            except ValueError:
                pass
    
    async def cancel_task(self, task_id: str) -> bool:
        """Cancela una tarea en ejecución"""
        if task_id in self.running_tasks:
            task = self.running_tasks[task_id]
            task.status = TaskStatus.CANCELLED
            task.completed_at = datetime.now()
            
            # Mover a historial
            self.task_history[task_id] = task
            del self.running_tasks[task_id]
            
            logger.info(f"Task {task_id} cancelled")
            return True
        
        return False
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """Obtiene una tarea por ID"""
        if task_id in self.running_tasks:
            return self.running_tasks[task_id]
        elif task_id in self.task_history:
            return self.task_history[task_id]
        return None
    
    def list_tasks(self, user_id: str = None, status: TaskStatus = None) -> List[Dict[str, Any]]:
        """Lista tareas con filtros opcionales"""
        all_tasks = {**self.running_tasks, **self.task_history}
        
        filtered_tasks = []
        for task in all_tasks.values():
            if user_id and task.user_id != user_id:
                continue
            if status and task.status != status:
                continue
            
            task_dict = asdict(task)
            # Convertir datetime a string para serialización JSON
            for field in ['created_at', 'started_at', 'completed_at']:
                if task_dict[field]:
                    task_dict[field] = task_dict[field].isoformat()
            
            # Convertir steps
            for step in task_dict['steps']:
                for field in ['started_at', 'completed_at']:
                    if step[field]:
                        step[field] = step[field].isoformat()
                step['status'] = step['status'].value if hasattr(step['status'], 'value') else step['status']
            
            task_dict['status'] = task_dict['status'].value if hasattr(task_dict['status'], 'value') else task_dict['status']
            filtered_tasks.append(task_dict)
        
        return filtered_tasks
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del sistema de tareas"""
        all_tasks = {**self.running_tasks, **self.task_history}
        
        stats = {
            "total_tasks": len(all_tasks),
            "running_tasks": len(self.running_tasks),
            "completed_tasks": len([t for t in all_tasks.values() if t.status == TaskStatus.COMPLETED]),
            "failed_tasks": len([t for t in all_tasks.values() if t.status == TaskStatus.FAILED]),
            "cancelled_tasks": len([t for t in all_tasks.values() if t.status == TaskStatus.CANCELLED]),
            "average_execution_time": 0,
            "success_rate": 0
        }
        
        completed_tasks = [t for t in all_tasks.values() if t.status == TaskStatus.COMPLETED and t.started_at and t.completed_at]
        if completed_tasks:
            total_time = sum((t.completed_at - t.started_at).total_seconds() for t in completed_tasks)
            stats["average_execution_time"] = total_time / len(completed_tasks)
        
        if stats["total_tasks"] > 0:
            stats["success_rate"] = (stats["completed_tasks"] / stats["total_tasks"]) * 100
        
        return stats

# Instancia global del servicio de ejecución de tareas
task_execution_service = TaskExecutionService()

