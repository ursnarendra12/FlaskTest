# product_routes.py
from flask import Blueprint, request, jsonify
from database import db
from models import Product

product_blueprint = Blueprint('product', __name__)

# GET all products with pagination and search
@product_blueprint.route('/products', methods=['GET'])
def get_products():
    search = request.args.get('search', '').strip()
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 10))

    query = Product.query
    if search:
        query = query.filter(Product.name.ilike(f"%{search}%"))

    pagination = query.order_by(Product.id.desc()).paginate(page=page, per_page=limit, error_out=False)
    data = [product.to_dict() for product in pagination.items]

    return jsonify({
        'page': page,
        'limit': limit,
        'total': pagination.total,
        'pages': pagination.pages,
        'data': data
    })


# GET single product by ID
@product_blueprint.route('/products/<int:id>', methods=['GET'])
def get_product(id):
    product = Product.query.get(id)
    if not product:
        return jsonify({'message': 'Product not found'}), 404
    return jsonify(product.to_dict())


# CREATE product
@product_blueprint.route('/products', methods=['POST'])
def create_product():
    data = request.get_json()
    name = data.get('name')
    price = data.get('price')
    description = data.get('description', '')

    if not name or price is None:
        return jsonify({'error': 'Name and price are required'}), 400

    new_product = Product(name=name, price=price, description=description)
    db.session.add(new_product)
    db.session.commit()

    return jsonify({
        'id': new_product.id,
        'name': name,
        'price': price,
        'description': description,
        'message': 'Product created successfully'
    }), 201


# UPDATE product
@product_blueprint.route('/products/<int:id>', methods=['PUT'])
def update_product(id):
    data = request.get_json()
    name = data.get('name')
    price = data.get('price')
    description = data.get('description', '')

    product = Product.query.get(id)
    if not product:
        return jsonify({'message': 'Product not found'}), 404

    if not name or price is None:
        return jsonify({'error': 'Name and price are required'}), 400

    product.name = name
    product.price = price
    product.description = description
    db.session.commit()

    return jsonify({'id': id, 'message': 'Product updated successfully'})


# DELETE product
@product_blueprint.route('/products/<int:id>', methods=['DELETE'])
def delete_product(id):
    product = Product.query.get(id)
    if not product:
        return jsonify({'message': 'Product not found'}), 404

    db.session.delete(product)
    db.session.commit()
    return jsonify({'message': 'Product deleted successfully'})
