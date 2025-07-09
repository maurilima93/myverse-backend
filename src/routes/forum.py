from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models.database import db, User, ForumPost, ForumReply

forum_bp = Blueprint('forum', __name__)

@forum_bp.route('/posts', methods=['GET'])
def get_posts():
    try:
        category = request.args.get('category', '')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        
        query = ForumPost.query
        
        if category:
            query = query.filter_by(category=category)
        
        posts = query.order_by(ForumPost.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'posts': [post.to_dict() for post in posts.items],
            'total': posts.total,
            'pages': posts.pages,
            'current_page': page,
            'per_page': per_page
        }), 200
        
    except Exception as e:
        print(f"Erro ao buscar posts: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@forum_bp.route('/posts', methods=['POST'])
@jwt_required()
def create_post():
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Dados não fornecidos'}), 400
        
        title = data.get('title', '').strip()
        content = data.get('content', '').strip()
        category = data.get('category', '').strip()
        
        if not all([title, content, category]):
            return jsonify({'error': 'title, content e category são obrigatórios'}), 400
        
        if len(title) < 5 or len(title) > 255:
            return jsonify({'error': 'Título deve ter entre 5 e 255 caracteres'}), 400
        
        if len(content) < 10:
            return jsonify({'error': 'Conteúdo deve ter pelo menos 10 caracteres'}), 400
        
        valid_categories = ['movies', 'tv_shows', 'games', 'general', 'recommendations']
        if category not in valid_categories:
            return jsonify({'error': f'Categoria deve ser uma de: {", ".join(valid_categories)}'}), 400
        
        post = ForumPost(
            title=title,
            content=content,
            category=category,
            author_id=current_user_id
        )
        
        db.session.add(post)
        db.session.commit()
        
        return jsonify({
            'message': 'Post criado com sucesso',
            'post': post.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao criar post: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@forum_bp.route('/posts/<int:post_id>', methods=['GET'])
def get_post(post_id):
    try:
        post = ForumPost.query.get(post_id)
        
        if not post:
            return jsonify({'error': 'Post não encontrado'}), 404
        
        # Buscar respostas
        replies = ForumReply.query.filter_by(post_id=post_id).order_by(ForumReply.created_at.asc()).all()
        
        return jsonify({
            'post': post.to_dict(),
            'replies': [reply.to_dict() for reply in replies]
        }), 200
        
    except Exception as e:
        print(f"Erro ao buscar post: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@forum_bp.route('/posts/<int:post_id>/replies', methods=['POST'])
@jwt_required()
def create_reply(post_id):
    try:
        current_user_id = get_jwt_identity()
        
        # Verificar se post existe
        post = ForumPost.query.get(post_id)
        if not post:
            return jsonify({'error': 'Post não encontrado'}), 404
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Dados não fornecidos'}), 400
        
        content = data.get('content', '').strip()
        
        if not content:
            return jsonify({'error': 'Conteúdo é obrigatório'}), 400
        
        if len(content) < 5:
            return jsonify({'error': 'Conteúdo deve ter pelo menos 5 caracteres'}), 400
        
        reply = ForumReply(
            content=content,
            post_id=post_id,
            author_id=current_user_id
        )
        
        db.session.add(reply)
        db.session.commit()
        
        return jsonify({
            'message': 'Resposta criada com sucesso',
            'reply': reply.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao criar resposta: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@forum_bp.route('/categories', methods=['GET'])
def get_categories():
    try:
        categories = [
            {'id': 'movies', 'name': 'Filmes', 'description': 'Discussões sobre filmes'},
            {'id': 'tv_shows', 'name': 'Séries', 'description': 'Discussões sobre séries de TV'},
            {'id': 'games', 'name': 'Jogos', 'description': 'Discussões sobre jogos'},
            {'id': 'recommendations', 'name': 'Recomendações', 'description': 'Recomende conteúdo para outros usuários'},
            {'id': 'general', 'name': 'Geral', 'description': 'Discussões gerais sobre entretenimento'}
        ]
        
        # Contar posts por categoria
        for category in categories:
            count = ForumPost.query.filter_by(category=category['id']).count()
            category['posts_count'] = count
        
        return jsonify({'categories': categories}), 200
        
    except Exception as e:
        print(f"Erro ao buscar categorias: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@forum_bp.route('/posts/<int:post_id>', methods=['DELETE'])
@jwt_required()
def delete_post(post_id):
    try:
        current_user_id = get_jwt_identity()
        
        post = ForumPost.query.filter_by(id=post_id, author_id=current_user_id).first()
        
        if not post:
            return jsonify({'error': 'Post não encontrado ou você não tem permissão'}), 404
        
        db.session.delete(post)
        db.session.commit()
        
        return jsonify({'message': 'Post deletado com sucesso'}), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao deletar post: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@forum_bp.route('/replies/<int:reply_id>', methods=['DELETE'])
@jwt_required()
def delete_reply(reply_id):
    try:
        current_user_id = get_jwt_identity()
        
        reply = ForumReply.query.filter_by(id=reply_id, author_id=current_user_id).first()
        
        if not reply:
            return jsonify({'error': 'Resposta não encontrada ou você não tem permissão'}), 404
        
        db.session.delete(reply)
        db.session.commit()
        
        return jsonify({'message': 'Resposta deletada com sucesso'}), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao deletar resposta: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

