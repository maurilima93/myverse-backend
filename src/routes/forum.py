from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models.database import db, User, ForumPost, ForumReply

forum_bp = Blueprint('forum', __name__)

FORUM_CATEGORIES = [
    'filmes',
    'series',
    'jogos',
    'livros',
    'discussao-geral',
    'recomendacoes',
    'noticias'
]

@forum_bp.route('/posts', methods=['GET'])
def get_posts():
    try:
        category = request.args.get('category')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        
        query = ForumPost.query
        
        if category and category in FORUM_CATEGORIES:
            query = query.filter_by(category=category)
        
        posts = query.order_by(ForumPost.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'posts': [post.to_dict() for post in posts.items],
            'total': posts.total,
            'pages': posts.pages,
            'current_page': page,
            'has_next': posts.has_next,
            'has_prev': posts.has_prev
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Erro interno do servidor: {str(e)}'}), 500

@forum_bp.route('/posts', methods=['POST'])
@jwt_required()
def create_post():
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data or not all(k in data for k in ('title', 'content', 'category')):
            return jsonify({'error': 'title, content e category são obrigatórios'}), 400
        
        title = data['title'].strip()
        content = data['content'].strip()
        category = data['category'].strip()
        
        # Validações
        if len(title) < 5:
            return jsonify({'error': 'Título deve ter pelo menos 5 caracteres'}), 400
        
        if len(content) < 10:
            return jsonify({'error': 'Conteúdo deve ter pelo menos 10 caracteres'}), 400
        
        if category not in FORUM_CATEGORIES:
            return jsonify({'error': 'Categoria inválida'}), 400
        
        # Criar post
        post = ForumPost(
            user_id=current_user_id,
            title=title,
            content=content,
            category=category
        )
        
        db.session.add(post)
        db.session.commit()
        
        return jsonify({
            'message': 'Post criado com sucesso!',
            'post': post.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro interno do servidor: {str(e)}'}), 500

@forum_bp.route('/posts/<int:post_id>', methods=['GET'])
def get_post(post_id):
    try:
        post = ForumPost.query.get_or_404(post_id)
        
        # Buscar replies
        replies = ForumReply.query.filter_by(post_id=post_id).order_by(ForumReply.created_at.asc()).all()
        
        post_dict = post.to_dict()
        post_dict['replies'] = [reply.to_dict() for reply in replies]
        
        return jsonify({'post': post_dict}), 200
        
    except Exception as e:
        return jsonify({'error': f'Erro interno do servidor: {str(e)}'}), 500

@forum_bp.route('/posts/<int:post_id>/replies', methods=['POST'])
@jwt_required()
def create_reply(post_id):
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data or 'content' not in data:
            return jsonify({'error': 'content é obrigatório'}), 400
        
        content = data['content'].strip()
        
        if len(content) < 5:
            return jsonify({'error': 'Resposta deve ter pelo menos 5 caracteres'}), 400
        
        # Verificar se post existe
        post = ForumPost.query.get_or_404(post_id)
        
        # Criar reply
        reply = ForumReply(
            post_id=post_id,
            user_id=current_user_id,
            content=content
        )
        
        db.session.add(reply)
        db.session.commit()
        
        return jsonify({
            'message': 'Resposta criada com sucesso!',
            'reply': reply.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro interno do servidor: {str(e)}'}), 500

@forum_bp.route('/posts/<int:post_id>', methods=['PUT'])
@jwt_required()
def update_post(post_id):
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        post = ForumPost.query.get_or_404(post_id)
        
        # Verificar se é o autor
        if post.user_id != current_user_id:
            return jsonify({'error': 'Você só pode editar seus próprios posts'}), 403
        
        if 'title' in data:
            title = data['title'].strip()
            if len(title) < 5:
                return jsonify({'error': 'Título deve ter pelo menos 5 caracteres'}), 400
            post.title = title
        
        if 'content' in data:
            content = data['content'].strip()
            if len(content) < 10:
                return jsonify({'error': 'Conteúdo deve ter pelo menos 10 caracteres'}), 400
            post.content = content
        
        if 'category' in data:
            category = data['category'].strip()
            if category not in FORUM_CATEGORIES:
                return jsonify({'error': 'Categoria inválida'}), 400
            post.category = category
        
        db.session.commit()
        
        return jsonify({
            'message': 'Post atualizado com sucesso!',
            'post': post.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro interno do servidor: {str(e)}'}), 500

@forum_bp.route('/posts/<int:post_id>', methods=['DELETE'])
@jwt_required()
def delete_post(post_id):
    try:
        current_user_id = get_jwt_identity()
        
        post = ForumPost.query.get_or_404(post_id)
        
        # Verificar se é o autor
        if post.user_id != current_user_id:
            return jsonify({'error': 'Você só pode deletar seus próprios posts'}), 403
        
        db.session.delete(post)
        db.session.commit()
        
        return jsonify({'message': 'Post deletado com sucesso!'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro interno do servidor: {str(e)}'}), 500

@forum_bp.route('/categories', methods=['GET'])
def get_categories():
    return jsonify({
        'categories': [
            {'id': 'filmes', 'name': 'Filmes', 'description': 'Discussões sobre filmes'},
            {'id': 'series', 'name': 'Séries', 'description': 'Discussões sobre séries de TV'},
            {'id': 'jogos', 'name': 'Jogos', 'description': 'Discussões sobre videogames'},
            {'id': 'livros', 'name': 'Livros', 'description': 'Discussões sobre livros'},
            {'id': 'discussao-geral', 'name': 'Discussão Geral', 'description': 'Tópicos gerais'},
            {'id': 'recomendacoes', 'name': 'Recomendações', 'description': 'Recomende conteúdo'},
            {'id': 'noticias', 'name': 'Notícias', 'description': 'Últimas notícias do entretenimento'}
        ]
    }), 200

