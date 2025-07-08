# Adicione estas rotas ao seu arquivo auth.py no backend

from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from src.models.database import db, User
import re

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        
        # Validação dos dados
        if not data:
            return jsonify({'error': 'Dados não fornecidos'}), 400
            
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '')
        
        # Validações
        if not username or not email or not password:
            return jsonify({'error': 'Username, email e password são obrigatórios'}), 400
            
        # Validar username
        if len(username) < 3 or len(username) > 20:
            return jsonify({'error': 'Username deve ter entre 3 e 20 caracteres'}), 400
            
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            return jsonify({'error': 'Username pode conter apenas letras, números e underscore'}), 400
            
        # Validar email
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, email):
            return jsonify({'error': 'Email inválido'}), 400
            
        # Validar password
        if len(password) < 8:
            return jsonify({'error': 'Password deve ter pelo menos 8 caracteres'}), 400
            
        if not re.search(r'[A-Z]', password):
            return jsonify({'error': 'Password deve ter pelo menos uma letra maiúscula'}), 400
            
        if not re.search(r'[a-z]', password):
            return jsonify({'error': 'Password deve ter pelo menos uma letra minúscula'}), 400
            
        if not re.search(r'\d', password):
            return jsonify({'error': 'Password deve ter pelo menos um número'}), 400
        
        # Verificar se usuário já existe
        existing_user = User.query.filter(
            (User.username == username) | (User.email == email)
        ).first()
        
        if existing_user:
            if existing_user.username == username:
                return jsonify({'error': 'Username já está em uso'}), 409
            else:
                return jsonify({'error': 'Email já está em uso'}), 409
        
        # Criar novo usuário
        password_hash = generate_password_hash(password)
        
        new_user = User(
            username=username,
            email=email,
            password_hash=password_hash
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        # Criar token de acesso
        access_token = create_access_token(identity=new_user.id)
        
        return jsonify({
            'message': 'Usuário criado com sucesso',
            'user': {
                'id': new_user.id,
                'username': new_user.username,
                'email': new_user.email
            },
            'access_token': access_token
        }), 201
        
    except Exception as e:
        db.session.rollback()
        print(f"Erro no registro: {str(e)}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Dados não fornecidos'}), 400
            
        email = data.get('email', '').strip()
        password = data.get('password', '')
        
        if not email or not password:
            return jsonify({'error': 'Email e password são obrigatórios'}), 400
        
        # Buscar usuário
        user = User.query.filter_by(email=email).first()
        
        if not user or not check_password_hash(user.password_hash, password):
            return jsonify({'error': 'Email ou password incorretos'}), 401
        
        # Criar token de acesso
        access_token = create_access_token(identity=user.id)
        
        return jsonify({
            'message': 'Login realizado com sucesso',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email
            },
            'access_token': access_token
        }), 200
        
    except Exception as e:
        print(f"Erro no login: {str(e)}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'Usuário não encontrado'}), 404
        
        return jsonify({
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email
            }
        }), 200
        
    except Exception as e:
        print(f"Erro ao buscar usuário: {str(e)}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

