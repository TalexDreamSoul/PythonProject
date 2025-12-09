from flask import Blueprint, request, g
from .models import Product, StockOperation, Order
from . import db
from .utils import role_required, Response, ValidationError, NotFoundError
from .schemas import stock_operation_to_dict
from sqlalchemy import select

bp = Blueprint('stock', __name__)

# 辅助函数：更新商品库存状态
def update_product_status(product):
    """根据库存数量更新商品状态"""
    if product.stock <= 0 or product.stock <= product.min_stock:
        product.status = 'out_of_stock'
    else:
        product.status = 'active'

@bp.route('/in', methods=['POST'])
@role_required(['admin', 'stock_operator'])
def stock_in():
    data = request.json or {}
    product_id = data.get('product_id')
    quantity = int(data.get('quantity', 0))
    reason = data.get('reason', 'stock in')
    order_id = data.get('order_id')
    
    # 验证参数
    if not product_id:
        raise ValidationError('Product ID is required')
    if quantity <= 0:
        raise ValidationError('Quantity must be positive')
    if not reason:
        raise ValidationError('Reason is required')
    
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
        update_product_status(product)
        
        # 记录库存操作
        so = StockOperation(
            product_id=product_id,
            op_type='in',
            quantity=quantity,
            stock_before=before_stock,
            stock_after=product.stock,
            order_id=order_id,
            reason=reason,
            operator_id=g.current_user.user_id
        )
        db.session.add(so)
    
    return Response.success({'operation_id': so.op_id})

@bp.route('/out', methods=['POST'])
@role_required(['admin', 'stock_operator', 'cashier'])
def stock_out():
    data = request.json or {}
    product_id = data.get('product_id')
    quantity = int(data.get('quantity', 0))
    reason = data.get('reason', 'stock out')
    order_id = data.get('order_id')
    
    # 验证参数
    if not product_id:
        raise ValidationError('Product ID is required')
    if quantity <= 0:
        raise ValidationError('Quantity must be positive')
    if not reason:
        raise ValidationError('Reason is required')
    
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
        update_product_status(product)
        
        # 记录库存操作
        so = StockOperation(
            product_id=product_id,
            op_type='out',
            quantity=quantity,
            stock_before=before_stock,
            stock_after=product.stock,
            order_id=order_id,
            reason=reason,
            operator_id=g.current_user.user_id
        )
        db.session.add(so)
    
    return Response.success({'operation_id': so.op_id})

@bp.route('/adjust', methods=['POST'])
@role_required(['admin', 'stock_operator'])
def adjust_stock():
    data = request.json or {}
    product_id = data.get('product_id')
    new_stock = int(data.get('new_stock', 0))
    reason = data.get('reason')
    notes = data.get('notes', '')
    
    # 验证参数
    if not product_id:
        raise ValidationError('Product ID is required')
    if reason is None:
        raise ValidationError('Reason is required for stock adjustment')
    
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
        update_product_status(product)
        
        # 记录库存操作
        so = StockOperation(
            product_id=product_id,
            op_type='adjust',
            quantity=quantity,
            stock_before=before_stock,
            stock_after=product.stock,
            reason=f'{reason} {notes}' if notes else reason,
            operator_id=g.current_user.user_id
        )
        db.session.add(so)
    
    return Response.success({'operation_id': so.op_id})

@bp.route('/operations', methods=['GET'])
@role_required(['admin', 'stock_operator', 'finance', 'viewer'])
def get_stock_operations():
    page = int(request.args.get('page', 1))
    size = int(request.args.get('size', 20))
    product_id = request.args.get('product_id')
    op_type = request.args.get('type')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    q = StockOperation.query
    
    # 过滤条件
    if product_id:
        q = q.filter_by(product_id=product_id)
    if op_type:
        q = q.filter_by(op_type=op_type)
    if start_date:
        q = q.filter(StockOperation.created_at >= start_date)
    if end_date:
        q = q.filter(StockOperation.created_at <= end_date)
    
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