from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from src.extensions import db  # Importe do mesmo lugar
import json

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relacionamentos
    favorites = db.relationship('Favorite', backref='user', lazy=True, cascade='all, delete-orphan')
    forum_posts = db.relationship('ForumPost', backref='author', lazy=True)
    forum_replies = db.relationship('ForumReply', backref='author', lazy=True)
    
    # Relacionamentos de amizade
    sent_requests = db.relationship('Friendship', 
                                   foreign_keys='Friendship.requester_id',
                                   backref='requester', lazy='dynamic')
    received_requests = db.relationship('Friendship',
                                       foreign_keys='Friendship.requested_id', 
                                       backref='requested', lazy='dynamic')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_friends(self):
        """Retorna lista de amigos aceitos"""
        friends = []
        
        # Amigos onde eu enviei a solicitação
        sent_friends = db.session.query(Friendship).filter(
            Friendship.requester_id == self.id,
            Friendship.status == 'accepted'
        ).all()
        
        for friendship in sent_friends:
            friends.append(User.query.get(friendship.requested_id))
        
        # Amigos onde eu recebi a solicitação
        received_friends = db.session.query(Friendship).filter(
            Friendship.requested_id == self.id,
            Friendship.status == 'accepted'
        ).all()
        
        for friendship in received_friends:
            friends.append(User.query.get(friendship.requester_id))
        
        return friends
    
    def get_friend_requests(self):
        """Retorna solicitações de amizade pendentes"""
        return db.session.query(Friendship).filter(
            Friendship.requested_id == self.id,
            Friendship.status == 'pending'
        ).all()
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_active': self.is_active
        }

class Favorite(db.Model):
    __tablename__ = 'favorites'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content_type = db.Column(db.String(20), nullable=False)  # 'movie', 'tv', 'game'
    content_id = db.Column(db.String(50), nullable=False)  # ID do TMDb/IGDB
    title = db.Column(db.String(255), nullable=False)
    poster_url = db.Column(db.Text)
    rating = db.Column(db.Float)
    genres = db.Column(db.Text)  # JSON string
    release_date = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Índice único para evitar duplicatas
    __table_args__ = (db.UniqueConstraint('user_id', 'content_type', 'content_id'),)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'content_type': self.content_type,
            'content_id': self.content_id,
            'title': self.title,
            'poster_url': self.poster_url,
            'rating': self.rating,
            'genres': json.loads(self.genres) if self.genres else [],
            'release_date': self.release_date,
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
    is_active = db.Column(db.Boolean, default=True)
    
    # Relacionamentos
    replies = db.relationship('ForumReply', backref='post', lazy=True, cascade='all, delete-orphan')
    
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
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'replies_count': len(self.replies),
            'is_active': self.is_active
        }

class ForumReply(db.Model):
    __tablename__ = 'forum_replies'
    
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('forum_posts.id'), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
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
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_active': self.is_active
        }

class Friendship(db.Model):
    __tablename__ = 'friendships'
    
    id = db.Column(db.Integer, primary_key=True)
    requester_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    requested_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # 'pending', 'accepted', 'rejected', 'blocked'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Índice único para evitar duplicatas
    __table_args__ = (db.UniqueConstraint('requester_id', 'requested_id'),)
    
    def to_dict(self):
        return {
            'id': self.id,
            'requester': {
                'id': self.requester.id,
                'username': self.requester.username
            } if self.requester else None,
            'requested': {
                'id': self.requested.id,
                'username': self.requested.username
            } if self.requested else None,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

