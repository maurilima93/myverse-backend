from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models.database import db, User, Favorite

user_bp = Blueprint('user', __name__)

@user_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'Usuário não encontrado'}), 404
        
        # Contar favoritos por tipo
        favorites_count = {
            'movies': Favorite.query.filter_by(user_id=current_user_id, content_type='movie').count(),
            'tv_shows': Favorite.query.filter_by(user_id=current_user_id, content_type='tv').count(),
            'games': Favorite.query.filter_by(user_id=current_user_id, content_type='game').count()
        }
        
        return jsonify({
            'user': user.to_dict(),
            'favorites_count': favorites_count,
            'total_favorites': sum(favorites_count.values())
        }), 200
        
    except Exception as e:
        print(f"Erro ao buscar perfil: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@user_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'Usuário não encontrado'}), 404
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Dados não fornecidos'}), 400
        
        # Atualizar campos permitidos
        if 'username' in data:
            username = data['username'].strip()
            if len(username) < 3 or len(username) > 20:
                return jsonify({'error': 'Username deve ter entre 3 e 20 caracteres'}), 400
            
            # Verificar se username já existe (exceto o atual)
            existing = User.query.filter(User.username == username, User.id != current_user_id).first()
            if existing:
                return jsonify({'error': 'Username já está em uso'}), 409
            
            user.username = username
        
        if 'email' in data:
            email = data['email'].strip()
            if not email:
                return jsonify({'error': 'Email não pode estar vazio'}), 400
            
            # Verificar se email já existe (exceto o atual)
            existing = User.query.filter(User.email == email, User.id != current_user_id).first()
            if existing:
                return jsonify({'error': 'Email já está em uso'}), 409
            
            user.email = email
        
        db.session.commit()
        
        return jsonify({
            'message': 'Perfil atualizado com sucesso',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao atualizar perfil: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@user_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_user_stats():
    try:
        current_user_id = get_jwt_identity()
        
        # Estatísticas de favoritos
        favorites = Favorite.query.filter_by(user_id=current_user_id).all()
        
        stats = {
            'total_favorites': len(favorites),
            'by_type': {
                'movies': len([f for f in favorites if f.content_type == 'movie']),
                'tv_shows': len([f for f in favorites if f.content_type == 'tv']),
                'games': len([f for f in favorites if f.content_type == 'game'])
            },
            'average_rating': 0,
            'recent_favorites': []
        }
        
        # Calcular média de avaliações
        ratings = [f.rating for f in favorites if f.rating]
        if ratings:
            stats['average_rating'] = round(sum(ratings) / len(ratings), 1)
        
        # Favoritos recentes (últimos 5)
        recent = sorted(favorites, key=lambda x: x.created_at, reverse=True)[:5]
        stats['recent_favorites'] = [fav.to_dict() for fav in recent]
        
        return jsonify(stats), 200
        
    except Exception as e:
        print(f"Erro ao buscar estatísticas: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@user_bp.route('/preferences', methods=['GET'])
@jwt_required()
def get_preferences():
    try:
        current_user_id = get_jwt_identity()
        
        # Por enquanto, retornar preferências básicas
        # Pode ser expandido no futuro com tabela de preferências
        preferences = {
            'favorite_genres': [],
            'preferred_content_types': ['movie', 'tv', 'game'],
            'language': 'pt-BR',
            'notifications': {
                'new_releases': True,
                'recommendations': True,
                'forum_replies': True
            }
        }
        
        return jsonify({'preferences': preferences}), 200
        
    except Exception as e:
        print(f"Erro ao buscar preferências: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@user_bp.route('/preferences', methods=['PUT'])
@jwt_required()
def update_preferences():
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Dados não fornecidos'}), 400
        
        # Por enquanto, apenas retornar sucesso
        # Implementação completa seria salvar em tabela de preferências
        
        return jsonify({
            'message': 'Preferências atualizadas com sucesso',
            'preferences': data
        }), 200
        
    except Exception as e:
        print(f"Erro ao atualizar preferências: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

