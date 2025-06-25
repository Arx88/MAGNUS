"""
Rutas para gestión de archivos en el sistema MANUS-like
Maneja subida, descarga, listado y gestión de archivos
"""

from flask import Blueprint, request, jsonify, send_file, current_app
import logging
import os
import uuid
import hashlib
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
import mimetypes

from src.models.database import db, BaseModel
from src.routes.auth import token_required

logger = logging.getLogger(__name__)

files_bp = Blueprint('files', __name__)

class FileModel(BaseModel):
    """Modelo para archivos"""
    
    def __init__(self):
        super().__init__("files")

def allowed_file(filename, allowed_extensions=None):
    """Verificar si el archivo tiene una extensión permitida"""
    if allowed_extensions is None:
        # Extensiones permitidas por defecto
        allowed_extensions = {
            'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx',
            'xls', 'xlsx', 'ppt', 'pptx', 'csv', 'json', 'xml', 'md',
            'py', 'js', 'html', 'css', 'zip', 'tar', 'gz', 'mp3', 'mp4',
            'avi', 'mov', 'wav', 'svg', 'webp', 'bmp', 'tiff'
        }
    
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

def get_file_hash(file_path):
    """Calcular hash SHA-256 de un archivo"""
    hash_sha256 = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    except Exception as e:
        logger.error(f"Error calculating file hash: {str(e)}")
        return None

@files_bp.route('/upload', methods=['POST'])
@token_required
def upload_file():
    """Subir un archivo"""
    try:
        user = request.current_user
        
        # Verificar si se envió un archivo
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Obtener parámetros adicionales
        conversation_id = request.form.get('conversation_id')
        task_id = request.form.get('task_id')
        is_temporary = request.form.get('is_temporary', 'false').lower() == 'true'
        expires_hours = int(request.form.get('expires_hours', 24))
        
        # Validar archivo
        if not allowed_file(file.filename):
            return jsonify({'error': 'File type not allowed'}), 400
        
        # Verificar tamaño del archivo
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        max_size = current_app.config.get('MAX_CONTENT_LENGTH', 104857600)  # 100MB por defecto
        if file_size > max_size:
            return jsonify({'error': f'File too large. Maximum size: {max_size} bytes'}), 413
        
        # Generar nombre único para el archivo
        original_filename = secure_filename(file.filename)
        file_extension = os.path.splitext(original_filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        
        # Crear directorio de subida si no existe
        upload_folder = current_app.config.get('UPLOAD_FOLDER', '/tmp/manus-uploads')
        os.makedirs(upload_folder, exist_ok=True)
        
        # Crear subdirectorio por fecha para organización
        date_folder = datetime.utcnow().strftime('%Y/%m/%d')
        full_upload_path = os.path.join(upload_folder, date_folder)
        os.makedirs(full_upload_path, exist_ok=True)
        
        # Ruta completa del archivo
        file_path = os.path.join(full_upload_path, unique_filename)
        
        # Guardar archivo
        file.save(file_path)
        
        # Calcular hash del archivo
        file_hash = get_file_hash(file_path)
        
        # Detectar tipo MIME
        mime_type, _ = mimetypes.guess_type(original_filename)
        if not mime_type:
            mime_type = 'application/octet-stream'
        
        # Calcular fecha de expiración si es temporal
        expires_at = None
        if is_temporary:
            expires_at = (datetime.utcnow() + timedelta(hours=expires_hours)).isoformat()
        
        # Guardar información en la base de datos
        file_data = {
            'conversation_id': conversation_id,
            'task_id': task_id,
            'filename': unique_filename,
            'original_filename': original_filename,
            'file_path': file_path,
            'file_size': file_size,
            'mime_type': mime_type,
            'file_hash': file_hash,
            'is_temporary': is_temporary,
            'expires_at': expires_at,
            'uploaded_by': user['id']
        }
        
        file_model = FileModel()
        created_file = file_model.create(file_data)
        
        return jsonify({
            'message': 'File uploaded successfully',
            'file': {
                'id': created_file['id'],
                'filename': created_file['filename'],
                'original_filename': created_file['original_filename'],
                'file_size': created_file['file_size'],
                'mime_type': created_file['mime_type'],
                'file_hash': created_file['file_hash'],
                'is_temporary': created_file['is_temporary'],
                'expires_at': created_file['expires_at'],
                'created_at': created_file['created_at']
            }
        }), 201
        
    except Exception as e:
        logger.error(f"File upload failed: {str(e)}")
        return jsonify({'error': 'Failed to upload file'}), 500

@files_bp.route('/', methods=['GET'])
@token_required
def get_files():
    """Obtener lista de archivos del usuario"""
    try:
        user = request.current_user
        conversation_id = request.args.get('conversation_id')
        task_id = request.args.get('task_id')
        include_temporary = request.args.get('include_temporary', 'true').lower() == 'true'
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 20, type=int)
        
        # Validar límites
        if limit > 100:
            limit = 100
        
        file_model = FileModel()
        
        # Construir filtros
        filters = {'uploaded_by': user['id']}
        
        if conversation_id:
            filters['conversation_id'] = conversation_id
        
        if task_id:
            filters['task_id'] = task_id
        
        if not include_temporary:
            filters['is_temporary'] = False
        
        # Obtener archivos
        offset = (page - 1) * limit
        files = file_model.get_all(filters, limit=limit, offset=offset)
        
        # Filtrar archivos expirados
        current_time = datetime.utcnow()
        valid_files = []
        
        for file_info in files:
            # Verificar si el archivo ha expirado
            if file_info.get('expires_at'):
                try:
                    expires_at = datetime.fromisoformat(file_info['expires_at'].replace('Z', '+00:00'))
                    if current_time > expires_at.replace(tzinfo=None):
                        # Archivo expirado, marcarlo para eliminación
                        continue
                except:
                    pass
            
            # Verificar si el archivo físico existe
            if os.path.exists(file_info['file_path']):
                valid_files.append(file_info)
            else:
                # Archivo físico no existe, eliminar registro de la base de datos
                try:
                    file_model.delete(file_info['id'])
                except:
                    pass
        
        return jsonify({
            'files': valid_files,
            'page': page,
            'limit': limit,
            'total_count': len(valid_files),
            'filters': filters
        }), 200
        
    except Exception as e:
        logger.error(f"Get files failed: {str(e)}")
        return jsonify({'error': 'Failed to get files'}), 500

@files_bp.route('/<file_id>', methods=['GET'])
@token_required
def get_file_info(file_id):
    """Obtener información de un archivo específico"""
    try:
        user = request.current_user
        
        file_model = FileModel()
        file_info = file_model.get_by_id(file_id)
        
        if not file_info:
            return jsonify({'error': 'File not found'}), 404
        
        # Verificar permisos
        if file_info['uploaded_by'] != user['id'] and user.get('role') != 'admin':
            return jsonify({'error': 'Access denied'}), 403
        
        # Verificar si el archivo ha expirado
        if file_info.get('expires_at'):
            try:
                expires_at = datetime.fromisoformat(file_info['expires_at'].replace('Z', '+00:00'))
                if datetime.utcnow() > expires_at.replace(tzinfo=None):
                    return jsonify({'error': 'File has expired'}), 410
            except:
                pass
        
        # Verificar si el archivo físico existe
        if not os.path.exists(file_info['file_path']):
            return jsonify({'error': 'File not found on disk'}), 404
        
        return jsonify({'file': file_info}), 200
        
    except Exception as e:
        logger.error(f"Get file info failed: {str(e)}")
        return jsonify({'error': 'Failed to get file info'}), 500

@files_bp.route('/<file_id>/download', methods=['GET'])
@token_required
def download_file(file_id):
    """Descargar un archivo"""
    try:
        user = request.current_user
        
        file_model = FileModel()
        file_info = file_model.get_by_id(file_id)
        
        if not file_info:
            return jsonify({'error': 'File not found'}), 404
        
        # Verificar permisos
        if file_info['uploaded_by'] != user['id'] and user.get('role') != 'admin':
            return jsonify({'error': 'Access denied'}), 403
        
        # Verificar si el archivo ha expirado
        if file_info.get('expires_at'):
            try:
                expires_at = datetime.fromisoformat(file_info['expires_at'].replace('Z', '+00:00'))
                if datetime.utcnow() > expires_at.replace(tzinfo=None):
                    return jsonify({'error': 'File has expired'}), 410
            except:
                pass
        
        # Verificar si el archivo físico existe
        if not os.path.exists(file_info['file_path']):
            return jsonify({'error': 'File not found on disk'}), 404
        
        # Enviar archivo
        return send_file(
            file_info['file_path'],
            as_attachment=True,
            download_name=file_info['original_filename'],
            mimetype=file_info['mime_type']
        )
        
    except Exception as e:
        logger.error(f"Download file failed: {str(e)}")
        return jsonify({'error': 'Failed to download file'}), 500

@files_bp.route('/<file_id>', methods=['DELETE'])
@token_required
def delete_file(file_id):
    """Eliminar un archivo"""
    try:
        user = request.current_user
        
        file_model = FileModel()
        file_info = file_model.get_by_id(file_id)
        
        if not file_info:
            return jsonify({'error': 'File not found'}), 404
        
        # Verificar permisos
        if file_info['uploaded_by'] != user['id'] and user.get('role') != 'admin':
            return jsonify({'error': 'Access denied'}), 403
        
        # Eliminar archivo físico
        try:
            if os.path.exists(file_info['file_path']):
                os.remove(file_info['file_path'])
        except Exception as fs_error:
            logger.warning(f"Could not delete physical file: {str(fs_error)}")
        
        # Eliminar registro de la base de datos
        file_model.delete(file_id)
        
        return jsonify({'message': 'File deleted successfully'}), 200
        
    except Exception as e:
        logger.error(f"Delete file failed: {str(e)}")
        return jsonify({'error': 'Failed to delete file'}), 500

@files_bp.route('/cleanup', methods=['POST'])
@token_required
def cleanup_expired_files():
    """Limpiar archivos expirados (solo para el usuario actual)"""
    try:
        user = request.current_user
        
        file_model = FileModel()
        
        # Obtener archivos temporales del usuario
        filters = {
            'uploaded_by': user['id'],
            'is_temporary': True
        }
        
        temp_files = file_model.get_all(filters)
        
        deleted_count = 0
        current_time = datetime.utcnow()
        
        for file_info in temp_files:
            if file_info.get('expires_at'):
                try:
                    expires_at = datetime.fromisoformat(file_info['expires_at'].replace('Z', '+00:00'))
                    if current_time > expires_at.replace(tzinfo=None):
                        # Archivo expirado, eliminarlo
                        try:
                            if os.path.exists(file_info['file_path']):
                                os.remove(file_info['file_path'])
                        except:
                            pass
                        
                        file_model.delete(file_info['id'])
                        deleted_count += 1
                except:
                    pass
        
        return jsonify({
            'message': 'Cleanup completed',
            'deleted_files': deleted_count
        }), 200
        
    except Exception as e:
        logger.error(f"Cleanup expired files failed: {str(e)}")
        return jsonify({'error': 'Failed to cleanup expired files'}), 500

@files_bp.route('/statistics', methods=['GET'])
@token_required
def get_file_statistics():
    """Obtener estadísticas de archivos del usuario"""
    try:
        user = request.current_user
        
        file_model = FileModel()
        
        # Obtener todos los archivos del usuario
        user_files = file_model.get_all({'uploaded_by': user['id']})
        
        # Calcular estadísticas
        stats = {
            'total_files': len(user_files),
            'total_size': 0,
            'temporary_files': 0,
            'permanent_files': 0,
            'by_mime_type': {},
            'by_date': {},
            'expired_files': 0
        }
        
        current_time = datetime.utcnow()
        
        for file_info in user_files:
            # Tamaño total
            stats['total_size'] += file_info.get('file_size', 0)
            
            # Archivos temporales vs permanentes
            if file_info.get('is_temporary', False):
                stats['temporary_files'] += 1
                
                # Verificar si ha expirado
                if file_info.get('expires_at'):
                    try:
                        expires_at = datetime.fromisoformat(file_info['expires_at'].replace('Z', '+00:00'))
                        if current_time > expires_at.replace(tzinfo=None):
                            stats['expired_files'] += 1
                    except:
                        pass
            else:
                stats['permanent_files'] += 1
            
            # Por tipo MIME
            mime_type = file_info.get('mime_type', 'unknown')
            if mime_type not in stats['by_mime_type']:
                stats['by_mime_type'][mime_type] = 0
            stats['by_mime_type'][mime_type] += 1
            
            # Por fecha
            try:
                created_date = file_info['created_at'][:10]  # YYYY-MM-DD
                if created_date not in stats['by_date']:
                    stats['by_date'][created_date] = 0
                stats['by_date'][created_date] += 1
            except:
                pass
        
        return jsonify({
            'statistics': stats,
            'user_id': user['id'],
            'generated_at': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Get file statistics failed: {str(e)}")
        return jsonify({'error': 'Failed to get file statistics'}), 500

@files_bp.route('/bulk-delete', methods=['POST'])
@token_required
def bulk_delete_files():
    """Eliminar múltiples archivos"""
    try:
        data = request.get_json()
        user = request.current_user
        
        file_ids = data.get('file_ids', [])
        
        if not file_ids:
            return jsonify({'error': 'No file IDs provided'}), 400
        
        if len(file_ids) > 50:
            return jsonify({'error': 'Cannot delete more than 50 files at once'}), 400
        
        file_model = FileModel()
        deleted_count = 0
        errors = []
        
        for file_id in file_ids:
            try:
                file_info = file_model.get_by_id(file_id)
                
                if not file_info:
                    errors.append(f"File {file_id} not found")
                    continue
                
                # Verificar permisos
                if file_info['uploaded_by'] != user['id'] and user.get('role') != 'admin':
                    errors.append(f"Access denied to file {file_id}")
                    continue
                
                # Eliminar archivo físico
                try:
                    if os.path.exists(file_info['file_path']):
                        os.remove(file_info['file_path'])
                except:
                    pass
                
                # Eliminar registro de la base de datos
                file_model.delete(file_id)
                deleted_count += 1
                
            except Exception as file_error:
                errors.append(f"Error deleting file {file_id}: {str(file_error)}")
        
        return jsonify({
            'message': f'Bulk delete completed',
            'deleted_files': deleted_count,
            'total_requested': len(file_ids),
            'errors': errors
        }), 200
        
    except Exception as e:
        logger.error(f"Bulk delete files failed: {str(e)}")
        return jsonify({'error': 'Failed to bulk delete files'}), 500

