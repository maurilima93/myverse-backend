from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from src.models.database import db, User
import re

auth_bp = Blueprint('auth', __name__)

def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    # Pelo menos 8 caracteres, 1 maiúscula, 1 minúscula, 1 número
    if len(password) < 8:
        return False
    if not re.search(r'[A-Z]', password):
        return False
    if not re.search(r'[a-z]', password):
        return False
    if not re.search(r'\d', password):
        return False
    return True

@auth_bp.route('/api/auth/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        
        # Validar dados obrigatórios
        if not data or not all(k in data for k in ('username', 'email', 'password')):
            return jsonify({'error': 'Username, email e password são obrigatórios'}), 400
        
        username = data['username'].strip()
        email = data['email'].strip().lower()
        password = data['password']
        accept_terms = data.get('acceptTerms', False)
        
        # Validações
        if len(username) < 3:
            return jsonify({'error': 'Username deve ter pelo menos 3 caracteres'}), 400
        
        if not validate_email(email):
            return jsonify({'error': 'Email inválido'}), 400
        
        if not validate_password(password):
            return jsonify({'error': 'Password deve ter pelo menos 8 caracteres, incluindo maiúscula, minúscula e número'}), 400
        
        if not accept_terms:
            return jsonify({'error': 'Você deve aceitar os termos de uso'}), 400
        
        # Verificar se usuário já existe
        if User.query.filter_by(username=username).first():
            return jsonify({'error': 'Username já está em uso'}), 409
        
        if User.query.filter_by(email=email).first():
            return jsonify({'error': 'Email já está em uso'}), 409
        
        # Criar usuário
        user = User(username=username, email=email)
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        # Criar token de acesso
        access_token = create_access_token(identity=user.id)
        
        return jsonify({
            'message': 'Usuário criado com sucesso!',
            'access_token': access_token,
            'user': user.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro interno do servidor: {str(e)}'}), 500

@auth_bp.route('/api/auth/login', methods=['OPTIONS'])
def handle_login_options():
    response = jsonify()
    response.headers.add('Access-Control-Allow-Origin', 'https://myverse.com.br')
    response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    response.headers.add('Access-Control-Max-Age', '600')
    return response

@auth_bp.route('/api/auth/login', methods=['POST'])
def login():
    def login():
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Dados não fornecidos'}), 400
            
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        
        if not email or not password:
            return jsonify({'error': 'Email e senha são obrigatórios'}), 400

        # Verifique se o usuário existe
        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({'error': 'Credenciais inválidas'}), 401
            
        # Verifique a senha
        if not user.check_password(password):
            return jsonify({'error': 'Credenciais inválidas'}), 401
            
        # Crie o token JWT
        access_token = create_access_token(identity=user.id)

        return jsonify({
            'access_token': access_token,
            'user': {
                'id': user.id,
                'email': user.email,
                'username': user.username
            }
        }), 200

    except SQLAlchemyError as e:
        db.session.rollback()
        print(f"Erro de banco de dados no login: {str(e)}")
        return jsonify({
            'error': 'Erro de conexão com banco de dados'
        }), 500
    except Exception as e:
        print(f"Erro no login: {str(e)}")
        return jsonify({
            'error': 'Ocorreu um erro durante o login'
        }), 500

@auth_bp.route('/api/auth/me', methods=['GET'])
@jwt_required()
def get_current_user():
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'Usuário não encontrado'}), 404
        
        return jsonify({
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Erro interno do servidor: {str(e)}'}), 500

