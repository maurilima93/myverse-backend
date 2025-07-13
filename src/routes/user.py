from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models.database import db, User, UserPreference, Favorite
from datetime import datetime

user_bp = Blueprint('user', __name__)

@content_bp.before_request
def handle_options():
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'preflight'})
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        return response

@user_bp.route('/preferences', methods=['GET'])
@jwt_required()
def get_preferences():
    try:
        user_id = get_jwt_identity()
        preferences = UserPreference.query.filter_by(user_id=user_id).first()
        if not preferences:
            return jsonify({
                'preferences': {
                    'categories': [],
                    'genres': []
                }
            }), 200
        return jsonify({
            'preferences': preferences.to_dict()
        }), 200

    except Exception as e:
        return jsonify({'error': f'Erro ao buscar preferências: {str(e)}'}), 500

@user_bp.route('/preferences', methods=['POST'])
@jwt_required()
def save_preferences():
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Dados não fornecidos'}), 400
        
        categories = data.get('preferred_categories', [])
        genres = data.get('preferred_genres', [])
        
        # Validar dados
        if not isinstance(categories, list) or not isinstance(genres, list):
            return jsonify({'error': 'Categorias e gêneros devem ser listas'}), 400
        
        # Buscar ou criar preferências
        preferences = UserPreference.query.filter_by(user_id=user_id).first()
        
        if not preferences:
            preferences = UserPreference(user_id=user_id)
            db.session.add(preferences)
        
        # Atualizar preferências
        preferences.set_categories(categories)
        preferences.set_genres(genres)
        preferences.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'message': 'Preferências salvas com sucesso',
            'preferences': preferences.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao salvar preferências: {str(e)}'}), 500

@user_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_user_stats():
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'Usuário não encontrado'}), 404       
        # Estatísticas do usuário
        stats = {
            'favorites_count': len(user.favorites),
            'posts_count': len(user.forum_posts),
            'comments_count': len(user.forum_replies),
            'member_since': user.created_at.isoformat() if user.created_at else None
        }

        # Estatísticas por categoria de favoritos
        favorites_by_type = {}
        for favorite in user.favorites:
            content_type = favorite.content_type
            if content_type not in favorites_by_type:
                favorites_by_type[content_type] = 0
            favorites_by_type[content_type] += 1
        stats['favorites_by_type'] = favorites_by_type
        return jsonify({
            'user': user.to_dict(),
            'stats': stats
        }), 200
    except Exception as e:
        return jsonify({'error': f'Erro ao buscar estatísticas: {str(e)}'}), 500

