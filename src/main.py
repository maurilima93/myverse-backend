import os
from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from src.models.database import db, init_db
from src.routes.auth import auth_bp
from src.routes.content import content_bp
from src.routes.user import user_bp
from src.routes.forum import forum_bp

def create_app():
    app = Flask(__name__)
    
    # Configurações
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-key-change-in-production')
    
    # Configuração do banco de dados AWS RDS
    # Construir URL de conexão com PostgreSQL da AWS
    db_host = os.environ.get('DB_HOST', 'personal-feed.c3yc0my6ywu9.sa-east-1.rds.amazonaws.com')
    db_port = os.environ.get('DB_PORT', '5432')
    db_name = os.environ.get('DB_NAME', 'personal-feed')
    db_user = os.environ.get('DB_USER', 'admin1')
    db_password = os.environ.get('DB_PASSWORD', 'Ruffus11!')
    
    # URL de conexão PostgreSQL para AWS RDS
    database_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Configurações específicas para AWS RDS
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'connect_args': {
            'sslmode': 'require',  # AWS RDS requer SSL
            'connect_timeout': 10
        }
    }
    
    # Inicializar extensões
    db.init_app(app)
    CORS(app, origins=['*'])
    jwt = JWTManager(app)
    
    # Registrar blueprints
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(content_bp, url_prefix='/api/content')
    app.register_blueprint(user_bp, url_prefix='/api/user')
    app.register_blueprint(forum_bp, url_prefix='/api/forum')
    
    # Rota de health check
    @app.route('/health')
    def health_check():
        try:
            # Testar conexão com banco de dados
            db.session.execute('SELECT 1')
            db_status = 'connected'
        except Exception as e:
            db_status = f'error: {str(e)}'
        
        return jsonify({
            'status': 'healthy',
            'message': 'MyVerse API is running',
            'database': db_status,
            'environment': os.environ.get('FLASK_ENV', 'development')
        })
    
    @app.route('/')
    def index():
        return jsonify({
            'message': 'MyVerse API',
            'version': '1.0.0',
            'status': 'running',
            'database': 'AWS RDS PostgreSQL'
        })
    
    # Inicializar banco de dados
    with app.app_context():
        try:
            init_db()
            print("✅ Banco de dados AWS RDS inicializado com sucesso!")
        except Exception as e:
            print(f"❌ Erro ao inicializar banco de dados: {e}")
    
    return app

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug)

