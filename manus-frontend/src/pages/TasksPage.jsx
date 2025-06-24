import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Progress } from '@/components/ui/progress'
import { useAuth } from '@/hooks/useAuth'
import { useSocket } from '@/contexts/SocketContext'
import {
  CheckSquare,
  Clock,
  AlertCircle,
  CheckCircle,
  XCircle,
  Play,
  Pause,
  Search,
  Filter,
  Download,
  Eye,
  Bot,
  User,
  Calendar,
  Timer,
  Activity
} from 'lucide-react'

const taskStatuses = {
  pending: { label: 'Pendiente', color: 'bg-yellow-100 text-yellow-800', icon: Clock },
  running: { label: 'Ejecutando', color: 'bg-blue-100 text-blue-800', icon: Play },
  completed: { label: 'Completada', color: 'bg-green-100 text-green-800', icon: CheckCircle },
  failed: { label: 'Fallida', color: 'bg-red-100 text-red-800', icon: XCircle },
  cancelled: { label: 'Cancelada', color: 'bg-gray-100 text-gray-800', icon: Pause }
}

export default function TasksPage() {
  const { user } = useAuth()
  const { socket, subscribeToTask, unsubscribeFromTask } = useSocket()
  const [tasks, setTasks] = useState([])
  const [filteredTasks, setFilteredTasks] = useState([])
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedTask, setSelectedTask] = useState(null)
  const [isDetailDialogOpen, setIsDetailDialogOpen] = useState(false)
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('all')
  const [statusFilter, setStatusFilter] = useState('all')

  useEffect(() => {
    loadTasks()
  }, [])

  useEffect(() => {
    filterTasks()
  }, [tasks, searchQuery, activeTab, statusFilter])

  // Socket event listeners for real-time task updates
  useEffect(() => {
    if (socket) {
      socket.on('task_updated', handleTaskUpdate)
      socket.on('task_progress', handleTaskProgress)
      
      return () => {
        socket.off('task_updated', handleTaskUpdate)
        socket.off('task_progress', handleTaskProgress)
      }
    }
  }, [socket])

  const loadTasks = async () => {
    try {
      // Simulated API call
      const mockTasks = [
        {
          id: '1',
          title: 'Análisis de datos de ventas Q4',
          description: 'Analizar los datos de ventas del último trimestre y generar un reporte con insights y recomendaciones.',
          status: 'completed',
          agent_id: '1',
          agent_name: 'Analista de Datos',
          conversation_id: '1',
          created_at: new Date(Date.now() - 3600000).toISOString(),
          started_at: new Date(Date.now() - 3500000).toISOString(),
          completed_at: new Date(Date.now() - 1800000).toISOString(),
          progress: 100,
          result: 'Análisis completado exitosamente. Se identificaron 3 tendencias principales y 5 oportunidades de mejora.',
          steps: [
            { id: 1, name: 'Cargar datos', status: 'completed', duration: 30 },
            { id: 2, name: 'Limpiar datos', status: 'completed', duration: 120 },
            { id: 3, name: 'Análisis estadístico', status: 'completed', duration: 300 },
            { id: 4, name: 'Generar visualizaciones', status: 'completed', duration: 180 },
            { id: 5, name: 'Crear reporte', status: 'completed', duration: 240 }
          ],
          tools_used: ['pandas', 'matplotlib', 'seaborn', 'jupyter'],
          files_generated: ['sales_analysis_q4.pdf', 'charts.png', 'data_clean.csv']
        },
        {
          id: '2',
          title: 'Desarrollo de API REST',
          description: 'Crear una API REST para gestión de usuarios con autenticación JWT.',
          status: 'running',
          agent_id: '3',
          agent_name: 'Programador',
          conversation_id: '2',
          created_at: new Date(Date.now() - 1800000).toISOString(),
          started_at: new Date(Date.now() - 1200000).toISOString(),
          progress: 65,
          current_step: 'Implementando endpoints de autenticación',
          steps: [
            { id: 1, name: 'Configurar proyecto', status: 'completed', duration: 180 },
            { id: 2, name: 'Diseñar modelos', status: 'completed', duration: 240 },
            { id: 3, name: 'Implementar autenticación', status: 'running', duration: null },
            { id: 4, name: 'Crear endpoints CRUD', status: 'pending', duration: null },
            { id: 5, name: 'Documentar API', status: 'pending', duration: null },
            { id: 6, name: 'Testing', status: 'pending', duration: null }
          ],
          tools_used: ['flask', 'sqlalchemy', 'jwt', 'pytest'],
          files_generated: ['app.py', 'models.py', 'auth.py']
        },
        {
          id: '3',
          title: 'Optimización de consultas SQL',
          description: 'Revisar y optimizar las consultas SQL más lentas de la base de datos.',
          status: 'failed',
          agent_id: '2',
          agent_name: 'Analista de Datos',
          conversation_id: '3',
          created_at: new Date(Date.now() - 7200000).toISOString(),
          started_at: new Date(Date.now() - 6900000).toISOString(),
          completed_at: new Date(Date.now() - 6600000).toISOString(),
          progress: 30,
          error_message: 'Error de conexión a la base de datos. Credenciales inválidas.',
          steps: [
            { id: 1, name: 'Conectar a BD', status: 'failed', duration: 10 },
            { id: 2, name: 'Analizar consultas', status: 'pending', duration: null },
            { id: 3, name: 'Optimizar índices', status: 'pending', duration: null }
          ],
          tools_used: ['postgresql', 'explain'],
          files_generated: []
        },
        {
          id: '4',
          title: 'Generar documentación técnica',
          description: 'Crear documentación completa del sistema incluyendo arquitectura y APIs.',
          status: 'pending',
          agent_id: '1',
          agent_name: 'Asistente General',
          conversation_id: '4',
          created_at: new Date(Date.now() - 300000).toISOString(),
          progress: 0,
          steps: [
            { id: 1, name: 'Analizar código fuente', status: 'pending', duration: null },
            { id: 2, name: 'Documentar arquitectura', status: 'pending', duration: null },
            { id: 3, name: 'Documentar APIs', status: 'pending', duration: null },
            { id: 4, name: 'Generar diagramas', status: 'pending', duration: null }
          ],
          tools_used: [],
          files_generated: []
        }
      ]
      
      setTasks(mockTasks)
    } catch (error) {
      console.error('Error loading tasks:', error)
    } finally {
      setLoading(false)
    }
  }

  const filterTasks = () => {
    let filtered = tasks

    // Filter by tab
    switch (activeTab) {
      case 'running':
        filtered = filtered.filter(task => task.status === 'running')
        break
      case 'completed':
        filtered = filtered.filter(task => task.status === 'completed')
        break
      case 'failed':
        filtered = filtered.filter(task => task.status === 'failed')
        break
      default:
        // 'all' - no additional filtering
        break
    }

    // Filter by status
    if (statusFilter !== 'all') {
      filtered = filtered.filter(task => task.status === statusFilter)
    }

    // Filter by search query
    if (searchQuery) {
      filtered = filtered.filter(task =>
        task.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        task.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
        task.agent_name.toLowerCase().includes(searchQuery.toLowerCase())
      )
    }

    setFilteredTasks(filtered)
  }

  const handleTaskUpdate = (taskData) => {
    setTasks(prev => prev.map(task =>
      task.id === taskData.task.id ? { ...task, ...taskData.task } : task
    ))
  }

  const handleTaskProgress = (progressData) => {
    setTasks(prev => prev.map(task =>
      task.id === progressData.task_id 
        ? { ...task, progress: progressData.progress, current_step: progressData.current_step }
        : task
    ))
  }

  const openTaskDetail = (task) => {
    setSelectedTask(task)
    setIsDetailDialogOpen(true)
    if (task.status === 'running') {
      subscribeToTask(task.id)
    }
  }

  const closeTaskDetail = () => {
    if (selectedTask && selectedTask.status === 'running') {
      unsubscribeFromTask(selectedTask.id)
    }
    setSelectedTask(null)
    setIsDetailDialogOpen(false)
  }

  const cancelTask = async (taskId) => {
    if (window.confirm('¿Estás seguro de que quieres cancelar esta tarea?')) {
      try {
        setTasks(prev => prev.map(task =>
          task.id === taskId ? { ...task, status: 'cancelled' } : task
        ))
      } catch (error) {
        console.error('Error cancelling task:', error)
      }
    }
  }

  const retryTask = async (taskId) => {
    try {
      setTasks(prev => prev.map(task =>
        task.id === taskId ? { ...task, status: 'pending', progress: 0, error_message: null } : task
      ))
    } catch (error) {
      console.error('Error retrying task:', error)
    }
  }

  const formatDuration = (seconds) => {
    if (!seconds) return 'N/A'
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    const secs = seconds % 60
    
    if (hours > 0) {
      return `${hours}h ${minutes}m ${secs}s`
    } else if (minutes > 0) {
      return `${minutes}m ${secs}s`
    } else {
      return `${secs}s`
    }
  }

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString('es-ES', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const getTaskDuration = (task) => {
    if (!task.started_at) return null
    
    const start = new Date(task.started_at)
    const end = task.completed_at ? new Date(task.completed_at) : new Date()
    
    return Math.floor((end - start) / 1000)
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-primary"></div>
      </div>
    )
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Tareas</h1>
          <p className="text-muted-foreground">
            Seguimiento de tareas ejecutadas por agentes
          </p>
        </div>
        
        <div className="flex items-center space-x-2">
          <Button variant="outline">
            <Download className="w-4 h-4 mr-2" />
            Exportar
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <CheckSquare className="w-5 h-5 text-primary" />
              <div>
                <p className="text-sm font-medium">Total Tareas</p>
                <p className="text-2xl font-bold">{tasks.length}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <Play className="w-5 h-5 text-blue-500" />
              <div>
                <p className="text-sm font-medium">En Ejecución</p>
                <p className="text-2xl font-bold">
                  {tasks.filter(t => t.status === 'running').length}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <CheckCircle className="w-5 h-5 text-green-500" />
              <div>
                <p className="text-sm font-medium">Completadas</p>
                <p className="text-2xl font-bold">
                  {tasks.filter(t => t.status === 'completed').length}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <XCircle className="w-5 h-5 text-red-500" />
              <div>
                <p className="text-sm font-medium">Fallidas</p>
                <p className="text-2xl font-bold">
                  {tasks.filter(t => t.status === 'failed').length}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Search and Filters */}
      <div className="flex items-center space-x-4">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Buscar tareas..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>
        
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="px-3 py-2 border border-input rounded-md"
        >
          <option value="all">Todos los estados</option>
          <option value="pending">Pendientes</option>
          <option value="running">En ejecución</option>
          <option value="completed">Completadas</option>
          <option value="failed">Fallidas</option>
          <option value="cancelled">Canceladas</option>
        </select>
        
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList>
            <TabsTrigger value="all">Todas</TabsTrigger>
            <TabsTrigger value="running">Ejecutando</TabsTrigger>
            <TabsTrigger value="completed">Completadas</TabsTrigger>
            <TabsTrigger value="failed">Fallidas</TabsTrigger>
          </TabsList>
        </Tabs>
      </div>

      {/* Tasks List */}
      <div className="space-y-4">
        {filteredTasks.map((task) => {
          const statusConfig = taskStatuses[task.status]
          const StatusIcon = statusConfig.icon
          const duration = getTaskDuration(task)
          
          return (
            <Card key={task.id} className="hover:shadow-md transition-shadow">
              <CardContent className="p-6">
                <div className="flex items-start justify-between">
                  <div className="flex-1 space-y-3">
                    {/* Header */}
                    <div className="flex items-start justify-between">
                      <div>
                        <h3 className="text-lg font-semibold">{task.title}</h3>
                        <p className="text-sm text-muted-foreground mt-1">
                          {task.description}
                        </p>
                      </div>
                      
                      <div className="flex items-center space-x-2">
                        <Badge className={statusConfig.color}>
                          <StatusIcon className="w-3 h-3 mr-1" />
                          {statusConfig.label}
                        </Badge>
                        
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => openTaskDetail(task)}
                        >
                          <Eye className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>
                    
                    {/* Progress */}
                    {task.status === 'running' && (
                      <div className="space-y-2">
                        <div className="flex items-center justify-between text-sm">
                          <span>Progreso: {task.progress}%</span>
                          {task.current_step && (
                            <span className="text-muted-foreground">
                              {task.current_step}
                            </span>
                          )}
                        </div>
                        <Progress value={task.progress} className="h-2" />
                      </div>
                    )}
                    
                    {/* Error Message */}
                    {task.status === 'failed' && task.error_message && (
                      <div className="bg-red-50 border border-red-200 rounded-md p-3">
                        <div className="flex items-center space-x-2">
                          <AlertCircle className="w-4 h-4 text-red-500" />
                          <span className="text-sm text-red-700">
                            {task.error_message}
                          </span>
                        </div>
                      </div>
                    )}
                    
                    {/* Meta Information */}
                    <div className="flex items-center space-x-6 text-sm text-muted-foreground">
                      <div className="flex items-center space-x-1">
                        <Bot className="w-4 h-4" />
                        <span>{task.agent_name}</span>
                      </div>
                      
                      <div className="flex items-center space-x-1">
                        <Calendar className="w-4 h-4" />
                        <span>{formatDate(task.created_at)}</span>
                      </div>
                      
                      {duration && (
                        <div className="flex items-center space-x-1">
                          <Timer className="w-4 h-4" />
                          <span>{formatDuration(duration)}</span>
                        </div>
                      )}
                      
                      {task.tools_used.length > 0 && (
                        <div className="flex items-center space-x-1">
                          <Activity className="w-4 h-4" />
                          <span>{task.tools_used.length} herramientas</span>
                        </div>
                      )}
                    </div>
                    
                    {/* Actions */}
                    <div className="flex items-center space-x-2">
                      {task.status === 'running' && (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => cancelTask(task.id)}
                        >
                          <Pause className="w-4 h-4 mr-2" />
                          Cancelar
                        </Button>
                      )}
                      
                      {task.status === 'failed' && (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => retryTask(task.id)}
                        >
                          <Play className="w-4 h-4 mr-2" />
                          Reintentar
                        </Button>
                      )}
                      
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => openTaskDetail(task)}
                      >
                        <Eye className="w-4 h-4 mr-2" />
                        Ver Detalles
                      </Button>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          )
        })}
      </div>

      {filteredTasks.length === 0 && (
        <div className="text-center py-12">
          <CheckSquare className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
          <h3 className="text-lg font-semibold mb-2">No se encontraron tareas</h3>
          <p className="text-muted-foreground">
            {searchQuery ? 'Intenta con otros términos de búsqueda' : 'Las tareas aparecerán aquí cuando los agentes las ejecuten'}
          </p>
        </div>
      )}

      {/* Task Detail Dialog */}
      <Dialog open={isDetailDialogOpen} onOpenChange={closeTaskDetail}>
        <DialogContent className="max-w-4xl max-h-[80vh]">
          <DialogHeader>
            <DialogTitle className="flex items-center space-x-2">
              <CheckSquare className="w-5 h-5" />
              <span>{selectedTask?.title}</span>
            </DialogTitle>
            <DialogDescription>
              Detalles completos de la tarea
            </DialogDescription>
          </DialogHeader>
          
          {selectedTask && (
            <ScrollArea className="max-h-[60vh]">
              <div className="space-y-6">
                {/* Status and Progress */}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label className="text-sm font-medium">Estado</Label>
                    <div className="mt-1">
                      <Badge className={taskStatuses[selectedTask.status].color}>
                        {taskStatuses[selectedTask.status].label}
                      </Badge>
                    </div>
                  </div>
                  
                  <div>
                    <Label className="text-sm font-medium">Progreso</Label>
                    <div className="mt-1">
                      <div className="flex items-center space-x-2">
                        <Progress value={selectedTask.progress} className="flex-1" />
                        <span className="text-sm">{selectedTask.progress}%</span>
                      </div>
                    </div>
                  </div>
                </div>
                
                {/* Description */}
                <div>
                  <Label className="text-sm font-medium">Descripción</Label>
                  <p className="mt-1 text-sm text-muted-foreground">
                    {selectedTask.description}
                  </p>
                </div>
                
                {/* Steps */}
                <div>
                  <Label className="text-sm font-medium">Pasos de Ejecución</Label>
                  <div className="mt-2 space-y-2">
                    {selectedTask.steps.map((step, index) => {
                      const stepStatusConfig = taskStatuses[step.status] || taskStatuses.pending
                      const StepIcon = stepStatusConfig.icon
                      
                      return (
                        <div key={step.id} className="flex items-center space-x-3 p-3 border rounded-md">
                          <div className="flex items-center justify-center w-6 h-6 rounded-full bg-muted">
                            <span className="text-xs font-medium">{index + 1}</span>
                          </div>
                          
                          <div className="flex-1">
                            <div className="flex items-center space-x-2">
                              <span className="text-sm font-medium">{step.name}</span>
                              <Badge variant="outline" className={stepStatusConfig.color}>
                                <StepIcon className="w-3 h-3 mr-1" />
                                {stepStatusConfig.label}
                              </Badge>
                            </div>
                            {step.duration && (
                              <p className="text-xs text-muted-foreground mt-1">
                                Duración: {formatDuration(step.duration)}
                              </p>
                            )}
                          </div>
                        </div>
                      )
                    })}
                  </div>
                </div>
                
                {/* Tools Used */}
                {selectedTask.tools_used.length > 0 && (
                  <div>
                    <Label className="text-sm font-medium">Herramientas Utilizadas</Label>
                    <div className="mt-2 flex flex-wrap gap-2">
                      {selectedTask.tools_used.map((tool) => (
                        <Badge key={tool} variant="outline">
                          {tool}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}
                
                {/* Files Generated */}
                {selectedTask.files_generated.length > 0 && (
                  <div>
                    <Label className="text-sm font-medium">Archivos Generados</Label>
                    <div className="mt-2 space-y-1">
                      {selectedTask.files_generated.map((file) => (
                        <div key={file} className="flex items-center space-x-2 text-sm">
                          <span>{file}</span>
                          <Button variant="ghost" size="sm">
                            <Download className="w-3 h-3" />
                          </Button>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                
                {/* Result */}
                {selectedTask.result && (
                  <div>
                    <Label className="text-sm font-medium">Resultado</Label>
                    <div className="mt-1 p-3 bg-muted rounded-md">
                      <p className="text-sm">{selectedTask.result}</p>
                    </div>
                  </div>
                )}
                
                {/* Error Message */}
                {selectedTask.error_message && (
                  <div>
                    <Label className="text-sm font-medium">Error</Label>
                    <div className="mt-1 p-3 bg-red-50 border border-red-200 rounded-md">
                      <p className="text-sm text-red-700">{selectedTask.error_message}</p>
                    </div>
                  </div>
                )}
                
                {/* Timestamps */}
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <Label className="text-sm font-medium">Creada</Label>
                    <p className="mt-1 text-muted-foreground">
                      {formatDate(selectedTask.created_at)}
                    </p>
                  </div>
                  
                  {selectedTask.started_at && (
                    <div>
                      <Label className="text-sm font-medium">Iniciada</Label>
                      <p className="mt-1 text-muted-foreground">
                        {formatDate(selectedTask.started_at)}
                      </p>
                    </div>
                  )}
                  
                  {selectedTask.completed_at && (
                    <div>
                      <Label className="text-sm font-medium">Completada</Label>
                      <p className="mt-1 text-muted-foreground">
                        {formatDate(selectedTask.completed_at)}
                      </p>
                    </div>
                  )}
                  
                  {getTaskDuration(selectedTask) && (
                    <div>
                      <Label className="text-sm font-medium">Duración Total</Label>
                      <p className="mt-1 text-muted-foreground">
                        {formatDuration(getTaskDuration(selectedTask))}
                      </p>
                    </div>
                  )}
                </div>
              </div>
            </ScrollArea>
          )}
        </DialogContent>
      </Dialog>
    </div>
  )
}

