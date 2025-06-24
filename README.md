# 🤖 MANUS-like System - Sistema de Agentes IA Autónomos

Un sistema completo de agentes de inteligencia artificial autónomos, similar a MANUS, que puede resolver cualquier tarea usando herramientas avanzadas y modelos de lenguaje locales.

## ✨ Características Principales

- 🧠 **Agentes IA Autónomos** - Capaces de resolver tareas complejas de forma independiente
- 🛠️ **Herramientas MCP** - Integración completa con Model Context Protocol y Docker
- 🎯 **Interfaz Similar a MANUS** - UI/UX idéntica para una experiencia familiar
- 🔧 **Configuración Extrema** - Panel de administración para configurar todo
- 🐳 **Docker Nativo** - Ejecución segura de herramientas en contenedores
- 🦙 **Ollama Integrado** - Modelos de lenguaje locales sin dependencias externas
- 🗄️ **Supabase Backend** - Base de datos robusta y escalable
- 🌐 **Multiplataforma** - Windows, Linux y macOS

## 🚀 Instalación Ultra-Sencilla

### Requisitos Mínimos
- **Sistema Operativo**: Windows 10+, Ubuntu 20.04+, o macOS 12+
- **RAM**: 8GB mínimo (16GB recomendado)
- **Almacenamiento**: 20GB libres
- **Internet**: Conexión estable para descarga inicial

### Instalación en 1 Comando

```bash
# Descargar e instalar automáticamente
python setup.py
```

**¡Eso es todo!** El instalador detectará tu sistema operativo y configurará automáticamente:

✅ Docker y Docker Compose  
✅ Node.js y dependencias  
✅ Python y librerías  
✅ Ollama y modelos IA  
✅ Base de datos PostgreSQL (local para desarrollo, ver sección Supabase)
✅ Todas las configuraciones  
✅ Scripts de inicio  
✅ Acceso directo en escritorio  

### Configuración de Supabase (Importante)

Este proyecto utiliza Supabase como backend de base de datos en producción o para una configuración más robusta. Después de la instalación general, necesitarás configurar tu instancia de Supabase.

1.  **Crea un proyecto en [Supabase](https://supabase.com/).**
2.  **Obtén la URL de tu proyecto y la clave de API anónima.** Las encontrarás en la configuración de API de tu proyecto Supabase.
3.  **Ejecuta el script de configuración de Supabase:**
    ```bash
    python supabase_setup.py
    ```
    Este script te guiará a través del proceso de configuración de tu base de datos Supabase utilizando la **Supabase CLI**.

    **Prerrequisitos para usar `supabase_setup.py`:**
    1.  **Supabase CLI Instalada:** Debes tener la Supabase CLI instalada en tu sistema. Si no la tienes, sigue las instrucciones en [Supabase CLI Documentation](https://supabase.com/docs/guides/cli).
    2.  **Login en Supabase CLI:** Debes haber iniciado sesión en la Supabase CLI usando el comando `supabase login` en tu terminal. El script verificará esto y te guiará si es necesario.
    3.  **Archivo `supabase_init.sql`:** Asegúrate de que el archivo `supabase_init.sql` (que contiene el esquema inicial de la base de datos) esté presente en el directorio raíz del proyecto.

    **¿Qué hace el script `supabase_setup.py`?**
    *   Verifica que la Supabase CLI esté instalada y que hayas iniciado sesión.
    *   Se asegura de que el directorio actual esté configurado como un proyecto Supabase local (ejecutando `supabase init` si es necesario y lo apruebas).
    *   Te pide el `PROJECT_REF` de tu proyecto Supabase (si no puede encontrarlo en `supabase/config.toml`).
    *   Vincula tu proyecto local con tu proyecto Supabase remoto usando `supabase link`.
    *   Crea un nuevo archivo de migración en el directorio `supabase/migrations/` a partir del contenido de `supabase_init.sql`.
    *   Te pide confirmación y luego ejecuta `supabase db push` para aplicar esta migración (y cualquier otra pendiente) a tu base de datos Supabase remota.
    *   Te proporciona retroalimentación basada en la salida de los comandos de la Supabase CLI.

    **Importante:**
    *   El script interactuará con la Supabase CLI. Lee atentamente los mensajes y las confirmaciones que solicita.
    *   Después de ejecutar el script, siempre es una buena práctica verificar tu dashboard de Supabase para confirmar que el esquema de la base de datos se haya aplicado correctamente.

### Instalación Paso a Paso (Alternativa)

Si prefieres instalar manualmente:

#### 1. Clonar el Repositorio
```bash
git clone https://github.com/tu-usuario/manus-like-system.git
cd manus-like-system
```

#### 2. Ejecutar Instalador
```bash
python setup.py
```

#### 3. Iniciar el Sistema
```bash
# Windows
scripts/start.bat

# Linux/macOS
./scripts/start.sh
```

## 🎮 Uso del Sistema

### Primer Inicio

1. **Abrir el navegador** en `http://localhost:3000`
2. **Iniciar sesión** con las credenciales por defecto:
   - Usuario: `admin@manus.local`
   - Contraseña: `admin123`
3. **¡Listo!** Ya puedes usar tu sistema MANUS-like

### Crear tu Primer Agente

1. Ve a la sección **"Agentes"**
2. Haz clic en **"Nuevo Agente"**
3. Configura:
   - **Nombre**: "Mi Asistente Personal"
   - **Modelo**: llama2 (o el que prefieras)
   - **Prompt del Sistema**: "Eres un asistente útil y eficiente"
   - **Herramientas**: Selecciona las que necesites
4. **Guardar** y ¡tu agente está listo!

### Ejecutar una Tarea

1. Ve a **"Chat"** o **"Conversaciones"**
2. Selecciona tu agente
3. Escribe tu solicitud, por ejemplo:
   ```
   "Analiza el archivo ventas.csv y crea un reporte con gráficos"
   ```
4. El agente ejecutará automáticamente:
   - Análisis del archivo
   - Procesamiento de datos
   - Generación de gráficos
   - Creación del reporte
   - Entrega de resultados

## 🛠️ Herramientas Disponibles

El sistema incluye herramientas MCP pre-configuradas:

### 📁 **Filesystem**
- Lectura y escritura de archivos
- Navegación de directorios
- Búsqueda de contenido

### 🐙 **GitHub**
- Gestión de repositorios
- Creación de issues
- Operaciones con archivos
- Webhooks

### 🗄️ **PostgreSQL**
- Consultas de base de datos
- Inspección de esquemas
- Análisis de datos

### 🌐 **Puppeteer**
- Automatización web
- Web scraping
- Capturas de pantalla
- Llenado de formularios

### 🧠 **Memory**
- Sistema de memoria persistente
- Búsqueda semántica
- Grafos de conocimiento

## ⚙️ Configuración Avanzada

### Panel de Administración

Accede a `http://localhost:3000/admin` para configurar:

- **Usuarios y Permisos**
- **Modelos de Ollama**
- **Herramientas MCP**
- **Configuración del Sistema**
- **Logs y Monitoreo**
- **Backups Automáticos**

### Agregar Nuevos Modelos

```bash
# Conectar a Ollama
ollama pull mistral
ollama pull codellama
ollama pull neural-chat
```

Los modelos aparecerán automáticamente en el panel de administración.

### Configurar Herramientas Personalizadas

1. Ve a **Admin → Herramientas**
2. Haz clic en **"Agregar Herramienta"**
3. Configura la imagen Docker y parámetros
4. **Instalar** y **Activar**

## 🔧 Comandos Útiles

### Gestión del Sistema
```bash
# Iniciar sistema
./scripts/start.sh

# Detener sistema
./scripts/stop.sh

# Ver logs
docker-compose logs -f

# Reiniciar servicios
docker-compose restart
```

### Gestión de Ollama
```bash
# Listar modelos instalados
ollama list

# Descargar nuevo modelo
ollama pull llama2:13b

# Eliminar modelo
ollama rm modelo_name
```

### Gestión de Base de Datos
```bash
# Backup de la base de datos
docker exec manus-postgres pg_dump -U manus_user manus_db > backup.sql

# Restaurar backup
docker exec -i manus-postgres psql -U manus_user manus_db < backup.sql
```

## 🌐 URLs de Acceso

- **Frontend Principal**: http://localhost:3000
- **API Backend**: http://localhost:5000
- **Documentación API**: http://localhost:5000/docs
- **Panel Admin**: http://localhost:3000/admin
- **Ollama API**: http://localhost:11434
- **Base de Datos**: localhost:5432

## 🔐 Seguridad

### Credenciales por Defecto
- **Admin**: admin@manus.local / admin123
- **Base de Datos**: manus_user / manus_password_2024

### Cambiar Contraseñas
1. Ve a **Configuración → Seguridad**
2. Cambia la contraseña del administrador
3. Actualiza las variables de entorno en `.env`

### Configurar HTTPS
1. Coloca certificados SSL en `docker/ssl/`
2. Actualiza `docker/nginx.conf`
3. Reinicia con `docker-compose restart nginx`

## 📊 Monitoreo y Logs

### Ver Estado del Sistema
```bash
# Estado de contenedores
docker-compose ps

# Uso de recursos
docker stats

# Logs en tiempo real
docker-compose logs -f backend
```

### Métricas Disponibles
- **CPU y Memoria** por servicio
- **Requests por minuto** al API
- **Tareas ejecutadas** por agente
- **Tiempo de respuesta** promedio
- **Errores y excepciones**

## 🆘 Solución de Problemas

### El sistema no inicia
```bash
# Verificar Docker
docker --version

# Verificar Ollama
ollama --version

# Reiniciar servicios
docker-compose down && docker-compose up -d
```

### Error de conexión a la base de datos
```bash
# Verificar PostgreSQL
docker logs manus-postgres

# Reiniciar base de datos
docker-compose restart postgres
```

### Ollama no responde
```bash
# Reiniciar Ollama
ollama serve

# Verificar modelos
ollama list
```

### Puerto ocupado
```bash
# Cambiar puertos en docker-compose.yml
# Por ejemplo: "3001:3000" en lugar de "3000:3000"
```

## 🤝 Contribuir

¡Las contribuciones son bienvenidas!

1. Fork el repositorio
2. Crea una rama para tu feature
3. Commit tus cambios
4. Push a la rama
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver `LICENSE` para más detalles.

## 🙏 Agradecimientos

- **Anthropic** por la inspiración de MANUS
- **Ollama** por los modelos de lenguaje locales
- **Docker** por la containerización
- **Supabase** por la infraestructura de base de datos
- **React** y **Flask** por los frameworks

## 📞 Soporte

¿Necesitas ayuda? 

- 📧 **Email**: soporte@manus-like.com
- 💬 **Discord**: [Servidor de la Comunidad](https://discord.gg/manus-like)
- 📖 **Documentación**: [docs.manus-like.com](https://docs.manus-like.com)
- 🐛 **Issues**: [GitHub Issues](https://github.com/tu-usuario/manus-like-system/issues)

---

**¡Disfruta construyendo con tu sistema MANUS-like! 🚀**

