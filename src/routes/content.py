from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models.database import db, User, UserPreference, Favorite
from src.services.tmdb_service import TMDbService
from src.services.igdb_service import IGDBService

content_bp = Blueprint('content', __name__)

# Inicializar serviços
tmdb_service = TMDbService()
igdb_service = IGDBService()

@content_bp.before_request
def handle_options():
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'preflight'})
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        return response

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
        print(f"Erro na pesquisa: {str(e)}")
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
        print(f"Erro ao buscar tendências: {str(e)}")
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
        print(f"Erro ao buscar recomendações: {str(e)}")
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
        print(f"Erro ao buscar favoritos: {str(e)}")
        return jsonify({'error': f'Erro ao buscar favoritos: {str(e)}'}), 500

@content_bp.route('/favorites', methods=['POST'])
@jwt_required()
def add_favorite():
    try:
        user_id = get_jwt_identity()
        
        # Verifique se o conteúdo é JSON
        if not request.is_json:
            return jsonify({"error": "Request must be JSON"}), 415
            
        data = request.get_json()
        
        # Validação mais robusta
        required_fields = ['content_type', 'content_id', 'title']
        if not all(field in data for field in required_fields):
            missing = [field for field in required_fields if field not in data]
            return jsonify({'error': f'Campos obrigatórios faltando: {missing}'}), 400
        
        # Verifique tipos válidos
        valid_types = ['movie', 'tv', 'game']
        if data['content_type'] not in valid_types:
            return jsonify({'error': f'Tipo de conteúdo inválido. Use: {valid_types}'}), 400
        
        content_type = data.get('content_type')
        content_id = str(data.get('content_id'))
        title = data.get('title')
        poster_url = data.get('poster_url')
        rating = data.get('rating')
        release_date = data.get('release_date')
        overview = data.get('overview')
        genres = data.get('genres', [])
        
        if not all([content_type, content_id, title]):
            return jsonify({'error': 'Dados obrigatórios: content_type, content_id, title'}), 400
        
        # Verificar se já existe
        existing = Favorite.query.filter_by(
            user_id=user_id,
            content_type=content_type,
            content_id=content_id
        ).first()
        
        if existing:
            return jsonify({'error': 'Item já está nos favoritos'}), 409
        
        # Adicionar aos favoritos
        favorite = Favorite(
            user_id=user_id,
            content_type=content_type,
            content_id=content_id,
            title=title,
            poster_url=poster_url,
            rating=rating,
            release_date=release_date,
            overview=overview
        )
        
        # Definir gêneros se fornecidos
        if genres:
            favorite.set_genres(genres)
        
        with db.session.begin():
            existing = Favorite.query.filter_by(
                user_id=user_id,
                content_type=data['content_type'],
                content_id=str(data['content_id'])
            ).first()
            
            if existing:
                return jsonify({'error': 'Item já está nos favoritos'}), 409
                
            favorite = Favorite(
                user_id=user_id,
                content_type=data['content_type'],
                content_id=str(data['content_id']),
                title=data['title'],
                poster_url=data.get('poster_url'),
                rating=data.get('rating'),
                release_date=data.get('release_date'),
                overview=data.get('overview')
            )
            
            db.session.add(favorite)
        
        return jsonify({'message': 'Adicionado com sucesso'}), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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
        
        return jsonify({'message': 'Removido dos favoritos com sucesso'}), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao remover favorito: {str(e)}")
        return jsonify({'error': f'Erro ao remover favorito: {str(e)}'}), 500

@content_bp.route('/favorites/check', methods=['POST'])
@jwt_required()
def check_favorite():
    """Verifica se um item está nos favoritos"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        content_type = data.get('content_type')
        content_id = str(data.get('content_id'))
        
        if not all([content_type, content_id]):
            return jsonify({'error': 'content_type e content_id são obrigatórios'}), 400
        
        favorite = Favorite.query.filter_by(
            user_id=user_id,
            content_type=content_type,
            content_id=content_id
        ).first()
        
        return jsonify({
            'is_favorite': favorite is not None,
            'favorite_id': favorite.id if favorite else None
        }), 200
        
    except Exception as e:
        print(f"Erro ao verificar favorito: {str(e)}")
        return jsonify({'error': f'Erro ao verificar favorito: {str(e)}'}), 500

@content_bp.route('/details/<content_type>/<content_id>', methods=['GET'])
def get_content_details(content_type, content_id):
    try:
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
        print(f"Erro ao buscar detalhes: {str(e)}")
        return jsonify({'error': f'Erro ao buscar detalhes: {str(e)}'}), 500

@content_bp.route('/preferences', methods=['GET'])
@jwt_required()
def get_user_preferences():
    try:
        user_id = get_jwt_identity()
        
        preferences = UserPreference.query.filter_by(user_id=user_id).first()
        
        if not preferences:
            # Criar preferências padrão
            preferences = UserPreference(
                user_id=user_id,
                favorite_categories='["movies", "tv", "games"]',
                favorite_genres='[]'
            )
            db.session.add(preferences)
            db.session.commit()
        
        return jsonify(preferences.to_dict()), 200
        
    except Exception as e:
        print(f"Erro ao buscar preferências: {str(e)}")
        return jsonify({'error': f'Erro ao buscar preferências: {str(e)}'}), 500

@content_bp.route('/preferences', methods=['PUT'])
@jwt_required()
def update_user_preferences():
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        preferences = UserPreference.query.filter_by(user_id=user_id).first()
        
        if not preferences:
            preferences = UserPreference(user_id=user_id)
            db.session.add(preferences)
        
        # Atualizar campos
        if 'favorite_genres' in data:
            preferences.set_genres(data['favorite_genres'])
        
        if 'favorite_categories' in data:
            preferences.set_categories(data['favorite_categories'])
        
        if 'language' in data:
            preferences.language = data['language']
        
        if 'notifications_enabled' in data:
            preferences.notifications_enabled = data['notifications_enabled']
        
        db.session.commit()
        
        return jsonify({
            'message': 'Preferências atualizadas com sucesso',
            'preferences': preferences.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao atualizar preferências: {str(e)}")
        return jsonify({'error': f'Erro ao atualizar preferências: {str(e)}'}), 500

