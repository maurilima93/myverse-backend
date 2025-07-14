import os
from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from datetime import timedelta

# Inicializar extensões
db = SQLAlchemy()
jwt = JWTManager()

def create_app():
    app = Flask(__name__)
    
    # Configurações
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
    app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-key')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)
    
    # Configuração do banco de dados
    db_host = os.environ.get('DB_HOST', 'personal-feed.c3yc0my6ywu9.sa-east-1.rds.amazonaws.com')
    db_port = os.environ.get('DB_PORT', '5432')
    db_name = os.environ.get('DB_NAME', 'postgres')
    db_user = os.environ.get('DB_USER', 'admin1')
    db_password = os.environ.get('DB_PASSWORD', 'EsNvDJNCydIdbKXcAZy5')
    
    app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}?sslmode=require'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'connect_args': {
            'sslmode': 'require',
            'connect_timeout': 10
        }
    }
    
    # Configurar CORS
    CORS(app,
     resources={
         r"/api/*": {
             "origins": ["https://myverse.com.br", "https://www.myverse.com.br"],
             "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
             "allow_headers": ["Content-Type", "Authorization"],
             "supports_credentials": True,
             "expose_headers": ["Content-Type"],
             "max_age": 600
         }
     })
    
    # Inicializar extensões
    db.init_app(app)
    jwt.init_app(app)
    
    # Importar modelos
    from src.models.database import User, UserPreference, Favorite, ForumPost, ForumReply
    
    # Registrar blueprints
    from src.routes.auth import auth_bp
    from src.routes.content import content_bp
    from src.routes.user import user_bp
    from src.routes.forum import forum_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(content_bp, url_prefix='/api/content')
    app.register_blueprint(user_bp, url_prefix='/api/user')
    app.register_blueprint(forum_bp, url_prefix='/api/forum')
    
    @app.route('/')
    def home():
        return jsonify({
            "status": "online",
            "message": "MyVerse API is running",
            "endpoints": {
                "auth": "/api/auth",
                "content": "/api/content",
                "forum": "/api/forum"
            }
        }), 200

    # Rota de health check
    @app.route('/health')
    def health_check():
        try:
            # Testar conexão com banco
            db.session.execute('SELECT 1')
            return jsonify({
                'status': 'healthy',
                'database': 'connected',
                'version': '1.0.0'
            })
        except Exception as e:
            return jsonify({
                'status': 'unhealthy',
                'database': 'disconnected',
                'error': str(e)
            }), 500
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({
            "error": "Endpoint not found",
            "message": "The requested URL was not found on the server",
            "status_code": 404
        }), 404
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
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

