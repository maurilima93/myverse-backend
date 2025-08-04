from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models.database import db, User, Friendship, Favorite
from datetime import datetime
import json

friends_bp = Blueprint('friends', __name__)

@friends_bp.route('/search', methods=['GET'])
@jwt_required()
def search_users():
    """Buscar usuários para adicionar como amigos"""
    try:
        user_id = get_jwt_identity()
        query = request.args.get('q', '').strip()
        
        if not query:
            return jsonify({'error': 'Parâmetro de busca é obrigatório'}), 400
        
        if len(query) < 2:
            return jsonify({'error': 'Busca deve ter pelo menos 2 caracteres'}), 400
        
        # Buscar usuários por username ou email (excluindo o próprio usuário)
        users = User.query.filter(
            User.id != user_id,
            User.is_active == True,
            db.or_(
                User.username.ilike(f'%{query}%'),
                User.email.ilike(f'%{query}%')
            )
        ).limit(20).all()
        
        # Verificar status de amizade para cada usuário
        results = []
        for user in users:
            # Verificar se já são amigos ou há solicitação pendente
            friendship = Friendship.query.filter(
                db.or_(
                    db.and_(Friendship.requester_id == user_id, Friendship.requested_id == user.id),
                    db.and_(Friendship.requester_id == user.id, Friendship.requested_id == user_id)
                )
            ).first()
            
            user_dict = user.to_dict()
            user_dict['friendship_status'] = friendship.status if friendship else 'none'
            user_dict['friendship_id'] = friendship.id if friendship else None
            
            results.append(user_dict)
        
        return jsonify({
            'users': results,
            'total': len(results),
            'query': query
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Erro na busca: {str(e)}'}), 500

@friends_bp.route('/request', methods=['POST'])
@jwt_required()
def send_friend_request():
    """Enviar solicitação de amizade"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data or 'user_id' not in data:
            return jsonify({'error': 'user_id é obrigatório'}), 400
        
        requested_id = data['user_id']
        
        # Validações
        if requested_id == user_id:
            return jsonify({'error': 'Não é possível adicionar a si mesmo'}), 400
        
        # Verificar se usuário existe
        requested_user = User.query.get(requested_id)
        if not requested_user:
            return jsonify({'error': 'Usuário não encontrado'}), 404
        
        if not requested_user.is_active:
            return jsonify({'error': 'Usuário não está ativo'}), 400
        
        # Verificar se já existe amizade ou solicitação
        existing = Friendship.query.filter(
            db.or_(
                db.and_(Friendship.requester_id == user_id, Friendship.requested_id == requested_id),
                db.and_(Friendship.requester_id == requested_id, Friendship.requested_id == user_id)
            )
        ).first()
        
        if existing:
            if existing.status == 'accepted':
                return jsonify({'error': 'Vocês já são amigos'}), 409
            elif existing.status == 'pending':
                return jsonify({'error': 'Solicitação já enviada'}), 409
            elif existing.status == 'blocked':
                return jsonify({'error': 'Não é possível enviar solicitação'}), 403
        
        # Criar solicitação de amizade
        friendship = Friendship(
            requester_id=user_id,
            requested_id=requested_id,
            status='pending'
        )
        
        db.session.add(friendship)
        db.session.commit()
        
        return jsonify({
            'message': 'Solicitação de amizade enviada!',
            'friendship': friendship.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao enviar solicitação: {str(e)}'}), 500

@friends_bp.route('/requests', methods=['GET'])
@jwt_required()
def get_friend_requests():
    """Listar solicitações de amizade recebidas"""
    try:
        user_id = get_jwt_identity()
        
        # Buscar solicitações pendentes recebidas
        requests = Friendship.query.filter_by(
            requested_id=user_id,
            status='pending'
        ).order_by(Friendship.created_at.desc()).all()
        
        return jsonify({
            'requests': [req.to_dict() for req in requests],
            'total': len(requests)
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Erro ao buscar solicitações: {str(e)}'}), 500

@friends_bp.route('/requests/<int:friendship_id>/accept', methods=['POST'])
@jwt_required()
def accept_friend_request(friendship_id):
    """Aceitar solicitação de amizade"""
    try:
        user_id = get_jwt_identity()
        
        # Buscar solicitação
        friendship = Friendship.query.filter_by(
            id=friendship_id,
            requested_id=user_id,
            status='pending'
        ).first()
        
        if not friendship:
            return jsonify({'error': 'Solicitação não encontrada'}), 404
        
        # Aceitar solicitação
        friendship.status = 'accepted'
        friendship.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Solicitação aceita! Vocês agora são amigos.',
            'friendship': friendship.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao aceitar solicitação: {str(e)}'}), 500

@friends_bp.route('/requests/<int:friendship_id>/reject', methods=['POST'])
@jwt_required()
def reject_friend_request(friendship_id):
    """Rejeitar solicitação de amizade"""
    try:
        user_id = get_jwt_identity()
        
        # Buscar solicitação
        friendship = Friendship.query.filter_by(
            id=friendship_id,
            requested_id=user_id,
            status='pending'
        ).first()
        
        if not friendship:
            return jsonify({'error': 'Solicitação não encontrada'}), 404
        
        # Rejeitar solicitação
        friendship.status = 'rejected'
        friendship.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Solicitação rejeitada.',
            'friendship': friendship.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao rejeitar solicitação: {str(e)}'}), 500

@friends_bp.route('/', methods=['GET'])
@jwt_required()
def get_friends():
    """Listar amigos do usuário"""
    try:
        user_id = get_jwt_identity()
        
        # Buscar amizades aceitas
        friendships = Friendship.query.filter(
            db.or_(
                db.and_(Friendship.requester_id == user_id, Friendship.status == 'accepted'),
                db.and_(Friendship.requested_id == user_id, Friendship.status == 'accepted')
            )
        ).order_by(Friendship.updated_at.desc()).all()
        
        friends = []
        for friendship in friendships:
            # Determinar qual é o amigo (não o usuário atual)
            friend_id = friendship.requested_id if friendship.requester_id == user_id else friendship.requester_id
            friend = User.query.get(friend_id)
            
            if friend and friend.is_active:
                friend_dict = friend.to_dict()
                friend_dict['friendship_id'] = friendship.id
                friend_dict['friends_since'] = friendship.updated_at.isoformat()
                friends.append(friend_dict)
        
        return jsonify({
            'friends': friends,
            'total': len(friends)
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Erro ao buscar amigos: {str(e)}'}), 500

@friends_bp.route('/<int:friendship_id>', methods=['DELETE'])
@jwt_required()
def remove_friend(friendship_id):
    """Remover amigo"""
    try:
        user_id = get_jwt_identity()
        
        # Buscar amizade
        friendship = Friendship.query.filter(
            Friendship.id == friendship_id,
            db.or_(
                Friendship.requester_id == user_id,
                Friendship.requested_id == user_id
            ),
            Friendship.status == 'accepted'
        ).first()
        
        if not friendship:
            return jsonify({'error': 'Amizade não encontrada'}), 404
        
        # Remover amizade
        db.session.delete(friendship)
        db.session.commit()
        
        return jsonify({
            'message': 'Amigo removido com sucesso.'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao remover amigo: {str(e)}'}), 500

@friends_bp.route('/<int:friend_id>/profile', methods=['GET'])
@jwt_required()
def get_friend_profile(friend_id):
    """Ver perfil de um amigo"""
    try:
        user_id = get_jwt_identity()
        
        # Verificar se são amigos
        friendship = Friendship.query.filter(
            db.or_(
                db.and__(Friendship.requester_id == user_id, Friendship.requested_id == friend_id),
                db.and__(Friendship.requester_id == friend_id, Friendship.requested_id == user_id)
            ),
            Friendship.status == 'accepted'
        ).first()
        
        if not friendship:
            return jsonify({'error': 'Vocês não são amigos'}), 403
        
        # Buscar perfil do amigo
        friend = User.query.get(friend_id)
        if not friend or not friend.is_active:
            return jsonify({'error': 'Usuário não encontrado'}), 404
        
        # Buscar favoritos do amigo (públicos)
        favorites = Favorite.query.filter_by(user_id=friend_id).order_by(Favorite.created_at.desc()).limit(20).all()
        
        # Agrupar favoritos por tipo
        favorites_by_type = {
            'movies': [],
            'tv': [],
            'games': []
        }
        
        for fav in favorites:
            if fav.content_type in favorites_by_type:
                favorites_by_type[fav.content_type].append(fav.to_dict())
        
        # Calcular estatísticas
        stats = {
            'total_favorites': len(favorites),
            'movies_count': len(favorites_by_type['movies']),
            'tv_count': len(favorites_by_type['tv']),
            'games_count': len(favorites_by_type['games'])
        }
        
        # Gêneros favoritos
        all_genres = []
        for fav in favorites:
            if fav.genres:
                try:
                    genres = json.loads(fav.genres)
                    all_genres.extend(genres)
                except:
                    pass
        
        from collections import Counter
        top_genres = [genre for genre, count in Counter(all_genres).most_common(5)]
        
        return jsonify({
            'profile': friend.to_dict(),
            'favorites': favorites_by_type,
            'stats': stats,
            'top_genres': top_genres,
            'friends_since': friendship.updated_at.isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Erro ao buscar perfil: {str(e)}'}), 500

@friends_bp.route('/suggestions', methods=['GET'])
@jwt_required()
def get_friend_suggestions():
    """Sugerir amigos baseado em gostos similares"""
    try:
        user_id = get_jwt_identity()
        
        # Buscar favoritos do usuário
        user_favorites = Favorite.query.filter_by(user_id=user_id).all()
        
        if not user_favorites:
            return jsonify({
                'suggestions': [],
                'message': 'Adicione alguns favoritos para receber sugestões de amigos!'
            }), 200
        
        # Extrair gêneros dos favoritos do usuário
        user_genres = []
        for fav in user_favorites:
            if fav.genres:
                try:
                    genres = json.loads(fav.genres)
                    user_genres.extend(genres)
                except:
                    pass
        
        if not user_genres:
            return jsonify({
                'suggestions': [],
                'message': 'Não foi possível encontrar sugestões no momento.'
            }), 200
        
        # Buscar usuários com gostos similares
        from collections import Counter
        user_genre_counts = Counter(user_genres)
        top_user_genres = set([genre for genre, count in user_genre_counts.most_common(10)])
        
        # Buscar outros usuários
        other_users = User.query.filter(
            User.id != user_id,
            User.is_active == True
        ).all()
        
        suggestions = []
        
        for other_user in other_users:
            # Verificar se já são amigos ou há solicitação
            existing = Friendship.query.filter(
                db.or_(
                    db.and__(Friendship.requester_id == user_id, Friendship.requested_id == other_user.id),
                    db.and__(Friendship.requester_id == other_user.id, Friendship.requested_id == user_id)
                )
            ).first()
            
            if existing:
                continue  # Pular se já são amigos ou há solicitação
            
            # Buscar favoritos do outro usuário
            other_favorites = Favorite.query.filter_by(user_id=other_user.id).all()
            
            if not other_favorites:
                continue
            
            # Extrair gêneros do outro usuário
            other_genres = []
            for fav in other_favorites:
                if fav.genres:
                    try:
                        genres = json.loads(fav.genres)
                        other_genres.extend(genres)
                    except:
                        pass
            
            if not other_genres:
                continue
            
            # Calcular similaridade
            other_genre_set = set(other_genres)
            common_genres = top_user_genres.intersection(other_genre_set)
            similarity_score = len(common_genres) / len(top_user_genres.union(other_genre_set))
            
            if similarity_score > 0.2:  # Pelo menos 20% de similaridade
                user_dict = other_user.to_dict()
                user_dict['similarity_score'] = round(similarity_score * 100, 1)
                user_dict['common_genres'] = list(common_genres)
                user_dict['total_favorites'] = len(other_favorites)
                suggestions.append(user_dict)
        
        # Ordenar por similaridade
        suggestions.sort(key=lambda x: x['similarity_score'], reverse=True)
        
        return jsonify({
            'suggestions': suggestions[:10],  # Limitar a 10 sugestões
            'total': len(suggestions)
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Erro ao buscar sugestões: {str(e)}'}), 500

