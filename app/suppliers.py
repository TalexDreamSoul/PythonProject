from flask import Blueprint, request
from sqlalchemy import func

from . import db
from .models import Supplier, Product
from .schemas import supplier_to_dict
from .utils import Response, ValidationError, NotFoundError, role_required

bp = Blueprint('suppliers', __name__)


@bp.route('', methods=['GET'])
def list_suppliers():
    page = int(request.args.get('page', 1))
    size = int(request.args.get('size', 20))
    keyword = (request.args.get('keyword') or '').strip()

    q = db.session.query(Supplier)
    if keyword:
        q = q.filter(Supplier.supplier_name.ilike(f'%{keyword}%'))

    total = q.count()
    rows = q.order_by(Supplier.supplier_id.desc()).offset((page - 1) * size).limit(size).all()

    supplier_ids = [x.supplier_id for x in rows]
    stats_map = {}
    if supplier_ids:
        stats_rows = (
            db.session.query(
                Product.supplier_id.label('supplier_id'),
                func.count(Product.product_id).label('product_count'),
                func.coalesce(func.sum(Product.stock), 0).label('total_stock'),
            )
            .filter(Product.supplier_id.in_(supplier_ids))
            .group_by(Product.supplier_id)
            .all()
        )
        stats_map = {
            r.supplier_id: {'product_count': int(r.product_count), 'total_stock': int(r.total_stock)}
            for r in stats_rows
        }

    payload = [supplier_to_dict(item, stats_map.get(item.supplier_id, {'product_count': 0, 'total_stock': 0})) for item in rows]
    return Response.pagination(payload, total, page, size)


@bp.route('', methods=['POST'])
@role_required(['admin', 'purchaser', 'stock_operator'])
def create_supplier():
    data = request.json or {}
    name = (data.get('supplier_name') or '').strip()

    if not name:
        raise ValidationError('supplier_name is required')

    supplier = Supplier(
        supplier_name=name,
        contact_person=(data.get('contact_person') or '').strip() or None,
        phone=(data.get('phone') or '').strip() or None,
        email=(data.get('email') or '').strip() or None,
        address=(data.get('address') or '').strip() or None,
    )
    db.session.add(supplier)
    db.session.commit()

    return Response.success({'supplier_id': supplier.supplier_id})


@bp.route('/<int:supplier_id>', methods=['GET'])
def get_supplier(supplier_id: int):
    supplier = Supplier.query.get(supplier_id)
    if not supplier:
        raise NotFoundError('Supplier not found')
    return Response.success(supplier_to_dict(supplier))


@bp.route('/<int:supplier_id>', methods=['PUT'])
@role_required(['admin', 'purchaser', 'stock_operator'])
def update_supplier(supplier_id: int):
    supplier = Supplier.query.get(supplier_id)
    if not supplier:
        raise NotFoundError('Supplier not found')

    data = request.json or {}

    if 'supplier_name' in data:
        name = (data.get('supplier_name') or '').strip()
        if not name:
            raise ValidationError('supplier_name is required')
        supplier.supplier_name = name

    if 'contact_person' in data:
        supplier.contact_person = (data.get('contact_person') or '').strip() or None
    if 'phone' in data:
        supplier.phone = (data.get('phone') or '').strip() or None
    if 'email' in data:
        supplier.email = (data.get('email') or '').strip() or None
    if 'address' in data:
        supplier.address = (data.get('address') or '').strip() or None

    db.session.commit()
    return Response.success(supplier_to_dict(supplier))


@bp.route('/<int:supplier_id>', methods=['DELETE'])
@role_required(['admin'])
def delete_supplier(supplier_id: int):
    supplier = Supplier.query.get(supplier_id)
    if not supplier:
        raise NotFoundError('Supplier not found')

    if Product.query.filter_by(supplier_id=supplier_id).first():
        raise ValidationError('Supplier is in use by products')

    db.session.delete(supplier)
    db.session.commit()
    return Response.success({'supplier_id': supplier_id})
