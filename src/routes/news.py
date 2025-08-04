from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models.database import db, News, User
from datetime import datetime

news_bp = Blueprint('news', __name__)

@news_bp.route('/', methods=['GET'])
def get_news():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        category = request.args.get('category', 'all')
        featured_only = request.args.get('featured', False, type=bool)
        
        query = News.query.filter_by(is_published=True)
        
        if category != 'all':
            query = query.filter_by(category=category)
            
        if featured_only:
            query = query.filter_by(is_featured=True)
        
        query = query.order_by(News.published_at.desc())
        
        pagination = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        news_list = [news.to_dict() for news in pagination.items]
        
        return jsonify({
            'news': news_list,
            'pagination': {
                'page': page,
                'pages': pagination.pages,
                'per_page': per_page,
                'total': pagination.total,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Erro ao buscar notícias: {str(e)}'}), 500

@news_bp.route('/<int:news_id>', methods=['GET'])
def get_news_by_id(news_id):
    try:
        news = News.query.filter_by(id=news_id, is_published=True).first()
        
        if not news:
            return jsonify({'error': 'Notícia não encontrada'}), 404
        
        return jsonify({
            'news': news.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Erro ao buscar notícia: {str(e)}'}), 500

@news_bp.route('/', methods=['POST'])
@jwt_required()
def create_news():
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        # Verificar se o usuário é admin (você pode implementar um sistema de roles)
        # Por enquanto, qualquer usuário logado pode criar notícias
        
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Dados não fornecidos'}), 400
        
        required_fields = ['title', 'content']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Campo {field} é obrigatório'}), 400
        
        news = News(
            title=data['title'],
            content=data['content'],
            summary=data.get('summary', ''),
            image_url=data.get('image_url', ''),
            source_url=data.get('source_url', ''),
            category=data.get('category', 'geral'),
            is_featured=data.get('is_featured', False),
            author_id=user_id,
            published_at=datetime.utcnow()
        )
        
        db.session.add(news)
        db.session.commit()
        
        return jsonify({
            'message': 'Notícia criada com sucesso',
            'news': news.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao criar notícia: {str(e)}'}), 500

@news_bp.route('/<int:news_id>', methods=['PUT'])
@jwt_required()
def update_news(news_id):
    try:
        user_id = get_jwt_identity()
        
        news = News.query.get(news_id)
        
        if not news:
            return jsonify({'error': 'Notícia não encontrada'}), 404
        
        # Verificar se o usuário é o autor ou admin
        if news.author_id != user_id:
            return jsonify({'error': 'Sem permissão para editar esta notícia'}), 403
        
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Dados não fornecidos'}), 400
        
        # Atualizar campos fornecidos
        if 'title' in data:
            news.title = data['title']
        if 'content' in data:
            news.content = data['content']
        if 'summary' in data:
            news.summary = data['summary']
        if 'image_url' in data:
            news.image_url = data['image_url']
        if 'source_url' in data:
            news.source_url = data['source_url']
        if 'category' in data:
            news.category = data['category']
        if 'is_featured' in data:
            news.is_featured = data['is_featured']
        if 'is_published' in data:
            news.is_published = data['is_published']
        
        news.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'message': 'Notícia atualizada com sucesso',
            'news': news.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao atualizar notícia: {str(e)}'}), 500

@news_bp.route('/<int:news_id>', methods=['DELETE'])
@jwt_required()
def delete_news(news_id):
    try:
        user_id = get_jwt_identity()
        
        news = News.query.get(news_id)
        
        if not news:
            return jsonify({'error': 'Notícia não encontrada'}), 404
        
        # Verificar se o usuário é o autor ou admin
        if news.author_id != user_id:
            return jsonify({'error': 'Sem permissão para deletar esta notícia'}), 403
        
        db.session.delete(news)
        db.session.commit()
        
        return jsonify({'message': 'Notícia deletada com sucesso'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao deletar notícia: {str(e)}'}), 500

@news_bp.route('/categories', methods=['GET'])
def get_categories():
    try:
        categories = [
            {'id': 'geral', 'name': 'Geral', 'description': 'Notícias gerais do entretenimento'},
            {'id': 'movies', 'name': 'Filmes', 'description': 'Notícias sobre filmes'},
            {'id': 'tv', 'name': 'Séries', 'description': 'Notícias sobre séries de TV'},
            {'id': 'games', 'name': 'Jogos', 'description': 'Notícias sobre jogos'},
        ]
        
        return jsonify({
            'categories': categories
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Erro ao buscar categorias: {str(e)}'}), 500

