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
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Switch } from '@/components/ui/switch'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Progress } from '@/components/ui/progress'
import { useAuth } from '@/hooks/useAuth'
import {
  Settings,
  Users,
  Activity,
  Database,
  Server,
  Shield,
  AlertTriangle,
  CheckCircle,
  XCircle,
  TrendingUp,
  TrendingDown,
  Cpu,
  HardDrive,
  Network,
  Zap,
  Eye,
  Edit,
  Trash2,
  Plus,
  Download,
  Upload,
  RefreshCw
} from 'lucide-react'

export default function AdminPage() {
  const { user, isAdmin } = useAuth()
  const [systemStats, setSystemStats] = useState({})
  const [users, setUsers] = useState([])
  const [systemLogs, setSystemLogs] = useState([])
  const [ollamaModels, setOllamaModels] = useState([])
  const [systemConfig, setSystemConfig] = useState({})
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('overview')

  useEffect(() => {
    if (isAdmin) {
      loadAdminData()
    }
  }, [isAdmin])

  const loadAdminData = async () => {
    try {
      // Simulated API calls
      const mockStats = {
        users: {
          total: 156,
          active: 89,
          new_today: 12,
          growth: 8.5
        },
        agents: {
          total: 45,
          active: 32,
          running: 8,
          success_rate: 94.2
        },
        tasks: {
          total: 1247,
          completed: 1156,
          failed: 91,
          avg_duration: 145
        },
        system: {
          cpu_usage: 45,
          memory_usage: 67,
          disk_usage: 34,
          network_io: 2.3,
          uptime: 2592000 // 30 days in seconds
        },
        ollama: {
          status: 'running',
          models: 8,
          requests_today: 342,
          avg_response_time: 1250
        }
      }

      const mockUsers = [
        {
          id: '1',
          email: 'admin@example.com',
          name: 'Administrador',
          role: 'admin',
          status: 'active',
          last_login: new Date(Date.now() - 3600000).toISOString(),
          created_at: new Date(Date.now() - 2592000000).toISOString(),
          agents_count: 5,
          tasks_count: 23
        },
        {
          id: '2',
          email: 'user1@example.com',
          name: 'Usuario Demo',
          role: 'user',
          status: 'active',
          last_login: new Date(Date.now() - 7200000).toISOString(),
          created_at: new Date(Date.now() - 1296000000).toISOString(),
          agents_count: 3,
          tasks_count: 15
        },
        {
          id: '3',
          email: 'user2@example.com',
          name: 'María García',
          role: 'user',
          status: 'inactive',
          last_login: new Date(Date.now() - 86400000).toISOString(),
          created_at: new Date(Date.now() - 604800000).toISOString(),
          agents_count: 1,
          tasks_count: 3
        }
      ]

      const mockLogs = [
        {
          id: '1',
          timestamp: new Date(Date.now() - 300000).toISOString(),
          level: 'info',
          component: 'agent_service',
          message: 'Agente "Analista de Datos" completó tarea exitosamente',
          user_id: '1'
        },
        {
          id: '2',
          timestamp: new Date(Date.now() - 600000).toISOString(),
          level: 'warning',
          component: 'ollama_service',
          message: 'Tiempo de respuesta elevado detectado (2.5s)',
          details: 'Modelo: llama2, Request ID: req_123'
        },
        {
          id: '3',
          timestamp: new Date(Date.now() - 900000).toISOString(),
          level: 'error',
          component: 'mcp_service',
          message: 'Error de conexión con herramienta GitHub',
          details: 'Token de autenticación inválido'
        },
        {
          id: '4',
          timestamp: new Date(Date.now() - 1200000).toISOString(),
          level: 'info',
          component: 'auth_service',
          message: 'Nuevo usuario registrado',
          user_id: '3'
        }
      ]

      const mockModels = [
        {
          name: 'llama2',
          size: '3.8GB',
          status: 'loaded',
          last_used: new Date(Date.now() - 300000).toISOString(),
          usage_count: 156,
          avg_response_time: 1200
        },
        {
          name: 'codellama',
          size: '7.3GB',
          status: 'loaded',
          last_used: new Date(Date.now() - 600000).toISOString(),
          usage_count: 89,
          avg_response_time: 1800
        },
        {
          name: 'mistral',
          size: '4.1GB',
          status: 'available',
          last_used: new Date(Date.now() - 86400000).toISOString(),
          usage_count: 23,
          avg_response_time: 950
        },
        {
          name: 'neural-chat',
          size: '3.2GB',
          status: 'loading',
          last_used: null,
          usage_count: 0,
          avg_response_time: 0
        }
      ]

      const mockConfig = {
        system: {
          max_users: 1000,
          max_agents_per_user: 10,
          max_concurrent_tasks: 50,
          session_timeout: 3600,
          file_upload_limit: 100,
          backup_enabled: true,
          maintenance_mode: false
        },
        ollama: {
          host: 'localhost',
          port: 11434,
          timeout: 30,
          max_concurrent_requests: 10,
          auto_load_models: true,
          model_cache_size: 4
        },
        security: {
          password_min_length: 8,
          require_2fa: false,
          session_encryption: true,
          audit_logging: true,
          rate_limiting: true,
          max_login_attempts: 5
        }
      }

      setSystemStats(mockStats)
      setUsers(mockUsers)
      setSystemLogs(mockLogs)
      setOllamaModels(mockModels)
      setSystemConfig(mockConfig)
    } catch (error) {
      console.error('Error loading admin data:', error)
    } finally {
      setLoading(false)
    }
  }

  const formatUptime = (seconds) => {
    const days = Math.floor(seconds / 86400)
    const hours = Math.floor((seconds % 86400) / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    return `${days}d ${hours}h ${minutes}m`
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

  const getLogLevelColor = (level) => {
    const colors = {
      info: 'text-blue-600',
      warning: 'text-yellow-600',
      error: 'text-red-600',
      debug: 'text-gray-600'
    }
    return colors[level] || 'text-gray-600'
  }

  const getStatusBadge = (status) => {
    const configs = {
      active: { color: 'bg-green-100 text-green-800', label: 'Activo' },
      inactive: { color: 'bg-gray-100 text-gray-800', label: 'Inactivo' },
      suspended: { color: 'bg-red-100 text-red-800', label: 'Suspendido' },
      loaded: { color: 'bg-green-100 text-green-800', label: 'Cargado' },
      available: { color: 'bg-blue-100 text-blue-800', label: 'Disponible' },
      loading: { color: 'bg-yellow-100 text-yellow-800', label: 'Cargando' },
      running: { color: 'bg-green-100 text-green-800', label: 'Ejecutando' },
      stopped: { color: 'bg-red-100 text-red-800', label: 'Detenido' }
    }
    const config = configs[status] || configs.inactive
    return <Badge className={config.color}>{config.label}</Badge>
  }

  if (!isAdmin) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <Shield className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
          <h3 className="text-lg font-semibold mb-2">Acceso Denegado</h3>
          <p className="text-muted-foreground">
            No tienes permisos para acceder al panel de administración
          </p>
        </div>
      </div>
    )
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
          <h1 className="text-3xl font-bold">Panel de Administración</h1>
          <p className="text-muted-foreground">
            Gestión y monitoreo del sistema MANUS-like
          </p>
        </div>
        
        <div className="flex items-center space-x-2">
          <Button variant="outline">
            <Download className="w-4 h-4 mr-2" />
            Exportar Logs
          </Button>
          <Button variant="outline">
            <RefreshCw className="w-4 h-4 mr-2" />
            Actualizar
          </Button>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-6">
          <TabsTrigger value="overview">Resumen</TabsTrigger>
          <TabsTrigger value="users">Usuarios</TabsTrigger>
          <TabsTrigger value="system">Sistema</TabsTrigger>
          <TabsTrigger value="ollama">Ollama</TabsTrigger>
          <TabsTrigger value="logs">Logs</TabsTrigger>
          <TabsTrigger value="config">Configuración</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-6">
          {/* Key Metrics */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center space-x-2">
                  <Users className="w-5 h-5 text-blue-500" />
                  <div>
                    <p className="text-sm font-medium">Usuarios Activos</p>
                    <p className="text-2xl font-bold">{systemStats.users?.active}</p>
                    <p className="text-xs text-green-600 flex items-center">
                      <TrendingUp className="w-3 h-3 mr-1" />
                      +{systemStats.users?.growth}%
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4">
                <div className="flex items-center space-x-2">
                  <Activity className="w-5 h-5 text-green-500" />
                  <div>
                    <p className="text-sm font-medium">Agentes Ejecutando</p>
                    <p className="text-2xl font-bold">{systemStats.agents?.running}</p>
                    <p className="text-xs text-muted-foreground">
                      {systemStats.agents?.success_rate}% éxito
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4">
                <div className="flex items-center space-x-2">
                  <Server className="w-5 h-5 text-purple-500" />
                  <div>
                    <p className="text-sm font-medium">Uso de CPU</p>
                    <p className="text-2xl font-bold">{systemStats.system?.cpu_usage}%</p>
                    <Progress value={systemStats.system?.cpu_usage} className="h-1 mt-1" />
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4">
                <div className="flex items-center space-x-2">
                  <Zap className="w-5 h-5 text-orange-500" />
                  <div>
                    <p className="text-sm font-medium">Uptime</p>
                    <p className="text-lg font-bold">{formatUptime(systemStats.system?.uptime)}</p>
                    <p className="text-xs text-green-600">Sistema estable</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* System Health */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Activity className="w-5 h-5" />
                  <span>Estado del Sistema</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm">CPU</span>
                    <div className="flex items-center space-x-2">
                      <Progress value={systemStats.system?.cpu_usage} className="w-24 h-2" />
                      <span className="text-sm font-medium">{systemStats.system?.cpu_usage}%</span>
                    </div>
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <span className="text-sm">Memoria</span>
                    <div className="flex items-center space-x-2">
                      <Progress value={systemStats.system?.memory_usage} className="w-24 h-2" />
                      <span className="text-sm font-medium">{systemStats.system?.memory_usage}%</span>
                    </div>
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <span className="text-sm">Disco</span>
                    <div className="flex items-center space-x-2">
                      <Progress value={systemStats.system?.disk_usage} className="w-24 h-2" />
                      <span className="text-sm font-medium">{systemStats.system?.disk_usage}%</span>
                    </div>
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <span className="text-sm">Red I/O</span>
                    <span className="text-sm font-medium">{systemStats.system?.network_io} MB/s</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Database className="w-5 h-5" />
                  <span>Estado de Ollama</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm">Estado</span>
                  {getStatusBadge(systemStats.ollama?.status)}
                </div>
                
                <div className="flex items-center justify-between">
                  <span className="text-sm">Modelos Cargados</span>
                  <span className="text-sm font-medium">{systemStats.ollama?.models}</span>
                </div>
                
                <div className="flex items-center justify-between">
                  <span className="text-sm">Requests Hoy</span>
                  <span className="text-sm font-medium">{systemStats.ollama?.requests_today}</span>
                </div>
                
                <div className="flex items-center justify-between">
                  <span className="text-sm">Tiempo Respuesta</span>
                  <span className="text-sm font-medium">{systemStats.ollama?.avg_response_time}ms</span>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Recent Activity */}
          <Card>
            <CardHeader>
              <CardTitle>Actividad Reciente</CardTitle>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-64">
                <div className="space-y-3">
                  {systemLogs.slice(0, 10).map((log) => (
                    <div key={log.id} className="flex items-start space-x-3 text-sm">
                      <div className={`w-2 h-2 rounded-full mt-2 ${
                        log.level === 'error' ? 'bg-red-500' :
                        log.level === 'warning' ? 'bg-yellow-500' :
                        'bg-green-500'
                      }`} />
                      <div className="flex-1">
                        <div className="flex items-center justify-between">
                          <span className={getLogLevelColor(log.level)}>{log.message}</span>
                          <span className="text-xs text-muted-foreground">
                            {formatDate(log.timestamp)}
                          </span>
                        </div>
                        <p className="text-xs text-muted-foreground">{log.component}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Users Tab */}
        <TabsContent value="users" className="space-y-6">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold">Gestión de Usuarios</h3>
            <Button>
              <Plus className="w-4 h-4 mr-2" />
              Nuevo Usuario
            </Button>
          </div>

          <Card>
            <CardContent className="p-0">
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="border-b">
                    <tr className="text-left">
                      <th className="p-4 font-medium">Usuario</th>
                      <th className="p-4 font-medium">Rol</th>
                      <th className="p-4 font-medium">Estado</th>
                      <th className="p-4 font-medium">Último Acceso</th>
                      <th className="p-4 font-medium">Agentes</th>
                      <th className="p-4 font-medium">Tareas</th>
                      <th className="p-4 font-medium">Acciones</th>
                    </tr>
                  </thead>
                  <tbody>
                    {users.map((user) => (
                      <tr key={user.id} className="border-b hover:bg-muted/50">
                        <td className="p-4">
                          <div>
                            <div className="font-medium">{user.name}</div>
                            <div className="text-sm text-muted-foreground">{user.email}</div>
                          </div>
                        </td>
                        <td className="p-4">
                          <Badge variant={user.role === 'admin' ? 'default' : 'outline'}>
                            {user.role === 'admin' ? 'Administrador' : 'Usuario'}
                          </Badge>
                        </td>
                        <td className="p-4">
                          {getStatusBadge(user.status)}
                        </td>
                        <td className="p-4 text-sm text-muted-foreground">
                          {formatDate(user.last_login)}
                        </td>
                        <td className="p-4 text-sm">{user.agents_count}</td>
                        <td className="p-4 text-sm">{user.tasks_count}</td>
                        <td className="p-4">
                          <div className="flex items-center space-x-2">
                            <Button variant="ghost" size="sm">
                              <Eye className="w-4 h-4" />
                            </Button>
                            <Button variant="ghost" size="sm">
                              <Edit className="w-4 h-4" />
                            </Button>
                            <Button variant="ghost" size="sm">
                              <Trash2 className="w-4 h-4" />
                            </Button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* System Tab */}
        <TabsContent value="system" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Cpu className="w-5 h-5" />
                  <span>Recursos del Sistema</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-3">
                  <div>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm">CPU</span>
                      <span className="text-sm font-medium">{systemStats.system?.cpu_usage}%</span>
                    </div>
                    <Progress value={systemStats.system?.cpu_usage} />
                  </div>
                  
                  <div>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm">Memoria</span>
                      <span className="text-sm font-medium">{systemStats.system?.memory_usage}%</span>
                    </div>
                    <Progress value={systemStats.system?.memory_usage} />
                  </div>
                  
                  <div>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm">Disco</span>
                      <span className="text-sm font-medium">{systemStats.system?.disk_usage}%</span>
                    </div>
                    <Progress value={systemStats.system?.disk_usage} />
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Network className="w-5 h-5" />
                  <span>Servicios</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm">Backend API</span>
                  <div className="flex items-center space-x-2">
                    <CheckCircle className="w-4 h-4 text-green-500" />
                    <span className="text-sm">Activo</span>
                  </div>
                </div>
                
                <div className="flex items-center justify-between">
                  <span className="text-sm">Base de Datos</span>
                  <div className="flex items-center space-x-2">
                    <CheckCircle className="w-4 h-4 text-green-500" />
                    <span className="text-sm">Conectado</span>
                  </div>
                </div>
                
                <div className="flex items-center justify-between">
                  <span className="text-sm">Ollama</span>
                  <div className="flex items-center space-x-2">
                    <CheckCircle className="w-4 h-4 text-green-500" />
                    <span className="text-sm">Ejecutando</span>
                  </div>
                </div>
                
                <div className="flex items-center justify-between">
                  <span className="text-sm">MCP Services</span>
                  <div className="flex items-center space-x-2">
                    <AlertTriangle className="w-4 h-4 text-yellow-500" />
                    <span className="text-sm">Parcial</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Ollama Tab */}
        <TabsContent value="ollama" className="space-y-6">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold">Gestión de Modelos Ollama</h3>
            <Button>
              <Download className="w-4 h-4 mr-2" />
              Descargar Modelo
            </Button>
          </div>

          <Card>
            <CardContent className="p-0">
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="border-b">
                    <tr className="text-left">
                      <th className="p-4 font-medium">Modelo</th>
                      <th className="p-4 font-medium">Tamaño</th>
                      <th className="p-4 font-medium">Estado</th>
                      <th className="p-4 font-medium">Último Uso</th>
                      <th className="p-4 font-medium">Usos</th>
                      <th className="p-4 font-medium">Tiempo Resp.</th>
                      <th className="p-4 font-medium">Acciones</th>
                    </tr>
                  </thead>
                  <tbody>
                    {ollamaModels.map((model) => (
                      <tr key={model.name} className="border-b hover:bg-muted/50">
                        <td className="p-4 font-medium">{model.name}</td>
                        <td className="p-4 text-sm">{model.size}</td>
                        <td className="p-4">
                          {getStatusBadge(model.status)}
                        </td>
                        <td className="p-4 text-sm text-muted-foreground">
                          {model.last_used ? formatDate(model.last_used) : 'Nunca'}
                        </td>
                        <td className="p-4 text-sm">{model.usage_count}</td>
                        <td className="p-4 text-sm">{model.avg_response_time}ms</td>
                        <td className="p-4">
                          <div className="flex items-center space-x-2">
                            {model.status === 'available' ? (
                              <Button variant="outline" size="sm">
                                Cargar
                              </Button>
                            ) : model.status === 'loaded' ? (
                              <Button variant="outline" size="sm">
                                Descargar
                              </Button>
                            ) : null}
                            <Button variant="ghost" size="sm">
                              <Trash2 className="w-4 h-4" />
                            </Button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Logs Tab */}
        <TabsContent value="logs" className="space-y-6">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold">Logs del Sistema</h3>
            <div className="flex items-center space-x-2">
              <select className="px-3 py-2 border border-input rounded-md text-sm">
                <option value="all">Todos los niveles</option>
                <option value="error">Errores</option>
                <option value="warning">Advertencias</option>
                <option value="info">Información</option>
              </select>
              <Button variant="outline">
                <RefreshCw className="w-4 h-4 mr-2" />
                Actualizar
              </Button>
            </div>
          </div>

          <Card>
            <CardContent className="p-0">
              <ScrollArea className="h-96">
                <div className="p-4 space-y-3">
                  {systemLogs.map((log) => (
                    <div key={log.id} className="border-b pb-3 last:border-b-0">
                      <div className="flex items-start justify-between">
                        <div className="flex items-start space-x-3">
                          <div className={`w-2 h-2 rounded-full mt-2 ${
                            log.level === 'error' ? 'bg-red-500' :
                            log.level === 'warning' ? 'bg-yellow-500' :
                            'bg-green-500'
                          }`} />
                          <div>
                            <p className={`text-sm ${getLogLevelColor(log.level)}`}>
                              {log.message}
                            </p>
                            <div className="flex items-center space-x-4 mt-1 text-xs text-muted-foreground">
                              <span>{log.component}</span>
                              <span>{formatDate(log.timestamp)}</span>
                              {log.user_id && <span>Usuario: {log.user_id}</span>}
                            </div>
                            {log.details && (
                              <p className="text-xs text-muted-foreground mt-1">
                                {log.details}
                              </p>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Configuration Tab */}
        <TabsContent value="config" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Configuración del Sistema</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <Label>Modo Mantenimiento</Label>
                    <Switch checked={systemConfig.system?.maintenance_mode} />
                  </div>
                  
                  <div className="space-y-2">
                    <Label>Máximo de Usuarios</Label>
                    <Input 
                      type="number" 
                      value={systemConfig.system?.max_users} 
                      className="w-32"
                    />
                  </div>
                  
                  <div className="space-y-2">
                    <Label>Agentes por Usuario</Label>
                    <Input 
                      type="number" 
                      value={systemConfig.system?.max_agents_per_user} 
                      className="w-32"
                    />
                  </div>
                  
                  <div className="space-y-2">
                    <Label>Tareas Concurrentes</Label>
                    <Input 
                      type="number" 
                      value={systemConfig.system?.max_concurrent_tasks} 
                      className="w-32"
                    />
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Configuración de Seguridad</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <Label>Autenticación 2FA</Label>
                    <Switch checked={systemConfig.security?.require_2fa} />
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <Label>Logging de Auditoría</Label>
                    <Switch checked={systemConfig.security?.audit_logging} />
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <Label>Rate Limiting</Label>
                    <Switch checked={systemConfig.security?.rate_limiting} />
                  </div>
                  
                  <div className="space-y-2">
                    <Label>Longitud Mínima Contraseña</Label>
                    <Input 
                      type="number" 
                      value={systemConfig.security?.password_min_length} 
                      className="w-32"
                    />
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          <div className="flex justify-end space-x-2">
            <Button variant="outline">Cancelar</Button>
            <Button>Guardar Configuración</Button>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  )
}

