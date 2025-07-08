# Adicione estes modelos ao seu arquivo database.py

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

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
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'created_at': self.created_at.isoformat() if self.created_at else None
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
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Índice único para evitar duplicatas
    __table_args__ = (db.UniqueConstraint('user_id', 'content_id', 'content_type'),)
    
    def __repr__(self):
        return f'<Favorite {self.title}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'content_id': self.content_id,
            'content_type': self.content_type,
            'title': self.title,
            'poster_url': self.poster_url,
            'rating': self.rating,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class ForumPost(db.Model):
    __tablename__ = 'forum_posts'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
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
            'author': self.author.username if self.author else None,
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
            'author': self.author.username if self.author else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

