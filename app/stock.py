"""库存中心：所有入库、出库、调整都在这调度，别在别的模块乱搞。"""

from decimal import Decimal
from typing import Optional

from flask import Blueprint, g, request
from sqlalchemy import or_, select
from sqlalchemy.orm import joinedload

from . import db
from .models import Order, Product, StockOperation
from .schemas import stock_operation_to_dict
from .utils import (
    NotFoundError,
    Response,
    ValidationError,
    parse_date_range,
    role_required,
    sync_product_status,
)

bp = Blueprint('stock', __name__)

ALLOWED_STOCK_REASONS = {'purchase', 'sale', 'adjustment', 'damaged', 'expired', 'transfer'}

def normalize_stock_reason(op_type: str, raw_reason: Optional[str]):
    """把用户乱填的 reason 兜底成库里能存的枚举，其他内容塞 notes。"""
    defaults = {
        'in': 'purchase',
        'out': 'sale',
        'adjust': 'adjustment',
        'transfer': 'transfer',
    }
    if raw_reason and raw_reason in ALLOWED_STOCK_REASONS:
        return raw_reason, None
    return defaults.get(op_type, 'adjustment'), raw_reason

@bp.route('/in', methods=['POST'])
@role_required(['admin', 'stock_operator'])
def stock_in():
    """普通入库接口，采购完了记得调它，不然库存永远是0。"""
    data = request.json or {}
    product_id = data.get('product_id')
    quantity = int(data.get('quantity', 0))
    raw_reason = data.get('reason')
    unit_price_raw = data.get('unit_price')
    order_id = data.get('order_id')
    
    # 验证参数
    if not product_id:
        raise ValidationError('Product ID is required')
    if quantity <= 0:
        raise ValidationError('Quantity must be positive')
    
    # 验证订单（如果提供）
    if order_id:
        order = Order.query.get(order_id)
        if not order:
            raise ValidationError('Order not found')
    
    with db.session.begin():
        # 使用行锁防止并发问题
        product = db.session.execute(
            select(Product).filter_by(product_id=product_id).with_for_update()
        ).scalar_one_or_none()
        
        if not product:
            raise NotFoundError('Product not found')
        
        # 执行入库操作
        before_stock = product.stock
        product.stock += quantity
        
        # 更新商品状态
        sync_product_status(product)

        if unit_price_raw is not None:
            unit_price = Decimal(str(unit_price_raw))
        else:
            unit_price = product.purchase_price

        reason, notes = normalize_stock_reason('in', raw_reason)
        
        # 记录库存操作
        so = StockOperation(
            product_id=product_id,
            op_type='in',
            quantity=quantity,
            stock_before=before_stock,
            stock_after=product.stock,
            order_id=order_id,
            unit_price=unit_price,
            total_price=unit_price * quantity,
            operator_id=g.current_user.user_id,
            user_id=g.current_user.user_id,
            operator_action='stock_in',
            reason=reason,
            notes=notes,
        )
        db.session.add(so)
    
    return Response.success({'operation_id': so.op_id})

@bp.route('/out', methods=['POST'])
@role_required(['admin', 'stock_operator', 'cashier'])
def stock_out():
    """出库接口，销售/调拨都走这，库存不足自己长眼睛看报错。"""
    data = request.json or {}
    product_id = data.get('product_id')
    quantity = int(data.get('quantity', 0))
    raw_reason = data.get('reason')
    unit_price_raw = data.get('unit_price')
    order_id = data.get('order_id')
    
    # 验证参数
    if not product_id:
        raise ValidationError('Product ID is required')
    if quantity <= 0:
        raise ValidationError('Quantity must be positive')
    
    # 验证订单（如果提供）
    if order_id:
        order = Order.query.get(order_id)
        if not order:
            raise ValidationError('Order not found')
    
    with db.session.begin():
        # 使用行锁防止并发问题
        product = db.session.execute(
            select(Product).filter_by(product_id=product_id).with_for_update()
        ).scalar_one_or_none()
        
        if not product:
            raise NotFoundError('Product not found')
        
        # 检查库存是否足够
        if product.stock < quantity:
            raise ValidationError('Insufficient stock')
        
        # 执行出库操作
        before_stock = product.stock
        product.stock -= quantity
        
        # 更新商品状态
        sync_product_status(product)

        if unit_price_raw is not None:
            unit_price = Decimal(str(unit_price_raw))
        else:
            unit_price = product.sale_price

        reason, notes = normalize_stock_reason('out', raw_reason)
        
        # 记录库存操作
        so = StockOperation(
            product_id=product_id,
            op_type='out',
            quantity=quantity,
            stock_before=before_stock,
            stock_after=product.stock,
            order_id=order_id,
            unit_price=unit_price,
            total_price=unit_price * quantity,
            operator_id=g.current_user.user_id,
            user_id=g.current_user.user_id,
            operator_action='stock_out',
            reason=reason,
            notes=notes,
        )
        db.session.add(so)
    
    return Response.success({'operation_id': so.op_id})

@bp.route('/adjust', methods=['POST'])
@role_required(['admin', 'stock_operator'])
def adjust_stock():
    """库存调整，一次性把手工盘点结果写进去。"""
    data = request.json or {}
    product_id = data.get('product_id')
    new_stock = int(data.get('new_stock', 0))
    raw_reason = data.get('reason')
    notes = data.get('notes', '')
    
    # 验证参数
    if not product_id:
        raise ValidationError('Product ID is required')
    
    with db.session.begin():
        # 使用行锁防止并发问题
        product = db.session.execute(
            select(Product).filter_by(product_id=product_id).with_for_update()
        ).scalar_one_or_none()
        
        if not product:
            raise NotFoundError('Product not found')
        
        # 计算调整数量
        before_stock = product.stock
        quantity = new_stock - before_stock
        
        # 执行调整操作
        product.stock = new_stock
        
        # 更新商品状态
        sync_product_status(product)

        reason, extra_note = normalize_stock_reason('adjust', raw_reason)
        merged_notes = ' '.join([x for x in [extra_note, notes] if x])
        
        # 记录库存操作
        so = StockOperation(
            product_id=product_id,
            op_type='adjust',
            quantity=quantity,
            stock_before=before_stock,
            stock_after=product.stock,
            unit_price=product.purchase_price,
            total_price=product.purchase_price * abs(quantity),
            operator_id=g.current_user.user_id,
            user_id=g.current_user.user_id,
            operator_action='stock_adjust',
            reason=reason,
            notes=merged_notes,
        )
        db.session.add(so)
    
    return Response.success({'operation_id': so.op_id})

@bp.route('/operations', methods=['GET'])
@role_required(['admin', 'stock_operator', 'finance', 'viewer'])
def get_stock_operations():
    page = int(request.args.get('page', 1))
    size = int(request.args.get('size', 20))
    product_id = request.args.get('product_id', type=int)
    op_type = (request.args.get('type') or '').strip()
    keyword = (request.args.get('keyword') or '').strip()
    start_date = (request.args.get('start_date') or '').strip()
    end_date = (request.args.get('end_date') or '').strip()

    q = StockOperation.query.options(joinedload(StockOperation.product))

    start_dt, end_dt = parse_date_range(start_date, end_date)
    
    # 过滤条件
    if product_id:
        q = q.filter_by(product_id=product_id)
    if op_type:
        q = q.filter_by(op_type=op_type)
    if keyword:
        q = q.join(StockOperation.product).filter(or_(
            Product.product_code.ilike(f'%{keyword}%'),
            Product.product_name.ilike(f'%{keyword}%'),
        ))

    if start_dt:
        q = q.filter(StockOperation.created_at >= start_dt)

    if end_dt:
        q = q.filter(StockOperation.created_at <= end_dt)
    
    # 按时间倒序排列
    q = q.order_by(StockOperation.created_at.desc())
    
    total = q.count()
    items = q.offset((page-1)*size).limit(size).all()
    
    return Response.pagination(
        [stock_operation_to_dict(item) for item in items], 
        total, page, size
    )

@bp.route('/operations/<int:op_id>', methods=['GET'])
@role_required(['admin', 'stock_operator', 'finance', 'viewer'])
def get_stock_operation(op_id):
    operation = StockOperation.query.get(op_id)
    if not operation:
        raise NotFoundError('Stock operation not found')
    return Response.success(stock_operation_to_dict(operation))
