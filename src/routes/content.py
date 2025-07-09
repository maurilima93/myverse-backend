from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models.database import db, UserPreference, Favorite
from src.services.tmdb_service import TMDbService
from src.services.igdb_service import IGDBService

content_bp = Blueprint('content', __name__)

# Inicializar serviços
tmdb_service = TMDbService()
igdb_service = IGDBService()

@content_bp.route('/search', methods=['GET'])
def search_content():
    try:
        query = request.args.get('q', '').strip()
        content_type = request.args.get('type', 'all')  # all, movie, tv, game
        
        if not query:
            return jsonify({'error': 'Query de pesquisa é obrigatória'}), 400
        
        results = []
        
        if content_type in ['all', 'movie']:
            # Buscar filmes
            movies = tmdb_service.search_movies(query)
            results.extend(movies)
        
        if content_type in ['all', 'tv']:
            # Buscar séries
            tv_shows = tmdb_service.search_tv_shows(query)
            results.extend(tv_shows)
        
        if content_type in ['all', 'game']:
            # Buscar jogos
            games = igdb_service.search_games(query)
            results.extend(games)
        
        return jsonify({
            'query': query,
            'results': results,
            'total': len(results)
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Erro na pesquisa: {str(e)}'}), 500

@content_bp.route('/trending', methods=['GET'])
def get_trending():
    try:
        content_type = request.args.get('type', 'all')
        
        trending = []
        
        if content_type in ['all', 'movie']:
            movies = tmdb_service.get_trending_movies()
            trending.extend(movies)
        
        if content_type in ['all', 'tv']:
            tv_shows = tmdb_service.get_trending_tv_shows()
            trending.extend(tv_shows)
        
        if content_type in ['all', 'game']:
            games = igdb_service.get_popular_games()
            trending.extend(games)
        
        return jsonify({
            'trending': trending,
            'total': len(trending)
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Erro ao buscar tendências: {str(e)}'}), 500

@content_bp.route('/recommendations', methods=['GET'])
@jwt_required()
def get_recommendations():
    try:
        user_id = get_jwt_identity()
        
        # Buscar preferências do usuário
        preferences = UserPreference.query.filter_by(user_id=user_id).first()
        
        if not preferences:
            # Se não tem preferências, retornar conteúdo popular
            return get_trending()
        
        categories = preferences.get_categories()
        genres = preferences.get_genres()
        
        recommendations = []
        
        # Recomendações baseadas em categorias e gêneros
        if 'movies' in categories:
            movies = tmdb_service.get_movies_by_genres(genres)
            recommendations.extend(movies)
        
        if 'tv' in categories:
            tv_shows = tmdb_service.get_tv_shows_by_genres(genres)
            recommendations.extend(tv_shows)
        
        if 'games' in categories:
            games = igdb_service.get_games_by_genres(genres)
            recommendations.extend(games)
        
        return jsonify({
            'recommendations': recommendations,
            'based_on': {
                'categories': categories,
                'genres': genres
            },
            'total': len(recommendations)
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Erro ao buscar recomendações: {str(e)}'}), 500

@content_bp.route('/favorites', methods=['GET'])
@jwt_required()
def get_favorites():
    try:
        user_id = get_jwt_identity()
        
        favorites = Favorite.query.filter_by(user_id=user_id).order_by(Favorite.created_at.desc()).all()
        
        return jsonify({
            'favorites': [fav.to_dict() for fav in favorites],
            'total': len(favorites)
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Erro ao buscar favoritos: {str(e)}'}), 500

@content_bp.route('/favorites', methods=['POST'])
@jwt_required()
def add_favorite():
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        content_type = data.get('content_type')
        content_id = data.get('content_id')
        title = data.get('title')
        poster_url = data.get('poster_url')
        
        if not all([content_type, content_id, title]):
            return jsonify({'error': 'Dados obrigatórios: content_type, content_id, title'}), 400
        
        # Verificar se já existe
        existing = Favorite.query.filter_by(
            user_id=user_id,
            content_type=content_type,
            content_id=content_id
        ).first()
        
        if existing:
            return jsonify({'error': 'Item já está nos favoritos'}), 400
        
        # Adicionar aos favoritos
        favorite = Favorite(
            user_id=user_id,
            content_type=content_type,
            content_id=content_id,
            title=title,
            poster_url=poster_url
        )
        
        db.session.add(favorite)
        db.session.commit()
        
        return jsonify({
            'message': 'Adicionado aos favoritos',
            'favorite': favorite.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao adicionar favorito: {str(e)}'}), 500

@content_bp.route('/favorites/<int:favorite_id>', methods=['DELETE'])
@jwt_required()
def remove_favorite(favorite_id):
    try:
        user_id = get_jwt_identity()
        
        favorite = Favorite.query.filter_by(id=favorite_id, user_id=user_id).first()
        
        if not favorite:
            return jsonify({'error': 'Favorito não encontrado'}), 404
        
        db.session.delete(favorite)
        db.session.commit()
        
        return jsonify({'message': 'Removido dos favoritos'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao remover favorito: {str(e)}'}), 500

@content_bp.route('/details/<content_type>/<content_id>', methods=['GET'])
def get_content_details(content_type, content_id):
    try:
        details = None
        
        if content_type == 'movie':
            details = tmdb_service.get_movie_details(content_id)
        elif content_type == 'tv':
            details = tmdb_service.get_tv_show_details(content_id)
        elif content_type == 'game':
            details = igdb_service.get_game_details(content_id)
        else:
            return jsonify({'error': 'Tipo de conteúdo inválido'}), 400
        
        if not details:
            return jsonify({'error': 'Conteúdo não encontrado'}), 404
        
        return jsonify(details), 200
        
    except Exception as e:
        return jsonify({'error': f'Erro ao buscar detalhes: {str(e)}'}), 500

