# Diseño de Base de Datos - Sistema MANUS-like

## Esquema de Base de Datos para Supabase

Este documento detalla el diseño completo de la base de datos PostgreSQL que se utilizará con Supabase para el sistema MANUS-like. El esquema está diseñado para soportar todas las funcionalidades requeridas: gestión de usuarios, agentes autónomos, tareas, herramientas, conversaciones y configuraciones del sistema.

## Tablas Principales

### 1. Tabla `users`
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    full_name VARCHAR(255),
    avatar_url TEXT,
    role VARCHAR(50) DEFAULT 'user' CHECK (role IN ('admin', 'user', 'viewer')),
    is_active BOOLEAN DEFAULT true,
    preferences JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Índices para optimización
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_role ON users(role);
```

### 2. Tabla `agents`
```sql
CREATE TABLE agents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    system_prompt TEXT NOT NULL,
    model_name VARCHAR(100) NOT NULL,
    temperature DECIMAL(3,2) DEFAULT 0.7 CHECK (temperature >= 0 AND temperature <= 2),
    max_tokens INTEGER DEFAULT 4096,
    tools_enabled TEXT[] DEFAULT '{}',
    memory_enabled BOOLEAN DEFAULT true,
    memory_limit INTEGER DEFAULT 10000,
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    is_public BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,
    configuration JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Índices
CREATE INDEX idx_agents_created_by ON agents(created_by);
CREATE INDEX idx_agents_is_public ON agents(is_public);
CREATE INDEX idx_agents_is_active ON agents(is_active);
```

### 3. Tabla `conversations`
```sql
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('active', 'completed', 'paused', 'error')),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Índices
CREATE INDEX idx_conversations_user_id ON conversations(user_id);
CREATE INDEX idx_conversations_agent_id ON conversations(agent_id);
CREATE INDEX idx_conversations_status ON conversations(status);
CREATE INDEX idx_conversations_created_at ON conversations(created_at DESC);
```

### 4. Tabla `messages`
```sql
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'system', 'tool')),
    content TEXT NOT NULL,
    tool_calls JSONB,
    tool_call_id VARCHAR(255),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Índices
CREATE INDEX idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX idx_messages_role ON messages(role);
CREATE INDEX idx_messages_created_at ON messages(created_at);
```

### 5. Tabla `tasks`
```sql
CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled')),
    priority INTEGER DEFAULT 1 CHECK (priority >= 1 AND priority <= 5),
    current_phase INTEGER DEFAULT 1,
    total_phases INTEGER DEFAULT 1,
    progress_percentage INTEGER DEFAULT 0 CHECK (progress_percentage >= 0 AND progress_percentage <= 100),
    result JSONB,
    error_message TEXT,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Índices
CREATE INDEX idx_tasks_conversation_id ON tasks(conversation_id);
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_priority ON tasks(priority);
CREATE INDEX idx_tasks_created_at ON tasks(created_at DESC);
```

### 6. Tabla `tools`
```sql
CREATE TABLE tools (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) UNIQUE NOT NULL,
    display_name VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    category VARCHAR(100) NOT NULL,
    function_schema JSONB NOT NULL,
    implementation_type VARCHAR(50) DEFAULT 'python' CHECK (implementation_type IN ('python', 'shell', 'api', 'builtin')),
    implementation_code TEXT,
    is_enabled BOOLEAN DEFAULT true,
    requires_confirmation BOOLEAN DEFAULT false,
    security_level VARCHAR(20) DEFAULT 'safe' CHECK (security_level IN ('safe', 'moderate', 'dangerous')),
    usage_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Índices
CREATE INDEX idx_tools_name ON tools(name);
CREATE INDEX idx_tools_category ON tools(category);
CREATE INDEX idx_tools_is_enabled ON tools(is_enabled);
```

### 7. Tabla `tool_executions`
```sql
CREATE TABLE tool_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    tool_id UUID NOT NULL REFERENCES tools(id) ON DELETE CASCADE,
    message_id UUID REFERENCES messages(id) ON DELETE SET NULL,
    input_parameters JSONB NOT NULL,
    output_result JSONB,
    status VARCHAR(50) DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed')),
    execution_time_ms INTEGER,
    error_message TEXT,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

-- Índices
CREATE INDEX idx_tool_executions_task_id ON tool_executions(task_id);
CREATE INDEX idx_tool_executions_tool_id ON tool_executions(tool_id);
CREATE INDEX idx_tool_executions_status ON tool_executions(status);
```

### 8. Tabla `files`
```sql
CREATE TABLE files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    task_id UUID REFERENCES tasks(id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    file_path TEXT NOT NULL,
    file_size BIGINT NOT NULL,
    mime_type VARCHAR(255) NOT NULL,
    file_hash VARCHAR(64),
    is_temporary BOOLEAN DEFAULT false,
    expires_at TIMESTAMP WITH TIME ZONE,
    uploaded_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Índices
CREATE INDEX idx_files_conversation_id ON files(conversation_id);
CREATE INDEX idx_files_task_id ON files(task_id);
CREATE INDEX idx_files_uploaded_by ON files(uploaded_by);
CREATE INDEX idx_files_expires_at ON files(expires_at);
```

### 9. Tabla `system_config`
```sql
CREATE TABLE system_config (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    config_key VARCHAR(255) UNIQUE NOT NULL,
    config_value JSONB NOT NULL,
    description TEXT,
    is_sensitive BOOLEAN DEFAULT false,
    updated_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Índices
CREATE INDEX idx_system_config_key ON system_config(config_key);
```

### 10. Tabla `audit_logs`
```sql
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100) NOT NULL,
    resource_id UUID,
    old_values JSONB,
    new_values JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Índices
CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_audit_logs_resource_type ON audit_logs(resource_type);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at DESC);
```

## Funciones y Triggers

### Función para actualizar `updated_at`
```sql
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';
```

### Triggers para actualización automática
```sql
-- Trigger para users
CREATE TRIGGER update_users_updated_at 
    BEFORE UPDATE ON users 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger para agents
CREATE TRIGGER update_agents_updated_at 
    BEFORE UPDATE ON agents 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger para conversations
CREATE TRIGGER update_conversations_updated_at 
    BEFORE UPDATE ON conversations 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger para tasks
CREATE TRIGGER update_tasks_updated_at 
    BEFORE UPDATE ON tasks 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger para tools
CREATE TRIGGER update_tools_updated_at 
    BEFORE UPDATE ON tools 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger para system_config
CREATE TRIGGER update_system_config_updated_at 
    BEFORE UPDATE ON system_config 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();
```

## Políticas de Seguridad (Row Level Security)

### Políticas para la tabla `users`
```sql
-- Habilitar RLS
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

-- Los usuarios pueden ver y editar su propio perfil
CREATE POLICY "Users can view own profile" ON users
    FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update own profile" ON users
    FOR UPDATE USING (auth.uid() = id);

-- Los administradores pueden ver todos los usuarios
CREATE POLICY "Admins can view all users" ON users
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM users 
            WHERE id = auth.uid() AND role = 'admin'
        )
    );
```

### Políticas para la tabla `conversations`
```sql
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;

-- Los usuarios pueden ver sus propias conversaciones
CREATE POLICY "Users can view own conversations" ON conversations
    FOR SELECT USING (user_id = auth.uid());

-- Los usuarios pueden crear conversaciones
CREATE POLICY "Users can create conversations" ON conversations
    FOR INSERT WITH CHECK (user_id = auth.uid());

-- Los usuarios pueden actualizar sus propias conversaciones
CREATE POLICY "Users can update own conversations" ON conversations
    FOR UPDATE USING (user_id = auth.uid());
```

### Políticas para la tabla `messages`
```sql
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;

-- Los usuarios pueden ver mensajes de sus conversaciones
CREATE POLICY "Users can view messages from own conversations" ON messages
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM conversations 
            WHERE id = conversation_id AND user_id = auth.uid()
        )
    );

-- Los usuarios pueden crear mensajes en sus conversaciones
CREATE POLICY "Users can create messages in own conversations" ON messages
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM conversations 
            WHERE id = conversation_id AND user_id = auth.uid()
        )
    );
```

## Datos Iniciales

### Configuración del sistema por defecto
```sql
INSERT INTO system_config (config_key, config_value, description) VALUES
('ollama_base_url', '"http://localhost:11434"', 'URL base para la API de Ollama'),
('default_model', '"llama2"', 'Modelo de lenguaje por defecto'),
('max_conversation_history', '100', 'Número máximo de mensajes en el historial'),
('file_upload_max_size', '104857600', 'Tamaño máximo de archivo en bytes (100MB)'),
('session_timeout', '3600', 'Tiempo de expiración de sesión en segundos'),
('enable_audit_logging', 'true', 'Habilitar logging de auditoría'),
('max_concurrent_tasks', '10', 'Número máximo de tareas concurrentes por usuario');
```

### Herramientas básicas
```sql
INSERT INTO tools (name, display_name, description, category, function_schema, implementation_type) VALUES
('shell_exec', 'Ejecutar Comando Shell', 'Ejecuta comandos en el shell del sistema', 'system', 
 '{"type": "function", "function": {"name": "shell_exec", "description": "Execute shell command", "parameters": {"type": "object", "properties": {"command": {"type": "string", "description": "Command to execute"}}, "required": ["command"]}}}', 
 'python'),
 
('file_read', 'Leer Archivo', 'Lee el contenido de un archivo de texto', 'file', 
 '{"type": "function", "function": {"name": "file_read", "description": "Read file content", "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "File path to read"}}, "required": ["path"]}}}', 
 'python'),
 
('file_write', 'Escribir Archivo', 'Escribe contenido a un archivo', 'file', 
 '{"type": "function", "function": {"name": "file_write", "description": "Write content to file", "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "File path to write"}, "content": {"type": "string", "description": "Content to write"}}, "required": ["path", "content"]}}}', 
 'python'),
 
('web_search', 'Búsqueda Web', 'Realiza búsquedas en la web', 'web', 
 '{"type": "function", "function": {"name": "web_search", "description": "Search the web", "parameters": {"type": "object", "properties": {"query": {"type": "string", "description": "Search query"}}, "required": ["query"]}}}', 
 'python'),
 
('browser_navigate', 'Navegar Web', 'Navega a una URL específica', 'web', 
 '{"type": "function", "function": {"name": "browser_navigate", "description": "Navigate to URL", "parameters": {"type": "object", "properties": {"url": {"type": "string", "description": "URL to navigate to"}}, "required": ["url"]}}}', 
 'python');
```

### Agente por defecto
```sql
INSERT INTO agents (name, description, system_prompt, model_name, tools_enabled) VALUES
('Asistente General', 'Agente de propósito general capaz de realizar múltiples tareas', 
 'Eres un asistente de IA útil y capaz. Puedes ayudar con una amplia variedad de tareas utilizando las herramientas disponibles. Siempre explica lo que estás haciendo y por qué.', 
 'llama2', 
 ARRAY['shell_exec', 'file_read', 'file_write', 'web_search', 'browser_navigate']);
```

## Vistas Útiles

### Vista de conversaciones con información del agente
```sql
CREATE VIEW conversation_details AS
SELECT 
    c.id,
    c.title,
    c.status,
    c.created_at,
    c.updated_at,
    u.username,
    u.full_name,
    a.name as agent_name,
    a.description as agent_description,
    (SELECT COUNT(*) FROM messages m WHERE m.conversation_id = c.id) as message_count,
    (SELECT COUNT(*) FROM tasks t WHERE t.conversation_id = c.id) as task_count
FROM conversations c
JOIN users u ON c.user_id = u.id
JOIN agents a ON c.agent_id = a.id;
```

### Vista de estadísticas de herramientas
```sql
CREATE VIEW tool_statistics AS
SELECT 
    t.id,
    t.name,
    t.display_name,
    t.category,
    t.usage_count,
    COUNT(te.id) as execution_count,
    AVG(te.execution_time_ms) as avg_execution_time,
    COUNT(CASE WHEN te.status = 'completed' THEN 1 END) as successful_executions,
    COUNT(CASE WHEN te.status = 'failed' THEN 1 END) as failed_executions
FROM tools t
LEFT JOIN tool_executions te ON t.id = te.tool_id
GROUP BY t.id, t.name, t.display_name, t.category, t.usage_count;
```

## Índices Adicionales para Rendimiento

```sql
-- Índices compuestos para consultas frecuentes
CREATE INDEX idx_messages_conversation_created ON messages(conversation_id, created_at DESC);
CREATE INDEX idx_tasks_status_priority ON tasks(status, priority DESC);
CREATE INDEX idx_tool_executions_tool_status ON tool_executions(tool_id, status);
CREATE INDEX idx_files_conversation_temporary ON files(conversation_id, is_temporary);

-- Índices para búsqueda de texto
CREATE INDEX idx_conversations_title_gin ON conversations USING gin(to_tsvector('spanish', title));
CREATE INDEX idx_messages_content_gin ON messages USING gin(to_tsvector('spanish', content));
CREATE INDEX idx_tasks_title_description_gin ON tasks USING gin(to_tsvector('spanish', title || ' ' || COALESCE(description, '')));
```

Este esquema de base de datos proporciona una base sólida para el sistema MANUS-like, con todas las tablas, relaciones, índices y políticas de seguridad necesarias para soportar las funcionalidades requeridas.

