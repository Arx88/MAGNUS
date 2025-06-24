import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Switch } from '@/components/ui/switch'
import { Slider } from '@/components/ui/slider'
import { useAuth } from '@/hooks/useAuth'
import {
  Bot,
  Plus,
  Search,
  MoreVertical,
  Edit,
  Trash2,
  Play,
  Pause,
  Settings,
  Activity,
  MessageSquare,
  CheckSquare,
  Clock,
  Zap
} from 'lucide-react'

export default function AgentsPage() {
  const { user, isAdmin } = useAuth()
  const [agents, setAgents] = useState([])
  const [filteredAgents, setFilteredAgents] = useState([])
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedAgent, setSelectedAgent] = useState(null)
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false)
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false)
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('all')

  // Form state for creating/editing agents
  const [agentForm, setAgentForm] = useState({
    name: '',
    description: '',
    model: 'llama2',
    system_prompt: '',
    temperature: [0.7],
    max_tokens: [4096],
    is_active: true,
    is_public: false,
    capabilities: '',
    memory_enabled: true
  })

  const [availableModels] = useState([
    { id: 'llama2', name: 'Llama 2', description: 'Modelo general de propósito' },
    { id: 'codellama', name: 'Code Llama', description: 'Especializado en programación' },
    { id: 'mistral', name: 'Mistral', description: 'Modelo eficiente y rápido' },
    { id: 'neural-chat', name: 'Neural Chat', description: 'Optimizado para conversaciones' }
  ])

  useEffect(() => {
    loadAgents()
  }, [])

  useEffect(() => {
    filterAgents()
  }, [agents, searchQuery, activeTab])

  const loadAgents = async () => {
    try {
      // Simulated API call
      const mockAgents = [
        {
          id: '1',
          name: 'Asistente General',
          description: 'Asistente de propósito general para tareas variadas',
          model: 'llama2',
          system_prompt: 'Eres un asistente útil y amigable.',
          temperature: 0.7,
          max_tokens: 4096,
          is_active: true,
          is_public: true,
          created_by: user.id,
          created_at: new Date().toISOString(),
          stats: {
            conversations: 45,
            messages: 1250,
            tasks_completed: 23,
            success_rate: 95
          }
        },
        {
          id: '2',
          name: 'Analista de Datos',
          description: 'Especializado en análisis y visualización de datos',
          model: 'codellama',
          system_prompt: 'Eres un experto en análisis de datos y estadísticas.',
          temperature: 0.3,
          max_tokens: 8192,
          is_active: true,
          is_public: false,
          created_by: user.id,
          created_at: new Date(Date.now() - 86400000).toISOString(),
          stats: {
            conversations: 12,
            messages: 340,
            tasks_completed: 8,
            success_rate: 100
          }
        },
        {
          id: '3',
          name: 'Programador',
          description: 'Asistente para desarrollo de software',
          model: 'codellama',
          system_prompt: 'Eres un programador experto en múltiples lenguajes.',
          temperature: 0.2,
          max_tokens: 8192,
          is_active: false,
          is_public: true,
          created_by: 'other_user',
          created_at: new Date(Date.now() - 172800000).toISOString(),
          stats: {
            conversations: 8,
            messages: 156,
            tasks_completed: 5,
            success_rate: 80
          }
        }
      ]
      
      setAgents(mockAgents)
    } catch (error) {
      console.error('Error loading agents:', error)
    } finally {
      setLoading(false)
    }
  }

  const filterAgents = () => {
    let filtered = agents

    // Filter by tab
    switch (activeTab) {
      case 'my':
        filtered = filtered.filter(agent => agent.created_by === user.id)
        break
      case 'public':
        filtered = filtered.filter(agent => agent.is_public)
        break
      case 'active':
        filtered = filtered.filter(agent => agent.is_active)
        break
      default:
        // 'all' - no additional filtering
        break
    }

    // Filter by search query
    if (searchQuery) {
      filtered = filtered.filter(agent =>
        agent.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        agent.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
        agent.model.toLowerCase().includes(searchQuery.toLowerCase())
      )
    }

    setFilteredAgents(filtered)
  }

  const handleCreateAgent = async () => {
    try {
      const newAgent = {
        id: Date.now().toString(),
        ...agentForm,
        temperature: agentForm.temperature[0],
        max_tokens: agentForm.max_tokens[0],
        created_by: user.id,
        created_at: new Date().toISOString(),
        stats: {
          conversations: 0,
          messages: 0,
          tasks_completed: 0,
          success_rate: 0
        }
      }

      setAgents(prev => [newAgent, ...prev])
      setIsCreateDialogOpen(false)
      resetForm()
    } catch (error) {
      console.error('Error creating agent:', error)
    }
  }

  const handleEditAgent = async () => {
    try {
      const updatedAgent = {
        ...selectedAgent,
        ...agentForm,
        temperature: agentForm.temperature[0],
        max_tokens: agentForm.max_tokens[0]
      }

      setAgents(prev => prev.map(agent => 
        agent.id === selectedAgent.id ? updatedAgent : agent
      ))
      setIsEditDialogOpen(false)
      setSelectedAgent(null)
      resetForm()
    } catch (error) {
      console.error('Error updating agent:', error)
    }
  }

  const handleDeleteAgent = async (agentId) => {
    if (window.confirm('¿Estás seguro de que quieres eliminar este agente?')) {
      try {
        setAgents(prev => prev.filter(agent => agent.id !== agentId))
      } catch (error) {
        console.error('Error deleting agent:', error)
      }
    }
  }

  const handleToggleAgent = async (agentId, isActive) => {
    try {
      setAgents(prev => prev.map(agent =>
        agent.id === agentId ? { ...agent, is_active: !isActive } : agent
      ))
    } catch (error) {
      console.error('Error toggling agent:', error)
    }
  }

  const resetForm = () => {
    setAgentForm({
      name: '',
      description: '',
      model: 'llama2',
      system_prompt: '',
      temperature: [0.7],
      max_tokens: [4096],
      is_active: true,
      is_public: false,
      capabilities: '',
      memory_enabled: true
    })
  }

  const openEditDialog = (agent) => {
    setSelectedAgent(agent)
    setAgentForm({
      name: agent.name,
      description: agent.description,
      model: agent.model,
      system_prompt: agent.system_prompt,
      temperature: [agent.temperature],
      max_tokens: [agent.max_tokens],
      is_active: agent.is_active,
      is_public: agent.is_public,
      capabilities: agent.capabilities || '',
      memory_enabled: agent.memory_enabled !== false
    })
    setIsEditDialogOpen(true)
  }

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('es-ES', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    })
  }

  const getModelBadgeColor = (model) => {
    const colors = {
      'llama2': 'bg-blue-100 text-blue-800',
      'codellama': 'bg-green-100 text-green-800',
      'mistral': 'bg-purple-100 text-purple-800',
      'neural-chat': 'bg-orange-100 text-orange-800'
    }
    return colors[model] || 'bg-gray-100 text-gray-800'
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
          <h1 className="text-3xl font-bold">Agentes</h1>
          <p className="text-muted-foreground">
            Gestiona y configura tus agentes IA
          </p>
        </div>
        
        <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="w-4 h-4 mr-2" />
              Crear Agente
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle>Crear Nuevo Agente</DialogTitle>
              <DialogDescription>
                Configura un nuevo agente IA con capacidades personalizadas
              </DialogDescription>
            </DialogHeader>
            
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="name">Nombre</Label>
                  <Input
                    id="name"
                    value={agentForm.name}
                    onChange={(e) => setAgentForm(prev => ({ ...prev, name: e.target.value }))}
                    placeholder="Nombre del agente"
                  />
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="model">Modelo</Label>
                  <select
                    id="model"
                    value={agentForm.model}
                    onChange={(e) => setAgentForm(prev => ({ ...prev, model: e.target.value }))}
                    className="w-full p-2 border border-input rounded-md"
                  >
                    {availableModels.map(model => (
                      <option key={model.id} value={model.id}>
                        {model.name} - {model.description}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="description">Descripción</Label>
                <Input
                  id="description"
                  value={agentForm.description}
                  onChange={(e) => setAgentForm(prev => ({ ...prev, description: e.target.value }))}
                  placeholder="Describe las capacidades del agente"
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="system_prompt">Prompt del Sistema</Label>
                <Textarea
                  id="system_prompt"
                  value={agentForm.system_prompt}
                  onChange={(e) => setAgentForm(prev => ({ ...prev, system_prompt: e.target.value }))}
                  placeholder="Define la personalidad y comportamiento del agente"
                  rows={4}
                />
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Temperatura: {agentForm.temperature[0]}</Label>
                  <Slider
                    value={agentForm.temperature}
                    onValueChange={(value) => setAgentForm(prev => ({ ...prev, temperature: value }))}
                    max={2}
                    min={0}
                    step={0.1}
                  />
                </div>
                
                <div className="space-y-2">
                  <Label>Tokens Máximos: {agentForm.max_tokens[0]}</Label>
                  <Slider
                    value={agentForm.max_tokens}
                    onValueChange={(value) => setAgentForm(prev => ({ ...prev, max_tokens: value }))}
                    max={8192}
                    min={512}
                    step={256}
                  />
                </div>
              </div>
              
              <div className="flex items-center space-x-4">
                <div className="flex items-center space-x-2">
                  <Switch
                    id="is_active"
                    checked={agentForm.is_active}
                    onCheckedChange={(checked) => setAgentForm(prev => ({ ...prev, is_active: checked }))}
                  />
                  <Label htmlFor="is_active">Activo</Label>
                </div>
                
                <div className="flex items-center space-x-2">
                  <Switch
                    id="is_public"
                    checked={agentForm.is_public}
                    onCheckedChange={(checked) => setAgentForm(prev => ({ ...prev, is_public: checked }))}
                  />
                  <Label htmlFor="is_public">Público</Label>
                </div>
                
                <div className="flex items-center space-x-2">
                  <Switch
                    id="memory_enabled"
                    checked={agentForm.memory_enabled}
                    onCheckedChange={(checked) => setAgentForm(prev => ({ ...prev, memory_enabled: checked }))}
                  />
                  <Label htmlFor="memory_enabled">Memoria</Label>
                </div>
              </div>
              
              <div className="flex justify-end space-x-2">
                <Button variant="outline" onClick={() => setIsCreateDialogOpen(false)}>
                  Cancelar
                </Button>
                <Button onClick={handleCreateAgent}>
                  Crear Agente
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {/* Search and Filters */}
      <div className="flex items-center space-x-4">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Buscar agentes..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>
        
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList>
            <TabsTrigger value="all">Todos</TabsTrigger>
            <TabsTrigger value="my">Mis Agentes</TabsTrigger>
            <TabsTrigger value="public">Públicos</TabsTrigger>
            <TabsTrigger value="active">Activos</TabsTrigger>
          </TabsList>
        </Tabs>
      </div>

      {/* Agents Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredAgents.map((agent) => (
          <Card key={agent.id} className="hover:shadow-lg transition-shadow">
            <CardHeader className="pb-3">
              <div className="flex items-start justify-between">
                <div className="flex items-center space-x-3">
                  <Avatar>
                    <AvatarFallback>
                      <Bot className="w-5 h-5" />
                    </AvatarFallback>
                  </Avatar>
                  <div>
                    <CardTitle className="text-lg">{agent.name}</CardTitle>
                    <div className="flex items-center space-x-2 mt-1">
                      <Badge className={getModelBadgeColor(agent.model)}>
                        {agent.model}
                      </Badge>
                      <Badge variant={agent.is_active ? "default" : "secondary"}>
                        {agent.is_active ? "Activo" : "Inactivo"}
                      </Badge>
                      {agent.is_public && (
                        <Badge variant="outline">Público</Badge>
                      )}
                    </div>
                  </div>
                </div>
                
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                      <MoreVertical className="w-4 h-4" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    <DropdownMenuItem onClick={() => openEditDialog(agent)}>
                      <Edit className="w-4 h-4 mr-2" />
                      Editar
                    </DropdownMenuItem>
                    <DropdownMenuItem 
                      onClick={() => handleToggleAgent(agent.id, agent.is_active)}
                    >
                      {agent.is_active ? (
                        <>
                          <Pause className="w-4 h-4 mr-2" />
                          Desactivar
                        </>
                      ) : (
                        <>
                          <Play className="w-4 h-4 mr-2" />
                          Activar
                        </>
                      )}
                    </DropdownMenuItem>
                    <DropdownMenuItem>
                      <Settings className="w-4 h-4 mr-2" />
                      Configurar
                    </DropdownMenuItem>
                    {(agent.created_by === user.id || isAdmin) && (
                      <DropdownMenuItem 
                        onClick={() => handleDeleteAgent(agent.id)}
                        className="text-destructive"
                      >
                        <Trash2 className="w-4 h-4 mr-2" />
                        Eliminar
                      </DropdownMenuItem>
                    )}
                  </DropdownMenuContent>
                </DropdownMenu>
              </div>
            </CardHeader>
            
            <CardContent className="space-y-4">
              <CardDescription className="text-sm">
                {agent.description}
              </CardDescription>
              
              {/* Stats */}
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div className="flex items-center space-x-2">
                  <MessageSquare className="w-4 h-4 text-muted-foreground" />
                  <span>{agent.stats.conversations} conversaciones</span>
                </div>
                <div className="flex items-center space-x-2">
                  <CheckSquare className="w-4 h-4 text-muted-foreground" />
                  <span>{agent.stats.tasks_completed} tareas</span>
                </div>
                <div className="flex items-center space-x-2">
                  <Activity className="w-4 h-4 text-muted-foreground" />
                  <span>{agent.stats.success_rate}% éxito</span>
                </div>
                <div className="flex items-center space-x-2">
                  <Clock className="w-4 h-4 text-muted-foreground" />
                  <span>{formatDate(agent.created_at)}</span>
                </div>
              </div>
              
              {/* Configuration Preview */}
              <div className="text-xs text-muted-foreground space-y-1">
                <div>Temperatura: {agent.temperature}</div>
                <div>Tokens máx: {agent.max_tokens}</div>
              </div>
              
              <div className="flex space-x-2">
                <Button size="sm" className="flex-1">
                  <MessageSquare className="w-4 h-4 mr-2" />
                  Chatear
                </Button>
                <Button size="sm" variant="outline">
                  <Zap className="w-4 h-4" />
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {filteredAgents.length === 0 && (
        <div className="text-center py-12">
          <Bot className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
          <h3 className="text-lg font-semibold mb-2">No se encontraron agentes</h3>
          <p className="text-muted-foreground mb-4">
            {searchQuery ? 'Intenta con otros términos de búsqueda' : 'Crea tu primer agente para comenzar'}
          </p>
          {!searchQuery && (
            <Button onClick={() => setIsCreateDialogOpen(true)}>
              <Plus className="w-4 h-4 mr-2" />
              Crear Primer Agente
            </Button>
          )}
        </div>
      )}

      {/* Edit Dialog */}
      <Dialog open={isEditDialogOpen} onOpenChange={setIsEditDialogOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Editar Agente</DialogTitle>
            <DialogDescription>
              Modifica la configuración del agente
            </DialogDescription>
          </DialogHeader>
          
          {/* Same form as create, but with handleEditAgent */}
          <div className="space-y-4">
            {/* Form content identical to create dialog */}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="edit-name">Nombre</Label>
                <Input
                  id="edit-name"
                  value={agentForm.name}
                  onChange={(e) => setAgentForm(prev => ({ ...prev, name: e.target.value }))}
                  placeholder="Nombre del agente"
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="edit-model">Modelo</Label>
                <select
                  id="edit-model"
                  value={agentForm.model}
                  onChange={(e) => setAgentForm(prev => ({ ...prev, model: e.target.value }))}
                  className="w-full p-2 border border-input rounded-md"
                >
                  {availableModels.map(model => (
                    <option key={model.id} value={model.id}>
                      {model.name} - {model.description}
                    </option>
                  ))}
                </select>
              </div>
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="edit-description">Descripción</Label>
              <Input
                id="edit-description"
                value={agentForm.description}
                onChange={(e) => setAgentForm(prev => ({ ...prev, description: e.target.value }))}
                placeholder="Describe las capacidades del agente"
              />
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="edit-system_prompt">Prompt del Sistema</Label>
              <Textarea
                id="edit-system_prompt"
                value={agentForm.system_prompt}
                onChange={(e) => setAgentForm(prev => ({ ...prev, system_prompt: e.target.value }))}
                placeholder="Define la personalidad y comportamiento del agente"
                rows={4}
              />
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Temperatura: {agentForm.temperature[0]}</Label>
                <Slider
                  value={agentForm.temperature}
                  onValueChange={(value) => setAgentForm(prev => ({ ...prev, temperature: value }))}
                  max={2}
                  min={0}
                  step={0.1}
                />
              </div>
              
              <div className="space-y-2">
                <Label>Tokens Máximos: {agentForm.max_tokens[0]}</Label>
                <Slider
                  value={agentForm.max_tokens}
                  onValueChange={(value) => setAgentForm(prev => ({ ...prev, max_tokens: value }))}
                  max={8192}
                  min={512}
                  step={256}
                />
              </div>
            </div>
            
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <Switch
                  id="edit-is_active"
                  checked={agentForm.is_active}
                  onCheckedChange={(checked) => setAgentForm(prev => ({ ...prev, is_active: checked }))}
                />
                <Label htmlFor="edit-is_active">Activo</Label>
              </div>
              
              <div className="flex items-center space-x-2">
                <Switch
                  id="edit-is_public"
                  checked={agentForm.is_public}
                  onCheckedChange={(checked) => setAgentForm(prev => ({ ...prev, is_public: checked }))}
                />
                <Label htmlFor="edit-is_public">Público</Label>
              </div>
              
              <div className="flex items-center space-x-2">
                <Switch
                  id="edit-memory_enabled"
                  checked={agentForm.memory_enabled}
                  onCheckedChange={(checked) => setAgentForm(prev => ({ ...prev, memory_enabled: checked }))}
                />
                <Label htmlFor="edit-memory_enabled">Memoria</Label>
              </div>
            </div>
            
            <div className="flex justify-end space-x-2">
              <Button variant="outline" onClick={() => setIsEditDialogOpen(false)}>
                Cancelar
              </Button>
              <Button onClick={handleEditAgent}>
                Guardar Cambios
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  )
}

