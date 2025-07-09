# Substitua seu arquivo main.py por este código completo

import os
from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from src.models.database import db, User, Favorite, ForumPost, ForumReply

def create_app():
    app = Flask(__name__)
    
    # Configurações
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'dev-jwt-secret')
    
    # Configuração do banco de dados
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        # Para Railway/Heroku que usam postgres://
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    else:
        # Configuração para AWS RDS
        db_host = os.getenv('DB_HOST', 'personal-feed.c3yc0my6ywu9.sa-east-1.rds.amazonaws.com')
        db_port = os.getenv('DB_PORT', '5432')
        db_name = os.getenv('DB_NAME', 'postgres')
        db_user = os.getenv('DB_USER', 'admin1')
        db_password = os.getenv('DB_PASSWORD', 'EsNvDJNCydIdbKXcAZy5')
        
        app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}?sslmode=require'
    
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'connect_args': {'sslmode': 'require'}
    }
    
    # Inicializar extensões
    db.init_app(app)
    jwt = JWTManager(app)
    
    # Configurar CORS
    CORS(app, origins=[
        'https://myverse.com.br',
        'https://www.myverse.com.br',
        'http://localhost:3000',
        'http://localhost:5173',
        'http://localhost:5000',
        'http://127.0.0.1:3000',
        'http://127.0.0.1:5173',
        'http://127.0.0.1:5000'
    ], supports_credentials=True)
    
    # Registrar blueprints
    from src.routes.auth import auth_bp
    from src.routes.content import content_bp
    from src.routes.user import user_bp
    from src.routes.forum import forum_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(content_bp, url_prefix='/api/content')
    app.register_blueprint(user_bp, url_prefix='/api/user')
    app.register_blueprint(forum_bp, url_prefix='/api/forum')
    
    # Rota de health check
    @app.route('/health')
    def health_check():
        try:
            # Testar conexão com banco
            db.session.execute(db.text('SELECT 1'))
            db_status = "connected"
        except Exception as e:
            db_status = f"error: {str(e)}"
        
        return jsonify({
            'status': 'healthy',
            'message': 'MyVerse API is running',
            'database': db_status,
            'environment': os.getenv('FLASK_ENV', 'development')
        })
    
    # Rota raiz
    @app.route('/')
    def index():
        return jsonify({
            'message': 'MyVerse API',
            'version': '1.0.0',
            'endpoints': {
                'health': '/health',
                'auth': '/api/auth',
                'content': '/api/content',
                'user': '/api/user',
                'forum': '/api/forum'
            }
        })
    
    # Criar tabelas
    with app.app_context():
        try:
            db.create_all()
            print("Tabelas criadas com sucesso!")
        except Exception as e:
            print(f"Erro ao criar tabelas: {e}")
    
    return app

# Para Railway
app = create_app()

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

