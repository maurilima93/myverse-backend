from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from src.models.database import db, ForumPost, ForumReply, User
from datetime import datetime

forum_bp = Blueprint('forum', __name__)

@forum_bp.route('/posts', methods=['GET'])
def get_posts():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        query = ForumPost.query
        
        # Ordenar por data
        query = query.order_by(ForumPost.created_at.desc())
        
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
            }
        }), 200
        
    except Exception as e:
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
        category = data.get('category', 'geral')
        
        if not title or len(title) < 5:
            return jsonify({'error': 'Título deve ter pelo menos 5 caracteres'}), 400
        
        if not content or len(content) < 10:
            return jsonify({'error': 'Conteúdo deve ter pelo menos 10 caracteres'}), 400
        
        # Criar post
        post = ForumPost(
            title=title,
            content=content,
            author_id=user_id,
            category=category
        )
        
        db.session.add(post)
        db.session.commit()
        
        return jsonify({
            'message': 'Post criado com sucesso',
            'post': post.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao criar post: {str(e)}'}), 500

@forum_bp.route('/posts/<int:post_id>', methods=['GET'])
def get_post(post_id):
    try:
        post = ForumPost.query.get(post_id)
        
        if not post:
            return jsonify({'error': 'Post não encontrado'}), 404
        
        # Buscar comentários do post
        comments = ForumReply.query.filter_by(post_id=post_id).order_by(ForumReply.created_at.asc()).all()
        
        post_data = post.to_dict()
        post_data['comments'] = [comment.to_dict() for comment in comments]
        
        return jsonify(post_data), 200
        
    except Exception as e:
        return jsonify({'error': f'Erro ao buscar post: {str(e)}'}), 500

@forum_bp.route('/posts/<int:post_id>', methods=['PUT'])
@jwt_required()
def update_post(post_id):
    try:
        user_id = get_jwt_identity()
        post = ForumPost.query.get(post_id)
        
        if not post:
            return jsonify({'error': 'Post não encontrado'}), 404
        
        if post.author_id != user_id:
            return jsonify({'error': 'Sem permissão para editar este post'}), 403
        
        data = request.get_json()
        
        if 'title' in data:
            title = data['title'].strip()
            if len(title) >= 5:
                post.title = title
        
        if 'content' in data:
            content = data['content'].strip()
            if len(content) >= 10:
                post.content = content
        
        post.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Post atualizado com sucesso',
            'post': post.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
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
            return jsonify({'error': 'Sem permissão para deletar este post'}), 403
        
        db.session.delete(post)
        db.session.commit()
        
        return jsonify({'message': 'Post deletado com sucesso'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao deletar post: {str(e)}'}), 500

@forum_bp.route('/posts/<int:post_id>/comments', methods=['POST'])
@jwt_required()
def create_comment(post_id):
    try:
        user_id = get_jwt_identity()
        post = ForumPost.query.get(post_id)
        
        if not post:
            return jsonify({'error': 'Post não encontrado'}), 404
        
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Dados não fornecidos'}), 400
        
        content = data.get('content', '').strip()
        
        if not content or len(content) < 5:
            return jsonify({'error': 'Comentário deve ter pelo menos 5 caracteres'}), 400
        
        # Criar comentário
        comment = ForumReply(
            content=content,
            author_id=user_id,
            post_id=post_id
        )
        
        db.session.add(comment)
        db.session.commit()
        
        return jsonify({
            'message': 'Comentário criado com sucesso',
            'comment': comment.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao criar comentário: {str(e)}'}), 500

@forum_bp.route('/comments/<int:comment_id>', methods=['PUT'])
@jwt_required()
def update_comment(comment_id):
    try:
        user_id = get_jwt_identity()
        comment = ForumReply.query.get(comment_id)
        
        if not comment:
            return jsonify({'error': 'Comentário não encontrado'}), 404
        
        if comment.author_id != user_id:
            return jsonify({'error': 'Sem permissão para editar este comentário'}), 403
        
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Dados não fornecidos'}), 400
        
        content = data.get('content', '').strip()
        
        if not content or len(content) < 5:
            return jsonify({'error': 'Comentário deve ter pelo menos 5 caracteres'}), 400
        
        comment.content = content
        comment.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Comentário atualizado com sucesso',
            'comment': comment.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao atualizar comentário: {str(e)}'}), 500

@forum_bp.route('/comments/<int:comment_id>', methods=['DELETE'])
@jwt_required()
def delete_comment(comment_id):
    try:
        user_id = get_jwt_identity()
        comment = ForumReply.query.get(comment_id)
        
        if not comment:
            return jsonify({'error': 'Comentário não encontrado'}), 404
        
        if comment.author_id != user_id:
            return jsonify({'error': 'Sem permissão para deletar este comentário'}), 403
        
        db.session.delete(comment)
        db.session.commit()
        
        return jsonify({'message': 'Comentário deletado com sucesso'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao deletar comentário: {str(e)}'}), 500

