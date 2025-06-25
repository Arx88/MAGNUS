"""
Rutas de autenticación para el sistema MANUS-like
Maneja registro, login, logout y gestión de usuarios con Supabase Auth
"""

from flask import Blueprint, request, jsonify, current_app
from functools import wraps
import logging
import jwt
from datetime import datetime, timedelta
import uuid

from src.models.database import db, UserModel

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)

def token_required(f):
    """Decorador para rutas que requieren autenticación"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Buscar token en headers
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]  # Bearer <token>
            except IndexError:
                return jsonify({'error': 'Invalid token format'}), 401
        
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
        
        try:
            # Verificar token con Supabase
            supabase = db.get_client()
            user_response = supabase.auth.get_user(token)
            
            if not user_response.user:
                return jsonify({'error': 'Invalid token'}), 401
            
            # Obtener información adicional del usuario desde nuestra base de datos
            user_model = UserModel()
            user_data = user_model.get_by_email(user_response.user.email)
            
            if not user_data:
                return jsonify({'error': 'User not found in system'}), 401
            
            # Agregar información del usuario al contexto de la request
            request.current_user = user_data
            
        except Exception as e:
            logger.error(f"Token verification failed: {str(e)}")
            return jsonify({'error': 'Token verification failed'}), 401
        
        return f(*args, **kwargs)
    
    return decorated

def admin_required(f):
    """Decorador para rutas que requieren permisos de administrador"""
    @wraps(f)
    @token_required
    def decorated(*args, **kwargs):
        if request.current_user.get('role') != 'admin':
            return jsonify({'error': 'Admin privileges required'}), 403
        return f(*args, **kwargs)
    
    return decorated

@auth_bp.route('/register', methods=['POST'])
def register():
    """Registrar un nuevo usuario"""
    try:
        data = request.get_json()
        
        # Validar datos requeridos
        required_fields = ['email', 'password', 'username', 'full_name']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        email = data['email']
        password = data['password']
        username = data['username']
        full_name = data['full_name']
        
        # Validar formato de email
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            return jsonify({'error': 'Invalid email format'}), 400
        
        # Validar longitud de contraseña
        if len(password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters long'}), 400
        
        # Verificar si el usuario ya existe
        user_model = UserModel()
        existing_user = user_model.get_by_email(email)
        if existing_user:
            return jsonify({'error': 'User with this email already exists'}), 409
        
        existing_username = user_model.get_by_username(username)
        if existing_username:
            return jsonify({'error': 'Username already taken'}), 409
        
        # Registrar usuario en Supabase Auth
        supabase = db.get_client()
        auth_response = supabase.auth.sign_up({
            "email": email,
            "password": password
        })
        
        if not auth_response.user:
            return jsonify({'error': 'Failed to create user account'}), 500
        
        # Crear registro en nuestra tabla de usuarios
        user_data = {
            'id': auth_response.user.id,
            'email': email,
            'username': username,
            'full_name': full_name,
            'role': 'user',
            'is_active': True,
            'preferences': {}
        }
        
        created_user = user_model.create(user_data)
        
        # Remover información sensible
        created_user.pop('id', None)
        
        return jsonify({
            'message': 'User registered successfully',
            'user': {
                'email': created_user['email'],
                'username': created_user['username'],
                'full_name': created_user['full_name'],
                'role': created_user['role']
            },
            'session': {
                'access_token': auth_response.session.access_token if auth_response.session else None,
                'refresh_token': auth_response.session.refresh_token if auth_response.session else None
            }
        }), 201
        
    except Exception as e:
        logger.error(f"Registration failed: {str(e)}")
        return jsonify({'error': 'Registration failed'}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """Iniciar sesión"""
    try:
        data = request.get_json()
        
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400
        
        # Autenticar con Supabase
        supabase = db.get_client()
        auth_response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        
        if not auth_response.user or not auth_response.session:
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Obtener información adicional del usuario
        user_model = UserModel()
        user_data = user_model.get_by_email(email)
        
        if not user_data:
            return jsonify({'error': 'User not found in system'}), 404
        
        if not user_data.get('is_active', True):
            return jsonify({'error': 'Account is deactivated'}), 403
        
        return jsonify({
            'message': 'Login successful',
            'user': {
                'id': user_data['id'],
                'email': user_data['email'],
                'username': user_data['username'],
                'full_name': user_data['full_name'],
                'role': user_data['role'],
                'avatar_url': user_data.get('avatar_url'),
                'preferences': user_data.get('preferences', {})
            },
            'session': {
                'access_token': auth_response.session.access_token,
                'refresh_token': auth_response.session.refresh_token,
                'expires_at': auth_response.session.expires_at
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Login failed: {str(e)}")
        return jsonify({'error': 'Login failed'}), 500

@auth_bp.route('/logout', methods=['POST'])
@token_required
def logout():
    """Cerrar sesión"""
    try:
        # Obtener token del header
        auth_header = request.headers.get('Authorization', '')
        token = auth_header.split(" ")[1] if " " in auth_header else None
        
        if token:
            # Cerrar sesión en Supabase
            supabase = db.get_client()
            supabase.auth.sign_out()
        
        return jsonify({'message': 'Logout successful'}), 200
        
    except Exception as e:
        logger.error(f"Logout failed: {str(e)}")
        return jsonify({'error': 'Logout failed'}), 500

@auth_bp.route('/refresh', methods=['POST'])
def refresh_token():
    """Renovar token de acceso"""
    try:
        data = request.get_json()
        refresh_token = data.get('refresh_token')
        
        if not refresh_token:
            return jsonify({'error': 'Refresh token is required'}), 400
        
        # Renovar token con Supabase
        supabase = db.get_client()
        auth_response = supabase.auth.refresh_session(refresh_token)
        
        if not auth_response.session:
            return jsonify({'error': 'Invalid refresh token'}), 401
        
        return jsonify({
            'session': {
                'access_token': auth_response.session.access_token,
                'refresh_token': auth_response.session.refresh_token,
                'expires_at': auth_response.session.expires_at
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Token refresh failed: {str(e)}")
        return jsonify({'error': 'Token refresh failed'}), 500

@auth_bp.route('/profile', methods=['GET'])
@token_required
def get_profile():
    """Obtener perfil del usuario actual"""
    try:
        user = request.current_user
        
        return jsonify({
            'user': {
                'id': user['id'],
                'email': user['email'],
                'username': user['username'],
                'full_name': user['full_name'],
                'role': user['role'],
                'avatar_url': user.get('avatar_url'),
                'preferences': user.get('preferences', {}),
                'is_active': user.get('is_active', True),
                'created_at': user.get('created_at'),
                'updated_at': user.get('updated_at')
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Get profile failed: {str(e)}")
        return jsonify({'error': 'Failed to get profile'}), 500

@auth_bp.route('/profile', methods=['PUT'])
@token_required
def update_profile():
    """Actualizar perfil del usuario"""
    try:
        data = request.get_json()
        user = request.current_user
        
        # Campos que se pueden actualizar
        updatable_fields = ['username', 'full_name', 'avatar_url', 'preferences']
        update_data = {}
        
        for field in updatable_fields:
            if field in data:
                update_data[field] = data[field]
        
        if not update_data:
            return jsonify({'error': 'No valid fields to update'}), 400
        
        # Verificar username único si se está actualizando
        if 'username' in update_data:
            user_model = UserModel()
            existing_user = user_model.get_by_username(update_data['username'])
            if existing_user and existing_user['id'] != user['id']:
                return jsonify({'error': 'Username already taken'}), 409
        
        # Actualizar usuario
        user_model = UserModel()
        updated_user = user_model.update(user['id'], update_data)
        
        return jsonify({
            'message': 'Profile updated successfully',
            'user': {
                'id': updated_user['id'],
                'email': updated_user['email'],
                'username': updated_user['username'],
                'full_name': updated_user['full_name'],
                'role': updated_user['role'],
                'avatar_url': updated_user.get('avatar_url'),
                'preferences': updated_user.get('preferences', {}),
                'updated_at': updated_user.get('updated_at')
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Update profile failed: {str(e)}")
        return jsonify({'error': 'Failed to update profile'}), 500

@auth_bp.route('/change-password', methods=['POST'])
@token_required
def change_password():
    """Cambiar contraseña del usuario"""
    try:
        data = request.get_json()
        
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        
        if not current_password or not new_password:
            return jsonify({'error': 'Current password and new password are required'}), 400
        
        if len(new_password) < 6:
            return jsonify({'error': 'New password must be at least 6 characters long'}), 400
        
        # Cambiar contraseña en Supabase
        supabase = db.get_client()
        
        # Primero verificar la contraseña actual
        auth_response = supabase.auth.sign_in_with_password({
            "email": request.current_user['email'],
            "password": current_password
        })
        
        if not auth_response.user:
            return jsonify({'error': 'Current password is incorrect'}), 400
        
        # Actualizar contraseña
        update_response = supabase.auth.update_user({
            "password": new_password
        })
        
        if not update_response.user:
            return jsonify({'error': 'Failed to update password'}), 500
        
        return jsonify({'message': 'Password changed successfully'}), 200
        
    except Exception as e:
        logger.error(f"Change password failed: {str(e)}")
        return jsonify({'error': 'Failed to change password'}), 500

@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    """Solicitar reset de contraseña"""
    try:
        data = request.get_json()
        email = data.get('email')
        
        if not email:
            return jsonify({'error': 'Email is required'}), 400
        
        # Enviar email de reset con Supabase
        supabase = db.get_client()
        supabase.auth.reset_password_email(email)
        
        return jsonify({'message': 'Password reset email sent'}), 200
        
    except Exception as e:
        logger.error(f"Password reset failed: {str(e)}")
        return jsonify({'error': 'Failed to send reset email'}), 500

@auth_bp.route('/verify-token', methods=['POST'])
def verify_token():
    """Verificar si un token es válido"""
    try:
        data = request.get_json()
        token = data.get('token')
        
        if not token:
            return jsonify({'error': 'Token is required'}), 400
        
        # Verificar token con Supabase
        supabase = db.get_client()
        user_response = supabase.auth.get_user(token)
        
        if not user_response.user:
            return jsonify({'valid': False}), 200
        
        # Obtener información del usuario
        user_model = UserModel()
        user_data = user_model.get_by_email(user_response.user.email)
        
        if not user_data or not user_data.get('is_active', True):
            return jsonify({'valid': False}), 200
        
        return jsonify({
            'valid': True,
            'user': {
                'id': user_data['id'],
                'email': user_data['email'],
                'username': user_data['username'],
                'full_name': user_data['full_name'],
                'role': user_data['role']
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Token verification failed: {str(e)}")
        return jsonify({'valid': False}), 200

