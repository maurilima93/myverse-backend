from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models.database import db, User, ForumPost, ForumReply

forum_bp = Blueprint('forum', __name__)

@content_bp.before_request
def handle_options():
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'preflight'})
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        return response

@forum_bp.route('/posts', methods=['GET'])
def get_posts():
    try:
        category = request.args.get('category', 'all')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        
        query = ForumPost.query
        
        if category != 'all':
            query = query.filter_by(category=category)
        
        # Ordenar por posts fixados primeiro, depois por data
        query = query.order_by(ForumPost.is_pinned.desc(), ForumPost.created_at.desc())
        
        posts = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        return jsonify({
            'posts': [post.to_dict() for post in posts.items],
            'total': posts.total,
            'pages': posts.pages,
            'current_page': page,
            'per_page': per_page
        }), 200
        
    except Exception as e:
        print(f"Erro ao buscar posts: {str(e)}")
        return jsonify({'error': f'Erro ao buscar posts: {str(e)}'}), 500

@forum_bp.route('/posts', methods=['POST'])
@jwt_required()
def create_post():
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Dados não fornecidos'}), 400
        
        title = data.get('title', '').strip()
        content = data.get('content', '').strip()
        category = data.get('category', 'geral').strip()
        
        if not all([title, content]):
            return jsonify({'error': 'Título e conteúdo são obrigatórios'}), 400
        
        if len(title) < 5:
            return jsonify({'error': 'Título deve ter pelo menos 5 caracteres'}), 400
        
        if len(content) < 10:
            return jsonify({'error': 'Conteúdo deve ter pelo menos 10 caracteres'}), 400
        
        # Verificar se o usuário existe
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
            'message': 'Post criado com sucesso',
            'post': post.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao criar post: {str(e)}")
        return jsonify({'error': f'Erro ao criar post: {str(e)}'}), 500

@forum_bp.route('/posts/<int:post_id>', methods=['GET'])
def get_post(post_id):
    try:
        post = ForumPost.query.get(post_id)
        
        if not post:
            return jsonify({'error': 'Post não encontrado'}), 404
        
        # Incrementar visualizações
        post.views += 1
        db.session.commit()
        
        # Buscar replies
        replies = ForumReply.query.filter_by(post_id=post_id).order_by(ForumReply.created_at.asc()).all()
        
        return jsonify({
            'post': post.to_dict(),
            'replies': [reply.to_dict() for reply in replies]
        }), 200
        
    except Exception as e:
        print(f"Erro ao buscar post: {str(e)}")
        return jsonify({'error': f'Erro ao buscar post: {str(e)}'}), 500

@forum_bp.route('/posts/<int:post_id>', methods=['PUT'])
@jwt_required()
def update_post(post_id):
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        post = ForumPost.query.get(post_id)
        
        if not post:
            return jsonify({'error': 'Post não encontrado'}), 404
        
        if post.author_id != user_id:
            return jsonify({'error': 'Você não tem permissão para editar este post'}), 403
        
        if post.is_locked:
            return jsonify({'error': 'Este post está bloqueado para edição'}), 403
        
        # Atualizar campos
        if 'title' in data:
            title = data['title'].strip()
            if len(title) >= 5:
                post.title = title
        
        if 'content' in data:
            content = data['content'].strip()
            if len(content) >= 10:
                post.content = content
        
        if 'category' in data:
            post.category = data['category'].strip()
        
        db.session.commit()
        
        return jsonify({
            'message': 'Post atualizado com sucesso',
            'post': post.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao atualizar post: {str(e)}")
        return jsonify({'error': f'Erro ao atualizar post: {str(e)}'}), 500

@forum_bp.route('/posts/<int:post_id>', methods=['DELETE'])
@jwt_required()
def delete_post(post_id):
    try:
        user_id = get_jwt_identity()
        
        post = ForumPost.query.get(post_id)
        
        if not post:
            return jsonify({'error': 'Post não encontrado'}), 404
        
        if post.author_id != user_id:
            return jsonify({'error': 'Você não tem permissão para deletar este post'}), 403
        
        db.session.delete(post)
        db.session.commit()
        
        return jsonify({'message': 'Post deletado com sucesso'}), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao deletar post: {str(e)}")
        return jsonify({'error': f'Erro ao deletar post: {str(e)}'}), 500

@forum_bp.route('/posts/<int:post_id>/replies', methods=['POST'])
@jwt_required()
def create_reply(post_id):
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Dados não fornecidos'}), 400
        
        content = data.get('content', '').strip()
        
        if not content:
            return jsonify({'error': 'Conteúdo é obrigatório'}), 400
        
        if len(content) < 5:
            return jsonify({'error': 'Resposta deve ter pelo menos 5 caracteres'}), 400
        
        # Verificar se o post existe
        post = ForumPost.query.get(post_id)
        if not post:
            return jsonify({'error': 'Post não encontrado'}), 404
        
        if post.is_locked:
            return jsonify({'error': 'Este post está bloqueado para novas respostas'}), 403
        
        # Verificar se o usuário existe
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'Usuário não encontrado'}), 404
        
        # Criar resposta
        reply = ForumReply(
            content=content,
            post_id=post_id,
            author_id=user_id
        )
        
        db.session.add(reply)
        db.session.commit()
        
        return jsonify({
            'message': 'Resposta criada com sucesso',
            'reply': reply.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao criar resposta: {str(e)}")
        return jsonify({'error': f'Erro ao criar resposta: {str(e)}'}), 500

@forum_bp.route('/replies/<int:reply_id>', methods=['PUT'])
@jwt_required()
def update_reply(reply_id):
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        reply = ForumReply.query.get(reply_id)
        
        if not reply:
            return jsonify({'error': 'Resposta não encontrada'}), 404
        
        if reply.author_id != user_id:
            return jsonify({'error': 'Você não tem permissão para editar esta resposta'}), 403
        
        # Verificar se o post não está bloqueado
        if reply.post.is_locked:
            return jsonify({'error': 'Este post está bloqueado para edições'}), 403
        
        content = data.get('content', '').strip()
        
        if not content:
            return jsonify({'error': 'Conteúdo é obrigatório'}), 400
        
        if len(content) < 5:
            return jsonify({'error': 'Resposta deve ter pelo menos 5 caracteres'}), 400
        
        reply.content = content
        db.session.commit()
        
        return jsonify({
            'message': 'Resposta atualizada com sucesso',
            'reply': reply.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao atualizar resposta: {str(e)}")
        return jsonify({'error': f'Erro ao atualizar resposta: {str(e)}'}), 500

@forum_bp.route('/replies/<int:reply_id>', methods=['DELETE'])
@jwt_required()
def delete_reply(reply_id):
    try:
        user_id = get_jwt_identity()
        
        reply = ForumReply.query.get(reply_id)
        
        if not reply:
            return jsonify({'error': 'Resposta não encontrada'}), 404
        
        if reply.author_id != user_id:
            return jsonify({'error': 'Você não tem permissão para deletar esta resposta'}), 403
        
        db.session.delete(reply)
        db.session.commit()
        
        return jsonify({'message': 'Resposta deletada com sucesso'}), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao deletar resposta: {str(e)}")
        return jsonify({'error': f'Erro ao deletar resposta: {str(e)}'}), 500

@forum_bp.route('/categories', methods=['GET'])
def get_categories():
    try:
        # Categorias padrão do fórum
        categories = [
            {'id': 'filmes', 'name': 'Filmes', 'description': 'Discussões sobre filmes'},
            {'id': 'series', 'name': 'Séries', 'description': 'Discussões sobre séries de TV'},
            {'id': 'jogos', 'name': 'Jogos', 'description': 'Discussões sobre videogames'},
            {'id': 'livros', 'name': 'Livros', 'description': 'Discussões sobre livros'},
            {'id': 'geral', 'name': 'Geral', 'description': 'Discussões gerais sobre entretenimento'},
            {'id': 'recomendacoes', 'name': 'Recomendações', 'description': 'Peça e dê recomendações'},
            {'id': 'noticias', 'name': 'Notícias', 'description': 'Últimas notícias do entretenimento'}
        ]
        
        return jsonify({'categories': categories}), 200
        
    except Exception as e:
        print(f"Erro ao buscar categorias: {str(e)}")
        return jsonify({'error': f'Erro ao buscar categorias: {str(e)}'}), 500

@forum_bp.route('/stats', methods=['GET'])
def get_forum_stats():
    try:
        total_posts = ForumPost.query.count()
        total_replies = ForumReply.query.count()
        total_users = User.query.count()
        
        # Posts mais recentes
        recent_posts = ForumPost.query.order_by(ForumPost.created_at.desc()).limit(5).all()
        
        return jsonify({
            'total_posts': total_posts,
            'total_replies': total_replies,
            'total_users': total_users,
            'recent_posts': [post.to_dict() for post in recent_posts]
        }), 200
        
    except Exception as e:
        print(f"Erro ao buscar estatísticas: {str(e)}")
        return jsonify({'error': f'Erro ao buscar estatísticas: {str(e)}'}), 500

