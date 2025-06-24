import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { useAuth } from '@/hooks/useAuth'
import { Zap, Bot, Loader2, Eye, EyeOff } from 'lucide-react'

export default function LoginPage() {
  const auth = useAuth(); // Get the whole context
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [activeTab, setActiveTab] = useState('login')

  if (!auth || !auth.login || !auth.register) {
    // This state should ideally not be reached if AppContent's checks are robust.
    // Rendering a clear message helps if it does.
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-background via-background to-accent/20 p-4">
        <div className="text-foreground">Auth Context not fully loaded for LoginPage...</div>
      </div>
    );
  }
  const { login, register } = auth; // Destructure after the check

  // Login form state
  const [loginForm, setLoginForm] = useState({
    username: '',
    password: ''
  })

  // Register form state
  const [registerForm, setRegisterForm] = useState({
    username: '',
    email: '',
    full_name: '',
    password: '',
    confirmPassword: ''
  })

  const handleLogin = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    try {
      const result = await login({
        username: loginForm.username,
        password: loginForm.password
      })

      if (!result.success) {
        setError(result.error)
      }
    } catch (err) {
      setError('Error de conexión. Verifica tu conexión a internet.')
    } finally {
      setLoading(false)
    }
  }

  const handleRegister = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    // Validaciones
    if (registerForm.password !== registerForm.confirmPassword) {
      setError('Las contraseñas no coinciden')
      setLoading(false)
      return
    }

    if (registerForm.password.length < 6) {
      setError('La contraseña debe tener al menos 6 caracteres')
      setLoading(false)
      return
    }

    try {
      const result = await register({
        username: registerForm.username,
        email: registerForm.email,
        full_name: registerForm.full_name,
        password: registerForm.password
      })

      if (!result.success) {
        setError(result.error)
      }
    } catch (err) {
      setError('Error de conexión. Verifica tu conexión a internet.')
    } finally {
      setLoading(false)
    }
  }

  const updateLoginForm = (field, value) => {
    setLoginForm(prev => ({ ...prev, [field]: value }))
    setError('')
  }

  const updateRegisterForm = (field, value) => {
    setRegisterForm(prev => ({ ...prev, [field]: value }))
    setError('')
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-background via-background to-accent/20 p-4">
      {/* Simplified content for testing */}
      <div className="w-full max-w-md space-y-8 bg-card p-8 rounded-lg shadow-xl">
        <h1 className="text-3xl font-bold text-center text-primary">LOGIN PAGE TEST</h1>
        <p className="text-center text-foreground">If you see this, the basic LoginPage component is rendering.</p>
        <div className="text-center text-xs text-muted-foreground">
          (Original form is temporarily removed for testing)
        </div>
      </div>
    </div>
  );
}

