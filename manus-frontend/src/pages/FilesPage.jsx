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
import {
  FileText,
  Upload,
  Download,
  Search,
  Filter,
  Folder,
  File,
  Image,
  Video,
  Music,
  Archive,
  Code,
  Trash2,
  Eye,
  Edit,
  Share,
  Copy,
  MoreVertical,
  Plus,
  FolderPlus
} from 'lucide-react'

const fileTypes = {
  document: { icon: FileText, color: 'text-blue-500', extensions: ['pdf', 'doc', 'docx', 'txt', 'md'] },
  image: { icon: Image, color: 'text-green-500', extensions: ['jpg', 'jpeg', 'png', 'gif', 'svg', 'webp'] },
  video: { icon: Video, color: 'text-purple-500', extensions: ['mp4', 'avi', 'mov', 'mkv', 'webm'] },
  audio: { icon: Music, color: 'text-orange-500', extensions: ['mp3', 'wav', 'flac', 'ogg'] },
  archive: { icon: Archive, color: 'text-yellow-500', extensions: ['zip', 'rar', '7z', 'tar', 'gz'] },
  code: { icon: Code, color: 'text-red-500', extensions: ['js', 'py', 'html', 'css', 'json', 'xml'] },
  default: { icon: File, color: 'text-gray-500', extensions: [] }
}

export default function FilesPage() {
  const { user } = useAuth()
  const [files, setFiles] = useState([])
  const [filteredFiles, setFilteredFiles] = useState([])
  const [currentPath, setCurrentPath] = useState('/')
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedFiles, setSelectedFiles] = useState([])
  const [isUploadDialogOpen, setIsUploadDialogOpen] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('all')
  const [sortBy, setSortBy] = useState('name')
  const [sortOrder, setSortOrder] = useState('asc')

  useEffect(() => {
    loadFiles()
  }, [currentPath])

  useEffect(() => {
    filterFiles()
  }, [files, searchQuery, activeTab])

  const loadFiles = async () => {
    try {
      // Simulated API call
      const mockFiles = [
        {
          id: '1',
          name: 'Documentos',
          type: 'folder',
          size: null,
          created_at: new Date(Date.now() - 86400000).toISOString(),
          modified_at: new Date(Date.now() - 43200000).toISOString(),
          owner: user.id,
          shared: false,
          path: '/Documentos'
        },
        {
          id: '2',
          name: 'Imágenes',
          type: 'folder',
          size: null,
          created_at: new Date(Date.now() - 172800000).toISOString(),
          modified_at: new Date(Date.now() - 86400000).toISOString(),
          owner: user.id,
          shared: true,
          path: '/Imágenes'
        },
        {
          id: '3',
          name: 'análisis_ventas_q4.pdf',
          type: 'file',
          extension: 'pdf',
          size: 2456789,
          created_at: new Date(Date.now() - 3600000).toISOString(),
          modified_at: new Date(Date.now() - 3600000).toISOString(),
          owner: user.id,
          shared: false,
          path: '/análisis_ventas_q4.pdf',
          generated_by: 'Analista de Datos',
          task_id: '1'
        },
        {
          id: '4',
          name: 'app.py',
          type: 'file',
          extension: 'py',
          size: 15678,
          created_at: new Date(Date.now() - 7200000).toISOString(),
          modified_at: new Date(Date.now() - 1800000).toISOString(),
          owner: user.id,
          shared: false,
          path: '/app.py',
          generated_by: 'Programador',
          task_id: '2'
        },
        {
          id: '5',
          name: 'charts.png',
          type: 'file',
          extension: 'png',
          size: 567890,
          created_at: new Date(Date.now() - 3600000).toISOString(),
          modified_at: new Date(Date.now() - 3600000).toISOString(),
          owner: user.id,
          shared: true,
          path: '/charts.png',
          generated_by: 'Analista de Datos',
          task_id: '1'
        },
        {
          id: '6',
          name: 'config.json',
          type: 'file',
          extension: 'json',
          size: 1234,
          created_at: new Date(Date.now() - 14400000).toISOString(),
          modified_at: new Date(Date.now() - 7200000).toISOString(),
          owner: user.id,
          shared: false,
          path: '/config.json'
        },
        {
          id: '7',
          name: 'backup.zip',
          type: 'file',
          extension: 'zip',
          size: 45678901,
          created_at: new Date(Date.now() - 259200000).toISOString(),
          modified_at: new Date(Date.now() - 259200000).toISOString(),
          owner: user.id,
          shared: false,
          path: '/backup.zip'
        }
      ]
      
      setFiles(mockFiles)
    } catch (error) {
      console.error('Error loading files:', error)
    } finally {
      setLoading(false)
    }
  }

  const filterFiles = () => {
    let filtered = files

    // Filter by tab
    switch (activeTab) {
      case 'documents':
        filtered = filtered.filter(file => 
          file.type === 'folder' || fileTypes.document.extensions.includes(file.extension)
        )
        break
      case 'images':
        filtered = filtered.filter(file => 
          file.type === 'folder' || fileTypes.image.extensions.includes(file.extension)
        )
        break
      case 'generated':
        filtered = filtered.filter(file => file.generated_by)
        break
      case 'shared':
        filtered = filtered.filter(file => file.shared)
        break
      default:
        // 'all' - no additional filtering
        break
    }

    // Filter by search query
    if (searchQuery) {
      filtered = filtered.filter(file =>
        file.name.toLowerCase().includes(searchQuery.toLowerCase())
      )
    }

    // Sort files
    filtered.sort((a, b) => {
      // Folders first
      if (a.type === 'folder' && b.type !== 'folder') return -1
      if (a.type !== 'folder' && b.type === 'folder') return 1

      let aValue, bValue
      switch (sortBy) {
        case 'name':
          aValue = a.name.toLowerCase()
          bValue = b.name.toLowerCase()
          break
        case 'size':
          aValue = a.size || 0
          bValue = b.size || 0
          break
        case 'modified':
          aValue = new Date(a.modified_at)
          bValue = new Date(b.modified_at)
          break
        default:
          aValue = a.name.toLowerCase()
          bValue = b.name.toLowerCase()
      }

      if (sortOrder === 'asc') {
        return aValue < bValue ? -1 : aValue > bValue ? 1 : 0
      } else {
        return aValue > bValue ? -1 : aValue < bValue ? 1 : 0
      }
    })

    setFilteredFiles(filtered)
  }

  const getFileType = (file) => {
    if (file.type === 'folder') return { icon: Folder, color: 'text-blue-500' }
    
    for (const [type, config] of Object.entries(fileTypes)) {
      if (config.extensions.includes(file.extension)) {
        return config
      }
    }
    return fileTypes.default
  }

  const formatFileSize = (bytes) => {
    if (!bytes) return '-'
    const sizes = ['B', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(1024))
    return `${(bytes / Math.pow(1024, i)).toFixed(1)} ${sizes[i]}`
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

  const handleFileClick = (file) => {
    if (file.type === 'folder') {
      setCurrentPath(file.path)
    } else {
      // Open file preview or download
      console.log('Opening file:', file.name)
    }
  }

  const handleFileSelect = (fileId) => {
    setSelectedFiles(prev => 
      prev.includes(fileId) 
        ? prev.filter(id => id !== fileId)
        : [...prev, fileId]
    )
  }

  const handleUpload = async (files) => {
    setIsUploadDialogOpen(false)
    setUploadProgress(0)

    // Simulate upload progress
    const interval = setInterval(() => {
      setUploadProgress(prev => {
        if (prev >= 100) {
          clearInterval(interval)
          // Add uploaded files to the list
          return 100
        }
        return prev + 10
      })
    }, 200)
  }

  const deleteFiles = async () => {
    if (window.confirm(`¿Estás seguro de que quieres eliminar ${selectedFiles.length} archivo(s)?`)) {
      try {
        setFiles(prev => prev.filter(file => !selectedFiles.includes(file.id)))
        setSelectedFiles([])
      } catch (error) {
        console.error('Error deleting files:', error)
      }
    }
  }

  const shareFiles = async () => {
    try {
      setFiles(prev => prev.map(file => 
        selectedFiles.includes(file.id) ? { ...file, shared: true } : file
      ))
      setSelectedFiles([])
    } catch (error) {
      console.error('Error sharing files:', error)
    }
  }

  const downloadFiles = async () => {
    // Simulate download
    console.log('Downloading files:', selectedFiles)
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
          <h1 className="text-3xl font-bold">Archivos</h1>
          <p className="text-muted-foreground">
            Gestiona archivos generados por agentes y documentos personales
          </p>
        </div>
        
        <div className="flex items-center space-x-2">
          <Dialog open={isUploadDialogOpen} onOpenChange={setIsUploadDialogOpen}>
            <DialogTrigger asChild>
              <Button variant="outline">
                <Upload className="w-4 h-4 mr-2" />
                Subir
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Subir Archivos</DialogTitle>
                <DialogDescription>
                  Selecciona archivos para subir al sistema
                </DialogDescription>
              </DialogHeader>
              
              <div className="space-y-4">
                <div className="border-2 border-dashed border-muted-foreground/25 rounded-lg p-8 text-center">
                  <Upload className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
                  <p className="text-sm text-muted-foreground mb-2">
                    Arrastra archivos aquí o haz clic para seleccionar
                  </p>
                  <Button variant="outline">
                    Seleccionar Archivos
                  </Button>
                </div>
                
                {uploadProgress > 0 && (
                  <div className="space-y-2">
                    <div className="flex items-center justify-between text-sm">
                      <span>Subiendo archivos...</span>
                      <span>{uploadProgress}%</span>
                    </div>
                    <Progress value={uploadProgress} />
                  </div>
                )}
              </div>
            </DialogContent>
          </Dialog>
          
          <Button>
            <FolderPlus className="w-4 h-4 mr-2" />
            Nueva Carpeta
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <FileText className="w-5 h-5 text-primary" />
              <div>
                <p className="text-sm font-medium">Total Archivos</p>
                <p className="text-2xl font-bold">
                  {files.filter(f => f.type === 'file').length}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <Folder className="w-5 h-5 text-blue-500" />
              <div>
                <p className="text-sm font-medium">Carpetas</p>
                <p className="text-2xl font-bold">
                  {files.filter(f => f.type === 'folder').length}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <Share className="w-5 h-5 text-green-500" />
              <div>
                <p className="text-sm font-medium">Compartidos</p>
                <p className="text-2xl font-bold">
                  {files.filter(f => f.shared).length}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <Download className="w-5 h-5 text-purple-500" />
              <div>
                <p className="text-sm font-medium">Espacio Usado</p>
                <p className="text-2xl font-bold">
                  {formatFileSize(files.reduce((total, file) => total + (file.size || 0), 0))}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Navigation and Controls */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          {/* Breadcrumb */}
          <div className="flex items-center space-x-2 text-sm">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setCurrentPath('/')}
              className="h-8 px-2"
            >
              Inicio
            </Button>
            {currentPath !== '/' && (
              <>
                <span>/</span>
                <span className="text-muted-foreground">{currentPath.split('/').pop()}</span>
              </>
            )}
          </div>
        </div>
        
        <div className="flex items-center space-x-4">
          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Buscar archivos..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10 w-64"
            />
          </div>
          
          {/* Sort */}
          <select
            value={`${sortBy}-${sortOrder}`}
            onChange={(e) => {
              const [field, order] = e.target.value.split('-')
              setSortBy(field)
              setSortOrder(order)
            }}
            className="px-3 py-2 border border-input rounded-md text-sm"
          >
            <option value="name-asc">Nombre A-Z</option>
            <option value="name-desc">Nombre Z-A</option>
            <option value="modified-desc">Más reciente</option>
            <option value="modified-asc">Más antiguo</option>
            <option value="size-desc">Mayor tamaño</option>
            <option value="size-asc">Menor tamaño</option>
          </select>
        </div>
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="all">Todos</TabsTrigger>
          <TabsTrigger value="documents">Documentos</TabsTrigger>
          <TabsTrigger value="images">Imágenes</TabsTrigger>
          <TabsTrigger value="generated">Generados</TabsTrigger>
          <TabsTrigger value="shared">Compartidos</TabsTrigger>
        </TabsList>
      </Tabs>

      {/* Selected Files Actions */}
      {selectedFiles.length > 0 && (
        <div className="flex items-center justify-between p-4 bg-muted rounded-lg">
          <span className="text-sm font-medium">
            {selectedFiles.length} archivo(s) seleccionado(s)
          </span>
          <div className="flex items-center space-x-2">
            <Button size="sm" variant="outline" onClick={downloadFiles}>
              <Download className="w-4 h-4 mr-2" />
              Descargar
            </Button>
            <Button size="sm" variant="outline" onClick={shareFiles}>
              <Share className="w-4 h-4 mr-2" />
              Compartir
            </Button>
            <Button size="sm" variant="outline" onClick={() => setSelectedFiles([])}>
              <Copy className="w-4 h-4 mr-2" />
              Copiar
            </Button>
            <Button size="sm" variant="destructive" onClick={deleteFiles}>
              <Trash2 className="w-4 h-4 mr-2" />
              Eliminar
            </Button>
          </div>
        </div>
      )}

      {/* Files Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {filteredFiles.map((file) => {
          const fileTypeConfig = getFileType(file)
          const FileIcon = fileTypeConfig.icon
          const isSelected = selectedFiles.includes(file.id)
          
          return (
            <Card 
              key={file.id} 
              className={`hover:shadow-md transition-shadow cursor-pointer ${
                isSelected ? 'ring-2 ring-primary' : ''
              }`}
              onClick={() => handleFileClick(file)}
            >
              <CardContent className="p-4">
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center space-x-3">
                    <div className={`w-10 h-10 rounded-lg bg-muted flex items-center justify-center ${fileTypeConfig.color}`}>
                      <FileIcon className="w-5 h-5" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <h3 className="text-sm font-medium truncate">{file.name}</h3>
                      {file.type === 'file' && (
                        <p className="text-xs text-muted-foreground">
                          {formatFileSize(file.size)}
                        </p>
                      )}
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-1">
                    <input
                      type="checkbox"
                      checked={isSelected}
                      onChange={(e) => {
                        e.stopPropagation()
                        handleFileSelect(file.id)
                      }}
                      className="rounded"
                    />
                    
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-6 w-6 p-0"
                      onClick={(e) => e.stopPropagation()}
                    >
                      <MoreVertical className="w-3 h-3" />
                    </Button>
                  </div>
                </div>
                
                {/* File metadata */}
                <div className="space-y-2 text-xs text-muted-foreground">
                  <div>Modificado: {formatDate(file.modified_at)}</div>
                  
                  {file.generated_by && (
                    <div className="flex items-center space-x-1">
                      <Badge variant="outline" className="text-xs">
                        Generado por {file.generated_by}
                      </Badge>
                    </div>
                  )}
                  
                  <div className="flex items-center space-x-2">
                    {file.shared && (
                      <Badge variant="outline" className="text-xs">
                        <Share className="w-3 h-3 mr-1" />
                        Compartido
                      </Badge>
                    )}
                    
                    {file.extension && (
                      <Badge variant="outline" className="text-xs uppercase">
                        {file.extension}
                      </Badge>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          )
        })}
      </div>

      {filteredFiles.length === 0 && (
        <div className="text-center py-12">
          <FileText className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
          <h3 className="text-lg font-semibold mb-2">No se encontraron archivos</h3>
          <p className="text-muted-foreground mb-4">
            {searchQuery ? 'Intenta con otros términos de búsqueda' : 'Sube archivos o genera contenido con agentes'}
          </p>
          <div className="flex items-center justify-center space-x-2">
            <Button onClick={() => setIsUploadDialogOpen(true)}>
              <Upload className="w-4 h-4 mr-2" />
              Subir Archivos
            </Button>
            <Button variant="outline">
              <FolderPlus className="w-4 h-4 mr-2" />
              Nueva Carpeta
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}

