from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models.database import db, User, Favorite, UserPreference
from ..services.tmdb_service import TMDbService
from ..services.igdb_service import IGDBService
import json

content_bp = Blueprint('content', __name__)

# Inicializar serviços
tmdb_service = TMDbService()
igdb_service = IGDBService()

@content_bp.route('/search', methods=['GET'])
def search_content():
    try:
        query = request.args.get('q', '').strip()
        
        if not query:
            return jsonify({'error': 'Parâmetro de busca é obrigatório'}), 400
        
        results = []
        
        # Buscar filmes e séries no TMDb
        try:
            movies = tmdb_service.search_movies(query)
            tv_shows = tmdb_service.search_tv_shows(query)
            results.extend(movies + tv_shows)
        except Exception as e:
            print(f"Erro TMDb: {e}")
        
        # Buscar jogos no IGDB
        try:
            games = igdb_service.search_games(query)
            results.extend(games)
        except Exception as e:
            print(f"Erro IGDB: {e}")
        
        # Se não encontrou nada nas APIs, retornar dados mock
        if not results:
            results = get_mock_data(query)
        
        return jsonify({
            'results': results,
            'total': len(results)
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Erro interno do servidor: {str(e)}'}), 500

@content_bp.route('/favorites', methods=['GET'])
@jwt_required()
def get_favorites():
    try:
        current_user_id = get_jwt_identity()
        
        favorites = Favorite.query.filter_by(user_id=current_user_id).order_by(Favorite.created_at.desc()).all()
        
        return jsonify({
            'favorites': [fav.to_dict() for fav in favorites],
            'total': len(favorites)
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Erro interno do servidor: {str(e)}'}), 500

@content_bp.route('/favorites', methods=['POST'])
@jwt_required()
def add_favorite():
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data or not all(k in data for k in ('content_id', 'content_type', 'title')):
            return jsonify({'error': 'content_id, content_type e title são obrigatórios'}), 400
        
        # Verificar se já está nos favoritos
        existing = Favorite.query.filter_by(
            user_id=current_user_id,
            content_id=data['content_id'],
            content_type=data['content_type']
        ).first()
        
        if existing:
            return jsonify({'error': 'Item já está nos favoritos'}), 409
        
        # Criar favorito
        favorite = Favorite(
            user_id=current_user_id,
            content_id=data['content_id'],
            content_type=data['content_type'],
            title=data['title'],
            poster_url=data.get('poster_url'),
            rating=data.get('rating'),
            release_date=data.get('release_date'),
            genres=json.dumps(data.get('genres', [])),
            description=data.get('description')
        )
        
        db.session.add(favorite)
        
        # Atualizar preferências do usuário
        if data.get('genres'):
            for genre in data['genres']:
                preference = UserPreference.query.filter_by(
                    user_id=current_user_id,
                    genre=genre,
                    content_type=data['content_type']
                ).first()
                
                if preference:
                    preference.weight += 0.1
                else:
                    preference = UserPreference(
                        user_id=current_user_id,
                        genre=genre,
                        content_type=data['content_type'],
                        weight=1.0
                    )
                    db.session.add(preference)
        
        db.session.commit()
        
        return jsonify({
            'message': 'Adicionado aos favoritos com sucesso!',
            'favorite': favorite.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro interno do servidor: {str(e)}'}), 500

@content_bp.route('/favorites/<int:favorite_id>', methods=['DELETE'])
@jwt_required()
def remove_favorite(favorite_id):
    try:
        current_user_id = get_jwt_identity()
        
        favorite = Favorite.query.filter_by(id=favorite_id, user_id=current_user_id).first()
        
        if not favorite:
            return jsonify({'error': 'Favorito não encontrado'}), 404
        
        db.session.delete(favorite)
        db.session.commit()
        
        return jsonify({'message': 'Removido dos favoritos com sucesso!'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro interno do servidor: {str(e)}'}), 500

@content_bp.route('/favorites/check', methods=['POST'])
@jwt_required()
def check_favorite():
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data or not all(k in data for k in ('content_id', 'content_type')):
            return jsonify({'error': 'content_id e content_type são obrigatórios'}), 400
        
        favorite = Favorite.query.filter_by(
            user_id=current_user_id,
            content_id=data['content_id'],
            content_type=data['content_type']
        ).first()
        
        return jsonify({
            'is_favorite': favorite is not None,
            'favorite_id': favorite.id if favorite else None
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Erro interno do servidor: {str(e)}'}), 500

def get_mock_data(query):
    """Dados mock para quando as APIs não estão disponíveis"""
    mock_data = [
        {
            'id': 'mock_1',
            'title': f'Resultado Mock para "{query}"',
            'type': 'movie',
            'poster_url': 'https://via.placeholder.com/300x450/8B5CF6/FFFFFF?text=Mock+Movie',
            'rating': 8.5,
            'release_date': '2023',
            'genres': ['Ação', 'Aventura'],
            'description': f'Este é um resultado mock para a busca "{query}". Em produção, este seria substituído por dados reais das APIs.'
        }
    ]
    return mock_data

