from flask import Blueprint, request
from sqlalchemy import func

from . import db
from .models import Category, Product
from .schemas import category_to_dict
from .utils import Response, ValidationError, NotFoundError, role_required

bp = Blueprint('categories_bp', __name__)


@bp.route('', methods=['GET'])
def list_categories():
    page = int(request.args.get('page', 1))
    size = int(request.args.get('size', 20))
    keyword = (request.args.get('keyword') or '').strip()

    q = db.session.query(Category)
    if keyword:
        q = q.filter(Category.category_name.ilike(f'%{keyword}%'))

    total = q.count()
    rows = q.order_by(Category.category_id.desc()).offset((page - 1) * size).limit(size).all()

    category_ids = [x.category_id for x in rows]
    stats_map = {}
    if category_ids:
        stats_rows = (
            db.session.query(
                Product.category_id.label('category_id'),
                func.count(Product.product_id).label('product_count'),
                func.coalesce(func.sum(Product.stock), 0).label('total_stock'),
            )
            .filter(Product.category_id.in_(category_ids))
            .group_by(Product.category_id)
            .all()
        )
        stats_map = {
            r.category_id: {'product_count': int(r.product_count), 'total_stock': int(r.total_stock)}
            for r in stats_rows
        }

    payload = [category_to_dict(item, stats_map.get(item.category_id, {'product_count': 0, 'total_stock': 0})) for item in rows]
    return Response.pagination(payload, total, page, size)


@bp.route('', methods=['POST'])
@role_required(['admin', 'stock_operator'])
def create_category():
    data = request.json or {}
    name = (data.get('category_name') or '').strip()
    description = (data.get('description') or '').strip() or None

    if not name:
        raise ValidationError('category_name is required')

    if Category.query.filter_by(category_name=name).first():
        raise ValidationError('Category name already exists')

    category = Category(category_name=name, description=description)
    db.session.add(category)
    db.session.commit()

    return Response.success({'category_id': category.category_id})


@bp.route('/<int:category_id>', methods=['GET'])
def get_category(category_id: int):
    category = Category.query.get(category_id)
    if not category:
        raise NotFoundError('Category not found')
    return Response.success(category_to_dict(category))


@bp.route('/<int:category_id>', methods=['PUT'])
@role_required(['admin', 'stock_operator'])
def update_category(category_id: int):
    category = Category.query.get(category_id)
    if not category:
        raise NotFoundError('Category not found')

    data = request.json or {}

    if 'category_name' in data:
        name = (data.get('category_name') or '').strip()
        if not name:
            raise ValidationError('category_name is required')
        exists = Category.query.filter(Category.category_name == name, Category.category_id != category_id).first()
        if exists:
            raise ValidationError('Category name already exists')
        category.category_name = name

    if 'description' in data:
        description = (data.get('description') or '').strip()
        category.description = description or None

    db.session.commit()
    return Response.success(category_to_dict(category))


@bp.route('/<int:category_id>', methods=['DELETE'])
@role_required(['admin'])
def delete_category(category_id: int):
    category = Category.query.get(category_id)
    if not category:
        raise NotFoundError('Category not found')

    if Product.query.filter_by(category_id=category_id).first():
        raise ValidationError('Category is in use by products')

    db.session.delete(category)
    db.session.commit()
    return Response.success({'category_id': category_id})
