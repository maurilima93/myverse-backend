from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.database import db, User, ForumPost, ForumReply
from datetime import datetime

forum_bp = Blueprint('forum', __name__)

# Categorias disponíveis
CATEGORIES = [
    'filmes',
    'series',
    'jogos',
    'livros',
    'discussao-geral',
    'recomendacoes',
    'noticias'
]

@forum_bp.route('/categories', methods=['GET'])
def get_categories():
    """Retorna categorias disponíveis do fórum"""
    return jsonify({
        'categories': CATEGORIES
    }), 200

@forum_bp.route('/posts', methods=['GET'])
def get_posts():
    """Lista posts do fórum com paginação"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        category = request.args.get('category', '').strip()
        
        # Limitar per_page
        per_page = min(per_page, 50)
        
        # Query base
        query = ForumPost.query.filter_by(is_active=True)
        
        # Filtrar por categoria se especificada
        if category and category in CATEGORIES:
            query = query.filter_by(category=category)
        
        # Ordenar por data de criação (mais recentes primeiro)
        query = query.order_by(ForumPost.created_at.desc())
        
        # Paginação
        posts = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        return jsonify({
            'posts': [post.to_dict() for post in posts.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': posts.total,
                'pages': posts.pages,
                'has_next': posts.has_next,
                'has_prev': posts.has_prev
            },
            'category': category if category else 'all'
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Erro ao buscar posts: {str(e)}'}), 500

@forum_bp.route('/posts', methods=['POST'])
@jwt_required()
def create_post():
    """Criar novo post no fórum"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validar dados obrigatórios
        if not data or not all(k in data for k in ['title', 'content', 'category']):
            return jsonify({'error': 'Title, content e category são obrigatórios'}), 400
        
        title = data['title'].strip()
        content = data['content'].strip()
        category = data['category'].strip()
        
        # Validações
        if len(title) < 5:
            return jsonify({'error': 'Título deve ter pelo menos 5 caracteres'}), 400
        
        if len(title) > 255:
            return jsonify({'error': 'Título deve ter no máximo 255 caracteres'}), 400
        
        if len(content) < 10:
            return jsonify({'error': 'Conteúdo deve ter pelo menos 10 caracteres'}), 400
        
        if len(content) > 10000:
            return jsonify({'error': 'Conteúdo deve ter no máximo 10.000 caracteres'}), 400
        
        if category not in CATEGORIES:
            return jsonify({'error': f'Categoria deve ser uma das: {", ".join(CATEGORIES)}'}), 400
        
        # Verificar se usuário existe
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'Usuário não encontrado'}), 404
        
        # Criar post
        post = ForumPost(
            title=title,
            content=content,
            category=category,
            author_id=user_id
        )
        
        db.session.add(post)
        db.session.commit()
        
        return jsonify({
            'message': 'Post criado com sucesso!',
            'post': post.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao criar post: {str(e)}'}), 500

@forum_bp.route('/posts/<int:post_id>', methods=['GET'])
def get_post(post_id):
    """Buscar post específico com replies"""
    try:
        post = ForumPost.query.filter_by(id=post_id, is_active=True).first()
        
        if not post:
            return jsonify({'error': 'Post não encontrado'}), 404
        
        # Buscar replies
        replies = ForumReply.query.filter_by(
            post_id=post_id, 
            is_active=True
        ).order_by(ForumReply.created_at.asc()).all()
        
        post_dict = post.to_dict()
        post_dict['replies'] = [reply.to_dict() for reply in replies]
        
        return jsonify({
            'post': post_dict
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Erro ao buscar post: {str(e)}'}), 500

@forum_bp.route('/posts/<int:post_id>/replies', methods=['POST'])
@jwt_required()
def create_reply(post_id):
    """Criar reply para um post"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validar dados obrigatórios
        if not data or 'content' not in data:
            return jsonify({'error': 'Content é obrigatório'}), 400
        
        content = data['content'].strip()
        
        # Validações
        if len(content) < 5:
            return jsonify({'error': 'Reply deve ter pelo menos 5 caracteres'}), 400
        
        if len(content) > 5000:
            return jsonify({'error': 'Reply deve ter no máximo 5.000 caracteres'}), 400
        
        # Verificar se post existe
        post = ForumPost.query.filter_by(id=post_id, is_active=True).first()
        if not post:
            return jsonify({'error': 'Post não encontrado'}), 404
        
        # Verificar se usuário existe
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'Usuário não encontrado'}), 404
        
        # Criar reply
        reply = ForumReply(
            content=content,
            post_id=post_id,
            author_id=user_id
        )
        
        db.session.add(reply)
        db.session.commit()
        
        return jsonify({
            'message': 'Reply criado com sucesso!',
            'reply': reply.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao criar reply: {str(e)}'}), 500

@forum_bp.route('/posts/<int:post_id>', methods=['PUT'])
@jwt_required()
def update_post(post_id):
    """Atualizar post (apenas autor pode editar)"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # Buscar post
        post = ForumPost.query.filter_by(id=post_id, is_active=True).first()
        if not post:
            return jsonify({'error': 'Post não encontrado'}), 404
        
        # Verificar se é o autor
        if post.author_id != user_id:
            return jsonify({'error': 'Apenas o autor pode editar o post'}), 403
        
        # Atualizar campos se fornecidos
        if 'title' in data:
            title = data['title'].strip()
            if len(title) < 5 or len(title) > 255:
                return jsonify({'error': 'Título deve ter entre 5 e 255 caracteres'}), 400
            post.title = title
        
        if 'content' in data:
            content = data['content'].strip()
            if len(content) < 10 or len(content) > 10000:
                return jsonify({'error': 'Conteúdo deve ter entre 10 e 10.000 caracteres'}), 400
            post.content = content
        
        if 'category' in data:
            category = data['category'].strip()
            if category not in CATEGORIES:
                return jsonify({'error': f'Categoria deve ser uma das: {", ".join(CATEGORIES)}'}), 400
            post.category = category
        
        post.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Post atualizado com sucesso!',
            'post': post.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao atualizar post: {str(e)}'}), 500

@forum_bp.route('/posts/<int:post_id>', methods=['DELETE'])
@jwt_required()
def delete_post(post_id):
    """Deletar post (apenas autor pode deletar)"""
    try:
        user_id = get_jwt_identity()
        
        # Buscar post
        post = ForumPost.query.filter_by(id=post_id, is_active=True).first()
        if not post:
            return jsonify({'error': 'Post não encontrado'}), 404
        
        # Verificar se é o autor
        if post.author_id != user_id:
            return jsonify({'error': 'Apenas o autor pode deletar o post'}), 403
        
        # Soft delete
        post.is_active = False
        post.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Post deletado com sucesso!'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao deletar post: {str(e)}'}), 500

@forum_bp.route('/replies/<int:reply_id>', methods=['PUT'])
@jwt_required()
def update_reply(reply_id):
    """Atualizar reply (apenas autor pode editar)"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # Buscar reply
        reply = ForumReply.query.filter_by(id=reply_id, is_active=True).first()
        if not reply:
            return jsonify({'error': 'Reply não encontrado'}), 404
        
        # Verificar se é o autor
        if reply.author_id != user_id:
            return jsonify({'error': 'Apenas o autor pode editar o reply'}), 403
        
        # Validar conteúdo
        if 'content' not in data:
            return jsonify({'error': 'Content é obrigatório'}), 400
        
        content = data['content'].strip()
        if len(content) < 5 or len(content) > 5000:
            return jsonify({'error': 'Reply deve ter entre 5 e 5.000 caracteres'}), 400
        
        reply.content = content
        reply.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Reply atualizado com sucesso!',
            'reply': reply.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao atualizar reply: {str(e)}'}), 500

@forum_bp.route('/replies/<int:reply_id>', methods=['DELETE'])
@jwt_required()
def delete_reply(reply_id):
    """Deletar reply (apenas autor pode deletar)"""
    try:
        user_id = get_jwt_identity()
        
        # Buscar reply
        reply = ForumReply.query.filter_by(id=reply_id, is_active=True).first()
        if not reply:
            return jsonify({'error': 'Reply não encontrado'}), 404
        
        # Verificar se é o autor
        if reply.author_id != user_id:
            return jsonify({'error': 'Apenas o autor pode deletar o reply'}), 403
        
        # Soft delete
        reply.is_active = False
        reply.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Reply deletado com sucesso!'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao deletar reply: {str(e)}'}), 500

