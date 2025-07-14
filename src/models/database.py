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
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    preferences = db.relationship('UserPreference', backref='user', lazy=True, cascade='all, delete-orphan')
    favorites = db.relationship('Favorite', backref='user', lazy=True, cascade='all, delete-orphan')
    forum_posts = db.relationship('ForumPost', backref='author', lazy=True, cascade='all, delete-orphan')
    forum_replies = db.relationship('ForumReply', backref='author', lazy=True, cascade='all, delete-orphan')
    
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
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class UserPreference(db.Model):
    __tablename__ = 'user_preferences'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    genre = db.Column(db.String(100), nullable=False)
    content_type = db.Column(db.String(50), nullable=False)  # movie, tv, game, book
    weight = db.Column(db.Float, default=1.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('user_id', 'genre', 'content_type'),)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'genre': self.genre,
            'content_type': self.content_type,
            'weight': self.weight,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Favorite(db.Model):
    __tablename__ = 'favorites'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content_id = db.Column(db.String(100), nullable=False)  # ID do TMDb/IGDB
    content_type = db.Column(db.String(50), nullable=False)  # movie, tv, game, book
    title = db.Column(db.String(255), nullable=False)
    poster_url = db.Column(db.String(500))
    rating = db.Column(db.Float)
    release_date = db.Column(db.String(50))
    genres = db.Column(db.Text)  # JSON string
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('user_id', 'content_id', 'content_type'),)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'content_id': self.content_id,
            'content_type': self.content_type,
            'title': self.title,
            'poster_url': self.poster_url,
            'rating': self.rating,
            'release_date': self.release_date,
            'genres': json.loads(self.genres) if self.genres else [],
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class ForumPost(db.Model):
    __tablename__ = 'forum_posts'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    replies = db.relationship('ForumReply', backref='post', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'author': self.author.username if self.author else None,
            'title': self.title,
            'content': self.content,
            'category': self.category,
            'replies_count': len(self.replies),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class ForumReply(db.Model):
    __tablename__ = 'forum_replies'
    
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('forum_posts.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'post_id': self.post_id,
            'user_id': self.user_id,
            'author': self.author.username if self.author else None,
            'content': self.content,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

