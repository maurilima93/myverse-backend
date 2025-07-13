import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from src.models.database import db

def configure_app(app):
    """Configurações básicas da aplicação"""
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'dev-jwt-secret')
    
    # Configuração do banco de dados (mantenha sua configuração atual)
    database_url = os.getenv('DATABASE_URL')
    if database_url and database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    else:
        app.config['SQLALCHEMY_DATABASE_URI'] = (
            f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
            f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT', '5432')}"
            f"/{os.getenv('DB_NAME')}?sslmode=require"
        )
    
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

def initialize_extensions(app):
    """Inicializa todas as extensões"""
    db.init_app(app)
    JWTManager(app)
    CORS(app, resources={
        r"/api/*": {
            "origins": [
                'https://myverse.com.br',
                'https://www.myverse.com.br',
                'http://localhost:3000'
            ],
            "supports_credentials": True,
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
        }
    })

def register_blueprints(app):
    """Registra todos os blueprints"""
    from src.routes.auth import auth_bp
    from src.routes.content import content_bp
    from src.routes.user import user_bp
    from src.routes.forum import forum_bp
    from src.routes.news import news_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(content_bp, url_prefix='/api/content')
    app.register_blueprint(user_bp, url_prefix='/api/user')
    app.register_blueprint(forum_bp, url_prefix='/api/forum')
    app.register_blueprint(news_bp, url_prefix='/api/news')

def create_app():
    """Factory principal da aplicação"""
    app = Flask(__name__)
    
    configure_app(app)
    initialize_extensions(app)
    
    # Configuração do before_request
    @app.before_request
    def handle_options():
        if request.method == 'OPTIONS':
            response = jsonify({'status': 'preflight'})
            response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
            return response
    
    register_blueprints(app)
    
    # Rotas básicas
    @app.route('/health')
    def health_check():
        return jsonify({'status': 'healthy'})
    
    @app.route('/')
    def index():
        return jsonify({'message': 'MyVerse API'})
    
    # Criar tabelas
    with app.app_context():
        db.create_all()
    
    return app

# Para produção com Gunicorn
app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)))