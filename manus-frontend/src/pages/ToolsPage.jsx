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
import { useAuth } from '@/hooks/useAuth'
import {
  Wrench,
  Search,
  Plus,
  Settings,
  Play,
  Pause,
  Download,
  Upload,
  Code,
  Database,
  Globe,
  FileText,
  Bot,
  Shield,
  Activity,
  CheckCircle,
  XCircle,
  AlertTriangle,
  ExternalLink,
  Docker
} from 'lucide-react'

const toolCategories = {
  development: { label: 'Desarrollo', icon: Code, color: 'bg-blue-100 text-blue-800' },
  data: { label: 'Datos', icon: Database, color: 'bg-green-100 text-green-800' },
  web: { label: 'Web', icon: Globe, color: 'bg-purple-100 text-purple-800' },
  files: { label: 'Archivos', icon: FileText, color: 'bg-orange-100 text-orange-800' },
  ai: { label: 'IA/ML', icon: Bot, color: 'bg-pink-100 text-pink-800' },
  security: { label: 'Seguridad', icon: Shield, color: 'bg-red-100 text-red-800' }
}

const toolStatuses = {
  available: { label: 'Disponible', color: 'bg-green-100 text-green-800', icon: CheckCircle },
  installed: { label: 'Instalada', color: 'bg-blue-100 text-blue-800', icon: CheckCircle },
  running: { label: 'Ejecutando', color: 'bg-yellow-100 text-yellow-800', icon: Activity },
  error: { label: 'Error', color: 'bg-red-100 text-red-800', icon: XCircle },
  updating: { label: 'Actualizando', color: 'bg-orange-100 text-orange-800', icon: AlertTriangle }
}

export default function ToolsPage() {
  const { user, isAdmin } = useAuth()
  const [tools, setTools] = useState([])
  const [filteredTools, setFilteredTools] = useState([])
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedTool, setSelectedTool] = useState(null)
  const [isConfigDialogOpen, setIsConfigDialogOpen] = useState(false)
  const [isInstallDialogOpen, setIsInstallDialogOpen] = useState(false)
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('all')
  const [categoryFilter, setCategoryFilter] = useState('all')

  // Tool configuration form
  const [toolConfig, setToolConfig] = useState({
    enabled: true,
    config: {},
    permissions: {
      read: true,
      write: false,
      execute: false
    }
  })

  useEffect(() => {
    loadTools()
  }, [])

  useEffect(() => {
    filterTools()
  }, [tools, searchQuery, activeTab, categoryFilter])

  const loadTools = async () => {
    try {
      // Simulated API call - MCP tools from Docker catalog
      const mockTools = [
        {
          id: 'github',
          name: 'GitHub',
          description: 'Gestión de repositorios, operaciones de archivos y integración con GitHub API',
          category: 'development',
          status: 'installed',
          version: '1.2.0',
          docker_image: 'docker.io/mcp/github:latest',
          author: 'Docker',
          official: true,
          downloads: 15420,
          rating: 4.8,
          last_updated: new Date(Date.now() - 86400000).toISOString(),
          config_schema: {
            github_token: { type: 'string', required: true, description: 'GitHub Personal Access Token' },
            default_org: { type: 'string', required: false, description: 'Organización por defecto' }
          },
          capabilities: ['read_repos', 'create_issues', 'manage_files', 'webhooks'],
          usage_stats: {
            calls_today: 45,
            calls_week: 312,
            avg_response_time: 150
          }
        },
        {
          id: 'filesystem',
          name: 'Filesystem',
          description: 'Operaciones seguras de archivos con controles de acceso configurables',
          category: 'files',
          status: 'installed',
          version: '2.1.0',
          docker_image: 'docker.io/mcp/filesystem:latest',
          author: 'Docker',
          official: true,
          downloads: 28750,
          rating: 4.9,
          last_updated: new Date(Date.now() - 172800000).toISOString(),
          config_schema: {
            allowed_paths: { type: 'array', required: true, description: 'Rutas permitidas' },
            max_file_size: { type: 'number', required: false, description: 'Tamaño máximo de archivo (MB)' }
          },
          capabilities: ['read_files', 'write_files', 'list_directories', 'file_search'],
          usage_stats: {
            calls_today: 128,
            calls_week: 892,
            avg_response_time: 45
          }
        },
        {
          id: 'postgresql',
          name: 'PostgreSQL',
          description: 'Acceso de solo lectura a bases de datos con inspección de esquemas',
          category: 'data',
          status: 'available',
          version: '1.5.2',
          docker_image: 'docker.io/mcp/postgresql:latest',
          author: 'Docker',
          official: true,
          downloads: 12340,
          rating: 4.7,
          last_updated: new Date(Date.now() - 259200000).toISOString(),
          config_schema: {
            connection_string: { type: 'string', required: true, description: 'Cadena de conexión PostgreSQL' },
            read_only: { type: 'boolean', required: false, description: 'Modo solo lectura' }
          },
          capabilities: ['query_data', 'inspect_schema', 'explain_queries'],
          usage_stats: null
        },
        {
          id: 'puppeteer',
          name: 'Puppeteer',
          description: 'Automatización de navegador y web scraping',
          category: 'web',
          status: 'running',
          version: '3.0.1',
          docker_image: 'docker.io/mcp/puppeteer:latest',
          author: 'Docker',
          official: true,
          downloads: 9876,
          rating: 4.6,
          last_updated: new Date(Date.now() - 345600000).toISOString(),
          config_schema: {
            headless: { type: 'boolean', required: false, description: 'Ejecutar en modo headless' },
            timeout: { type: 'number', required: false, description: 'Timeout en segundos' }
          },
          capabilities: ['navigate_pages', 'extract_data', 'take_screenshots', 'fill_forms'],
          usage_stats: {
            calls_today: 23,
            calls_week: 156,
            avg_response_time: 2300
          }
        },
        {
          id: 'memory',
          name: 'Memory',
          description: 'Sistema de memoria persistente basado en grafos de conocimiento',
          category: 'ai',
          status: 'installed',
          version: '1.0.5',
          docker_image: 'docker.io/mcp/memory:latest',
          author: 'Docker',
          official: true,
          downloads: 7654,
          rating: 4.5,
          last_updated: new Date(Date.now() - 432000000).toISOString(),
          config_schema: {
            storage_path: { type: 'string', required: true, description: 'Ruta de almacenamiento' },
            max_memories: { type: 'number', required: false, description: 'Máximo número de memorias' }
          },
          capabilities: ['store_memories', 'retrieve_memories', 'semantic_search', 'knowledge_graph'],
          usage_stats: {
            calls_today: 67,
            calls_week: 445,
            avg_response_time: 89
          }
        },
        {
          id: 'slack',
          name: 'Slack',
          description: 'Gestión de canales y capacidades de mensajería',
          category: 'web',
          status: 'error',
          version: '1.3.0',
          docker_image: 'docker.io/mcp/slack:latest',
          author: 'Docker',
          official: true,
          downloads: 5432,
          rating: 4.4,
          last_updated: new Date(Date.now() - 518400000).toISOString(),
          config_schema: {
            bot_token: { type: 'string', required: true, description: 'Slack Bot Token' },
            signing_secret: { type: 'string', required: true, description: 'Slack Signing Secret' }
          },
          capabilities: ['send_messages', 'read_channels', 'manage_users', 'file_upload'],
          usage_stats: null,
          error_message: 'Token de autenticación inválido'
        }
      ]
      
      setTools(mockTools)
    } catch (error) {
      console.error('Error loading tools:', error)
    } finally {
      setLoading(false)
    }
  }

  const filterTools = () => {
    let filtered = tools

    // Filter by tab
    switch (activeTab) {
      case 'installed':
        filtered = filtered.filter(tool => ['installed', 'running', 'error'].includes(tool.status))
        break
      case 'available':
        filtered = filtered.filter(tool => tool.status === 'available')
        break
      case 'running':
        filtered = filtered.filter(tool => tool.status === 'running')
        break
      default:
        // 'all' - no additional filtering
        break
    }

    // Filter by category
    if (categoryFilter !== 'all') {
      filtered = filtered.filter(tool => tool.category === categoryFilter)
    }

    // Filter by search query
    if (searchQuery) {
      filtered = filtered.filter(tool =>
        tool.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        tool.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
        tool.capabilities.some(cap => cap.toLowerCase().includes(searchQuery.toLowerCase()))
      )
    }

    setFilteredTools(filtered)
  }

  const installTool = async (toolId) => {
    try {
      setTools(prev => prev.map(tool =>
        tool.id === toolId ? { ...tool, status: 'updating' } : tool
      ))

      // Simulate installation delay
      setTimeout(() => {
        setTools(prev => prev.map(tool =>
          tool.id === toolId ? { 
            ...tool, 
            status: 'installed',
            usage_stats: {
              calls_today: 0,
              calls_week: 0,
              avg_response_time: 0
            }
          } : tool
        ))
      }, 3000)
    } catch (error) {
      console.error('Error installing tool:', error)
    }
  }

  const uninstallTool = async (toolId) => {
    if (window.confirm('¿Estás seguro de que quieres desinstalar esta herramienta?')) {
      try {
        setTools(prev => prev.map(tool =>
          tool.id === toolId ? { ...tool, status: 'available', usage_stats: null } : tool
        ))
      } catch (error) {
        console.error('Error uninstalling tool:', error)
      }
    }
  }

  const toggleTool = async (toolId, currentStatus) => {
    try {
      const newStatus = currentStatus === 'running' ? 'installed' : 'running'
      setTools(prev => prev.map(tool =>
        tool.id === toolId ? { ...tool, status: newStatus } : tool
      ))
    } catch (error) {
      console.error('Error toggling tool:', error)
    }
  }

  const openConfigDialog = (tool) => {
    setSelectedTool(tool)
    // Load existing configuration
    setToolConfig({
      enabled: tool.status === 'running',
      config: {},
      permissions: {
        read: true,
        write: false,
        execute: false
      }
    })
    setIsConfigDialogOpen(true)
  }

  const saveToolConfig = async () => {
    try {
      // Save configuration logic here
      setIsConfigDialogOpen(false)
      setSelectedTool(null)
    } catch (error) {
      console.error('Error saving tool config:', error)
    }
  }

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('es-ES', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    })
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
          <h1 className="text-3xl font-bold">Herramientas</h1>
          <p className="text-muted-foreground">
            Gestiona herramientas MCP para tus agentes
          </p>
        </div>
        
        <div className="flex items-center space-x-2">
          <Button variant="outline">
            <Upload className="w-4 h-4 mr-2" />
            Importar
          </Button>
          <Dialog open={isInstallDialogOpen} onOpenChange={setIsInstallDialogOpen}>
            <DialogTrigger asChild>
              <Button>
                <Plus className="w-4 h-4 mr-2" />
                Instalar Herramienta
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Instalar Herramienta Personalizada</DialogTitle>
                <DialogDescription>
                  Instala una herramienta MCP desde Docker Hub o un registro personalizado
                </DialogDescription>
              </DialogHeader>
              
              <div className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="docker-image">Imagen Docker</Label>
                  <Input
                    id="docker-image"
                    placeholder="docker.io/usuario/herramienta:latest"
                  />
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="tool-name">Nombre de la Herramienta</Label>
                  <Input
                    id="tool-name"
                    placeholder="Mi Herramienta Personalizada"
                  />
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="tool-description">Descripción</Label>
                  <Textarea
                    id="tool-description"
                    placeholder="Describe qué hace esta herramienta"
                    rows={3}
                  />
                </div>
                
                <div className="flex justify-end space-x-2">
                  <Button variant="outline" onClick={() => setIsInstallDialogOpen(false)}>
                    Cancelar
                  </Button>
                  <Button>
                    Instalar
                  </Button>
                </div>
              </div>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <Wrench className="w-5 h-5 text-primary" />
              <div>
                <p className="text-sm font-medium">Total Herramientas</p>
                <p className="text-2xl font-bold">{tools.length}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <CheckCircle className="w-5 h-5 text-green-500" />
              <div>
                <p className="text-sm font-medium">Instaladas</p>
                <p className="text-2xl font-bold">
                  {tools.filter(t => ['installed', 'running', 'error'].includes(t.status)).length}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <Activity className="w-5 h-5 text-blue-500" />
              <div>
                <p className="text-sm font-medium">Ejecutando</p>
                <p className="text-2xl font-bold">
                  {tools.filter(t => t.status === 'running').length}
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
                <p className="text-sm font-medium">Con Errores</p>
                <p className="text-2xl font-bold">
                  {tools.filter(t => t.status === 'error').length}
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
            placeholder="Buscar herramientas..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>
        
        <select
          value={categoryFilter}
          onChange={(e) => setCategoryFilter(e.target.value)}
          className="px-3 py-2 border border-input rounded-md"
        >
          <option value="all">Todas las categorías</option>
          {Object.entries(toolCategories).map(([key, category]) => (
            <option key={key} value={key}>{category.label}</option>
          ))}
        </select>
        
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList>
            <TabsTrigger value="all">Todas</TabsTrigger>
            <TabsTrigger value="installed">Instaladas</TabsTrigger>
            <TabsTrigger value="available">Disponibles</TabsTrigger>
            <TabsTrigger value="running">Ejecutando</TabsTrigger>
          </TabsList>
        </Tabs>
      </div>

      {/* Tools Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredTools.map((tool) => {
          const categoryConfig = toolCategories[tool.category]
          const statusConfig = toolStatuses[tool.status]
          const CategoryIcon = categoryConfig.icon
          const StatusIcon = statusConfig.icon
          
          return (
            <Card key={tool.id} className="hover:shadow-lg transition-shadow">
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between">
                  <div className="flex items-center space-x-3">
                    <div className="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center">
                      <CategoryIcon className="w-5 h-5 text-primary" />
                    </div>
                    <div>
                      <CardTitle className="text-lg flex items-center space-x-2">
                        <span>{tool.name}</span>
                        {tool.official && (
                          <Badge variant="outline" className="text-xs">
                            <Docker className="w-3 h-3 mr-1" />
                            Oficial
                          </Badge>
                        )}
                      </CardTitle>
                      <div className="flex items-center space-x-2 mt-1">
                        <Badge className={categoryConfig.color}>
                          {categoryConfig.label}
                        </Badge>
                        <Badge className={statusConfig.color}>
                          <StatusIcon className="w-3 h-3 mr-1" />
                          {statusConfig.label}
                        </Badge>
                      </div>
                    </div>
                  </div>
                </div>
              </CardHeader>
              
              <CardContent className="space-y-4">
                <CardDescription className="text-sm">
                  {tool.description}
                </CardDescription>
                
                {/* Error Message */}
                {tool.status === 'error' && tool.error_message && (
                  <div className="bg-red-50 border border-red-200 rounded-md p-2">
                    <p className="text-xs text-red-700">{tool.error_message}</p>
                  </div>
                )}
                
                {/* Capabilities */}
                <div>
                  <Label className="text-xs font-medium text-muted-foreground">Capacidades</Label>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {tool.capabilities.slice(0, 3).map((capability) => (
                      <Badge key={capability} variant="outline" className="text-xs">
                        {capability}
                      </Badge>
                    ))}
                    {tool.capabilities.length > 3 && (
                      <Badge variant="outline" className="text-xs">
                        +{tool.capabilities.length - 3}
                      </Badge>
                    )}
                  </div>
                </div>
                
                {/* Stats */}
                {tool.usage_stats && (
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div>
                      <span className="text-muted-foreground">Hoy: </span>
                      <span className="font-medium">{tool.usage_stats.calls_today}</span>
                    </div>
                    <div>
                      <span className="text-muted-foreground">Semana: </span>
                      <span className="font-medium">{tool.usage_stats.calls_week}</span>
                    </div>
                    <div className="col-span-2">
                      <span className="text-muted-foreground">Tiempo resp: </span>
                      <span className="font-medium">{tool.usage_stats.avg_response_time}ms</span>
                    </div>
                  </div>
                )}
                
                {/* Meta Info */}
                <div className="text-xs text-muted-foreground space-y-1">
                  <div>Versión: {tool.version}</div>
                  <div>Descargas: {tool.downloads.toLocaleString()}</div>
                  <div>Actualizada: {formatDate(tool.last_updated)}</div>
                  <div className="flex items-center space-x-1">
                    <span>Rating:</span>
                    <div className="flex">
                      {[...Array(5)].map((_, i) => (
                        <span key={i} className={i < Math.floor(tool.rating) ? 'text-yellow-400' : 'text-gray-300'}>
                          ★
                        </span>
                      ))}
                    </div>
                    <span>({tool.rating})</span>
                  </div>
                </div>
                
                {/* Actions */}
                <div className="flex space-x-2">
                  {tool.status === 'available' ? (
                    <Button 
                      size="sm" 
                      className="flex-1"
                      onClick={() => installTool(tool.id)}
                    >
                      <Download className="w-4 h-4 mr-2" />
                      Instalar
                    </Button>
                  ) : (
                    <>
                      <Button
                        size="sm"
                        variant={tool.status === 'running' ? 'outline' : 'default'}
                        onClick={() => toggleTool(tool.id, tool.status)}
                        disabled={tool.status === 'error'}
                      >
                        {tool.status === 'running' ? (
                          <>
                            <Pause className="w-4 h-4 mr-2" />
                            Detener
                          </>
                        ) : (
                          <>
                            <Play className="w-4 h-4 mr-2" />
                            Iniciar
                          </>
                        )}
                      </Button>
                      
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => openConfigDialog(tool)}
                      >
                        <Settings className="w-4 h-4" />
                      </Button>
                    </>
                  )}
                </div>
                
                {tool.status !== 'available' && (
                  <Button
                    size="sm"
                    variant="outline"
                    className="w-full text-destructive hover:text-destructive"
                    onClick={() => uninstallTool(tool.id)}
                  >
                    Desinstalar
                  </Button>
                )}
              </CardContent>
            </Card>
          )
        })}
      </div>

      {filteredTools.length === 0 && (
        <div className="text-center py-12">
          <Wrench className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
          <h3 className="text-lg font-semibold mb-2">No se encontraron herramientas</h3>
          <p className="text-muted-foreground mb-4">
            {searchQuery ? 'Intenta con otros términos de búsqueda' : 'Explora el catálogo MCP para encontrar herramientas'}
          </p>
          <Button>
            <ExternalLink className="w-4 h-4 mr-2" />
            Explorar Catálogo MCP
          </Button>
        </div>
      )}

      {/* Tool Configuration Dialog */}
      <Dialog open={isConfigDialogOpen} onOpenChange={setIsConfigDialogOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Configurar {selectedTool?.name}</DialogTitle>
            <DialogDescription>
              Configura los parámetros y permisos de la herramienta
            </DialogDescription>
          </DialogHeader>
          
          {selectedTool && (
            <ScrollArea className="max-h-[60vh]">
              <div className="space-y-6">
                {/* General Settings */}
                <div className="space-y-4">
                  <h4 className="text-sm font-medium">Configuración General</h4>
                  
                  <div className="flex items-center space-x-2">
                    <Switch
                      id="enabled"
                      checked={toolConfig.enabled}
                      onCheckedChange={(checked) => 
                        setToolConfig(prev => ({ ...prev, enabled: checked }))
                      }
                    />
                    <Label htmlFor="enabled">Herramienta habilitada</Label>
                  </div>
                </div>
                
                {/* Tool-specific Configuration */}
                {selectedTool.config_schema && (
                  <div className="space-y-4">
                    <h4 className="text-sm font-medium">Configuración Específica</h4>
                    
                    {Object.entries(selectedTool.config_schema).map(([key, schema]) => (
                      <div key={key} className="space-y-2">
                        <Label htmlFor={key}>
                          {key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                          {schema.required && <span className="text-red-500 ml-1">*</span>}
                        </Label>
                        
                        {schema.type === 'string' ? (
                          <Input
                            id={key}
                            type={key.includes('token') || key.includes('secret') ? 'password' : 'text'}
                            placeholder={schema.description}
                            value={toolConfig.config[key] || ''}
                            onChange={(e) => setToolConfig(prev => ({
                              ...prev,
                              config: { ...prev.config, [key]: e.target.value }
                            }))}
                          />
                        ) : schema.type === 'number' ? (
                          <Input
                            id={key}
                            type="number"
                            placeholder={schema.description}
                            value={toolConfig.config[key] || ''}
                            onChange={(e) => setToolConfig(prev => ({
                              ...prev,
                              config: { ...prev.config, [key]: parseInt(e.target.value) }
                            }))}
                          />
                        ) : schema.type === 'boolean' ? (
                          <Switch
                            id={key}
                            checked={toolConfig.config[key] || false}
                            onCheckedChange={(checked) => setToolConfig(prev => ({
                              ...prev,
                              config: { ...prev.config, [key]: checked }
                            }))}
                          />
                        ) : schema.type === 'array' ? (
                          <Textarea
                            id={key}
                            placeholder={`${schema.description} (uno por línea)`}
                            value={Array.isArray(toolConfig.config[key]) ? toolConfig.config[key].join('\n') : ''}
                            onChange={(e) => setToolConfig(prev => ({
                              ...prev,
                              config: { ...prev.config, [key]: e.target.value.split('\n').filter(Boolean) }
                            }))}
                            rows={3}
                          />
                        ) : null}
                        
                        <p className="text-xs text-muted-foreground">
                          {schema.description}
                        </p>
                      </div>
                    ))}
                  </div>
                )}
                
                {/* Permissions */}
                <div className="space-y-4">
                  <h4 className="text-sm font-medium">Permisos</h4>
                  
                  <div className="space-y-3">
                    <div className="flex items-center space-x-2">
                      <Switch
                        id="read-permission"
                        checked={toolConfig.permissions.read}
                        onCheckedChange={(checked) => 
                          setToolConfig(prev => ({
                            ...prev,
                            permissions: { ...prev.permissions, read: checked }
                          }))
                        }
                      />
                      <Label htmlFor="read-permission">Lectura</Label>
                      <span className="text-xs text-muted-foreground">
                        Permite leer datos y archivos
                      </span>
                    </div>
                    
                    <div className="flex items-center space-x-2">
                      <Switch
                        id="write-permission"
                        checked={toolConfig.permissions.write}
                        onCheckedChange={(checked) => 
                          setToolConfig(prev => ({
                            ...prev,
                            permissions: { ...prev.permissions, write: checked }
                          }))
                        }
                      />
                      <Label htmlFor="write-permission">Escritura</Label>
                      <span className="text-xs text-muted-foreground">
                        Permite modificar y crear datos
                      </span>
                    </div>
                    
                    <div className="flex items-center space-x-2">
                      <Switch
                        id="execute-permission"
                        checked={toolConfig.permissions.execute}
                        onCheckedChange={(checked) => 
                          setToolConfig(prev => ({
                            ...prev,
                            permissions: { ...prev.permissions, execute: checked }
                          }))
                        }
                      />
                      <Label htmlFor="execute-permission">Ejecución</Label>
                      <span className="text-xs text-muted-foreground">
                        Permite ejecutar comandos y scripts
                      </span>
                    </div>
                  </div>
                </div>
                
                <div className="flex justify-end space-x-2">
                  <Button variant="outline" onClick={() => setIsConfigDialogOpen(false)}>
                    Cancelar
                  </Button>
                  <Button onClick={saveToolConfig}>
                    Guardar Configuración
                  </Button>
                </div>
              </div>
            </ScrollArea>
          )}
        </DialogContent>
      </Dialog>
    </div>
  )
}

