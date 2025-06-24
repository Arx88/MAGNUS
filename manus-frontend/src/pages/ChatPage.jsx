import { useState, useEffect, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Separator } from '@/components/ui/separator'
import { Badge } from '@/components/ui/badge'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Textarea } from '@/components/ui/textarea'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { useAuth } from '@/hooks/useAuth'
import { useSocket } from '@/contexts/SocketContext'
import {
  Send,
  Plus,
  Bot,
  User,
  MoreVertical,
  Trash2,
  Edit,
  Copy,
  Download,
  Paperclip,
  Mic,
  Square,
  Play,
  MessageSquare,
  Clock,
  CheckCircle,
  AlertCircle
} from 'lucide-react'

export default function ChatPage() {
  const { conversationId } = useParams()
  const navigate = useNavigate()
  const { user } = useAuth()
  const { socket, connected, joinConversation, leaveConversation } = useSocket()
  
  const [conversations, setConversations] = useState([])
  const [currentConversation, setCurrentConversation] = useState(null)
  const [messages, setMessages] = useState([])
  const [newMessage, setNewMessage] = useState('')
  const [loading, setLoading] = useState(false)
  const [agents, setAgents] = useState([])
  const [selectedAgent, setSelectedAgent] = useState(null)
  const [isTyping, setIsTyping] = useState(false)
  
  const messagesEndRef = useRef(null)
  const textareaRef = useRef(null)

  // Scroll to bottom when new messages arrive
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // Load conversations and agents on mount
  useEffect(() => {
    loadConversations()
    loadAgents()
  }, [])

  // Handle conversation selection
  useEffect(() => {
    if (conversationId) {
      loadConversation(conversationId)
      joinConversation(conversationId)
      
      return () => {
        leaveConversation(conversationId)
      }
    }
  }, [conversationId])

  // Socket event listeners
  useEffect(() => {
    if (socket) {
      socket.on('new_message', handleNewMessage)
      socket.on('agent_typing', handleAgentTyping)
      socket.on('agent_stopped_typing', handleAgentStoppedTyping)
      
      return () => {
        socket.off('new_message', handleNewMessage)
        socket.off('agent_typing', handleAgentTyping)
        socket.off('agent_stopped_typing', handleAgentStoppedTyping)
      }
    }
  }, [socket, conversationId])

  const loadConversations = async () => {
    try {
      // Simulated API call
      const mockConversations = [
        {
          id: '1',
          title: 'Asistente General',
          agent_name: 'GPT Assistant',
          last_message: 'Hola, ¿en qué puedo ayudarte hoy?',
          updated_at: new Date().toISOString(),
          status: 'active'
        },
        {
          id: '2',
          title: 'Análisis de Datos',
          agent_name: 'Data Analyst',
          last_message: 'He completado el análisis de los datos que me proporcionaste.',
          updated_at: new Date(Date.now() - 3600000).toISOString(),
          status: 'active'
        }
      ]
      setConversations(mockConversations)
    } catch (error) {
      console.error('Error loading conversations:', error)
    }
  }

  const loadAgents = async () => {
    try {
      // Simulated API call
      const mockAgents = [
        {
          id: '1',
          name: 'Asistente General',
          description: 'Asistente de propósito general para tareas variadas',
          model: 'llama2',
          is_active: true
        },
        {
          id: '2',
          name: 'Analista de Datos',
          description: 'Especializado en análisis y visualización de datos',
          model: 'codellama',
          is_active: true
        },
        {
          id: '3',
          name: 'Programador',
          description: 'Asistente para desarrollo de software',
          model: 'codellama',
          is_active: true
        }
      ]
      setAgents(mockAgents)
      if (mockAgents.length > 0) {
        setSelectedAgent(mockAgents[0])
      }
    } catch (error) {
      console.error('Error loading agents:', error)
    }
  }

  const loadConversation = async (id) => {
    try {
      // Simulated API call
      const mockMessages = [
        {
          id: '1',
          role: 'user',
          content: 'Hola, necesito ayuda con un proyecto de análisis de datos.',
          created_at: new Date(Date.now() - 7200000).toISOString(),
          user_id: user.id
        },
        {
          id: '2',
          role: 'assistant',
          content: 'Hola! Estaré encantado de ayudarte con tu proyecto de análisis de datos. ¿Podrías contarme más detalles sobre:\n\n1. ¿Qué tipo de datos tienes?\n2. ¿Cuál es el objetivo del análisis?\n3. ¿Hay alguna pregunta específica que quieres responder?\n\nCon esta información podré guiarte mejor en el proceso.',
          created_at: new Date(Date.now() - 7100000).toISOString(),
          agent_id: '1'
        },
        {
          id: '3',
          role: 'user',
          content: 'Tengo datos de ventas de los últimos 2 años y quiero identificar patrones estacionales.',
          created_at: new Date(Date.now() - 3600000).toISOString(),
          user_id: user.id
        },
        {
          id: '4',
          role: 'assistant',
          content: 'Perfecto! Para identificar patrones estacionales en datos de ventas, te sugiero seguir estos pasos:\n\n**1. Preparación de datos:**\n- Asegurar que las fechas estén en formato correcto\n- Verificar que no haya valores faltantes\n- Agregar columnas de tiempo (mes, trimestre, día de la semana)\n\n**2. Análisis exploratorio:**\n- Gráfico de serie temporal\n- Análisis de tendencias por mes/trimestre\n- Comparación año a año\n\n**3. Técnicas específicas:**\n- Descomposición estacional\n- Análisis de autocorrelación\n- Modelos SARIMA si es necesario\n\n¿Tienes los datos en algún formato específico (CSV, Excel, base de datos)?',
          created_at: new Date(Date.now() - 3500000).toISOString(),
          agent_id: '1'
        }
      ]
      
      setMessages(mockMessages)
      
      const conversation = conversations.find(c => c.id === id)
      setCurrentConversation(conversation)
    } catch (error) {
      console.error('Error loading conversation:', error)
    }
  }

  const handleNewMessage = (messageData) => {
    if (messageData.conversation_id === conversationId) {
      setMessages(prev => [...prev, messageData.message])
      setIsTyping(false)
    }
  }

  const handleAgentTyping = (data) => {
    if (data.conversation_id === conversationId) {
      setIsTyping(true)
    }
  }

  const handleAgentStoppedTyping = (data) => {
    if (data.conversation_id === conversationId) {
      setIsTyping(false)
    }
  }

  const sendMessage = async () => {
    if (!newMessage.trim() || loading) return

    const messageContent = newMessage.trim()
    setNewMessage('')
    setLoading(true)

    try {
      // Add user message immediately
      const userMessage = {
        id: Date.now().toString(),
        role: 'user',
        content: messageContent,
        created_at: new Date().toISOString(),
        user_id: user.id
      }
      
      setMessages(prev => [...prev, userMessage])
      
      // Simulate agent typing
      setIsTyping(true)
      
      // Simulate API call delay
      setTimeout(() => {
        const agentMessage = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: `Entiendo tu consulta: "${messageContent}". Estoy procesando esta información y te ayudaré con una respuesta detallada. ¿Hay algún aspecto específico en el que te gustaría que me enfoque?`,
          created_at: new Date().toISOString(),
          agent_id: selectedAgent?.id
        }
        
        setMessages(prev => [...prev, agentMessage])
        setIsTyping(false)
        setLoading(false)
      }, 2000)
      
    } catch (error) {
      console.error('Error sending message:', error)
      setLoading(false)
      setIsTyping(false)
    }
  }

  const createNewConversation = async () => {
    if (!selectedAgent) return

    try {
      const newConv = {
        id: Date.now().toString(),
        title: `Chat con ${selectedAgent.name}`,
        agent_name: selectedAgent.name,
        last_message: '',
        updated_at: new Date().toISOString(),
        status: 'active'
      }
      
      setConversations(prev => [newConv, ...prev])
      navigate(`/chat/${newConv.id}`)
    } catch (error) {
      console.error('Error creating conversation:', error)
    }
  }

  const formatTime = (timestamp) => {
    const date = new Date(timestamp)
    const now = new Date()
    const diffInHours = (now - date) / (1000 * 60 * 60)
    
    if (diffInHours < 1) {
      return 'Hace unos minutos'
    } else if (diffInHours < 24) {
      return `Hace ${Math.floor(diffInHours)} horas`
    } else {
      return date.toLocaleDateString()
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  return (
    <div className="flex h-full bg-background">
      {/* Conversations Sidebar */}
      <div className="w-80 border-r border-border flex flex-col">
        {/* Header */}
        <div className="p-4 border-b border-border">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold">Conversaciones</h2>
            <Button size="sm" onClick={createNewConversation}>
              <Plus className="w-4 h-4 mr-2" />
              Nueva
            </Button>
          </div>
          
          {/* Agent Selector */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline" className="w-full justify-start">
                <Bot className="w-4 h-4 mr-2" />
                {selectedAgent?.name || 'Seleccionar Agente'}
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent className="w-72">
              {agents.map((agent) => (
                <DropdownMenuItem
                  key={agent.id}
                  onClick={() => setSelectedAgent(agent)}
                  className="flex flex-col items-start p-3"
                >
                  <div className="flex items-center w-full">
                    <Bot className="w-4 h-4 mr-2" />
                    <span className="font-medium">{agent.name}</span>
                    <Badge variant="outline" className="ml-auto text-xs">
                      {agent.model}
                    </Badge>
                  </div>
                  <p className="text-xs text-muted-foreground mt-1">
                    {agent.description}
                  </p>
                </DropdownMenuItem>
              ))}
            </DropdownMenuContent>
          </DropdownMenu>
        </div>

        {/* Conversations List */}
        <ScrollArea className="flex-1">
          <div className="p-2 space-y-2">
            {conversations.map((conversation) => (
              <Card
                key={conversation.id}
                className={`cursor-pointer transition-colors hover:bg-accent/50 ${
                  conversationId === conversation.id ? 'bg-accent' : ''
                }`}
                onClick={() => navigate(`/chat/${conversation.id}`)}
              >
                <CardContent className="p-3">
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center space-x-2 mb-1">
                        <Bot className="w-4 h-4 text-primary flex-shrink-0" />
                        <h3 className="text-sm font-medium truncate">
                          {conversation.title}
                        </h3>
                      </div>
                      <p className="text-xs text-muted-foreground truncate">
                        {conversation.last_message}
                      </p>
                      <p className="text-xs text-muted-foreground mt-1">
                        {formatTime(conversation.updated_at)}
                      </p>
                    </div>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="sm" className="h-6 w-6 p-0">
                          <MoreVertical className="w-3 h-3" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent>
                        <DropdownMenuItem>
                          <Edit className="w-4 h-4 mr-2" />
                          Renombrar
                        </DropdownMenuItem>
                        <DropdownMenuItem>
                          <Download className="w-4 h-4 mr-2" />
                          Exportar
                        </DropdownMenuItem>
                        <DropdownMenuItem className="text-destructive">
                          <Trash2 className="w-4 h-4 mr-2" />
                          Eliminar
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </ScrollArea>
      </div>

      {/* Chat Area */}
      <div className="flex-1 flex flex-col">
        {currentConversation ? (
          <>
            {/* Chat Header */}
            <div className="p-4 border-b border-border">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <Avatar>
                    <AvatarFallback>
                      <Bot className="w-5 h-5" />
                    </AvatarFallback>
                  </Avatar>
                  <div>
                    <h3 className="font-semibold">{currentConversation.agent_name}</h3>
                    <div className="flex items-center space-x-2">
                      <div className={`w-2 h-2 rounded-full ${connected ? 'bg-green-500' : 'bg-red-500'}`} />
                      <span className="text-xs text-muted-foreground">
                        {connected ? 'En línea' : 'Desconectado'}
                      </span>
                      {isTyping && (
                        <span className="text-xs text-primary">Escribiendo...</span>
                      )}
                    </div>
                  </div>
                </div>
                
                <div className="flex items-center space-x-2">
                  <Badge variant="outline">
                    {messages.filter(m => m.role === 'user').length} mensajes
                  </Badge>
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" size="sm">
                        <MoreVertical className="w-4 h-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent>
                      <DropdownMenuItem>
                        <Download className="w-4 h-4 mr-2" />
                        Exportar Chat
                      </DropdownMenuItem>
                      <DropdownMenuItem>
                        <Copy className="w-4 h-4 mr-2" />
                        Copiar Conversación
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>
              </div>
            </div>

            {/* Messages */}
            <ScrollArea className="flex-1 p-4">
              <div className="space-y-4">
                {messages.map((message) => (
                  <div
                    key={message.id}
                    className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    <div className={`flex space-x-3 max-w-[80%] ${message.role === 'user' ? 'flex-row-reverse space-x-reverse' : ''}`}>
                      <Avatar className="w-8 h-8">
                        <AvatarFallback>
                          {message.role === 'user' ? (
                            <User className="w-4 h-4" />
                          ) : (
                            <Bot className="w-4 h-4" />
                          )}
                        </AvatarFallback>
                      </Avatar>
                      
                      <div className={`rounded-lg p-3 ${
                        message.role === 'user'
                          ? 'bg-primary text-primary-foreground'
                          : 'bg-muted'
                      }`}>
                        <div className="whitespace-pre-wrap text-sm">
                          {message.content}
                        </div>
                        <div className={`text-xs mt-2 ${
                          message.role === 'user' 
                            ? 'text-primary-foreground/70' 
                            : 'text-muted-foreground'
                        }`}>
                          {formatTime(message.created_at)}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
                
                {isTyping && (
                  <div className="flex justify-start">
                    <div className="flex space-x-3 max-w-[80%]">
                      <Avatar className="w-8 h-8">
                        <AvatarFallback>
                          <Bot className="w-4 h-4" />
                        </AvatarFallback>
                      </Avatar>
                      <div className="bg-muted rounded-lg p-3">
                        <div className="flex space-x-1">
                          <div className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce" />
                          <div className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce" style={{ animationDelay: '0.1s' }} />
                          <div className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
                        </div>
                      </div>
                    </div>
                  </div>
                )}
                
                <div ref={messagesEndRef} />
              </div>
            </ScrollArea>

            {/* Message Input */}
            <div className="p-4 border-t border-border">
              <div className="flex items-end space-x-2">
                <div className="flex-1">
                  <Textarea
                    ref={textareaRef}
                    value={newMessage}
                    onChange={(e) => setNewMessage(e.target.value)}
                    onKeyPress={handleKeyPress}
                    placeholder="Escribe tu mensaje..."
                    className="min-h-[60px] max-h-32 resize-none"
                    disabled={loading || !connected}
                  />
                </div>
                
                <div className="flex flex-col space-y-2">
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-8 w-8 p-0"
                  >
                    <Paperclip className="w-4 h-4" />
                  </Button>
                  
                  <Button
                    onClick={sendMessage}
                    disabled={!newMessage.trim() || loading || !connected}
                    className="h-10 w-10 p-0"
                  >
                    <Send className="w-4 h-4" />
                  </Button>
                </div>
              </div>
              
              <div className="flex items-center justify-between mt-2 text-xs text-muted-foreground">
                <span>
                  Presiona Enter para enviar, Shift+Enter para nueva línea
                </span>
                <span>
                  {connected ? 'Conectado' : 'Desconectado'}
                </span>
              </div>
            </div>
          </>
        ) : (
          /* Welcome Screen */
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center space-y-4">
              <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center mx-auto">
                <MessageSquare className="w-8 h-8 text-primary" />
              </div>
              <h3 className="text-xl font-semibold">Bienvenido a MANUS</h3>
              <p className="text-muted-foreground max-w-md">
                Selecciona una conversación existente o crea una nueva para comenzar a chatear con tus agentes IA.
              </p>
              <Button onClick={createNewConversation}>
                <Plus className="w-4 h-4 mr-2" />
                Iniciar Nueva Conversación
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

