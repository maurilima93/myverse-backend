from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models.database import User, Favorite, ForumPost, Friendship
from src.extensions import db
from datetime import datetime
import json

user_bp = Blueprint('user', __name__)

@user_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """Buscar perfil do usuário atual"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'Usuário não encontrado'}), 404
        
        # Buscar estatísticas
        favorites_count = Favorite.query.filter_by(user_id=user_id).count()
        posts_count = ForumPost.query.filter_by(author_id=user_id, is_active=True).count()
        friends_count = Friendship.query.filter(
            db.or_(
                db.and_(Friendship.requester_id == user_id, Friendship.status == 'accepted'),
                db.and_(Friendship.requested_id == user_id, Friendship.status == 'accepted')
            )
        ).count()
        
        # Buscar favoritos recentes
        recent_favorites = Favorite.query.filter_by(user_id=user_id).order_by(Favorite.created_at.desc()).limit(10).all()
        
        # Agrupar favoritos por tipo
        favorites_by_type = {
            'movies': 0,
            'tv': 0,
            'games': 0
        }
        
        all_favorites = Favorite.query.filter_by(user_id=user_id).all()
        for fav in all_favorites:
            if fav.content_type in favorites_by_type:
                favorites_by_type[fav.content_type] += 1
        
        # Gêneros favoritos
        all_genres = []
        for fav in all_favorites:
            if fav.genres:
                try:
                    genres = json.loads(fav.genres)
                    all_genres.extend(genres)
                except:
                    pass
        
        from collections import Counter
        top_genres = [genre for genre, count in Counter(all_genres).most_common(5)]
        
        profile_data = user.to_dict()
        profile_data.update({
            'stats': {
                'favorites_count': favorites_count,
                'posts_count': posts_count,
                'friends_count': friends_count,
                'favorites_by_type': favorites_by_type
            },
            'recent_favorites': [fav.to_dict() for fav in recent_favorites],
            'top_genres': top_genres
        })
        
        return jsonify({
            'profile': profile_data
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Erro ao buscar perfil: {str(e)}'}), 500

@user_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """Atualizar perfil do usuário"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'Usuário não encontrado'}), 404
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Dados não fornecidos'}), 400
        
        # Atualizar username se fornecido
        if 'username' in data:
            new_username = data['username'].strip()
            
            if len(new_username) < 3:
                return jsonify({'error': 'Username deve ter pelo menos 3 caracteres'}), 400
            
            # Verificar se username já existe (excluindo o próprio usuário)
            existing = User.query.filter(
                User.username == new_username,
                User.id != user_id
            ).first()
            
            if existing:
                return jsonify({'error': 'Username já existe'}), 409
            
            user.username = new_username
        
        # Atualizar email se fornecido
        if 'email' in data:
            new_email = data['email'].strip().lower()
            
            if '@' not in new_email:
                return jsonify({'error': 'Email inválido'}), 400
            
            # Verificar se email já existe (excluindo o próprio usuário)
            existing = User.query.filter(
                User.email == new_email,
                User.id != user_id
            ).first()
            
            if existing:
                return jsonify({'error': 'Email já cadastrado'}), 409
            
            user.email = new_email
        
        user.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Perfil atualizado com sucesso!',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao atualizar perfil: {str(e)}'}), 500

@user_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    """Alterar senha do usuário"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'Usuário não encontrado'}), 404
        
        data = request.get_json()
        
        if not data or not all(k in data for k in ['current_password', 'new_password']):
            return jsonify({'error': 'Senha atual e nova senha são obrigatórias'}), 400
        
        current_password = data['current_password']
        new_password = data['new_password']
        
        # Verificar senha atual
        if not user.check_password(current_password):
            return jsonify({'error': 'Senha atual incorreta'}), 401
        
        # Validar nova senha
        if len(new_password) < 6:
            return jsonify({'error': 'Nova senha deve ter pelo menos 6 caracteres'}), 400
        
        if new_password == current_password:
            return jsonify({'error': 'Nova senha deve ser diferente da atual'}), 400
        
        # Atualizar senha
        user.set_password(new_password)
        user.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Senha alterada com sucesso!'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao alterar senha: {str(e)}'}), 500

@user_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_user_stats():
    """Buscar estatísticas detalhadas do usuário"""
    try:
        user_id = get_jwt_identity()
        
        # Estatísticas básicas
        favorites_count = Favorite.query.filter_by(user_id=user_id).count()
        posts_count = ForumPost.query.filter_by(author_id=user_id, is_active=True).count()
        friends_count = Friendship.query.filter(
            db.or_(
                db.and_(Friendship.requester_id == user_id, Friendship.status == 'accepted'),
                db.and_(Friendship.requested_id == user_id, Friendship.status == 'accepted')
            )
        ).count()
        
        # Favoritos por tipo
        favorites_by_type = {
            'movies': Favorite.query.filter_by(user_id=user_id, content_type='movie').count(),
            'tv': Favorite.query.filter_by(user_id=user_id, content_type='tv').count(),
            'games': Favorite.query.filter_by(user_id=user_id, content_type='game').count()
        }
        
        # Favoritos por mês (últimos 12 meses)
        from sqlalchemy import func, extract
        favorites_by_month = db.session.query(
            extract('month', Favorite.created_at).label('month'),
            func.count(Favorite.id).label('count')
        ).filter(
            Favorite.user_id == user_id,
            Favorite.created_at >= datetime.utcnow().replace(month=1, day=1)  # Ano atual
        ).group_by(extract('month', Favorite.created_at)).all()
        
        monthly_data = {str(month): 0 for month in range(1, 13)}
        for month, count in favorites_by_month:
            monthly_data[str(int(month))] = count
        
        # Top gêneros
        all_favorites = Favorite.query.filter_by(user_id=user_id).all()
        all_genres = []
        
        for fav in all_favorites:
            if fav.genres:
                try:
                    genres = json.loads(fav.genres)
                    all_genres.extend(genres)
                except:
                    pass
        
        from collections import Counter
        genre_counts = Counter(all_genres)
        top_genres = [
            {'genre': genre, 'count': count}
            for genre, count in genre_counts.most_common(10)
        ]
        
        # Atividade no fórum por mês
        forum_by_month = db.session.query(
            extract('month', ForumPost.created_at).label('month'),
            func.count(ForumPost.id).label('count')
        ).filter(
            ForumPost.author_id == user_id,
            ForumPost.is_active == True,
            ForumPost.created_at >= datetime.utcnow().replace(month=1, day=1)
        ).group_by(extract('month', ForumPost.created_at)).all()
        
        forum_monthly_data = {str(month): 0 for month in range(1, 13)}
        for month, count in forum_by_month:
            forum_monthly_data[str(int(month))] = count
        
        return jsonify({
            'stats': {
                'totals': {
                    'favorites': favorites_count,
                    'posts': posts_count,
                    'friends': friends_count
                },
                'favorites_by_type': favorites_by_type,
                'favorites_by_month': monthly_data,
                'forum_by_month': forum_monthly_data,
                'top_genres': top_genres
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Erro ao buscar estatísticas: {str(e)}'}), 500

@user_bp.route('/deactivate', methods=['POST'])
@jwt_required()
def deactivate_account():
    """Desativar conta do usuário"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'Usuário não encontrado'}), 404
        
        data = request.get_json()
        
        if not data or 'password' not in data:
            return jsonify({'error': 'Senha é obrigatória para desativar a conta'}), 400
        
        password = data['password']
        
        # Verificar senha
        if not user.check_password(password):
            return jsonify({'error': 'Senha incorreta'}), 401
        
        # Desativar conta
        user.is_active = False
        user.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Conta desativada com sucesso. Você pode reativá-la fazendo login novamente.'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao desativar conta: {str(e)}'}), 500

