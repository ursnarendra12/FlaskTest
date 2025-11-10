# category_routes.py
from flask import Blueprint, request, jsonify
from database import db
from models import Category

category_blueprint = Blueprint('category', __name__)

# GET all categories with pagination and search
@category_blueprint.route('/categories', methods=['GET'])
def get_categories():
    search = request.args.get('search', '').strip()
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 10))

    query = Category.query
    if search:
        query = query.filter(Category.name.ilike(f"%{search}%"))

    pagination = query.order_by(Category.id.desc()).paginate(page=page, per_page=limit, error_out=False)
    data = [category.to_dict() for category in pagination.items]

    return jsonify({
        'page': page,
        'limit': limit,
        'total': pagination.total,
        'pages': pagination.pages,
        'data': data
    })


# GET single category by ID
@category_blueprint.route('/categories/<int:id>', methods=['GET'])
def get_category(id):
    category = Category.query.get(id)
    if not category:
        return jsonify({'message': 'Category not found'}), 404
    return jsonify(category.to_dict())


# CREATE category
@category_blueprint.route('/categories', methods=['POST'])
def create_category():
    data = request.get_json()
    name = data.get('name')

    if not name:
        return jsonify({'error': 'Name is required'}), 400

    new_category = Category(name=name)
    db.session.add(new_category)
    db.session.commit()

    return jsonify({'id': new_category.id, 'name': name, 'message': 'Category created successfully'}), 201


# UPDATE category
@category_blueprint.route('/categories/<int:id>', methods=['PUT'])
def update_category(id):
    data = request.get_json()
    name = data.get('name')

    category = Category.query.get(id)
    if not category:
        return jsonify({'message': 'Category not found'}), 404

    if not name:
        return jsonify({'error': 'Name is required'}), 400

    category.name = name
    db.session.commit()
    return jsonify({'id': id, 'name': name, 'message': 'Category updated successfully'})


# DELETE category
@category_blueprint.route('/categories/<int:id>', methods=['DELETE'])
def delete_category(id):
    category = Category.query.get(id)
    if not category:
        return jsonify({'message': 'Category not found'}), 404

    db.session.delete(category)
    db.session.commit()
    return jsonify({'message': 'Category deleted successfully'})
