import { useState, useEffect } from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { Toaster } from '@/components/ui/sonner'
import { ThemeProvider } from '@/components/theme-provider'
import { AuthProvider } from '@/contexts/AuthContext'
import { SocketProvider } from '@/contexts/SocketContext'

// Layout Components
import Sidebar from '@/components/layout/Sidebar'
import Header from '@/components/layout/Header'

// Page Components
import LoginPage from '@/pages/LoginPage'
import ChatPage from '@/pages/ChatPage'
import AgentsPage from '@/pages/AgentsPage'
import TasksPage from '@/pages/TasksPage'
import ToolsPage from '@/pages/ToolsPage'
import FilesPage from '@/pages/FilesPage'
import AdminPage from '@/pages/AdminPage'
import SettingsPage from '@/pages/SettingsPage'

// Hooks
import { useAuth } from '@/hooks/useAuth'

import './App.css'

function AppContent() {
  const { user, loading } = useAuth()
  const [sidebarOpen, setSidebarOpen] = useState(true)

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-primary"></div>
      </div>
    )
  }

  if (!user) {
    return <LoginPage />
  }

  return (
    <div className="flex h-screen bg-background">
      <Sidebar open={sidebarOpen} onToggle={() => setSidebarOpen(!sidebarOpen)} />
      
      <div className="flex-1 flex flex-col overflow-hidden">
        <Header onMenuClick={() => setSidebarOpen(!sidebarOpen)} />
        
        <main className="flex-1 overflow-auto">
          <Routes>
            <Route path="/" element={<Navigate to="/chat" replace />} />
            <Route path="/chat" element={<ChatPage />} />
            <Route path="/chat/:conversationId" element={<ChatPage />} />
            <Route path="/agents" element={<AgentsPage />} />
            <Route path="/tasks" element={<TasksPage />} />
            <Route path="/tools" element={<ToolsPage />} />
            <Route path="/files" element={<FilesPage />} />
            <Route path="/admin" element={<AdminPage />} />
            <Route path="/settings" element={<SettingsPage />} />
          </Routes>
        </main>
      </div>
    </div>
  )
}

function App() {
  return (
    <ThemeProvider defaultTheme="system" storageKey="manus-theme">
      <AuthProvider>
        <SocketProvider>
          <Router>
            <AppContent />
            <Toaster />
          </Router>
        </SocketProvider>
      </AuthProvider>
    </ThemeProvider>
  )
}

export default App
