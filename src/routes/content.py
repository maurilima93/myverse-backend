from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models.database import db, User, Favorite
from src.services.tmdb_service import TMDbService
from src.services.igdb_service import IGDBService

content_bp = Blueprint('content', __name__)

@content_bp.route('/search', methods=['GET'])
def search_content():
    try:
        query = request.args.get('q', '').strip()
        
        if not query:
            return jsonify({'error': 'Query parameter "q" is required'}), 400
        
        if len(query) < 2:
            return jsonify({'error': 'Query must be at least 2 characters'}), 400
        
        # Inicializar serviços
        tmdb_service = TMDbService()
        igdb_service = IGDBService()
        
        results = []
        
        # Buscar filmes
        try:
            movies = tmdb_service.search_movies(query)
            for movie in movies:
                results.append({
                    'id': str(movie.get('id')),
                    'title': movie.get('title', 'N/A'),
                    'type': 'movie',
                    'poster_url': tmdb_service.get_poster_url(movie.get('poster_path')),
                    'rating': movie.get('vote_average', 0),
                    'year': movie.get('release_date', '')[:4] if movie.get('release_date') else '',
                    'overview': movie.get('overview', ''),
                    'genres': [genre['name'] for genre in movie.get('genres', [])] if movie.get('genres') else []
                })
        except Exception as e:
            print(f"Erro ao buscar filmes: {e}")
        
        # Buscar séries
        try:
            tv_shows = tmdb_service.search_tv_shows(query)
            for show in tv_shows:
                results.append({
                    'id': str(show.get('id')),
                    'title': show.get('name', 'N/A'),
                    'type': 'tv',
                    'poster_url': tmdb_service.get_poster_url(show.get('poster_path')),
                    'rating': show.get('vote_average', 0),
                    'year': show.get('first_air_date', '')[:4] if show.get('first_air_date') else '',
                    'overview': show.get('overview', ''),
                    'genres': [genre['name'] for genre in show.get('genres', [])] if show.get('genres') else []
                })
        except Exception as e:
            print(f"Erro ao buscar séries: {e}")
        
        # Buscar jogos
        try:
            games = igdb_service.search_games(query)
            for game in games:
                results.append({
                    'id': str(game.get('id')),
                    'title': game.get('name', 'N/A'),
                    'type': 'game',
                    'poster_url': igdb_service.get_cover_url(game.get('cover')),
                    'rating': game.get('rating', 0) / 10 if game.get('rating') else 0,  # IGDB usa 0-100
                    'year': str(game.get('first_release_date', '')[:4]) if game.get('first_release_date') else '',
                    'overview': game.get('summary', ''),
                    'genres': [genre['name'] for genre in game.get('genres', [])] if game.get('genres') else [],
                    'platforms': [platform['name'] for platform in game.get('platforms', [])] if game.get('platforms') else []
                })
        except Exception as e:
            print(f"Erro ao buscar jogos: {e}")
        
        # Ordenar por relevância (rating)
        results.sort(key=lambda x: x.get('rating', 0), reverse=True)
        
        return jsonify({
            'results': results,
            'total': len(results),
            'query': query
        }), 200
        
    except Exception as e:
        print(f"Erro na busca: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@content_bp.route('/favorites', methods=['GET'])
@jwt_required()
def get_favorites():
    try:
        current_user_id = get_jwt_identity()
        
        favorites = Favorite.query.filter_by(user_id=current_user_id).order_by(Favorite.created_at.desc()).all()
        
        return jsonify({
            'favorites': [fav.to_dict() for fav in favorites]
        }), 200
        
    except Exception as e:
        print(f"Erro ao buscar favoritos: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@content_bp.route('/favorites', methods=['POST'])
@jwt_required()
def add_favorite():
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Dados não fornecidos'}), 400
        
        content_id = data.get('content_id')
        content_type = data.get('content_type')
        title = data.get('title')
        poster_url = data.get('poster_url')
        rating = data.get('rating')
        
        if not all([content_id, content_type, title]):
            return jsonify({'error': 'content_id, content_type e title são obrigatórios'}), 400
        
        if content_type not in ['movie', 'tv', 'game']:
            return jsonify({'error': 'content_type deve ser movie, tv ou game'}), 400
        
        # Verificar se já existe
        existing = Favorite.query.filter_by(
            user_id=current_user_id,
            content_id=content_id,
            content_type=content_type
        ).first()
        
        if existing:
            return jsonify({'error': 'Item já está nos favoritos'}), 409
        
        # Criar novo favorito
        favorite = Favorite(
            user_id=current_user_id,
            content_id=content_id,
            content_type=content_type,
            title=title,
            poster_url=poster_url,
            rating=rating
        )
        
        db.session.add(favorite)
        db.session.commit()
        
        return jsonify({
            'message': 'Adicionado aos favoritos',
            'favorite': favorite.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao adicionar favorito: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@content_bp.route('/favorites/<int:favorite_id>', methods=['DELETE'])
@jwt_required()
def remove_favorite(favorite_id):
    try:
        current_user_id = get_jwt_identity()
        
        favorite = Favorite.query.filter_by(
            id=favorite_id,
            user_id=current_user_id
        ).first()
        
        if not favorite:
            return jsonify({'error': 'Favorito não encontrado'}), 404
        
        db.session.delete(favorite)
        db.session.commit()
        
        return jsonify({'message': 'Removido dos favoritos'}), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao remover favorito: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@content_bp.route('/trending', methods=['GET'])
def get_trending():
    try:
        tmdb_service = TMDbService()
        igdb_service = IGDBService()
        
        results = []
        
        # Filmes em alta
        try:
            trending_movies = tmdb_service.get_trending_movies()
            for movie in trending_movies[:5]:  # Limitar a 5
                results.append({
                    'id': str(movie.get('id')),
                    'title': movie.get('title', 'N/A'),
                    'type': 'movie',
                    'poster_url': tmdb_service.get_poster_url(movie.get('poster_path')),
                    'rating': movie.get('vote_average', 0),
                    'year': movie.get('release_date', '')[:4] if movie.get('release_date') else '',
                    'overview': movie.get('overview', '')
                })
        except Exception as e:
            print(f"Erro ao buscar filmes em alta: {e}")
        
        # Séries em alta
        try:
            trending_tv = tmdb_service.get_trending_tv()
            for show in trending_tv[:5]:  # Limitar a 5
                results.append({
                    'id': str(show.get('id')),
                    'title': show.get('name', 'N/A'),
                    'type': 'tv',
                    'poster_url': tmdb_service.get_poster_url(show.get('poster_path')),
                    'rating': show.get('vote_average', 0),
                    'year': show.get('first_air_date', '')[:4] if show.get('first_air_date') else '',
                    'overview': show.get('overview', '')
                })
        except Exception as e:
            print(f"Erro ao buscar séries em alta: {e}")
        
        # Jogos populares
        try:
            popular_games = igdb_service.get_popular_games()
            for game in popular_games[:5]:  # Limitar a 5
                results.append({
                    'id': str(game.get('id')),
                    'title': game.get('name', 'N/A'),
                    'type': 'game',
                    'poster_url': igdb_service.get_cover_url(game.get('cover')),
                    'rating': game.get('rating', 0) / 10 if game.get('rating') else 0,
                    'year': str(game.get('first_release_date', '')[:4]) if game.get('first_release_date') else '',
                    'overview': game.get('summary', '')
                })
        except Exception as e:
            print(f"Erro ao buscar jogos populares: {e}")
        
        return jsonify({
            'trending': results,
            'total': len(results)
        }), 200
        
    except Exception as e:
        print(f"Erro ao buscar conteúdo em alta: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

