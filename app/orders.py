from flask import Blueprint, request, g
from .models import Order, Product, StockOperation
from . import db
from .utils import role_required, Response, ValidationError, NotFoundError
from .schemas import order_to_dict, stock_operation_to_dict
from decimal import Decimal
from datetime import datetime

bp = Blueprint('orders', __name__)

# 辅助函数：更新商品库存状态
def update_product_status(product):
    """根据库存数量更新商品状态"""
    if product.stock <= 0 or product.stock <= product.min_stock:
        product.status = 'out_of_stock'
    else:
        product.status = 'active'

@bp.route('', methods=['POST'])
@role_required(['admin', 'purchaser', 'cashier'])
def create_order():
    data = request.json or {}
    order_id = data.get('order_id')
    order_type = data.get('order_type')
    items = data.get('items')
    
    # 验证参数
    if not order_id:
        raise ValidationError('Order ID is required')
    if order_type not in ['purchase', 'sale']:
        raise ValidationError('Order type must be either purchase or sale')
    if not items or not isinstance(items, list):
        raise ValidationError('Items must be a non-empty list')
    
    # 检查订单ID是否已存在
    if Order.query.get(order_id):
        raise ValidationError('Order ID already exists')
    
    with db.session.begin():
        # 创建订单
        order = Order(
            order_id=order_id,
            order_type=order_type,
            status='pending',  # 初始状态为pending
            total_amount=Decimal('0.00')
        )
        db.session.add(order)
        db.session.flush()
        
        total = Decimal('0.00')
        
        # 处理订单商品
        for item in items:
            product_id = item.get('product_id')
            quantity = int(item.get('quantity', 0))
            unit_price = Decimal(str(item.get('unit_price', '0')))
            
            # 验证商品项
            if not product_id:
                raise ValidationError('Product ID is required for each item')
            if quantity <= 0:
                raise ValidationError('Quantity must be positive for each item')
            if unit_price < 0:
                raise ValidationError('Unit price cannot be negative')
            
            # 使用行锁获取商品
            product = db.session.query(Product).filter_by(product_id=product_id).with_for_update().first()
            if not product:
                raise NotFoundError(f'Product {product_id} not found')
            
            # 执行库存操作
            before_stock = product.stock
            so_type = 'in' if order_type == 'purchase' else 'out'

            # 计算商品总价（后面写入库存流水）
            item_total = unit_price * quantity
            
            if order_type == 'purchase':
                # 采购订单：增加库存
                product.stock += quantity
            else:
                # 销售订单：减少库存
                if before_stock < quantity:
                    raise ValidationError(f'Insufficient stock for product {product_id}')
                product.stock -= quantity
            
            # 更新商品状态
            update_product_status(product)
            
            # 记录库存操作
            reason_enum = 'purchase' if order_type == 'purchase' else 'sale'
            so = StockOperation(
                product_id=product_id,
                op_type=so_type,
                quantity=quantity,
                stock_before=before_stock,
                stock_after=product.stock,
                order_id=order.order_id,
                unit_price=unit_price,
                total_price=item_total,
                operator_id=g.current_user.user_id,
                user_id=g.current_user.user_id,
                operator_action=f'order_{order_type}',
                reason=reason_enum,
                notes=f'order {order_id}',
            )
            db.session.add(so)

            total += item_total
        
        # 更新订单总金额和状态
        order.total_amount = total
        order.status = 'completed'  # 直接完成订单
    
    return Response.success({'order_id': order.order_id})

@bp.route('', methods=['GET'])
@role_required(['admin', 'stock_operator', 'purchaser', 'cashier', 'finance', 'viewer'])
def list_orders():
    page = int(request.args.get('page', 1))
    size = int(request.args.get('size', 20))
    order_type = request.args.get('order_type')
    status = request.args.get('status')
    keyword = (request.args.get('keyword') or '').strip()
    start_date = (request.args.get('start_date') or '').strip()
    end_date = (request.args.get('end_date') or '').strip()

    def parse_dt(value: str, is_end: bool):
        if not value:
            return None
        try:
            if len(value) == 10:
                d = datetime.strptime(value, '%Y-%m-%d').date()
                return datetime.combine(d, datetime.max.time() if is_end else datetime.min.time())
            return datetime.fromisoformat(value)
        except ValueError:
            return None
    
    q = Order.query
    
    # 过滤条件
    if keyword:
        q = q.filter(Order.order_id.ilike(f'%{keyword}%'))
    if order_type:
        q = q.filter_by(order_type=order_type)
    if status:
        q = q.filter_by(status=status)
    start_dt = parse_dt(start_date, False)
    if start_dt:
        q = q.filter(Order.created_at >= start_dt)
    end_dt = parse_dt(end_date, True)
    if end_dt:
        q = q.filter(Order.created_at <= end_dt)
    
    # 按创建时间倒序排列
    q = q.order_by(Order.created_at.desc())
    
    total = q.count()
    items = q.offset((page-1)*size).limit(size).all()
    
    return Response.pagination(
        [order_to_dict(item) for item in items], 
        total, page, size
    )

@bp.route('/<string:order_id>', methods=['GET'])
@role_required(['admin', 'stock_operator', 'purchaser', 'cashier', 'finance', 'viewer'])
def get_order(order_id):
    order = Order.query.get(order_id)
    if not order:
        raise NotFoundError('Order not found')
    return Response.success(order_to_dict(order))

@bp.route('/<string:order_id>/operations', methods=['GET'])
@role_required(['admin', 'stock_operator', 'finance', 'viewer'])
def get_order_operations(order_id):
    # 验证订单是否存在
    if not Order.query.get(order_id):
        raise NotFoundError('Order not found')
    
    operations = StockOperation.query.filter_by(order_id=order_id).all()
    return Response.success([stock_operation_to_dict(op) for op in operations])

@bp.route('/<string:order_id>/status', methods=['PUT'])
@role_required(['admin', 'stock_operator'])
def update_order_status(order_id):
    order = Order.query.get(order_id)
    if not order:
        raise NotFoundError('Order not found')
    
    data = request.json or {}
    new_status = data.get('status')
    
    if not new_status:
        raise ValidationError('Status is required')
    
    # 验证状态流转是否合法
    valid_transitions = {
        'pending': ['processing', 'cancelled'],
        'processing': ['completed', 'cancelled'],
        'completed': [],
        'cancelled': []
    }
    
    if new_status not in valid_transitions.get(order.status, []):
        raise ValidationError(f'Invalid status transition from {order.status} to {new_status}')
    
    # 更新订单状态
    order.status = new_status
    db.session.commit()
    
    return Response.success(order_to_dict(order))
