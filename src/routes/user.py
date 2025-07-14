from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models.database import db, User, UserPreference, Favorite

user_bp = Blueprint('user', __name__)

@user_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get_or_404(current_user_id)
        
        # Estatísticas do usuário
        favorites_count = Favorite.query.filter_by(user_id=current_user_id).count()
        preferences = UserPreference.query.filter_by(user_id=current_user_id).all()
        
        # Gêneros favoritos
        top_genres = []
        if preferences:
            genre_weights = {}
            for pref in preferences:
                if pref.genre in genre_weights:
                    genre_weights[pref.genre] += pref.weight
                else:
                    genre_weights[pref.genre] = pref.weight
            
            top_genres = sorted(genre_weights.items(), key=lambda x: x[1], reverse=True)[:5]
            top_genres = [{'genre': genre, 'weight': weight} for genre, weight in top_genres]
        
        return jsonify({
            'user': user.to_dict(),
            'stats': {
                'favorites_count': favorites_count,
                'top_genres': top_genres
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Erro interno do servidor: {str(e)}'}), 500

@user_bp.route('/preferences', methods=['GET'])
@jwt_required()
def get_preferences():
    try:
        current_user_id = get_jwt_identity()
        preferences = UserPreference.query.filter_by(user_id=current_user_id).all()
        
        return jsonify({
            'preferences': [pref.to_dict() for pref in preferences]
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Erro interno do servidor: {str(e)}'}), 500

@user_bp.route('/preferences', methods=['POST'])
@jwt_required()
def update_preferences():
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data or 'preferences' not in data:
            return jsonify({'error': 'preferences é obrigatório'}), 400
        
        # Limpar preferências existentes
        UserPreference.query.filter_by(user_id=current_user_id).delete()
        
        # Adicionar novas preferências
        for pref_data in data['preferences']:
            if all(k in pref_data for k in ('genre', 'content_type')):
                preference = UserPreference(
                    user_id=current_user_id,
                    genre=pref_data['genre'],
                    content_type=pref_data['content_type'],
                    weight=pref_data.get('weight', 1.0)
                )
                db.session.add(preference)
        
        db.session.commit()
        
        return jsonify({'message': 'Preferências atualizadas com sucesso!'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro interno do servidor: {str(e)}'}), 500

