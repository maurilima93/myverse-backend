import os
from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from sqlalchemy import text
from datetime import timedelta

# Inicializar extensões
db = SQLAlchemy()
jwt = JWTManager()

def create_app():
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
    
    # Configurar CORS para permitir requisições do frontend
    CORS(app,
     resources={
         r"/api/*": {
             "origins": [
                 "https://myverse.com.br", 
                 "https://www.myverse.com.br",
                 "http://localhost:3000",  # Para desenvolvimento
                 "http://localhost:5173",  # Vite dev server
                 "http://127.0.0.1:3000",
                 "http://127.0.0.1:5173"
             ],
             "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
             "allow_headers": ["Content-Type", "Authorization", "Access-Control-Allow-Credentials"],
             "supports_credentials": True,
             "expose_headers": ["Content-Type"],
             "max_age": 600
         }
     })
    
    # Inicializar extensões
    db.init_app(app)
    jwt.init_app(app)
    
    # Importar modelos
    from src.models.database import User, Favorite, ForumPost, ForumReply, Friendship
    
    # Importar e registrar blueprints
    from src.routes.auth import auth_bp
    from src.routes.content import content_bp
    from src.routes.forum import forum_bp
    from src.routes.user import user_bp
    from src.routes.friends import friends_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(content_bp, url_prefix='/api/content')
    app.register_blueprint(forum_bp, url_prefix='/api/forum')
    app.register_blueprint(user_bp, url_prefix='/api/user')
    app.register_blueprint(friends_bp, url_prefix='/api/friends')
    
    # Rota de health check
    @app.route('/health')
    def health_check():
        try:
            # Testar conexão com banco usando text() para SQLAlchemy 2.0+
            result = db.session.execute(text('SELECT 1'))
            result.fetchone()  # Garantir que a query foi executada
            db.session.commit()  # Fechar a transação
            
            return jsonify({
                'status': 'healthy',
                'database': 'connected',
                'message': 'MyVerse Backend is running!',
                'version': '1.1.0'
            })
        except Exception as e:
            # Log do erro para debugging
            print(f"Health check error: {e}")
            
            return jsonify({
                'status': 'unhealthy',
                'database': 'disconnected',
                'error': str(e),
                'message': 'Database connection failed'
            }), 500
    
    # Rota raiz
    @app.route('/')
    def index():
        return jsonify({
            'message': 'MyVerse API',
            'version': '1.2.0-cors-fixed',
            'status': 'running',
            'endpoints': {
                'health': '/health',
                'auth': '/api/auth/*',
                'content': '/api/content/*',
                'forum': '/api/forum/*',
                'user': '/api/user/*',
                'friends': '/api/friends/*'
            },
            'cors': 'enabled',
            'frontend_url': 'https://myverse.com.br'
        })
    
    # Rota de teste de conexão adicional
    @app.route('/test-db')
    def test_db():
        try:
            # Teste mais detalhado da conexão
            result = db.session.execute(text('SELECT version()'))
            version = result.fetchone()[0]
            db.session.commit()
            
            return jsonify({
                'status': 'success',
                'database': 'connected',
                'postgres_version': version,
                'connection_info': {
                    'host': db_host,
                    'port': db_port,
                    'database': db_name,
                    'user': db_user
                }
            })
        except Exception as e:
            return jsonify({
                'status': 'error',
                'database': 'disconnected',
                'error': str(e),
                'connection_info': {
                    'host': db_host,
                    'port': db_port,
                    'database': db_name,
                    'user': db_user
                }
            }), 500
    
    # Criar tabelas
    with app.app_context():
        try:
            db.create_all()
            print("✅ Tabelas criadas com sucesso!")
        except Exception as e:
            print(f"❌ Erro ao criar tabelas: {e}")
    
    return app

# Criar aplicação
app = create_app()

if __name__ == '__main__':
    app = create_app()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)