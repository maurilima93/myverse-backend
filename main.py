import os
import sys
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import text
import requests

# Inicializar Flask app
app = Flask(__name__)

# Configurações
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-myverse-2024')
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-key-myverse-2024')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)

# Configuração do banco de dados AWS RDS
db_host = os.environ.get('DB_HOST', 'personal-feed.c3yc0my6ywu9.sa-east-1.rds.amazonaws.com')
db_port = os.environ.get('DB_PORT', '5432')
db_name = os.environ.get('DB_NAME', 'personal-feed')
db_user = os.environ.get('DB_USER', 'admin1')
db_password = os.environ.get('DB_PASSWORD', 'Ruffus11!')

app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}?sslmode=require'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_recycle': 300,
    'pool_timeout': 20,
    'pool_size': 5,
    'max_overflow': 10,
    'connect_args': {
        'sslmode': 'require',
        'connect_timeout': 30
    }
}

# Configurar CORS
CORS(app, 
     origins=[
         "https://myverse.com.br", 
         "https://www.myverse.com.br",
         "http://localhost:3000",
         "http://localhost:5173",
         "http://127.0.0.1:3000",
         "http://127.0.0.1:5173"
     ],
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
     allow_headers=["Content-Type", "Authorization", "Access-Control-Allow-Credentials"],
     supports_credentials=True,
     expose_headers=["Content-Type"],
     max_age=600
)

# Inicializar extensões
db = SQLAlchemy(app)
jwt = JWTManager(app)

# Modelos do banco de dados
class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    favorites = db.relationship('Favorite', backref='user', lazy=True, cascade='all, delete-orphan')
    posts = db.relationship('ForumPost', backref='author', lazy=True, cascade='all, delete-orphan')
    replies = db.relationship('ForumReply', backref='author', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Favorite(db.Model):
    __tablename__ = 'favorites'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content_id = db.Column(db.String(50), nullable=False)
    content_type = db.Column(db.String(20), nullable=False)  # 'movie', 'tv', 'game', 'book'
    title = db.Column(db.String(255), nullable=False)
    poster_url = db.Column(db.Text)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'content_id': self.content_id,
            'content_type': self.content_type,
            'title': self.title,
            'poster_url': self.poster_url,
            'added_at': self.added_at.isoformat() if self.added_at else None
        }

class ForumPost(db.Model):
    __tablename__ = 'forum_posts'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    replies = db.relationship('ForumReply', backref='post', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'category': self.category,
            'author': self.author.username if self.author else 'Unknown',
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'replies_count': len(self.replies)
        }

class ForumReply(db.Model):
    __tablename__ = 'forum_replies'
    
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('forum_posts.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'content': self.content,
            'author': self.author.username if self.author else 'Unknown',
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Friendship(db.Model):
    __tablename__ = 'friendships'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    friend_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # 'pending', 'accepted', 'rejected'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'friend_id': self.friend_id,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

# Rotas de autenticação
@app.route('/api/auth/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Dados não fornecidos'}), 400
        
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        
        if not username or not email or not password:
            return jsonify({'error': 'Username, email e password são obrigatórios'}), 400
        
        # Verificar se usuário já existe
        if User.query.filter_by(username=username).first():
            return jsonify({'error': 'Username já existe'}), 400
        
        if User.query.filter_by(email=email).first():
            return jsonify({'error': 'Email já está em uso'}), 400
        
        # Criar novo usuário
        user = User(username=username, email=email)
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        # Criar token JWT
        access_token = create_access_token(identity=user.id)
        
        return jsonify({
            'message': 'Usuário criado com sucesso',
            'user': user.to_dict(),
            'access_token': access_token
        }), 201
        
    except Exception as e:
        db.session.rollback()
        print(f"Erro no registro: {e}")
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Dados não fornecidos'}), 400
        
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'error': 'Username e password são obrigatórios'}), 400
        
        # Buscar usuário
        user = User.query.filter_by(username=username).first()
        
        if not user or not user.check_password(password):
            return jsonify({'error': 'Credenciais inválidas'}), 401
        
        # Criar token JWT
        access_token = create_access_token(identity=user.id)
        
        return jsonify({
            'message': 'Login realizado com sucesso',
            'user': user.to_dict(),
            'access_token': access_token
        }), 200
        
    except Exception as e:
        print(f"Erro no login: {e}")
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500

# Rotas de conteúdo
@app.route('/api/content/search', methods=['GET'])
def search_content():
    try:
        query = request.args.get('q', '')
        content_type = request.args.get('type', 'all')
        
        if not query:
            return jsonify({'error': 'Query de busca é obrigatória'}), 400
        
        # Dados mock para demonstração
        mock_results = [
            {
                'id': '1',
                'title': f'Resultado para "{query}"',
                'type': 'movie',
                'poster_url': 'https://via.placeholder.com/300x450',
                'overview': f'Descrição do resultado para {query}',
                'release_date': '2024-01-01'
            }
        ]
        
        return jsonify({
            'results': mock_results,
            'total_results': len(mock_results),
            'query': query,
            'type': content_type
        }), 200
        
    except Exception as e:
        print(f"Erro na busca: {e}")
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500

@app.route('/api/content/favorites', methods=['GET', 'POST'])
@jwt_required()
def favorites():
    try:
        user_id = get_jwt_identity()
        
        if request.method == 'GET':
            # Listar favoritos
            user_favorites = Favorite.query.filter_by(user_id=user_id).all()
            return jsonify({
                'favorites': [fav.to_dict() for fav in user_favorites]
            }), 200
        
        elif request.method == 'POST':
            # Adicionar favorito
            data = request.get_json()
            
            if not data:
                return jsonify({'error': 'Dados não fornecidos'}), 400
            
            content_id = data.get('content_id')
            content_type = data.get('content_type')
            title = data.get('title')
            poster_url = data.get('poster_url')
            
            if not content_id or not content_type or not title:
                return jsonify({'error': 'content_id, content_type e title são obrigatórios'}), 400
            
            # Verificar se já existe
            existing = Favorite.query.filter_by(
                user_id=user_id,
                content_id=content_id,
                content_type=content_type
            ).first()
            
            if existing:
                return jsonify({'error': 'Item já está nos favoritos'}), 400
            
            # Criar favorito
            favorite = Favorite(
                user_id=user_id,
                content_id=content_id,
                content_type=content_type,
                title=title,
                poster_url=poster_url
            )
            
            db.session.add(favorite)
            db.session.commit()
            
            return jsonify({
                'message': 'Favorito adicionado com sucesso',
                'favorite': favorite.to_dict()
            }), 201
            
    except Exception as e:
        db.session.rollback()
        print(f"Erro nos favoritos: {e}")
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500

# Rotas do fórum
@app.route('/api/forum/posts', methods=['GET', 'POST'])
@jwt_required()
def forum_posts():
    try:
        if request.method == 'GET':
            # Listar posts
            posts = ForumPost.query.order_by(ForumPost.created_at.desc()).all()
            return jsonify({
                'posts': [post.to_dict() for post in posts]
            }), 200
        
        elif request.method == 'POST':
            # Criar post
            user_id = get_jwt_identity()
            data = request.get_json()
            
            if not data:
                return jsonify({'error': 'Dados não fornecidos'}), 400
            
            title = data.get('title')
            content = data.get('content')
            category = data.get('category', 'geral')
            
            if not title or not content:
                return jsonify({'error': 'Título e conteúdo são obrigatórios'}), 400
            
            # Criar post
            post = ForumPost(
                title=title,
                content=content,
                category=category,
                user_id=user_id
            )
            
            db.session.add(post)
            db.session.commit()
            
            return jsonify({
                'message': 'Post criado com sucesso',
                'post': post.to_dict()
            }), 201
            
    except Exception as e:
        db.session.rollback()
        print(f"Erro no fórum: {e}")
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500

# Rota de health check
@app.route('/health')
def health_check():
    try:
        # Testar conexão com banco usando text() para SQLAlchemy 2.0+
        result = db.session.execute(text('SELECT 1'))
        result.fetchone()
        db.session.commit()
        
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'message': 'MyVerse Backend is running!',
            'version': '1.3.0-sqlalchemy-fixed'
        })
    except Exception as e:
        print(f"Health check error: {e}")
        return jsonify({
            'status': 'unhealthy',
            'database': 'disconnected',
            'error': str(e)
        }), 500

# Rota raiz
@app.route('/')
def index():
    return jsonify({
        'message': 'MyVerse API',
        'version': '1.3.0-sqlalchemy-fixed',
        'status': 'running',
        'endpoints': {
            'health': '/health',
            'auth': '/api/auth/*',
            'content': '/api/content/*',
            'forum': '/api/forum/*'
        },
        'cors': 'enabled',
        'frontend_url': 'https://myverse.com.br'
    })

# Rota de teste CORS
@app.route('/api/test-cors', methods=['GET', 'POST', 'OPTIONS'])
def test_cors():
    return jsonify({
        'message': 'CORS test successful',
        'method': request.method,
        'origin': request.headers.get('Origin', 'unknown'),
        'timestamp': datetime.utcnow().isoformat()
    })

# Criar tabelas
with app.app_context():
    try:
        db.create_all()
        print("✅ Tabelas criadas com sucesso!")
    except Exception as e:
        print(f"❌ Erro ao criar tabelas: {e}")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

