import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO
import logging
from datetime import datetime
import uuid

# Importar modelos y rutas
from src.models.database import db, init_db
from src.routes.auth import auth_bp
from src.routes.agents import agents_bp
from src.routes.conversations import conversations_bp
from src.routes.tasks import tasks_bp
from src.routes.tools import tools_bp
from src.routes.files import files_bp
from src.routes.admin import admin_bp
from src.routes.ollama import ollama_bp
from src.services.config_service import ConfigService

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_app():
    """Factory function para crear la aplicación Flask"""
    app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
    
    # Configuración básica
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'manus-secret-key-change-in-production')
    app.config['DEBUG'] = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    
    # Configuración de Supabase
    app.config['SUPABASE_URL'] = os.environ.get('SUPABASE_URL', 'http://localhost:54321')
    app.config['SUPABASE_KEY'] = os.environ.get('SUPABASE_KEY', 'your-supabase-anon-key')
    app.config['SUPABASE_SERVICE_KEY'] = os.environ.get('SUPABASE_SERVICE_KEY', 'your-supabase-service-key')
    
    # Configuración de Ollama
    app.config['OLLAMA_BASE_URL'] = os.environ.get('OLLAMA_BASE_URL', 'http://localhost:11434')
    
    # Configuración de archivos
    app.config['UPLOAD_FOLDER'] = os.environ.get('UPLOAD_FOLDER', '/tmp/manus-uploads')
    app.config['MAX_CONTENT_LENGTH'] = int(os.environ.get('MAX_CONTENT_LENGTH', '104857600'))  # 100MB
    
    # Habilitar CORS para todas las rutas
    CORS(app, origins="*", supports_credentials=True)
    
    # Inicializar SocketIO para comunicación en tiempo real
    socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')
    app.socketio = socketio
    
    # Inicializar base de datos
    init_db(app)
    
    # Registrar blueprints
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(agents_bp, url_prefix='/api/agents')
    app.register_blueprint(conversations_bp, url_prefix='/api/conversations')
    app.register_blueprint(tasks_bp, url_prefix='/api/tasks')
    app.register_blueprint(tools_bp, url_prefix='/api/tools')
    app.register_blueprint(files_bp, url_prefix='/api/files')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(ollama_bp, url_prefix='/api/ollama')
    
    # Middleware para logging de requests
    @app.before_request
    def log_request_info():
        if request.path.startswith('/api/'):
            logger.info(f"{request.method} {request.path} - {request.remote_addr}")
    
    # Middleware para manejo de errores
    @app.errorhandler(404)
    def not_found(error):
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Endpoint not found'}), 404
        return serve_frontend('index.html')
    
    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Internal server error: {str(error)}")
        return jsonify({'error': 'Internal server error'}), 500
    
    @app.errorhandler(413)
    def too_large(error):
        return jsonify({'error': 'File too large'}), 413
    
    # Ruta de health check
    @app.route('/api/health')
    def health_check():
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'version': '1.0.0',
            'services': {
                'database': 'connected',
                'ollama': 'checking...'
            }
        })
    
    # Ruta para servir el frontend
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve_frontend(path):
        static_folder_path = app.static_folder
        if static_folder_path is None:
            return "Static folder not configured", 404

        if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
            return send_from_directory(static_folder_path, path)
        else:
            index_path = os.path.join(static_folder_path, 'index.html')
            if os.path.exists(index_path):
                return send_from_directory(static_folder_path, 'index.html')
            else:
                return jsonify({
                    'message': 'MANUS-like Backend API',
                    'version': '1.0.0',
                    'endpoints': {
                        'health': '/api/health',
                        'auth': '/api/auth/*',
                        'agents': '/api/agents/*',
                        'conversations': '/api/conversations/*',
                        'tasks': '/api/tasks/*',
                        'tools': '/api/tools/*',
                        'files': '/api/files/*',
                        'admin': '/api/admin/*',
                        'ollama': '/api/ollama/*'
                    }
                }), 200
    
    # Eventos de SocketIO
    @socketio.on('connect')
    def handle_connect():
        logger.info(f"Client connected: {request.sid}")
    
    @socketio.on('disconnect')
    def handle_disconnect():
        logger.info(f"Client disconnected: {request.sid}")
    
    @socketio.on('join_conversation')
    def handle_join_conversation(data):
        conversation_id = data.get('conversation_id')
        if conversation_id:
            from flask_socketio import join_room
            join_room(conversation_id)
            logger.info(f"Client {request.sid} joined conversation {conversation_id}")
    
    return app, socketio

# Crear la aplicación
app, socketio = create_app()

if __name__ == '__main__':
    # Crear directorio de uploads si no existe
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Inicializar configuración del sistema
    with app.app_context():
        config_service = ConfigService()
        config_service.initialize_default_config()
    
    logger.info("Starting MANUS-like Backend Server...")
    logger.info(f"Supabase URL: {app.config['SUPABASE_URL']}")
    logger.info(f"Ollama URL: {app.config['OLLAMA_BASE_URL']}")
    logger.info(f"Upload folder: {app.config['UPLOAD_FOLDER']}")
    
    # Ejecutar con SocketIO
    socketio.run(app, host='0.0.0.0', port=5000, debug=app.config['DEBUG'])

