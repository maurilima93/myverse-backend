import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from datetime import datetime, timedelta
import psycopg2
from psycopg2.extras import RealDictCursor
import requests
from functools import wraps
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configurações
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'dev-jwt-secret')

# CORS configurado para permitir todas as origens
CORS(app, origins=['*'], supports_credentials=True)

# Configurações do banco de dados
DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'localhost'),
    'port': os.environ.get('DB_PORT', '5432'),
    'database': os.environ.get('DB_NAME', 'myverse'),
    'user': os.environ.get('DB_USER', 'postgres'),
    'password': os.environ.get('DB_PASSWORD', 'password'),
    'sslmode': 'require'
}

# APIs externas
TMDB_API_KEY = os.environ.get('TMDB_API_KEY')
IGDB_CLIENT_ID = os.environ.get('IGDB_CLIENT_ID')
IGDB_ACCESS_TOKEN = os.environ.get('IGDB_ACCESS_TOKEN')

def get_db_connection():
    """Criar conexão com o banco de dados"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        logger.error(f"Erro ao conectar com o banco: {e}")
        return None

def init_database():
    """Inicializar tabelas do banco de dados"""
    try:
        conn = get_db_connection()
        if not conn:
            return False
            
        cursor = conn.cursor()
        
        # Criar tabelas
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS favorites (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                content_id VARCHAR(50) NOT NULL,
                content_type VARCHAR(20) NOT NULL,
                title VARCHAR(255) NOT NULL,
                poster_url TEXT,
                rating FLOAT,
                genres TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, content_id, content_type)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS forum_posts (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                title VARCHAR(255) NOT NULL,
                content TEXT NOT NULL,
                category VARCHAR(50) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS forum_replies (
                id SERIAL PRIMARY KEY,
                post_id INTEGER REFERENCES forum_posts(id) ON DELETE CASCADE,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS friendships (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                friend_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                status VARCHAR(20) DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, friend_id)
            )
        ''')
        
        conn.commit()
        cursor.close()
        conn.close()
        logger.info("Banco de dados inicializado com sucesso")
        return True
        
    except Exception as e:
        logger.error(f"Erro ao inicializar banco: {e}")
        return False

def token_required(f):
    """Decorator para verificar token JWT"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({'error': 'Token não fornecido'}), 401
            
        try:
            if token.startswith('Bearer '):
                token = token[7:]
            data = jwt.decode(token, app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
            current_user_id = data['user_id']
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token expirado'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Token inválido'}), 401
            
        return f(current_user_id, *args, **kwargs)
    return decorated

# Rotas de Health Check
@app.route('/health', methods=['GET'])
def health_check():
    """Verificar saúde da aplicação"""
    try:
        conn = get_db_connection()
        if conn:
            conn.close()
            return jsonify({
                'status': 'healthy',
                'database': 'connected',
                'timestamp': datetime.utcnow().isoformat()
            })
        else:
            return jsonify({
                'status': 'unhealthy',
                'database': 'disconnected',
                'timestamp': datetime.utcnow().isoformat()
            }), 500
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500

# Rotas de Autenticação
@app.route('/auth/register', methods=['POST'])
def register():
    """Registrar novo usuário"""
    try:
        data = request.get_json()
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        
        if not all([username, email, password]):
            return jsonify({'error': 'Todos os campos são obrigatórios'}), 400
            
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Erro de conexão com banco'}), 500
            
        cursor = conn.cursor()
        
        # Verificar se usuário já existe
        cursor.execute('SELECT id FROM users WHERE username = %s OR email = %s', (username, email))
        if cursor.fetchone():
            return jsonify({'error': 'Usuário ou email já existe'}), 400
            
        # Criar usuário
        password_hash = generate_password_hash(password)
        cursor.execute(
            'INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s) RETURNING id',
            (username, email, password_hash)
        )
        user_id = cursor.fetchone()[0]
        
        conn.commit()
        cursor.close()
        conn.close()
        
        # Gerar token
        token = jwt.encode({
            'user_id': user_id,
            'exp': datetime.utcnow() + timedelta(days=30)
        }, app.config['JWT_SECRET_KEY'], algorithm='HS256')
        
        return jsonify({
            'message': 'Usuário criado com sucesso',
            'token': token,
            'user': {'id': user_id, 'username': username, 'email': email}
        })
        
    except Exception as e:
        logger.error(f"Erro no registro: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@app.route('/auth/login', methods=['POST'])
def login():
    """Fazer login"""
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        if not all([email, password]):
            return jsonify({'error': 'Email e senha são obrigatórios'}), 400
            
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Erro de conexão com banco'}), 500
            
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
        user = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if not user or not check_password_hash(user['password_hash'], password):
            return jsonify({'error': 'Credenciais inválidas'}), 401
            
        # Gerar token
        token = jwt.encode({
            'user_id': user['id'],
            'exp': datetime.utcnow() + timedelta(days=30)
        }, app.config['JWT_SECRET_KEY'], algorithm='HS256')
        
        return jsonify({
            'message': 'Login realizado com sucesso',
            'token': token,
            'user': {
                'id': user['id'],
                'username': user['username'],
                'email': user['email']
            }
        })
        
    except Exception as e:
        logger.error(f"Erro no login: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

# Rotas de Conteúdo
@app.route('/content/search', methods=['GET'])
@token_required
def search_content(current_user_id):
    """Buscar filmes, séries e jogos"""
    try:
        query = request.args.get('q', '')
        if not query:
            return jsonify({'error': 'Parâmetro de busca obrigatório'}), 400
            
        results = []
        
        # Buscar filmes no TMDb
        if TMDB_API_KEY:
            try:
                response = requests.get(
                    f'https://api.themoviedb.org/3/search/movie',
                    params={'api_key': TMDB_API_KEY, 'query': query}
                )
                if response.status_code == 200:
                    movies = response.json().get('results', [])
                    for movie in movies[:10]:
                        results.append({
                            'id': f"movie_{movie['id']}",
                            'title': movie['title'],
                            'type': 'movie',
                            'poster_url': f"https://image.tmdb.org/t/p/w500{movie['poster_path']}" if movie.get('poster_path') else None,
                            'rating': movie.get('vote_average'),
                            'year': movie.get('release_date', '')[:4] if movie.get('release_date') else '',
                            'overview': movie.get('overview', ''),
                            'genres': []
                        })
            except Exception as e:
                logger.error(f"Erro ao buscar filmes: {e}")
        
        # Buscar séries no TMDb
        if TMDB_API_KEY:
            try:
                response = requests.get(
                    f'https://api.themoviedb.org/3/search/tv',
                    params={'api_key': TMDB_API_KEY, 'query': query}
                )
                if response.status_code == 200:
                    shows = response.json().get('results', [])
                    for show in shows[:10]:
                        results.append({
                            'id': f"tv_{show['id']}",
                            'title': show['name'],
                            'type': 'tv',
                            'poster_url': f"https://image.tmdb.org/t/p/w500{show['poster_path']}" if show.get('poster_path') else None,
                            'rating': show.get('vote_average'),
                            'year': show.get('first_air_date', '')[:4] if show.get('first_air_date') else '',
                            'overview': show.get('overview', ''),
                            'genres': []
                        })
            except Exception as e:
                logger.error(f"Erro ao buscar séries: {e}")
        
        # Buscar jogos no IGDB
        if IGDB_CLIENT_ID and IGDB_ACCESS_TOKEN:
            try:
                headers = {
                    'Client-ID': IGDB_CLIENT_ID,
                    'Authorization': f'Bearer {IGDB_ACCESS_TOKEN}'
                }
                data = f'search "{query}"; fields name,cover.url,rating,first_release_date,summary; limit 10;'
                
                response = requests.post(
                    'https://api.igdb.com/v4/games',
                    headers=headers,
                    data=data
                )
                if response.status_code == 200:
                    games = response.json()
                    for game in games:
                        cover_url = None
                        if game.get('cover') and game['cover'].get('url'):
                            cover_url = f"https:{game['cover']['url'].replace('t_thumb', 't_cover_big')}"
                            
                        results.append({
                            'id': f"game_{game['id']}",
                            'title': game['name'],
                            'type': 'game',
                            'poster_url': cover_url,
                            'rating': game.get('rating', 0) / 10 if game.get('rating') else None,
                            'year': str(datetime.fromtimestamp(game['first_release_date']).year) if game.get('first_release_date') else '',
                            'overview': game.get('summary', ''),
                            'genres': []
                        })
            except Exception as e:
                logger.error(f"Erro ao buscar jogos: {e}")
        
        # Se não há APIs configuradas, retornar dados mock
        if not results:
            results = [
                {
                    'id': 'movie_1',
                    'title': f'Filme sobre {query}',
                    'type': 'movie',
                    'poster_url': None,
                    'rating': 8.5,
                    'year': '2023',
                    'overview': f'Um filme incrível sobre {query}',
                    'genres': ['Ação', 'Drama']
                },
                {
                    'id': 'tv_1',
                    'title': f'Série {query}',
                    'type': 'tv',
                    'poster_url': None,
                    'rating': 9.0,
                    'year': '2023',
                    'overview': f'Uma série fantástica sobre {query}',
                    'genres': ['Drama', 'Thriller']
                },
                {
                    'id': 'game_1',
                    'title': f'Jogo {query}',
                    'type': 'game',
                    'poster_url': None,
                    'rating': 8.8,
                    'year': '2023',
                    'overview': f'Um jogo épico sobre {query}',
                    'genres': ['Ação', 'Aventura']
                }
            ]
        
        return jsonify({'results': results})
        
    except Exception as e:
        logger.error(f"Erro na busca: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

# Rotas de Favoritos
@app.route('/content/favorites', methods=['POST'])
@token_required
def add_favorite(current_user_id):
    """Adicionar aos favoritos"""
    try:
        data = request.get_json()
        content_id = data.get('content_id')
        content_type = data.get('content_type')
        title = data.get('title')
        poster_url = data.get('poster_url')
        rating = data.get('rating')
        genres = data.get('genres', [])
        
        if not all([content_id, content_type, title]):
            return jsonify({'error': 'Dados obrigatórios faltando'}), 400
            
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Erro de conexão com banco'}), 500
            
        cursor = conn.cursor()
        
        # Verificar se já está nos favoritos
        cursor.execute(
            'SELECT id FROM favorites WHERE user_id = %s AND content_id = %s AND content_type = %s',
            (current_user_id, content_id, content_type)
        )
        if cursor.fetchone():
            return jsonify({'error': 'Item já está nos favoritos'}), 400
            
        # Adicionar aos favoritos
        cursor.execute('''
            INSERT INTO favorites (user_id, content_id, content_type, title, poster_url, rating, genres)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        ''', (current_user_id, content_id, content_type, title, poster_url, rating, ','.join(genres)))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'message': 'Adicionado aos favoritos com sucesso'})
        
    except Exception as e:
        logger.error(f"Erro ao adicionar favorito: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@app.route('/content/favorites', methods=['GET'])
@token_required
def get_favorites(current_user_id):
    """Listar favoritos do usuário"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Erro de conexão com banco'}), 500
            
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute('''
            SELECT * FROM favorites 
            WHERE user_id = %s 
            ORDER BY created_at DESC
        ''', (current_user_id,))
        
        favorites = cursor.fetchall()
        cursor.close()
        conn.close()
        
        # Converter para formato JSON
        result = []
        for fav in favorites:
            result.append({
                'id': fav['id'],
                'content_id': fav['content_id'],
                'content_type': fav['content_type'],
                'title': fav['title'],
                'poster_url': fav['poster_url'],
                'rating': fav['rating'],
                'genres': fav['genres'].split(',') if fav['genres'] else [],
                'created_at': fav['created_at'].isoformat()
            })
        
        return jsonify({'favorites': result})
        
    except Exception as e:
        logger.error(f"Erro ao buscar favoritos: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@app.route('/content/favorites/check', methods=['POST'])
@token_required
def check_favorite(current_user_id):
    """Verificar se item está nos favoritos"""
    try:
        data = request.get_json()
        content_id = data.get('content_id')
        content_type = data.get('content_type')
        
        if not all([content_id, content_type]):
            return jsonify({'error': 'content_id e content_type são obrigatórios'}), 400
            
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Erro de conexão com banco'}), 500
            
        cursor = conn.cursor()
        cursor.execute(
            'SELECT id FROM favorites WHERE user_id = %s AND content_id = %s AND content_type = %s',
            (current_user_id, content_id, content_type)
        )
        
        is_favorite = cursor.fetchone() is not None
        cursor.close()
        conn.close()
        
        return jsonify({'is_favorite': is_favorite})
        
    except Exception as e:
        logger.error(f"Erro ao verificar favorito: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

# Rotas de Fórum
@app.route('/forum/posts', methods=['POST'])
@token_required
def create_post(current_user_id):
    """Criar post no fórum"""
    try:
        data = request.get_json()
        title = data.get('title')
        content = data.get('content')
        category = data.get('category')
        
        if not all([title, content, category]):
            return jsonify({'error': 'Título, conteúdo e categoria são obrigatórios'}), 400
            
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Erro de conexão com banco'}), 500
            
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO forum_posts (user_id, title, content, category)
            VALUES (%s, %s, %s, %s) RETURNING id
        ''', (current_user_id, title, content, category))
        
        post_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            'message': 'Post criado com sucesso',
            'post_id': post_id
        })
        
    except Exception as e:
        logger.error(f"Erro ao criar post: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@app.route('/forum/posts', methods=['GET'])
@token_required
def get_posts(current_user_id):
    """Listar posts do fórum"""
    try:
        category = request.args.get('category')
        
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Erro de conexão com banco'}), 500
            
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        if category:
            cursor.execute('''
                SELECT p.*, u.username 
                FROM forum_posts p 
                JOIN users u ON p.user_id = u.id 
                WHERE p.category = %s 
                ORDER BY p.created_at DESC
            ''', (category,))
        else:
            cursor.execute('''
                SELECT p.*, u.username 
                FROM forum_posts p 
                JOIN users u ON p.user_id = u.id 
                ORDER BY p.created_at DESC
            ''')
        
        posts = cursor.fetchall()
        cursor.close()
        conn.close()
        
        # Converter para formato JSON
        result = []
        for post in posts:
            result.append({
                'id': post['id'],
                'title': post['title'],
                'content': post['content'],
                'category': post['category'],
                'username': post['username'],
                'user_id': post['user_id'],
                'created_at': post['created_at'].isoformat()
            })
        
        return jsonify({'posts': result})
        
    except Exception as e:
        logger.error(f"Erro ao buscar posts: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

# Inicializar banco de dados na inicialização
with app.app_context():
    init_database()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

