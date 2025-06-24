import { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Separator } from '@/components/ui/separator'
import { Badge } from '@/components/ui/badge'
import { useAuth } from '@/hooks/useAuth'
import { useSocket } from '@/contexts/SocketContext'
import {
  MessageSquare,
  Bot,
  CheckSquare,
  Wrench,
  FileText,
  Settings,
  Shield,
  Users,
  Activity,
  ChevronLeft,
  ChevronRight,
  LogOut,
  User,
  Zap
} from 'lucide-react'

const navigation = [
  {
    name: 'Chat',
    href: '/chat',
    icon: MessageSquare,
    description: 'Conversaciones con agentes'
  },
  {
    name: 'Agentes',
    href: '/agents',
    icon: Bot,
    description: 'Gestionar agentes IA'
  },
  {
    name: 'Tareas',
    href: '/tasks',
    icon: CheckSquare,
    description: 'Seguimiento de tareas'
  },
  {
    name: 'Herramientas',
    href: '/tools',
    icon: Wrench,
    description: 'Herramientas disponibles'
  },
  {
    name: 'Archivos',
    href: '/files',
    icon: FileText,
    description: 'Gestión de archivos'
  }
]

const adminNavigation = [
  {
    name: 'Panel Admin',
    href: '/admin',
    icon: Shield,
    description: 'Administración del sistema'
  }
]

const bottomNavigation = [
  {
    name: 'Configuración',
    href: '/settings',
    icon: Settings,
    description: 'Configuración personal'
  }
]

export default function Sidebar({ open, onToggle }) {
  const location = useLocation()
  const { user, logout, isAdmin } = useAuth()
  const { connected, onlineUsers } = useSocket()
  const [hoveredItem, setHoveredItem] = useState(null)

  const isActive = (href) => {
    if (href === '/chat') {
      return location.pathname === '/chat' || location.pathname.startsWith('/chat/')
    }
    return location.pathname === href
  }

  const handleLogout = async () => {
    await logout()
  }

  return (
    <div className={cn(
      "relative flex flex-col bg-sidebar border-r border-sidebar-border transition-all duration-300",
      open ? "w-64" : "w-16"
    )}>
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-sidebar-border">
        {open && (
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
              <Zap className="w-5 h-5 text-primary-foreground" />
            </div>
            <div>
              <h1 className="text-lg font-semibold text-sidebar-foreground">MANUS</h1>
              <p className="text-xs text-sidebar-foreground/60">AI Agent Platform</p>
            </div>
          </div>
        )}
        
        <Button
          variant="ghost"
          size="sm"
          onClick={onToggle}
          className="h-8 w-8 p-0"
        >
          {open ? (
            <ChevronLeft className="h-4 w-4" />
          ) : (
            <ChevronRight className="h-4 w-4" />
          )}
        </Button>
      </div>

      {/* User Info */}
      {open && (
        <div className="p-4 border-b border-sidebar-border">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-primary/10 rounded-full flex items-center justify-center">
              <User className="w-5 h-5 text-primary" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-sidebar-foreground truncate">
                {user?.full_name || user?.username}
              </p>
              <div className="flex items-center space-x-2">
                <div className={cn(
                  "w-2 h-2 rounded-full",
                  connected ? "bg-green-500" : "bg-red-500"
                )} />
                <p className="text-xs text-sidebar-foreground/60">
                  {connected ? 'En línea' : 'Desconectado'}
                </p>
              </div>
            </div>
          </div>
          
          {isAdmin && (
            <Badge variant="secondary" className="mt-2 text-xs">
              Administrador
            </Badge>
          )}
        </div>
      )}

      {/* Navigation */}
      <ScrollArea className="flex-1 px-2 py-4">
        <nav className="space-y-1">
          {/* Main Navigation */}
          {navigation.map((item) => {
            const Icon = item.icon
            const active = isActive(item.href)
            
            return (
              <Link
                key={item.name}
                to={item.href}
                onMouseEnter={() => setHoveredItem(item.name)}
                onMouseLeave={() => setHoveredItem(null)}
                className={cn(
                  "flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors relative",
                  active
                    ? "bg-sidebar-accent text-sidebar-accent-foreground"
                    : "text-sidebar-foreground hover:bg-sidebar-accent/50 hover:text-sidebar-accent-foreground"
                )}
              >
                <Icon className={cn("flex-shrink-0", open ? "mr-3 h-5 w-5" : "h-5 w-5")} />
                {open && <span>{item.name}</span>}
                
                {/* Tooltip for collapsed sidebar */}
                {!open && hoveredItem === item.name && (
                  <div className="absolute left-full ml-2 px-2 py-1 bg-popover text-popover-foreground text-xs rounded-md shadow-lg border z-50 whitespace-nowrap">
                    {item.name}
                    <div className="text-xs text-muted-foreground mt-1">
                      {item.description}
                    </div>
                  </div>
                )}
              </Link>
            )
          })}

          {/* Admin Navigation */}
          {isAdmin && (
            <>
              <Separator className="my-4" />
              {adminNavigation.map((item) => {
                const Icon = item.icon
                const active = isActive(item.href)
                
                return (
                  <Link
                    key={item.name}
                    to={item.href}
                    onMouseEnter={() => setHoveredItem(item.name)}
                    onMouseLeave={() => setHoveredItem(null)}
                    className={cn(
                      "flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors relative",
                      active
                        ? "bg-sidebar-accent text-sidebar-accent-foreground"
                        : "text-sidebar-foreground hover:bg-sidebar-accent/50 hover:text-sidebar-accent-foreground"
                    )}
                  >
                    <Icon className={cn("flex-shrink-0", open ? "mr-3 h-5 w-5" : "h-5 w-5")} />
                    {open && <span>{item.name}</span>}
                    
                    {!open && hoveredItem === item.name && (
                      <div className="absolute left-full ml-2 px-2 py-1 bg-popover text-popover-foreground text-xs rounded-md shadow-lg border z-50 whitespace-nowrap">
                        {item.name}
                        <div className="text-xs text-muted-foreground mt-1">
                          {item.description}
                        </div>
                      </div>
                    )}
                  </Link>
                )
              })}
            </>
          )}
        </nav>
      </ScrollArea>

      {/* Online Users */}
      {open && onlineUsers.length > 0 && (
        <div className="p-4 border-t border-sidebar-border">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-medium text-sidebar-foreground/60">
              Usuarios en línea
            </span>
            <Badge variant="outline" className="text-xs">
              {onlineUsers.length}
            </Badge>
          </div>
          <div className="space-y-1">
            {onlineUsers.slice(0, 3).map((onlineUser) => (
              <div key={onlineUser.id} className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-green-500 rounded-full" />
                <span className="text-xs text-sidebar-foreground/80 truncate">
                  {onlineUser.username}
                </span>
              </div>
            ))}
            {onlineUsers.length > 3 && (
              <div className="text-xs text-sidebar-foreground/60">
                +{onlineUsers.length - 3} más
              </div>
            )}
          </div>
        </div>
      )}

      {/* Bottom Navigation */}
      <div className="p-2 border-t border-sidebar-border">
        {bottomNavigation.map((item) => {
          const Icon = item.icon
          const active = isActive(item.href)
          
          return (
            <Link
              key={item.name}
              to={item.href}
              onMouseEnter={() => setHoveredItem(item.name)}
              onMouseLeave={() => setHoveredItem(null)}
              className={cn(
                "flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors relative mb-1",
                active
                  ? "bg-sidebar-accent text-sidebar-accent-foreground"
                  : "text-sidebar-foreground hover:bg-sidebar-accent/50 hover:text-sidebar-accent-foreground"
              )}
            >
              <Icon className={cn("flex-shrink-0", open ? "mr-3 h-5 w-5" : "h-5 w-5")} />
              {open && <span>{item.name}</span>}
              
              {!open && hoveredItem === item.name && (
                <div className="absolute left-full ml-2 px-2 py-1 bg-popover text-popover-foreground text-xs rounded-md shadow-lg border z-50 whitespace-nowrap">
                  {item.name}
                  <div className="text-xs text-muted-foreground mt-1">
                    {item.description}
                  </div>
                </div>
              )}
            </Link>
          )
        })}
        
        <Button
          variant="ghost"
          onClick={handleLogout}
          onMouseEnter={() => setHoveredItem('logout')}
          onMouseLeave={() => setHoveredItem(null)}
          className={cn(
            "w-full justify-start px-3 py-2 text-sm font-medium relative",
            "text-sidebar-foreground hover:bg-destructive/10 hover:text-destructive"
          )}
        >
          <LogOut className={cn("flex-shrink-0", open ? "mr-3 h-5 w-5" : "h-5 w-5")} />
          {open && <span>Cerrar Sesión</span>}
          
          {!open && hoveredItem === 'logout' && (
            <div className="absolute left-full ml-2 px-2 py-1 bg-popover text-popover-foreground text-xs rounded-md shadow-lg border z-50 whitespace-nowrap">
              Cerrar Sesión
            </div>
          )}
        </Button>
      </div>
    </div>
  )
}

