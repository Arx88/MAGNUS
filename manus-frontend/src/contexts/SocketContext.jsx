import { createContext, useContext, useEffect, useState } from 'react'
import { io } from 'socket.io-client'
import { useAuth } from './AuthContext'
import { toast } from '@/hooks/use-toast'

const SocketContext = createContext({})

export const useSocket = () => {
  const context = useContext(SocketContext)
  if (!context) {
    throw new Error('useSocket must be used within a SocketProvider')
  }
  return context
}

export const SocketProvider = ({ children }) => {
  const [socket, setSocket] = useState(null)
  const [connected, setConnected] = useState(false)
  const [onlineUsers, setOnlineUsers] = useState([])
  const { user, token } = useAuth()

  useEffect(() => {
    if (user && token) {
      // Conectar al servidor WebSocket
      const newSocket = io(process.env.REACT_APP_BACKEND_URL || 'http://localhost:5000', {
        auth: {
          token: token
        },
        transports: ['websocket', 'polling']
      })

      newSocket.on('connect', () => {
        console.log('Connected to server')
        setConnected(true)
        toast({
          title: "Conectado",
          description: "Conexión en tiempo real establecida",
          duration: 2000
        })
      })

      newSocket.on('disconnect', () => {
        console.log('Disconnected from server')
        setConnected(false)
        toast({
          title: "Desconectado",
          description: "Conexión en tiempo real perdida",
          variant: "destructive",
          duration: 3000
        })
      })

      newSocket.on('connect_error', (error) => {
        console.error('Connection error:', error)
        setConnected(false)
      })

      // Eventos de usuarios en línea
      newSocket.on('users_online', (users) => {
        setOnlineUsers(users)
      })

      newSocket.on('user_joined', (userData) => {
        setOnlineUsers(prev => [...prev, userData])
        toast({
          title: "Usuario conectado",
          description: `${userData.username} se ha conectado`,
          duration: 2000
        })
      })

      newSocket.on('user_left', (userData) => {
        setOnlineUsers(prev => prev.filter(u => u.id !== userData.id))
        toast({
          title: "Usuario desconectado",
          description: `${userData.username} se ha desconectado`,
          duration: 2000
        })
      })

      // Eventos de conversaciones
      newSocket.on('new_message', (messageData) => {
        // Este evento será manejado por los componentes específicos
        console.log('New message received:', messageData)
      })

      newSocket.on('conversation_updated', (conversationData) => {
        console.log('Conversation updated:', conversationData)
      })

      // Eventos de tareas
      newSocket.on('task_created', (taskData) => {
        toast({
          title: "Nueva tarea",
          description: `Tarea "${taskData.task.title}" creada`,
          duration: 3000
        })
      })

      newSocket.on('task_updated', (taskData) => {
        toast({
          title: "Tarea actualizada",
          description: `Tarea "${taskData.task.title}" - ${taskData.task.status}`,
          duration: 3000
        })
      })

      newSocket.on('task_completed', (taskData) => {
        toast({
          title: "Tarea completada",
          description: `Tarea "${taskData.task.title}" completada exitosamente`,
          duration: 5000
        })
      })

      newSocket.on('task_failed', (taskData) => {
        toast({
          title: "Tarea fallida",
          description: `Tarea "${taskData.task.title}" falló: ${taskData.task.error_message}`,
          variant: "destructive",
          duration: 5000
        })
      })

      // Eventos del sistema
      newSocket.on('system_notification', (notification) => {
        toast({
          title: notification.title,
          description: notification.message,
          variant: notification.type === 'error' ? 'destructive' : 'default',
          duration: notification.duration || 5000
        })
      })

      newSocket.on('maintenance_mode', (data) => {
        toast({
          title: "Modo mantenimiento",
          description: data.enabled ? "El sistema entrará en mantenimiento" : "Mantenimiento finalizado",
          variant: data.enabled ? "destructive" : "default",
          duration: 10000
        })
      })

      setSocket(newSocket)

      return () => {
        newSocket.close()
        setSocket(null)
        setConnected(false)
      }
    }
  }, [user, token])

  // Funciones de utilidad para emitir eventos
  const joinConversation = (conversationId) => {
    if (socket) {
      socket.emit('join_conversation', conversationId)
    }
  }

  const leaveConversation = (conversationId) => {
    if (socket) {
      socket.emit('leave_conversation', conversationId)
    }
  }

  const sendMessage = (conversationId, message) => {
    if (socket) {
      socket.emit('send_message', {
        conversation_id: conversationId,
        content: message
      })
    }
  }

  const subscribeToTask = (taskId) => {
    if (socket) {
      socket.emit('subscribe_task', taskId)
    }
  }

  const unsubscribeFromTask = (taskId) => {
    if (socket) {
      socket.emit('unsubscribe_task', taskId)
    }
  }

  const value = {
    socket,
    connected,
    onlineUsers,
    joinConversation,
    leaveConversation,
    sendMessage,
    subscribeToTask,
    unsubscribeFromTask
  }

  return (
    <SocketContext.Provider value={value}>
      {children}
    </SocketContext.Provider>
  )
}

