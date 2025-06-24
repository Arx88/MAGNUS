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
import { Separator } from '@/components/ui/separator'
import { useAuth } from '@/hooks/useAuth'
import { useTheme } from '@/components/theme-provider'
import {
  Settings,
  User,
  Bell,
  Shield,
  Palette,
  Globe,
  Key,
  Download,
  Upload,
  Trash2,
  Eye,
  EyeOff,
  Save,
  RefreshCw,
  Smartphone,
  Mail,
  Lock,
  AlertTriangle
} from 'lucide-react'

export default function SettingsPage() {
  const { user, updateProfile } = useAuth()
  const { theme, setTheme } = useTheme()
  const [activeTab, setActiveTab] = useState('profile')
  const [loading, setLoading] = useState(false)
  const [showPassword, setShowPassword] = useState(false)
  const [showCurrentPassword, setShowCurrentPassword] = useState(false)

  // Profile settings
  const [profileData, setProfileData] = useState({
    name: user?.name || '',
    email: user?.email || '',
    bio: user?.bio || '',
    avatar: user?.avatar || '',
    timezone: user?.timezone || 'America/Mexico_City',
    language: user?.language || 'es'
  })

  // Security settings
  const [securityData, setSecurityData] = useState({
    current_password: '',
    new_password: '',
    confirm_password: '',
    two_factor_enabled: user?.two_factor_enabled || false,
    login_notifications: user?.login_notifications || true,
    session_timeout: user?.session_timeout || 3600
  })

  // Notification settings
  const [notificationData, setNotificationData] = useState({
    email_notifications: user?.email_notifications || true,
    push_notifications: user?.push_notifications || true,
    task_completed: user?.task_completed_notifications || true,
    task_failed: user?.task_failed_notifications || true,
    agent_updates: user?.agent_updates_notifications || false,
    system_alerts: user?.system_alerts_notifications || true,
    marketing_emails: user?.marketing_emails || false
  })

  // Appearance settings
  const [appearanceData, setAppearanceData] = useState({
    theme: theme,
    compact_mode: user?.compact_mode || false,
    sidebar_collapsed: user?.sidebar_collapsed || false,
    animations_enabled: user?.animations_enabled || true,
    font_size: user?.font_size || 'medium'
  })

  // Privacy settings
  const [privacyData, setPrivacyData] = useState({
    profile_visibility: user?.profile_visibility || 'private',
    activity_tracking: user?.activity_tracking || true,
    data_collection: user?.data_collection || true,
    third_party_sharing: user?.third_party_sharing || false
  })

  const [apiKeys, setApiKeys] = useState([
    {
      id: '1',
      name: 'API Key Principal',
      key: 'manus_sk_1234567890abcdef',
      created_at: new Date(Date.now() - 2592000000).toISOString(),
      last_used: new Date(Date.now() - 86400000).toISOString(),
      permissions: ['read', 'write']
    },
    {
      id: '2',
      name: 'API Key Solo Lectura',
      key: 'manus_sk_fedcba0987654321',
      created_at: new Date(Date.now() - 1296000000).toISOString(),
      last_used: new Date(Date.now() - 604800000).toISOString(),
      permissions: ['read']
    }
  ])

  const timezones = [
    { value: 'America/Mexico_City', label: 'Ciudad de México (GMT-6)' },
    { value: 'America/New_York', label: 'Nueva York (GMT-5)' },
    { value: 'Europe/Madrid', label: 'Madrid (GMT+1)' },
    { value: 'Europe/London', label: 'Londres (GMT+0)' },
    { value: 'Asia/Tokyo', label: 'Tokio (GMT+9)' },
    { value: 'UTC', label: 'UTC (GMT+0)' }
  ]

  const languages = [
    { value: 'es', label: 'Español' },
    { value: 'en', label: 'English' },
    { value: 'fr', label: 'Français' },
    { value: 'de', label: 'Deutsch' },
    { value: 'pt', label: 'Português' }
  ]

  const handleSaveProfile = async () => {
    setLoading(true)
    try {
      await updateProfile(profileData)
      // Show success message
    } catch (error) {
      console.error('Error updating profile:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleSaveSecurity = async () => {
    setLoading(true)
    try {
      // Validate passwords match
      if (securityData.new_password !== securityData.confirm_password) {
        throw new Error('Las contraseñas no coinciden')
      }
      
      // API call to update security settings
      // await updateSecuritySettings(securityData)
      
      // Clear password fields
      setSecurityData(prev => ({
        ...prev,
        current_password: '',
        new_password: '',
        confirm_password: ''
      }))
    } catch (error) {
      console.error('Error updating security settings:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleSaveNotifications = async () => {
    setLoading(true)
    try {
      // API call to update notification settings
      // await updateNotificationSettings(notificationData)
    } catch (error) {
      console.error('Error updating notification settings:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleSaveAppearance = async () => {
    setLoading(true)
    try {
      setTheme(appearanceData.theme)
      // API call to update appearance settings
      // await updateAppearanceSettings(appearanceData)
    } catch (error) {
      console.error('Error updating appearance settings:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleSavePrivacy = async () => {
    setLoading(true)
    try {
      // API call to update privacy settings
      // await updatePrivacySettings(privacyData)
    } catch (error) {
      console.error('Error updating privacy settings:', error)
    } finally {
      setLoading(false)
    }
  }

  const generateApiKey = () => {
    const newKey = {
      id: Date.now().toString(),
      name: 'Nueva API Key',
      key: `manus_sk_${Math.random().toString(36).substring(2, 18)}`,
      created_at: new Date().toISOString(),
      last_used: null,
      permissions: ['read']
    }
    setApiKeys(prev => [...prev, newKey])
  }

  const deleteApiKey = (keyId) => {
    if (window.confirm('¿Estás seguro de que quieres eliminar esta API key?')) {
      setApiKeys(prev => prev.filter(key => key.id !== keyId))
    }
  }

  const exportData = () => {
    // Simulate data export
    const data = {
      profile: profileData,
      settings: {
        notifications: notificationData,
        appearance: appearanceData,
        privacy: privacyData
      },
      exported_at: new Date().toISOString()
    }
    
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'manus-data-export.json'
    a.click()
    URL.revokeObjectURL(url)
  }

  const deleteAccount = () => {
    if (window.confirm('¿Estás seguro de que quieres eliminar tu cuenta? Esta acción no se puede deshacer.')) {
      // API call to delete account
      console.log('Deleting account...')
    }
  }

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('es-ES', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Configuración</h1>
          <p className="text-muted-foreground">
            Gestiona tu perfil y preferencias del sistema
          </p>
        </div>
        
        <div className="flex items-center space-x-2">
          <Button variant="outline" onClick={exportData}>
            <Download className="w-4 h-4 mr-2" />
            Exportar Datos
          </Button>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-6">
          <TabsTrigger value="profile">Perfil</TabsTrigger>
          <TabsTrigger value="security">Seguridad</TabsTrigger>
          <TabsTrigger value="notifications">Notificaciones</TabsTrigger>
          <TabsTrigger value="appearance">Apariencia</TabsTrigger>
          <TabsTrigger value="privacy">Privacidad</TabsTrigger>
          <TabsTrigger value="api">API Keys</TabsTrigger>
        </Tabs>

        {/* Profile Tab */}
        <TabsContent value="profile" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <User className="w-5 h-5" />
                <span>Información Personal</span>
              </CardTitle>
              <CardDescription>
                Actualiza tu información personal y preferencias de cuenta
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-2">
                  <Label htmlFor="name">Nombre Completo</Label>
                  <Input
                    id="name"
                    value={profileData.name}
                    onChange={(e) => setProfileData(prev => ({ ...prev, name: e.target.value }))}
                    placeholder="Tu nombre completo"
                  />
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="email">Correo Electrónico</Label>
                  <Input
                    id="email"
                    type="email"
                    value={profileData.email}
                    onChange={(e) => setProfileData(prev => ({ ...prev, email: e.target.value }))}
                    placeholder="tu@email.com"
                  />
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="timezone">Zona Horaria</Label>
                  <select
                    id="timezone"
                    value={profileData.timezone}
                    onChange={(e) => setProfileData(prev => ({ ...prev, timezone: e.target.value }))}
                    className="w-full p-2 border border-input rounded-md"
                  >
                    {timezones.map(tz => (
                      <option key={tz.value} value={tz.value}>{tz.label}</option>
                    ))}
                  </select>
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="language">Idioma</Label>
                  <select
                    id="language"
                    value={profileData.language}
                    onChange={(e) => setProfileData(prev => ({ ...prev, language: e.target.value }))}
                    className="w-full p-2 border border-input rounded-md"
                  >
                    {languages.map(lang => (
                      <option key={lang.value} value={lang.value}>{lang.label}</option>
                    ))}
                  </select>
                </div>
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="bio">Biografía</Label>
                <Textarea
                  id="bio"
                  value={profileData.bio}
                  onChange={(e) => setProfileData(prev => ({ ...prev, bio: e.target.value }))}
                  placeholder="Cuéntanos sobre ti..."
                  rows={4}
                />
              </div>
              
              <div className="flex justify-end">
                <Button onClick={handleSaveProfile} disabled={loading}>
                  {loading ? <RefreshCw className="w-4 h-4 mr-2 animate-spin" /> : <Save className="w-4 h-4 mr-2" />}
                  Guardar Cambios
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Security Tab */}
        <TabsContent value="security" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Shield className="w-5 h-5" />
                <span>Seguridad de la Cuenta</span>
              </CardTitle>
              <CardDescription>
                Gestiona la seguridad de tu cuenta y contraseñas
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Change Password */}
              <div className="space-y-4">
                <h4 className="text-sm font-medium">Cambiar Contraseña</h4>
                
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="current-password">Contraseña Actual</Label>
                    <div className="relative">
                      <Input
                        id="current-password"
                        type={showCurrentPassword ? 'text' : 'password'}
                        value={securityData.current_password}
                        onChange={(e) => setSecurityData(prev => ({ ...prev, current_password: e.target.value }))}
                        placeholder="Contraseña actual"
                      />
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        className="absolute right-0 top-0 h-full px-3"
                        onClick={() => setShowCurrentPassword(!showCurrentPassword)}
                      >
                        {showCurrentPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                      </Button>
                    </div>
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor="new-password">Nueva Contraseña</Label>
                    <div className="relative">
                      <Input
                        id="new-password"
                        type={showPassword ? 'text' : 'password'}
                        value={securityData.new_password}
                        onChange={(e) => setSecurityData(prev => ({ ...prev, new_password: e.target.value }))}
                        placeholder="Nueva contraseña"
                      />
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        className="absolute right-0 top-0 h-full px-3"
                        onClick={() => setShowPassword(!showPassword)}
                      >
                        {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                      </Button>
                    </div>
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor="confirm-password">Confirmar Contraseña</Label>
                    <Input
                      id="confirm-password"
                      type="password"
                      value={securityData.confirm_password}
                      onChange={(e) => setSecurityData(prev => ({ ...prev, confirm_password: e.target.value }))}
                      placeholder="Confirmar contraseña"
                    />
                  </div>
                </div>
              </div>
              
              <Separator />
              
              {/* Two-Factor Authentication */}
              <div className="space-y-4">
                <h4 className="text-sm font-medium">Autenticación de Dos Factores</h4>
                
                <div className="flex items-center justify-between">
                  <div className="space-y-1">
                    <p className="text-sm">Habilitar 2FA</p>
                    <p className="text-xs text-muted-foreground">
                      Agrega una capa extra de seguridad a tu cuenta
                    </p>
                  </div>
                  <Switch
                    checked={securityData.two_factor_enabled}
                    onCheckedChange={(checked) => setSecurityData(prev => ({ ...prev, two_factor_enabled: checked }))}
                  />
                </div>
                
                {securityData.two_factor_enabled && (
                  <div className="bg-muted p-4 rounded-lg">
                    <div className="flex items-center space-x-2 mb-2">
                      <Smartphone className="w-4 h-4" />
                      <span className="text-sm font-medium">Configurar Aplicación Autenticadora</span>
                    </div>
                    <p className="text-xs text-muted-foreground mb-3">
                      Escanea el código QR con tu aplicación autenticadora
                    </p>
                    <div className="bg-white p-4 rounded border inline-block">
                      <div className="w-32 h-32 bg-gray-200 flex items-center justify-center text-xs">
                        Código QR
                      </div>
                    </div>
                  </div>
                )}
              </div>
              
              <Separator />
              
              {/* Other Security Settings */}
              <div className="space-y-4">
                <h4 className="text-sm font-medium">Otras Configuraciones</h4>
                
                <div className="flex items-center justify-between">
                  <div className="space-y-1">
                    <p className="text-sm">Notificaciones de Inicio de Sesión</p>
                    <p className="text-xs text-muted-foreground">
                      Recibe notificaciones cuando alguien acceda a tu cuenta
                    </p>
                  </div>
                  <Switch
                    checked={securityData.login_notifications}
                    onCheckedChange={(checked) => setSecurityData(prev => ({ ...prev, login_notifications: checked }))}
                  />
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="session-timeout">Tiempo de Sesión (segundos)</Label>
                  <Input
                    id="session-timeout"
                    type="number"
                    value={securityData.session_timeout}
                    onChange={(e) => setSecurityData(prev => ({ ...prev, session_timeout: parseInt(e.target.value) }))}
                    className="w-32"
                  />
                </div>
              </div>
              
              <div className="flex justify-end">
                <Button onClick={handleSaveSecurity} disabled={loading}>
                  {loading ? <RefreshCw className="w-4 h-4 mr-2 animate-spin" /> : <Save className="w-4 h-4 mr-2" />}
                  Guardar Cambios
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Notifications Tab */}
        <TabsContent value="notifications" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Bell className="w-5 h-5" />
                <span>Preferencias de Notificaciones</span>
              </CardTitle>
              <CardDescription>
                Controla qué notificaciones quieres recibir y cómo
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-4">
                <h4 className="text-sm font-medium">Métodos de Notificación</h4>
                
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <Mail className="w-4 h-4" />
                      <div>
                        <p className="text-sm">Notificaciones por Email</p>
                        <p className="text-xs text-muted-foreground">Recibe notificaciones en tu correo</p>
                      </div>
                    </div>
                    <Switch
                      checked={notificationData.email_notifications}
                      onCheckedChange={(checked) => setNotificationData(prev => ({ ...prev, email_notifications: checked }))}
                    />
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <Bell className="w-4 h-4" />
                      <div>
                        <p className="text-sm">Notificaciones Push</p>
                        <p className="text-xs text-muted-foreground">Notificaciones en tiempo real en el navegador</p>
                      </div>
                    </div>
                    <Switch
                      checked={notificationData.push_notifications}
                      onCheckedChange={(checked) => setNotificationData(prev => ({ ...prev, push_notifications: checked }))}
                    />
                  </div>
                </div>
              </div>
              
              <Separator />
              
              <div className="space-y-4">
                <h4 className="text-sm font-medium">Tipos de Notificaciones</h4>
                
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm">Tareas Completadas</p>
                      <p className="text-xs text-muted-foreground">Cuando un agente complete una tarea</p>
                    </div>
                    <Switch
                      checked={notificationData.task_completed}
                      onCheckedChange={(checked) => setNotificationData(prev => ({ ...prev, task_completed: checked }))}
                    />
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm">Tareas Fallidas</p>
                      <p className="text-xs text-muted-foreground">Cuando una tarea falle o tenga errores</p>
                    </div>
                    <Switch
                      checked={notificationData.task_failed}
                      onCheckedChange={(checked) => setNotificationData(prev => ({ ...prev, task_failed: checked }))}
                    />
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm">Actualizaciones de Agentes</p>
                      <p className="text-xs text-muted-foreground">Cuando haya nuevas versiones de agentes</p>
                    </div>
                    <Switch
                      checked={notificationData.agent_updates}
                      onCheckedChange={(checked) => setNotificationData(prev => ({ ...prev, agent_updates: checked }))}
                    />
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm">Alertas del Sistema</p>
                      <p className="text-xs text-muted-foreground">Mantenimiento y alertas importantes</p>
                    </div>
                    <Switch
                      checked={notificationData.system_alerts}
                      onCheckedChange={(checked) => setNotificationData(prev => ({ ...prev, system_alerts: checked }))}
                    />
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm">Emails de Marketing</p>
                      <p className="text-xs text-muted-foreground">Noticias, actualizaciones y ofertas</p>
                    </div>
                    <Switch
                      checked={notificationData.marketing_emails}
                      onCheckedChange={(checked) => setNotificationData(prev => ({ ...prev, marketing_emails: checked }))}
                    />
                  </div>
                </div>
              </div>
              
              <div className="flex justify-end">
                <Button onClick={handleSaveNotifications} disabled={loading}>
                  {loading ? <RefreshCw className="w-4 h-4 mr-2 animate-spin" /> : <Save className="w-4 h-4 mr-2" />}
                  Guardar Cambios
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Appearance Tab */}
        <TabsContent value="appearance" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Palette className="w-5 h-5" />
                <span>Apariencia y Tema</span>
              </CardTitle>
              <CardDescription>
                Personaliza la apariencia de la interfaz
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-4">
                <h4 className="text-sm font-medium">Tema</h4>
                
                <div className="grid grid-cols-3 gap-4">
                  <div 
                    className={`border rounded-lg p-4 cursor-pointer ${appearanceData.theme === 'light' ? 'border-primary' : 'border-muted'}`}
                    onClick={() => setAppearanceData(prev => ({ ...prev, theme: 'light' }))}
                  >
                    <div className="w-full h-20 bg-white border rounded mb-2"></div>
                    <p className="text-sm text-center">Claro</p>
                  </div>
                  
                  <div 
                    className={`border rounded-lg p-4 cursor-pointer ${appearanceData.theme === 'dark' ? 'border-primary' : 'border-muted'}`}
                    onClick={() => setAppearanceData(prev => ({ ...prev, theme: 'dark' }))}
                  >
                    <div className="w-full h-20 bg-gray-900 border rounded mb-2"></div>
                    <p className="text-sm text-center">Oscuro</p>
                  </div>
                  
                  <div 
                    className={`border rounded-lg p-4 cursor-pointer ${appearanceData.theme === 'system' ? 'border-primary' : 'border-muted'}`}
                    onClick={() => setAppearanceData(prev => ({ ...prev, theme: 'system' }))}
                  >
                    <div className="w-full h-20 bg-gradient-to-r from-white to-gray-900 border rounded mb-2"></div>
                    <p className="text-sm text-center">Sistema</p>
                  </div>
                </div>
              </div>
              
              <Separator />
              
              <div className="space-y-4">
                <h4 className="text-sm font-medium">Configuración de Interfaz</h4>
                
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm">Modo Compacto</p>
                      <p className="text-xs text-muted-foreground">Reduce el espaciado para mostrar más contenido</p>
                    </div>
                    <Switch
                      checked={appearanceData.compact_mode}
                      onCheckedChange={(checked) => setAppearanceData(prev => ({ ...prev, compact_mode: checked }))}
                    />
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm">Sidebar Colapsado</p>
                      <p className="text-xs text-muted-foreground">Mantener la barra lateral colapsada por defecto</p>
                    </div>
                    <Switch
                      checked={appearanceData.sidebar_collapsed}
                      onCheckedChange={(checked) => setAppearanceData(prev => ({ ...prev, sidebar_collapsed: checked }))}
                    />
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm">Animaciones</p>
                      <p className="text-xs text-muted-foreground">Habilitar animaciones y transiciones</p>
                    </div>
                    <Switch
                      checked={appearanceData.animations_enabled}
                      onCheckedChange={(checked) => setAppearanceData(prev => ({ ...prev, animations_enabled: checked }))}
                    />
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor="font-size">Tamaño de Fuente</Label>
                    <select
                      id="font-size"
                      value={appearanceData.font_size}
                      onChange={(e) => setAppearanceData(prev => ({ ...prev, font_size: e.target.value }))}
                      className="w-full p-2 border border-input rounded-md"
                    >
                      <option value="small">Pequeño</option>
                      <option value="medium">Mediano</option>
                      <option value="large">Grande</option>
                    </select>
                  </div>
                </div>
              </div>
              
              <div className="flex justify-end">
                <Button onClick={handleSaveAppearance} disabled={loading}>
                  {loading ? <RefreshCw className="w-4 h-4 mr-2 animate-spin" /> : <Save className="w-4 h-4 mr-2" />}
                  Guardar Cambios
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Privacy Tab */}
        <TabsContent value="privacy" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Lock className="w-5 h-5" />
                <span>Privacidad y Datos</span>
              </CardTitle>
              <CardDescription>
                Controla cómo se usan y comparten tus datos
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-4">
                <h4 className="text-sm font-medium">Visibilidad del Perfil</h4>
                
                <div className="space-y-2">
                  <Label htmlFor="profile-visibility">Quién puede ver tu perfil</Label>
                  <select
                    id="profile-visibility"
                    value={privacyData.profile_visibility}
                    onChange={(e) => setPrivacyData(prev => ({ ...prev, profile_visibility: e.target.value }))}
                    className="w-full p-2 border border-input rounded-md"
                  >
                    <option value="public">Público</option>
                    <option value="private">Privado</option>
                    <option value="contacts">Solo contactos</option>
                  </select>
                </div>
              </div>
              
              <Separator />
              
              <div className="space-y-4">
                <h4 className="text-sm font-medium">Recopilación de Datos</h4>
                
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm">Seguimiento de Actividad</p>
                      <p className="text-xs text-muted-foreground">Permitir el seguimiento para mejorar la experiencia</p>
                    </div>
                    <Switch
                      checked={privacyData.activity_tracking}
                      onCheckedChange={(checked) => setPrivacyData(prev => ({ ...prev, activity_tracking: checked }))}
                    />
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm">Recopilación de Datos de Uso</p>
                      <p className="text-xs text-muted-foreground">Ayudar a mejorar el producto con datos anónimos</p>
                    </div>
                    <Switch
                      checked={privacyData.data_collection}
                      onCheckedChange={(checked) => setPrivacyData(prev => ({ ...prev, data_collection: checked }))}
                    />
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm">Compartir con Terceros</p>
                      <p className="text-xs text-muted-foreground">Permitir compartir datos con socios de confianza</p>
                    </div>
                    <Switch
                      checked={privacyData.third_party_sharing}
                      onCheckedChange={(checked) => setPrivacyData(prev => ({ ...prev, third_party_sharing: checked }))}
                    />
                  </div>
                </div>
              </div>
              
              <Separator />
              
              <div className="space-y-4">
                <h4 className="text-sm font-medium">Gestión de Datos</h4>
                
                <div className="space-y-3">
                  <Button variant="outline" onClick={exportData}>
                    <Download className="w-4 h-4 mr-2" />
                    Exportar Mis Datos
                  </Button>
                  
                  <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                    <div className="flex items-center space-x-2 mb-2">
                      <AlertTriangle className="w-4 h-4 text-red-500" />
                      <span className="text-sm font-medium text-red-700">Zona de Peligro</span>
                    </div>
                    <p className="text-xs text-red-600 mb-3">
                      Eliminar tu cuenta borrará permanentemente todos tus datos, agentes y conversaciones.
                    </p>
                    <Button variant="destructive" size="sm" onClick={deleteAccount}>
                      <Trash2 className="w-4 h-4 mr-2" />
                      Eliminar Cuenta
                    </Button>
                  </div>
                </div>
              </div>
              
              <div className="flex justify-end">
                <Button onClick={handleSavePrivacy} disabled={loading}>
                  {loading ? <RefreshCw className="w-4 h-4 mr-2 animate-spin" /> : <Save className="w-4 h-4 mr-2" />}
                  Guardar Cambios
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* API Keys Tab */}
        <TabsContent value="api" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Key className="w-5 h-5" />
                <span>API Keys</span>
              </CardTitle>
              <CardDescription>
                Gestiona las claves API para integrar con servicios externos
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="flex justify-between items-center">
                <p className="text-sm text-muted-foreground">
                  Las API keys te permiten acceder programáticamente a tu cuenta
                </p>
                <Button onClick={generateApiKey}>
                  <Plus className="w-4 h-4 mr-2" />
                  Nueva API Key
                </Button>
              </div>
              
              <div className="space-y-4">
                {apiKeys.map((apiKey) => (
                  <div key={apiKey.id} className="border rounded-lg p-4">
                    <div className="flex items-center justify-between mb-3">
                      <div>
                        <h4 className="text-sm font-medium">{apiKey.name}</h4>
                        <p className="text-xs text-muted-foreground">
                          Creada: {formatDate(apiKey.created_at)}
                        </p>
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => deleteApiKey(apiKey.id)}
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                    
                    <div className="space-y-2">
                      <div className="flex items-center space-x-2">
                        <Input
                          value={apiKey.key}
                          readOnly
                          className="font-mono text-xs"
                        />
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => navigator.clipboard.writeText(apiKey.key)}
                        >
                          Copiar
                        </Button>
                      </div>
                      
                      <div className="flex items-center justify-between text-xs text-muted-foreground">
                        <div className="flex items-center space-x-4">
                          <span>Permisos: {apiKey.permissions.join(', ')}</span>
                          {apiKey.last_used && (
                            <span>Último uso: {formatDate(apiKey.last_used)}</span>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
              
              {apiKeys.length === 0 && (
                <div className="text-center py-8">
                  <Key className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
                  <h3 className="text-lg font-semibold mb-2">No tienes API Keys</h3>
                  <p className="text-muted-foreground mb-4">
                    Crea tu primera API key para comenzar a integrar con servicios externos
                  </p>
                  <Button onClick={generateApiKey}>
                    <Plus className="w-4 h-4 mr-2" />
                    Crear Primera API Key
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}

