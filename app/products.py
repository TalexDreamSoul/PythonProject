from flask import Blueprint, request, g
from sqlalchemy import or_
from sqlalchemy.orm import joinedload
from .models import Product, StockOperation
from . import db
from .schemas import product_to_dict
from .utils import role_required, Response, ValidationError, NotFoundError

bp = Blueprint('products', __name__)

@bp.route('', methods=['POST'])
@role_required(['admin', 'stock_operator', 'purchaser'])
def create_product():
    data = request.json or {}
    required = ['product_code', 'product_name', 'category_id', 'purchase_price', 'sale_price']
    
    for f in required:
        if f not in data:
            raise ValidationError(f'{f} is required')
    
    # 检查商品编码是否已存在
    if Product.query.filter_by(product_code=data['product_code']).first():
        raise ValidationError('Product code already exists')
    
    p = Product(
        product_code=data['product_code'],
        product_name=data['product_name'],
        category_id=data.get('category_id'),
        supplier_id=data.get('supplier_id'),
        purchase_price=data['purchase_price'],
        sale_price=data['sale_price'],
        min_stock=data.get('min_stock', 10),
        max_stock=data.get('max_stock', 1000),
        storage_location=data.get('storage_location'),
        created_by=g.current_user.user_id  # 自动记录创建者
    )
    
    db.session.add(p)
    db.session.commit()
    
    return Response.success({'product_id': p.product_id})

@bp.route('', methods=['GET'])
def list_products():
    page = int(request.args.get('page', 1))
    size = int(request.args.get('size', 20))
    keyword = (request.args.get('keyword') or '').strip()
    
    # 过滤条件
    category_id = request.args.get('category_id')
    supplier_id = request.args.get('supplier_id')
    status = request.args.get('status')
    
    q = Product.query.options(joinedload(Product.category), joinedload(Product.supplier))

    if keyword:
        q = q.filter(or_(
            Product.product_code.ilike(f'%{keyword}%'),
            Product.product_name.ilike(f'%{keyword}%'),
        ))
    
    if category_id:
        q = q.filter_by(category_id=category_id)
    if supplier_id:
        q = q.filter_by(supplier_id=supplier_id)
    if status:
        q = q.filter_by(status=status)
    
    total = q.count()
    items = q.offset((page-1)*size).limit(size).all()
    
    return Response.pagination([product_to_dict(x) for x in items], total, page, size)

@bp.route('/<int:product_id>', methods=['GET'])
def get_product(product_id):
    product = Product.query.get(product_id)
    if not product:
        raise NotFoundError('Product not found')
    return Response.success(product_to_dict(product))

@bp.route('/<int:product_id>', methods=['PUT'])
@role_required(['admin', 'stock_operator'])
def update_product(product_id):
    product = Product.query.get(product_id)
    if not product:
        raise NotFoundError('Product not found')
    
    data = request.json or {}
    
    # 不允许修改商品编码
    if 'product_code' in data and data['product_code'] != product.product_code:
        raise ValidationError('Product code cannot be modified')
    
    # 更新字段
    if 'product_name' in data:
        product.product_name = data['product_name']
    if 'category_id' in data:
        product.category_id = data['category_id']
    if 'supplier_id' in data:
        product.supplier_id = data['supplier_id']
    if 'purchase_price' in data:
        product.purchase_price = data['purchase_price']
    if 'sale_price' in data:
        product.sale_price = data['sale_price']
    if 'min_stock' in data:
        product.min_stock = data['min_stock']
    if 'max_stock' in data:
        product.max_stock = data['max_stock']
    if 'storage_location' in data:
        product.storage_location = data['storage_location']
    if 'status' in data:
        product.status = data['status']
    
    db.session.commit()
    return Response.success(product_to_dict(product))

@bp.route('/<int:product_id>', methods=['DELETE'])
@role_required(['admin'])
def delete_product(product_id):
    product = Product.query.get(product_id)
    if not product:
        raise NotFoundError('Product not found')
    
    # 检查是否存在库存流水，若存在则只能禁用
    if StockOperation.query.filter_by(product_id=product_id).first():
        # 禁用商品
        product.status = 'inactive'
        db.session.commit()
        return Response.success({'message': 'Product set to inactive instead of deleted (stock operations exist)', 'product_id': product_id})
    
    # 直接删除
    db.session.delete(product)
    db.session.commit()
    return Response.success({'product_id': product_id})

@bp.route('/<int:product_id>/stock', methods=['GET'])
def get_product_stock(product_id):
    product = Product.query.get(product_id)
    if not product:
        raise NotFoundError('Product not found')
    
    return Response.success({
        'product_id': product.product_id,
        'product_name': product.product_name,
        'stock': product.stock,
        'min_stock': product.min_stock,
        'max_stock': product.max_stock,
        'status': product.status
    })
