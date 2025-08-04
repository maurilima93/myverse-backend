#!/usr/bin/env python3
"""
MyVerse Backend - Ultra Simples
Sem Procfile, sem gunicorn, só Python puro
"""

import os
import sys
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

# Criar app Flask
app = Flask(__name__)

# Configurações básicas
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'myverse-ultra-simples-2024')
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'jwt-ultra-simples-2024')

# CORS total
CORS(app, origins=['*'], supports_credentials=True, allow_headers=['*'], methods=['*'])

# Configuração do banco
DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'localhost'),
    'port': int(os.environ.get('DB_PORT', 5432)),
    'database': os.environ.get('DB_NAME', 'myverse'),
    'user': os.environ.get('DB_USER', 'postgres'),
    'password': os.environ.get('DB_PASSWORD', 'password'),
    'sslmode': 'require',
    'connect_timeout': 10
}

# APIs
TMDB_KEY = os.environ.get('TMDB_API_KEY')
IGDB_ID = os.environ.get('IGDB_CLIENT_ID')
IGDB_TOKEN = os.environ.get('IGDB_ACCESS_TOKEN')

def db_connect():
    """Conectar ao banco"""
    try:
        return psycopg2.connect(**DB_CONFIG)
    except Exception as e:
        logger.error(f"DB: {e}")
        return None

def init_tables():
    """Criar tabelas"""
    try:
        conn = db_connect()
        if not conn:
            logger.warning("DB indisponível")
            return False
            
        cur = conn.cursor()
        
        # Users
        cur.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Favorites
        cur.execute('''
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
        
        # Forum
        cur.execute('''
            CREATE TABLE IF NOT EXISTS forum_posts (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                title VARCHAR(255) NOT NULL,
                content TEXT NOT NULL,
                category VARCHAR(50) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        cur.close()
        conn.close()
        logger.info("Tabelas criadas")
        return True
        
    except Exception as e:
        logger.error(f"Init: {e}")
        return False

def require_auth(f):
    """Auth decorator"""
    @wraps(f)
    def wrapper(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'error': 'Token necessário'}), 401
            
        try:
            if token.startswith('Bearer '):
                token = token[7:]
            data = jwt.decode(token, app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
            user_id = data['user_id']
        except:
            return jsonify({'error': 'Token inválido'}), 401
            
        return f(user_id, *args, **kwargs)
    return wrapper

# ==================== ROTAS ====================

@app.route('/health')
def health():
    """Health check"""
    try:
        conn = db_connect()
        db_ok = 'connected' if conn else 'disconnected'
        if conn:
            conn.close()
            
        return jsonify({
            'status': 'healthy',
            'database': db_ok,
            'timestamp': datetime.utcnow().isoformat(),
            'version': 'ultra-simples-3.0',
            'method': 'python-direct'
        })
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/auth/register', methods=['POST'])
def register():
    """Registro"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        
        if not all([username, email, password]):
            return jsonify({'error': 'Campos obrigatórios'}), 400
            
        if len(password) < 6:
            return jsonify({'error': 'Senha mínimo 6 chars'}), 400
            
        conn = db_connect()
        if not conn:
            return jsonify({'error': 'DB indisponível'}), 500
            
        cur = conn.cursor()
        
        # Check existing
        cur.execute('SELECT id FROM users WHERE username = %s OR email = %s', (username, email))
        if cur.fetchone():
            cur.close()
            conn.close()
            return jsonify({'error': 'Usuário existe'}), 400
            
        # Create
        hash_pw = generate_password_hash(password)
        cur.execute(
            'INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s) RETURNING id',
            (username, email, hash_pw)
        )
        user_id = cur.fetchone()[0]
        
        conn.commit()
        cur.close()
        conn.close()
        
        # Token
        token = jwt.encode({
            'user_id': user_id,
            'exp': datetime.utcnow() + timedelta(days=30)
        }, app.config['JWT_SECRET_KEY'])
        
        return jsonify({
            'message': 'Usuário criado',
            'token': token,
            'user': {'id': user_id, 'username': username, 'email': email}
        })
        
    except Exception as e:
        logger.error(f"Register: {e}")
        return jsonify({'error': 'Erro interno'}), 500

@app.route('/auth/login', methods=['POST'])
def login():
    """Login"""
    try:
        data = request.get_json()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        
        if not all([email, password]):
            return jsonify({'error': 'Email e senha obrigatórios'}), 400
            
        conn = db_connect()
        if not conn:
            return jsonify({'error': 'DB indisponível'}), 500
            
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute('SELECT * FROM users WHERE email = %s', (email,))
        user = cur.fetchone()
        
        cur.close()
        conn.close()
        
        if not user or not check_password_hash(user['password_hash'], password):
            return jsonify({'error': 'Credenciais inválidas'}), 401
            
        token = jwt.encode({
            'user_id': user['id'],
            'exp': datetime.utcnow() + timedelta(days=30)
        }, app.config['JWT_SECRET_KEY'])
        
        return jsonify({
            'message': 'Login OK',
            'token': token,
            'user': {'id': user['id'], 'username': user['username'], 'email': user['email']}
        })
        
    except Exception as e:
        logger.error(f"Login: {e}")
        return jsonify({'error': 'Erro interno'}), 500

@app.route('/content/search')
@require_auth
def search(user_id):
    """Busca"""
    try:
        query = request.args.get('q', '').strip()
        if not query:
            return jsonify({'error': 'Query obrigatória'}), 400
            
        results = []
        
        # TMDb Movies
        if TMDB_KEY:
            try:
                r = requests.get(
                    'https://api.themoviedb.org/3/search/movie',
                    params={'api_key': TMDB_KEY, 'query': query, 'language': 'pt-BR'},
                    timeout=5
                )
                if r.status_code == 200:
                    for m in r.json().get('results', [])[:8]:
                        results.append({
                            'id': f"movie_{m['id']}",
                            'title': m['title'],
                            'type': 'movie',
                            'poster_url': f"https://image.tmdb.org/t/p/w500{m['poster_path']}" if m.get('poster_path') else None,
                            'rating': m.get('vote_average'),
                            'year': m.get('release_date', '')[:4] if m.get('release_date') else '',
                            'overview': m.get('overview', ''),
                            'genres': []
                        })
            except:
                pass
        
        # TMDb TV
        if TMDB_KEY:
            try:
                r = requests.get(
                    'https://api.themoviedb.org/3/search/tv',
                    params={'api_key': TMDB_KEY, 'query': query, 'language': 'pt-BR'},
                    timeout=5
                )
                if r.status_code == 200:
                    for s in r.json().get('results', [])[:8]:
                        results.append({
                            'id': f"tv_{s['id']}",
                            'title': s['name'],
                            'type': 'tv',
                            'poster_url': f"https://image.tmdb.org/t/p/w500{s['poster_path']}" if s.get('poster_path') else None,
                            'rating': s.get('vote_average'),
                            'year': s.get('first_air_date', '')[:4] if s.get('first_air_date') else '',
                            'overview': s.get('overview', ''),
                            'genres': []
                        })
            except:
                pass
        
        # IGDB Games
        if IGDB_ID and IGDB_TOKEN:
            try:
                headers = {'Client-ID': IGDB_ID, 'Authorization': f'Bearer {IGDB_TOKEN}'}
                data = f'search "{query}"; fields name,cover.url,rating,first_release_date,summary; limit 8;'
                
                r = requests.post('https://api.igdb.com/v4/games', headers=headers, data=data, timeout=5)
                if r.status_code == 200:
                    for g in r.json():
                        cover = None
                        if g.get('cover') and g['cover'].get('url'):
                            cover = f"https:{g['cover']['url'].replace('t_thumb', 't_cover_big')}"
                            
                        results.append({
                            'id': f"game_{g['id']}",
                            'title': g['name'],
                            'type': 'game',
                            'poster_url': cover,
                            'rating': g.get('rating', 0) / 10 if g.get('rating') else None,
                            'year': str(datetime.fromtimestamp(g['first_release_date']).year) if g.get('first_release_date') else '',
                            'overview': g.get('summary', ''),
                            'genres': []
                        })
            except:
                pass
        
        # Fallback
        if not results:
            results = [
                {
                    'id': f'movie_mock_{abs(hash(query)) % 1000}',
                    'title': f'Filme: {query}',
                    'type': 'movie',
                    'poster_url': None,
                    'rating': 8.5,
                    'year': '2024',
                    'overview': f'Um filme sobre {query}',
                    'genres': ['Ação']
                },
                {
                    'id': f'tv_mock_{abs(hash(query)) % 1000}',
                    'title': f'Série: {query}',
                    'type': 'tv',
                    'poster_url': None,
                    'rating': 9.0,
                    'year': '2024',
                    'overview': f'Uma série sobre {query}',
                    'genres': ['Drama']
                }
            ]
        
        return jsonify({'results': results})
        
    except Exception as e:
        logger.error(f"Search: {e}")
        return jsonify({'error': 'Erro na busca'}), 500

@app.route('/content/favorites', methods=['POST'])
@require_auth
def add_favorite(user_id):
    """Add favorito"""
    try:
        data = request.get_json()
        content_id = data.get('content_id')
        content_type = data.get('content_type')
        title = data.get('title')
        poster_url = data.get('poster_url')
        rating = data.get('rating')
        genres = data.get('genres', [])
        
        if not all([content_id, content_type, title]):
            return jsonify({'error': 'Dados faltando'}), 400
            
        conn = db_connect()
        if not conn:
            return jsonify({'error': 'DB indisponível'}), 500
            
        cur = conn.cursor()
        
        # Check
        cur.execute(
            'SELECT id FROM favorites WHERE user_id = %s AND content_id = %s AND content_type = %s',
            (user_id, content_id, content_type)
        )
        if cur.fetchone():
            cur.close()
            conn.close()
            return jsonify({'error': 'Já nos favoritos'}), 400
            
        # Insert
        cur.execute('''
            INSERT INTO favorites (user_id, content_id, content_type, title, poster_url, rating, genres)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        ''', (user_id, content_id, content_type, title, poster_url, rating, ','.join(genres) if genres else ''))
        
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({'message': 'Adicionado aos favoritos'})
        
    except Exception as e:
        logger.error(f"Add fav: {e}")
        return jsonify({'error': 'Erro interno'}), 500

@app.route('/content/favorites')
@require_auth
def get_favorites(user_id):
    """Get favoritos"""
    try:
        conn = db_connect()
        if not conn:
            return jsonify({'error': 'DB indisponível'}), 500
            
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute('SELECT * FROM favorites WHERE user_id = %s ORDER BY created_at DESC', (user_id,))
        
        favs = cur.fetchall()
        cur.close()
        conn.close()
        
        result = []
        for f in favs:
            result.append({
                'id': f['id'],
                'content_id': f['content_id'],
                'content_type': f['content_type'],
                'title': f['title'],
                'poster_url': f['poster_url'],
                'rating': f['rating'],
                'genres': f['genres'].split(',') if f['genres'] else [],
                'created_at': f['created_at'].isoformat()
            })
        
        return jsonify({'favorites': result})
        
    except Exception as e:
        logger.error(f"Get favs: {e}")
        return jsonify({'error': 'Erro interno'}), 500

@app.route('/content/favorites/check', methods=['POST'])
@require_auth
def check_favorite(user_id):
    """Check favorito"""
    try:
        data = request.get_json()
        content_id = data.get('content_id')
        content_type = data.get('content_type')
        
        if not all([content_id, content_type]):
            return jsonify({'error': 'Dados faltando'}), 400
            
        conn = db_connect()
        if not conn:
            return jsonify({'error': 'DB indisponível'}), 500
            
        cur = conn.cursor()
        cur.execute(
            'SELECT id FROM favorites WHERE user_id = %s AND content_id = %s AND content_type = %s',
            (user_id, content_id, content_type)
        )
        
        is_fav = cur.fetchone() is not None
        cur.close()
        conn.close()
        
        return jsonify({'is_favorite': is_fav})
        
    except Exception as e:
        logger.error(f"Check fav: {e}")
        return jsonify({'error': 'Erro interno'}), 500

@app.route('/forum/posts', methods=['POST'])
@require_auth
def create_post(user_id):
    """Create post"""
    try:
        data = request.get_json()
        title = data.get('title', '').strip()
        content = data.get('content', '').strip()
        category = data.get('category', '').strip()
        
        if not all([title, content, category]):
            return jsonify({'error': 'Dados obrigatórios'}), 400
            
        if len(title) < 5 or len(content) < 10:
            return jsonify({'error': 'Título min 5, conteúdo min 10'}), 400
            
        conn = db_connect()
        if not conn:
            return jsonify({'error': 'DB indisponível'}), 500
            
        cur = conn.cursor()
        cur.execute('''
            INSERT INTO forum_posts (user_id, title, content, category)
            VALUES (%s, %s, %s, %s) RETURNING id
        ''', (user_id, title, content, category))
        
        post_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({'message': 'Post criado', 'post_id': post_id})
        
    except Exception as e:
        logger.error(f"Create post: {e}")
        return jsonify({'error': 'Erro interno'}), 500

@app.route('/forum/posts')
@require_auth
def get_posts(user_id):
    """Get posts"""
    try:
        category = request.args.get('category')
        
        conn = db_connect()
        if not conn:
            return jsonify({'error': 'DB indisponível'}), 500
            
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        if category:
            cur.execute('''
                SELECT p.*, u.username 
                FROM forum_posts p 
                JOIN users u ON p.user_id = u.id 
                WHERE p.category = %s 
                ORDER BY p.created_at DESC LIMIT 50
            ''', (category,))
        else:
            cur.execute('''
                SELECT p.*, u.username 
                FROM forum_posts p 
                JOIN users u ON p.user_id = u.id 
                ORDER BY p.created_at DESC LIMIT 50
            ''')
        
        posts = cur.fetchall()
        cur.close()
        conn.close()
        
        result = []
        for p in posts:
            result.append({
                'id': p['id'],
                'title': p['title'],
                'content': p['content'],
                'category': p['category'],
                'username': p['username'],
                'user_id': p['user_id'],
                'created_at': p['created_at'].isoformat()
            })
        
        return jsonify({'posts': result})
        
    except Exception as e:
        logger.error(f"Get posts: {e}")
        return jsonify({'error': 'Erro interno'}), 500

# Inicializar
try:
    init_tables()
except Exception as e:
    logger.error(f"Init error: {e}")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') != 'production'
    
    print("🚀 MyVerse Backend Ultra Simples")
    print(f"📁 Arquivo: main.py")
    print(f"🌐 Porta: {port}")
    print(f"🔧 Debug: {debug}")
    print("⚡ Método: Python direto (sem gunicorn)")
    
    # Rodar Flask diretamente
    app.run(host='0.0.0.0', port=port, debug=debug, threaded=True)

