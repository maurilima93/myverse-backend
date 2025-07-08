from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from src.models.database import db, ForumCategory, ForumPost, ForumComment, User
from datetime import datetime

forum_bp = Blueprint('forum', __name__)

@forum_bp.route('/categories', methods=['GET'])
def get_categories():
    try:
        categories = ForumCategory.query.all()
        
        return jsonify({
            'categories': [cat.to_dict() for cat in categories],
            'total': len(categories)
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Erro ao buscar categorias: {str(e)}'}), 500

@forum_bp.route('/posts', methods=['GET'])
def get_posts():
    try:
        category_id = request.args.get('category_id', type=int)
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        query = ForumPost.query
        
        if category_id:
            query = query.filter_by(category_id=category_id)
        
        # Ordenar por posts fixos primeiro, depois por data
        query = query.order_by(ForumPost.is_pinned.desc(), ForumPost.created_at.desc())
        
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
        category_id = data.get('category_id')
        
        if not title or len(title) < 5:
            return jsonify({'error': 'Título deve ter pelo menos 5 caracteres'}), 400
        
        if not content or len(content) < 10:
            return jsonify({'error': 'Conteúdo deve ter pelo menos 10 caracteres'}), 400
        
        if not category_id:
            return jsonify({'error': 'Categoria é obrigatória'}), 400
        
        # Verificar se categoria existe
        category = ForumCategory.query.get(category_id)
        if not category:
            return jsonify({'error': 'Categoria não encontrada'}), 404
        
        # Criar post
        post = ForumPost(
            title=title,
            content=content,
            author_id=user_id,
            category_id=category_id
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
        comments = ForumComment.query.filter_by(post_id=post_id, parent_id=None).order_by(ForumComment.created_at.asc()).all()
        
        post_data = post.to_dict()
        post_data['comments'] = []
        
        for comment in comments:
            comment_data = comment.to_dict()
            # Buscar respostas do comentário
            replies = ForumComment.query.filter_by(parent_id=comment.id).order_by(ForumComment.created_at.asc()).all()
            comment_data['replies'] = [reply.to_dict() for reply in replies]
            post_data['comments'].append(comment_data)
        
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
        
        if post.is_locked:
            return jsonify({'error': 'Post está bloqueado para edição'}), 403
        
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
        
        if post.is_locked:
            return jsonify({'error': 'Post está bloqueado para comentários'}), 403
        
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Dados não fornecidos'}), 400
        
        content = data.get('content', '').strip()
        parent_id = data.get('parent_id')  # Para respostas
        
        if not content or len(content) < 5:
            return jsonify({'error': 'Comentário deve ter pelo menos 5 caracteres'}), 400
        
        # Se é uma resposta, verificar se o comentário pai existe
        if parent_id:
            parent_comment = ForumComment.query.filter_by(id=parent_id, post_id=post_id).first()
            if not parent_comment:
                return jsonify({'error': 'Comentário pai não encontrado'}), 404
        
        # Criar comentário
        comment = ForumComment(
            content=content,
            author_id=user_id,
            post_id=post_id,
            parent_id=parent_id
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
        comment = ForumComment.query.get(comment_id)
        
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
        comment = ForumComment.query.get(comment_id)
        
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

