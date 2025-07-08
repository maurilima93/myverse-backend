from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import json

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relacionamentos
    preferences = db.relationship('UserPreference', backref='user', lazy=True, cascade='all, delete-orphan')
    favorites = db.relationship('UserFavorite', backref='user', lazy=True, cascade='all, delete-orphan')
    posts = db.relationship('ForumPost', backref='author', lazy=True)
    comments = db.relationship('ForumComment', backref='author', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_active': self.is_active
        }

class UserPreference(db.Model):
    __tablename__ = 'user_preferences'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    categories = db.Column(db.Text)  # JSON string
    genres = db.Column(db.Text)     # JSON string
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def set_categories(self, categories_list):
        self.categories = json.dumps(categories_list)
    
    def get_categories(self):
        return json.loads(self.categories) if self.categories else []
    
    def set_genres(self, genres_list):
        self.genres = json.dumps(genres_list)
    
    def get_genres(self):
        return json.loads(self.genres) if self.genres else []
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'categories': self.get_categories(),
            'genres': self.get_genres(),
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class UserFavorite(db.Model):
    __tablename__ = 'user_favorites'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content_type = db.Column(db.String(20), nullable=False)  # movie, tv, game, book
    content_id = db.Column(db.String(50), nullable=False)    # External API ID
    title = db.Column(db.String(255), nullable=False)
    poster_url = db.Column(db.String(500))
    added_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'content_type': self.content_type,
            'content_id': self.content_id,
            'title': self.title,
            'poster_url': self.poster_url,
            'added_at': self.added_at.isoformat() if self.added_at else None
        }

class ForumCategory(db.Model):
    __tablename__ = 'forum_categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    color = db.Column(db.String(7), default='#8B5CF6')  # Hex color
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    posts = db.relationship('ForumPost', backref='category', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'color': self.color,
            'post_count': len(self.posts)
        }

class ForumPost(db.Model):
    __tablename__ = 'forum_posts'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('forum_categories.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_pinned = db.Column(db.Boolean, default=False)
    is_locked = db.Column(db.Boolean, default=False)
    
    # Relacionamentos
    comments = db.relationship('ForumComment', backref='post', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'author': self.author.username if self.author else None,
            'category': self.category.name if self.category else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_pinned': self.is_pinned,
            'is_locked': self.is_locked,
            'comment_count': len(self.comments)
        }

class ForumComment(db.Model):
    __tablename__ = 'forum_comments'
    
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('forum_posts.id'), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('forum_comments.id'), nullable=True)  # Para respostas
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos para comentários aninhados
    replies = db.relationship('ForumComment', backref=db.backref('parent', remote_side=[id]), lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'content': self.content,
            'author': self.author.username if self.author else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'parent_id': self.parent_id,
            'reply_count': len(self.replies)
        }

def init_db():
    """Inicializar banco de dados com dados padrão"""
    db.create_all()
    
    # Criar categorias padrão do fórum se não existirem
    if not ForumCategory.query.first():
        categories = [
            {'name': 'Filmes', 'description': 'Discussões sobre filmes', 'color': '#FF6B6B'},
            {'name': 'Séries', 'description': 'Discussões sobre séries de TV', 'color': '#4ECDC4'},
            {'name': 'Jogos', 'description': 'Discussões sobre videogames', 'color': '#45B7D1'},
            {'name': 'Livros', 'description': 'Discussões sobre livros', 'color': '#96CEB4'},
            {'name': 'Geral', 'description': 'Discussões gerais', 'color': '#8B5CF6'},
        ]
        
        for cat_data in categories:
            category = ForumCategory(**cat_data)
            db.session.add(category)
        
        db.session.commit()
        print("Categorias do fórum criadas com sucesso!")

