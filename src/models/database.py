from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    favorites = db.relationship('Favorite', backref='user', lazy=True, cascade='all, delete-orphan')
    forum_posts = db.relationship('ForumPost', backref='author', lazy=True)
    forum_replies = db.relationship('ForumReply', backref='author', lazy=True)
    preferences = db.relationship('UserPreference', backref='user', uselist=False, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class UserPreference(db.Model):
    __tablename__ = 'user_preferences'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    favorite_genres = db.Column(db.Text)  # JSON string
    favorite_categories = db.Column(db.Text)  # JSON string
    language = db.Column(db.String(10), default='pt-BR')
    notifications_enabled = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def get_genres(self):
        """Retorna lista de gêneros favoritos"""
        if self.favorite_genres:
            try:
                return json.loads(self.favorite_genres)
            except:
                return []
        return []
    
    def set_genres(self, genres):
        """Define lista de gêneros favoritos"""
        self.favorite_genres = json.dumps(genres) if genres else None
    
    def get_categories(self):
        """Retorna lista de categorias favoritas"""
        if self.favorite_categories:
            try:
                return json.loads(self.favorite_categories)
            except:
                return []
        return ['movies', 'tv', 'games']  # Default
    
    def set_categories(self, categories):
        """Define lista de categorias favoritas"""
        self.favorite_categories = json.dumps(categories) if categories else None
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'favorite_genres': self.get_genres(),
            'favorite_categories': self.get_categories(),
            'language': self.language,
            'notifications_enabled': self.notifications_enabled,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Favorite(db.Model):
    __tablename__ = 'favorites'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content_id = db.Column(db.String(50), nullable=False)
    content_type = db.Column(db.String(20), nullable=False)  # movie, tv, game
    title = db.Column(db.String(255), nullable=False)
    poster_url = db.Column(db.Text)
    rating = db.Column(db.Float)
    release_date = db.Column(db.String(20))
    overview = db.Column(db.Text)
    genres = db.Column(db.Text)  # JSON string
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Índice único para evitar duplicatas
    __table_args__ = (db.UniqueConstraint('user_id', 'content_id', 'content_type'),)
    
    def __repr__(self):
        return f'<Favorite {self.title}>'
    
    def get_genres(self):
        """Retorna lista de gêneros"""
        if self.genres:
            try:
                return json.loads(self.genres)
            except:
                return []
        return []
    
    def set_genres(self, genres_list):
        """Define lista de gêneros"""
        self.genres = json.dumps(genres_list) if genres_list else None
    
    def to_dict(self):
        return {
            'id': self.id,
            'content_id': self.content_id,
            'content_type': self.content_type,
            'title': self.title,
            'poster_url': self.poster_url,
            'rating': self.rating,
            'release_date': self.release_date,
            'overview': self.overview,
            'genres': self.get_genres(),
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class ForumPost(db.Model):
    __tablename__ = 'forum_posts'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    views = db.Column(db.Integer, default=0)
    is_pinned = db.Column(db.Boolean, default=False)
    is_locked = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    replies = db.relationship('ForumReply', backref='post', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<ForumPost {self.title}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'category': self.category,
            'author': {
                'id': self.author.id,
                'username': self.author.username
            } if self.author else None,
            'views': self.views,
            'is_pinned': self.is_pinned,
            'is_locked': self.is_locked,
            'replies_count': len(self.replies),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class ForumReply(db.Model):
    __tablename__ = 'forum_replies'
    
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('forum_posts.id'), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<ForumReply {self.id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'content': self.content,
            'post_id': self.post_id,
            'author': {
                'id': self.author.id,
                'username': self.author.username
            } if self.author else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

