-- Datos iniciales para el sistema MANUS-like
-- Este script debe ejecutarse después de supabase_init.sql

-- Configuración del sistema por defecto
INSERT INTO system_config (config_key, config_value, description, is_sensitive) VALUES
('ollama_base_url', '"http://localhost:11434"', 'URL base para la API de Ollama', false),
('default_model', '"llama2"', 'Modelo de lenguaje por defecto', false),
('max_conversation_history', '100', 'Número máximo de mensajes en el historial', false),
('file_upload_max_size', '104857600', 'Tamaño máximo de archivo en bytes (100MB)', false),
('session_timeout', '3600', 'Tiempo de expiración de sesión en segundos', false),
('enable_audit_logging', 'true', 'Habilitar logging de auditoría', false),
('max_concurrent_tasks', '10', 'Número máximo de tareas concurrentes por usuario', false),
('system_name', '"MANUS-like System"', 'Nombre del sistema', false),
('system_version', '"1.0.0"', 'Versión del sistema', false),
('enable_tool_confirmation', 'false', 'Requerir confirmación para herramientas peligrosas', false),
('default_agent_temperature', '0.7', 'Temperatura por defecto para agentes', false),
('max_tokens_per_request', '4096', 'Máximo de tokens por solicitud', false),
('enable_memory_persistence', 'true', 'Habilitar persistencia de memoria de agentes', false),
('docker_network', '"manus_network"', 'Red de Docker para contenedores', false),
('backup_retention_days', '30', 'Días de retención de backups', false);

-- Herramientas básicas del sistema
INSERT INTO tools (name, display_name, description, category, function_schema, implementation_type, implementation_code, security_level, requires_confirmation) VALUES

-- Herramientas de sistema
('shell_exec', 'Ejecutar Comando Shell', 'Ejecuta comandos en el shell del sistema operativo', 'system', 
 '{"type": "function", "function": {"name": "shell_exec", "description": "Execute shell command", "parameters": {"type": "object", "properties": {"command": {"type": "string", "description": "Command to execute"}, "working_dir": {"type": "string", "description": "Working directory for command execution"}, "timeout": {"type": "integer", "description": "Timeout in seconds", "default": 30}}, "required": ["command"]}}}', 
 'python', 
 'import subprocess
import os
import signal
from typing import Dict, Any

def execute(params: Dict[str, Any]) -> Dict[str, Any]:
    command = params["command"]
    working_dir = params.get("working_dir", "/tmp")
    timeout = params.get("timeout", 30)
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=working_dir,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        return {
            "success": True,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "return_code": result.returncode
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": f"Command timed out after {timeout} seconds"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }',
 'moderate', true),

-- Herramientas de archivos
('file_read', 'Leer Archivo', 'Lee el contenido de un archivo de texto', 'file', 
 '{"type": "function", "function": {"name": "file_read", "description": "Read file content", "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "File path to read"}, "encoding": {"type": "string", "description": "File encoding", "default": "utf-8"}, "max_lines": {"type": "integer", "description": "Maximum lines to read"}}, "required": ["path"]}}}', 
 'python',
 'import os
from typing import Dict, Any

def execute(params: Dict[str, Any]) -> Dict[str, Any]:
    file_path = params["path"]
    encoding = params.get("encoding", "utf-8")
    max_lines = params.get("max_lines")
    
    try:
        if not os.path.exists(file_path):
            return {
                "success": False,
                "error": f"File not found: {file_path}"
            }
        
        with open(file_path, "r", encoding=encoding) as f:
            if max_lines:
                lines = []
                for i, line in enumerate(f):
                    if i >= max_lines:
                        break
                    lines.append(line)
                content = "".join(lines)
            else:
                content = f.read()
        
        return {
            "success": True,
            "content": content,
            "file_size": os.path.getsize(file_path)
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }',
 'safe', false),

('file_write', 'Escribir Archivo', 'Escribe contenido a un archivo', 'file', 
 '{"type": "function", "function": {"name": "file_write", "description": "Write content to file", "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "File path to write"}, "content": {"type": "string", "description": "Content to write"}, "encoding": {"type": "string", "description": "File encoding", "default": "utf-8"}, "append": {"type": "boolean", "description": "Append to file instead of overwriting", "default": false}}, "required": ["path", "content"]}}}', 
 'python',
 'import os
from typing import Dict, Any

def execute(params: Dict[str, Any]) -> Dict[str, Any]:
    file_path = params["path"]
    content = params["content"]
    encoding = params.get("encoding", "utf-8")
    append = params.get("append", False)
    
    try:
        # Crear directorio si no existe
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        mode = "a" if append else "w"
        with open(file_path, mode, encoding=encoding) as f:
            f.write(content)
        
        return {
            "success": True,
            "bytes_written": len(content.encode(encoding)),
            "file_path": file_path
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }',
 'safe', false),

('file_list', 'Listar Archivos', 'Lista archivos y directorios en una ruta', 'file', 
 '{"type": "function", "function": {"name": "file_list", "description": "List files and directories", "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "Directory path to list"}, "recursive": {"type": "boolean", "description": "List recursively", "default": false}, "show_hidden": {"type": "boolean", "description": "Show hidden files", "default": false}}, "required": ["path"]}}}', 
 'python',
 'import os
from typing import Dict, Any, List

def execute(params: Dict[str, Any]) -> Dict[str, Any]:
    dir_path = params["path"]
    recursive = params.get("recursive", False)
    show_hidden = params.get("show_hidden", False)
    
    try:
        if not os.path.exists(dir_path):
            return {
                "success": False,
                "error": f"Directory not found: {dir_path}"
            }
        
        files = []
        
        if recursive:
            for root, dirs, filenames in os.walk(dir_path):
                for filename in filenames:
                    if not show_hidden and filename.startswith("."):
                        continue
                    full_path = os.path.join(root, filename)
                    stat = os.stat(full_path)
                    files.append({
                        "name": filename,
                        "path": full_path,
                        "size": stat.st_size,
                        "is_directory": False,
                        "modified": stat.st_mtime
                    })
        else:
            for item in os.listdir(dir_path):
                if not show_hidden and item.startswith("."):
                    continue
                full_path = os.path.join(dir_path, item)
                stat = os.stat(full_path)
                files.append({
                    "name": item,
                    "path": full_path,
                    "size": stat.st_size if os.path.isfile(full_path) else 0,
                    "is_directory": os.path.isdir(full_path),
                    "modified": stat.st_mtime
                })
        
        return {
            "success": True,
            "files": files,
            "total_count": len(files)
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }',
 'safe', false),

-- Herramientas web
('web_search', 'Búsqueda Web', 'Realiza búsquedas en la web usando DuckDuckGo', 'web', 
 '{"type": "function", "function": {"name": "web_search", "description": "Search the web", "parameters": {"type": "object", "properties": {"query": {"type": "string", "description": "Search query"}, "max_results": {"type": "integer", "description": "Maximum number of results", "default": 10}, "region": {"type": "string", "description": "Search region", "default": "es-es"}}, "required": ["query"]}}}', 
 'python',
 'import requests
from typing import Dict, Any
from urllib.parse import quote

def execute(params: Dict[str, Any]) -> Dict[str, Any]:
    query = params["query"]
    max_results = params.get("max_results", 10)
    region = params.get("region", "es-es")
    
    try:
        # Usar DuckDuckGo Instant Answer API
        url = f"https://api.duckduckgo.com/?q={quote(query)}&format=json&no_html=1&skip_disambig=1"
        
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        results = []
        
        # Agregar respuesta abstracta si existe
        if data.get("Abstract"):
            results.append({
                "title": data.get("AbstractText", ""),
                "url": data.get("AbstractURL", ""),
                "snippet": data.get("Abstract", ""),
                "type": "abstract"
            })
        
        # Agregar resultados relacionados
        for item in data.get("RelatedTopics", [])[:max_results]:
            if isinstance(item, dict) and "Text" in item:
                results.append({
                    "title": item.get("Text", "").split(" - ")[0] if " - " in item.get("Text", "") else item.get("Text", ""),
                    "url": item.get("FirstURL", ""),
                    "snippet": item.get("Text", ""),
                    "type": "related"
                })
        
        return {
            "success": True,
            "results": results[:max_results],
            "query": query,
            "total_results": len(results)
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }',
 'safe', false),

('browser_navigate', 'Navegar Web', 'Navega a una URL específica y extrae contenido', 'web', 
 '{"type": "function", "function": {"name": "browser_navigate", "description": "Navigate to URL and extract content", "parameters": {"type": "object", "properties": {"url": {"type": "string", "description": "URL to navigate to"}, "extract_text": {"type": "boolean", "description": "Extract text content", "default": true}, "extract_links": {"type": "boolean", "description": "Extract links", "default": false}}, "required": ["url"]}}}', 
 'python',
 'import requests
from bs4 import BeautifulSoup
from typing import Dict, Any
from urllib.parse import urljoin, urlparse

def execute(params: Dict[str, Any]) -> Dict[str, Any]:
    url = params["url"]
    extract_text = params.get("extract_text", True)
    extract_links = params.get("extract_links", False)
    
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, "html.parser")
        
        result = {
            "success": True,
            "url": url,
            "title": soup.title.string if soup.title else "",
            "status_code": response.status_code
        }
        
        if extract_text:
            # Remover scripts y estilos
            for script in soup(["script", "style"]):
                script.decompose()
            
            text = soup.get_text()
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = " ".join(chunk for chunk in chunks if chunk)
            
            result["text"] = text[:5000]  # Limitar a 5000 caracteres
        
        if extract_links:
            links = []
            for link in soup.find_all("a", href=True):
                href = link["href"]
                absolute_url = urljoin(url, href)
                links.append({
                    "text": link.get_text(strip=True),
                    "url": absolute_url
                })
            result["links"] = links[:50]  # Limitar a 50 enlaces
        
        return result
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }',
 'safe', false),

-- Herramientas de análisis
('text_analyze', 'Analizar Texto', 'Analiza texto para extraer información útil', 'analysis', 
 '{"type": "function", "function": {"name": "text_analyze", "description": "Analyze text content", "parameters": {"type": "object", "properties": {"text": {"type": "string", "description": "Text to analyze"}, "analysis_type": {"type": "string", "description": "Type of analysis", "enum": ["summary", "keywords", "sentiment", "language"], "default": "summary"}}, "required": ["text"]}}}', 
 'python',
 'import re
from collections import Counter
from typing import Dict, Any

def execute(params: Dict[str, Any]) -> Dict[str, Any]:
    text = params["text"]
    analysis_type = params.get("analysis_type", "summary")
    
    try:
        result = {
            "success": True,
            "analysis_type": analysis_type,
            "text_length": len(text),
            "word_count": len(text.split())
        }
        
        if analysis_type == "summary":
            sentences = re.split(r"[.!?]+", text)
            sentences = [s.strip() for s in sentences if s.strip()]
            result["sentence_count"] = len(sentences)
            result["avg_sentence_length"] = sum(len(s.split()) for s in sentences) / len(sentences) if sentences else 0
            result["first_sentences"] = sentences[:3]
        
        elif analysis_type == "keywords":
            words = re.findall(r"\b\w+\b", text.lower())
            words = [w for w in words if len(w) > 3]  # Filtrar palabras cortas
            word_freq = Counter(words)
            result["top_keywords"] = word_freq.most_common(10)
        
        elif analysis_type == "sentiment":
            # Análisis básico de sentimiento
            positive_words = ["bueno", "excelente", "genial", "fantástico", "increíble", "perfecto", "maravilloso"]
            negative_words = ["malo", "terrible", "horrible", "pésimo", "awful", "disgusting"]
            
            text_lower = text.lower()
            positive_count = sum(1 for word in positive_words if word in text_lower)
            negative_count = sum(1 for word in negative_words if word in text_lower)
            
            if positive_count > negative_count:
                sentiment = "positive"
            elif negative_count > positive_count:
                sentiment = "negative"
            else:
                sentiment = "neutral"
            
            result["sentiment"] = sentiment
            result["positive_indicators"] = positive_count
            result["negative_indicators"] = negative_count
        
        elif analysis_type == "language":
            # Detección básica de idioma
            spanish_words = ["el", "la", "de", "que", "y", "en", "un", "es", "se", "no", "te", "lo", "le", "da", "su", "por", "son", "con", "para", "al", "una", "del", "todo", "está", "muy", "fue", "han", "era", "sobre", "ser", "tiene", "pero", "ya", "las", "él", "hasta", "puede", "va", "mi", "porque", "qué", "sólo", "sin", "vez", "tanto", "donde", "mucho", "hay", "también", "fue", "tiempo", "cada", "uno", "hace", "más", "como", "ahora", "entre", "cuando", "quiere", "desde", "aquí", "nos", "durante", "todos", "uno", "les", "ni", "contra", "otros", "ese", "eso", "ante", "ellos", "e", "esto", "mí", "antes", "algunos", "qué", "unos", "yo", "otro", "otras", "otra", "él", "tanto", "esa", "estos", "mucho", "quienes", "nada", "muchos", "cual", "poco", "ella", "estar", "estas", "algunas", "algo", "nosotros", "mi", "mis", "tú", "te", "ti", "tu", "tus", "ellas", "nosotras", "vosotros", "vosotras", "os", "mío", "mía", "míos", "mías", "tuyo", "tuya", "tuyos", "tuyas", "suyo", "suya", "suyos", "suyas", "nuestro", "nuestra", "nuestros", "nuestras", "vuestro", "vuestra", "vuestros", "vuestras", "esos", "esas"]
            english_words = ["the", "be", "to", "of", "and", "a", "in", "that", "have", "i", "it", "for", "not", "on", "with", "he", "as", "you", "do", "at", "this", "but", "his", "by", "from", "they", "she", "or", "an", "will", "my", "one", "all", "would", "there", "their", "what", "so", "up", "out", "if", "about", "who", "get", "which", "go", "me", "when", "make", "can", "like", "time", "no", "just", "him", "know", "take", "people", "into", "year", "your", "good", "some", "could", "them", "see", "other", "than", "then", "now", "look", "only", "come", "its", "over", "think", "also", "back", "after", "use", "two", "how", "our", "work", "first", "well", "way", "even", "new", "want", "because", "any", "these", "give", "day", "most", "us"]
            
            words = re.findall(r"\b\w+\b", text.lower())
            spanish_count = sum(1 for word in words if word in spanish_words)
            english_count = sum(1 for word in words if word in english_words)
            
            if spanish_count > english_count:
                language = "spanish"
            elif english_count > spanish_count:
                language = "english"
            else:
                language = "unknown"
            
            result["detected_language"] = language
            result["spanish_indicators"] = spanish_count
            result["english_indicators"] = english_count
        
        return result
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }',
 'safe', false),

-- Herramientas de utilidad
('json_parse', 'Parsear JSON', 'Parsea y valida contenido JSON', 'utility', 
 '{"type": "function", "function": {"name": "json_parse", "description": "Parse and validate JSON content", "parameters": {"type": "object", "properties": {"json_string": {"type": "string", "description": "JSON string to parse"}, "pretty_print": {"type": "boolean", "description": "Format output nicely", "default": true}}, "required": ["json_string"]}}}', 
 'python',
 'import json
from typing import Dict, Any

def execute(params: Dict[str, Any]) -> Dict[str, Any]:
    json_string = params["json_string"]
    pretty_print = params.get("pretty_print", True)
    
    try:
        parsed_data = json.loads(json_string)
        
        result = {
            "success": True,
            "valid_json": True,
            "data": parsed_data
        }
        
        if pretty_print:
            result["formatted"] = json.dumps(parsed_data, indent=2, ensure_ascii=False)
        
        # Información adicional sobre el JSON
        if isinstance(parsed_data, dict):
            result["type"] = "object"
            result["keys"] = list(parsed_data.keys())
            result["key_count"] = len(parsed_data)
        elif isinstance(parsed_data, list):
            result["type"] = "array"
            result["length"] = len(parsed_data)
        else:
            result["type"] = type(parsed_data).__name__
        
        return result
    except json.JSONDecodeError as e:
        return {
            "success": False,
            "valid_json": False,
            "error": f"JSON parsing error: {str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }',
 'safe', false);

-- Agente por defecto
INSERT INTO agents (name, description, system_prompt, model_name, tools_enabled, is_public) VALUES
('Asistente General', 
 'Agente de propósito general capaz de realizar múltiples tareas usando herramientas disponibles. Puede ejecutar comandos, manipular archivos, buscar en la web y analizar contenido.',
 'Eres un asistente de IA útil y capaz llamado MANUS. Puedes ayudar con una amplia variedad de tareas utilizando las herramientas disponibles. 

Características principales:
- Siempre explica lo que estás haciendo y por qué
- Usa las herramientas de manera eficiente y segura
- Proporciona respuestas detalladas y útiles
- Mantén un tono profesional pero amigable
- Si una tarea requiere múltiples pasos, explica el plan antes de ejecutarlo
- Siempre verifica los resultados de las herramientas antes de continuar

Herramientas disponibles:
- shell_exec: Para ejecutar comandos del sistema
- file_read/file_write/file_list: Para manipular archivos
- web_search/browser_navigate: Para buscar información en la web
- text_analyze: Para analizar contenido de texto
- json_parse: Para trabajar con datos JSON

Recuerda siempre priorizar la seguridad y pedir confirmación para operaciones que puedan ser destructivas.',
 'llama2', 
 ARRAY['shell_exec', 'file_read', 'file_write', 'file_list', 'web_search', 'browser_navigate', 'text_analyze', 'json_parse'],
 true),

('Desarrollador', 
 'Agente especializado en tareas de desarrollo de software, programación y análisis de código.',
 'Eres un desarrollador de software experto. Tu especialidad es ayudar con tareas de programación, análisis de código, debugging y desarrollo de aplicaciones.

Capacidades principales:
- Análisis y revisión de código
- Debugging y resolución de problemas
- Desarrollo de scripts y aplicaciones
- Documentación técnica
- Optimización de rendimiento
- Mejores prácticas de programación

Siempre:
- Proporciona código limpio y bien documentado
- Explica las decisiones técnicas
- Sugiere mejores prácticas
- Considera la seguridad y el rendimiento
- Usa las herramientas disponibles para probar el código',
 'llama2',
 ARRAY['shell_exec', 'file_read', 'file_write', 'file_list', 'text_analyze', 'json_parse'],
 true),

('Investigador Web', 
 'Agente especializado en investigación web, análisis de contenido y recopilación de información.',
 'Eres un investigador especializado en búsqueda y análisis de información web. Tu objetivo es encontrar, analizar y sintetizar información de manera eficiente y precisa.

Capacidades principales:
- Búsqueda avanzada en la web
- Análisis de contenido web
- Verificación de fuentes
- Síntesis de información
- Extracción de datos relevantes

Metodología:
- Usa múltiples fuentes para verificar información
- Analiza la credibilidad de las fuentes
- Proporciona resúmenes claros y estructurados
- Cita las fuentes utilizadas
- Identifica posibles sesgos o limitaciones',
 'llama2',
 ARRAY['web_search', 'browser_navigate', 'text_analyze', 'file_write', 'json_parse'],
 true);

-- Usuario administrador por defecto (debe actualizarse con datos reales)
INSERT INTO users (email, username, full_name, role) VALUES
('admin@manus-system.local', 'admin', 'Administrador del Sistema', 'admin');

-- Actualizar contadores de uso de herramientas
UPDATE tools SET usage_count = 0;

