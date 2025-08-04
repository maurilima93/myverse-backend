from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models.database import db, User, Favorite
from src.services.tmdb_service import TMDbService
from src.services.igdb_service import IGDBService
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
        
        if len(query) < 2:
            return jsonify({'error': 'Busca deve ter pelo menos 2 caracteres'}), 400
        
        results = []
        
        # Buscar filmes
        try:
            movies = tmdb_service.search_movies(query)
            results.extend(movies)
        except Exception as e:
            print(f"Erro ao buscar filmes: {e}")
        
        # Buscar séries
        try:
            tv_shows = tmdb_service.search_tv_shows(query)
            results.extend(tv_shows)
        except Exception as e:
            print(f"Erro ao buscar séries: {e}")
        
        # Buscar jogos
        try:
            games = igdb_service.search_games(query)
            results.extend(games)
        except Exception as e:
            print(f"Erro ao buscar jogos: {e}")
        
        # Ordenar por relevância (rating/popularity)
        results.sort(key=lambda x: x.get('rating', 0), reverse=True)
        
        return jsonify({
            'results': results[:50],  # Limitar a 50 resultados
            'total': len(results),
            'query': query
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Erro na busca: {str(e)}'}), 500

@content_bp.route('/favorites', methods=['GET'])
@jwt_required()
def get_favorites():
    try:
        user_id = get_jwt_identity()
        
        # Buscar favoritos do usuário
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
        
        # Validar dados obrigatórios
        required_fields = ['content_type', 'content_id', 'title']
        if not data or not all(k in data for k in required_fields):
            return jsonify({'error': 'content_type, content_id e title são obrigatórios'}), 400
        
        content_type = data['content_type']
        content_id = str(data['content_id'])
        title = data['title']
        
        # Validar tipo de conteúdo
        if content_type not in ['movie', 'tv', 'game']:
            return jsonify({'error': 'content_type deve ser movie, tv ou game'}), 400
        
        # Verificar se já existe
        existing = Favorite.query.filter_by(
            user_id=user_id,
            content_type=content_type,
            content_id=content_id
        ).first()
        
        if existing:
            return jsonify({'error': 'Item já está nos favoritos'}), 409
        
        # Criar favorito
        favorite = Favorite(
            user_id=user_id,
            content_type=content_type,
            content_id=content_id,
            title=title,
            poster_url=data.get('poster_url'),
            rating=data.get('rating'),
            genres=json.dumps(data.get('genres', [])),
            release_date=data.get('release_date')
        )
        
        db.session.add(favorite)
        db.session.commit()
        
        return jsonify({
            'message': 'Adicionado aos favoritos!',
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
        
        # Buscar favorito
        favorite = Favorite.query.filter_by(id=favorite_id, user_id=user_id).first()
        
        if not favorite:
            return jsonify({'error': 'Favorito não encontrado'}), 404
        
        db.session.delete(favorite)
        db.session.commit()
        
        return jsonify({
            'message': 'Removido dos favoritos!'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao remover favorito: {str(e)}'}), 500

@content_bp.route('/favorites/check', methods=['POST'])
@jwt_required()
def check_favorite():
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data or not all(k in data for k in ['content_type', 'content_id']):
            return jsonify({'error': 'content_type e content_id são obrigatórios'}), 400
        
        content_type = data['content_type']
        content_id = str(data['content_id'])
        
        # Verificar se existe
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
        return jsonify({'error': f'Erro ao verificar favorito: {str(e)}'}), 500

@content_bp.route('/recommendations', methods=['GET'])
@jwt_required()
def get_recommendations():
    try:
        user_id = get_jwt_identity()
        
        # Buscar favoritos do usuário para gerar recomendações
        favorites = Favorite.query.filter_by(user_id=user_id).all()
        
        if not favorites:
            # Se não tem favoritos, retornar conteúdo popular
            recommendations = []
            
            try:
                popular_movies = tmdb_service.get_popular_movies()
                recommendations.extend(popular_movies[:10])
            except:
                pass
            
            try:
                popular_tv = tmdb_service.get_popular_tv_shows()
                recommendations.extend(popular_tv[:10])
            except:
                pass
            
            try:
                popular_games = igdb_service.get_popular_games()
                recommendations.extend(popular_games[:10])
            except:
                pass
            
            return jsonify({
                'recommendations': recommendations,
                'based_on': 'popular_content'
            }), 200
        
        # Gerar recomendações baseadas nos favoritos
        recommendations = []
        favorite_genres = []
        
        # Extrair gêneros dos favoritos
        for fav in favorites:
            if fav.genres:
                try:
                    genres = json.loads(fav.genres)
                    favorite_genres.extend(genres)
                except:
                    pass
        
        # Contar gêneros mais frequentes
        from collections import Counter
        genre_counts = Counter(favorite_genres)
        top_genres = [genre for genre, count in genre_counts.most_common(3)]
        
        # Buscar conteúdo similar
        for genre in top_genres:
            try:
                similar_movies = tmdb_service.get_movies_by_genre(genre)
                recommendations.extend(similar_movies[:5])
            except:
                pass
            
            try:
                similar_tv = tmdb_service.get_tv_shows_by_genre(genre)
                recommendations.extend(similar_tv[:5])
            except:
                pass
        
        # Remover duplicatas e favoritos já existentes
        favorite_ids = {f"{fav.content_type}_{fav.content_id}" for fav in favorites}
        unique_recommendations = []
        seen_ids = set()
        
        for rec in recommendations:
            rec_id = f"{rec['type']}_{rec['id']}"
            if rec_id not in favorite_ids and rec_id not in seen_ids:
                unique_recommendations.append(rec)
                seen_ids.add(rec_id)
        
        return jsonify({
            'recommendations': unique_recommendations[:20],
            'based_on': 'user_preferences',
            'favorite_genres': top_genres
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Erro ao gerar recomendações: {str(e)}'}), 500

