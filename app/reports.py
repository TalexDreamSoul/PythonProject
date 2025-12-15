from flask import Blueprint, request
from . import scheduler, db
from datetime import date, datetime, timedelta
from typing import Optional
from .models import InventorySummary, Product
from .utils import Response, role_required

bp = Blueprint('reports', __name__)

@bp.route('/inventory_alerts', methods=['GET'])
@role_required(['admin', 'stock_operator', 'purchaser', 'finance', 'viewer'])
def get_inventory_alerts():
    """获取库存预警信息"""
    # 查询所有库存异常的商品
    low_stock_products = Product.query.filter(
        Product.stock <= Product.min_stock
    ).all()
    
    high_stock_products = Product.query.filter(
        Product.stock >= Product.max_stock
    ).all()
    
    # 构造响应数据
    low_stock_items = []
    for product in low_stock_products:
        low_stock_items.append({
            'product_id': product.product_id,
            'product_code': product.product_code,
            'product_name': product.product_name,
            'stock': product.stock,
            'min_stock': product.min_stock,
            'max_stock': product.max_stock,
            'status': product.status,
            'alert_type': 'low_stock'
        })
    
    high_stock_items = []
    for product in high_stock_products:
        high_stock_items.append({
            'product_id': product.product_id,
            'product_code': product.product_code,
            'product_name': product.product_name,
            'stock': product.stock,
            'min_stock': product.min_stock,
            'max_stock': product.max_stock,
            'status': product.status,
            'alert_type': 'high_stock'
        })
    
    # 合并所有预警信息
    all_alerts = low_stock_items + high_stock_items
    
    return Response.success({
        'low_stock_count': len(low_stock_items),
        'high_stock_count': len(high_stock_items),
        'total_alerts': len(all_alerts),
        'items': all_alerts
    })

@bp.route('/daily_summary', methods=['GET'])
def daily_summary():
    """获取每日库存汇总"""
    target = request.args.get('date')
    if target:
        t = datetime.strptime(target, '%Y-%m-%d').date()
    else:
        t = date.today()
    
    rows = InventorySummary.query.filter_by(summary_date=t).all()
    items = [
        {
            'product_id': r.product_id,
            'date': r.summary_date.isoformat(),
            'stock': r.closing_stock
        }
        for r in rows
    ]
    
    return Response.success({'items': items})

@bp.route('/inventory_report', methods=['GET'])
@role_required(['admin', 'stock_operator', 'finance', 'viewer'])
def inventory_report():
    """获取库存日报"""
    target = request.args.get('date')
    if target:
        report_date = datetime.strptime(target, '%Y-%m-%d').date()
    else:
        report_date = date.today()
    
    from .models import StockOperation
    
    # 获取当日库存汇总
    summary_rows = InventorySummary.query.filter_by(summary_date=report_date).all()
    
    # 获取当日库存操作记录
    start_time = datetime.combine(report_date, datetime.min.time())
    end_time = datetime.combine(report_date, datetime.max.time())
    
    stock_operations = StockOperation.query.filter(
        StockOperation.created_at >= start_time,
        StockOperation.created_at <= end_time
    ).all()
    
    # 统计当日出入库数据
    in_total = 0
    out_total = 0
    adjust_total = 0
    
    for op in stock_operations:
        if op.op_type == 'in':
            in_total += op.quantity
        elif op.op_type == 'out':
            out_total += op.quantity
        else:
            adjust_total += abs(op.quantity)
    
    # 构造响应数据
    summary_items = []
    for r in summary_rows:
        summary_items.append({
            'product_id': r.product_id,
            'stock': r.closing_stock
        })
    
    operation_items = []
    for op in stock_operations:
        operation_items.append({
            'op_id': op.op_id,
            'product_id': op.product_id,
            'op_type': op.op_type,
            'quantity': op.quantity,
            'created_at': op.created_at.isoformat(),
            'reason': op.reason,
            'order_id': op.order_id,
        })
    
    return Response.success({
        'report_date': report_date.isoformat(),
        'summary': {
            'total_products': len(summary_rows),
            'total_in': in_total,
            'total_out': out_total,
            'total_adjust': adjust_total
        },
        'stock_summary': summary_items,
        'stock_operations': operation_items
    })

@bp.route('/stock_trend', methods=['GET'])
@role_required(['admin', 'stock_operator', 'finance', 'viewer'])
def stock_trend():
    """获取商品出入库趋势图数据"""
    # 获取参数
    product_id = request.args.get('product_id', type=int)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # 默认时间范围：最近30天
    if not start_date:
        start_date = (date.today() - timedelta(days=30)).strftime('%Y-%m-%d')
    if not end_date:
        end_date = date.today().strftime('%Y-%m-%d')
    
    # 解析日期
    start = datetime.strptime(start_date, '%Y-%m-%d').date()
    end = datetime.strptime(end_date, '%Y-%m-%d').date()
    
    from .models import StockOperation
    
    # 构建查询
    start_dt = datetime.combine(start, datetime.min.time())
    end_dt = datetime.combine(end, datetime.max.time())
    query = StockOperation.query.filter(
        StockOperation.created_at >= start_dt,
        StockOperation.created_at <= end_dt
    )
    
    # 如果指定了商品ID，则过滤
    if product_id:
        query = query.filter_by(product_id=product_id)
    
    # 执行查询
    operations = query.all()
    
    # 按日期和操作类型分组统计
    trend_data = {}
    current_date = start
    
    # 初始化日期范围
    while current_date <= end:
        date_str = current_date.strftime('%Y-%m-%d')
        trend_data[date_str] = {
            'date': date_str,
            'in': 0,
            'out': 0,
            'adjust': 0
        }
        current_date += timedelta(days=1)
    
    # 统计数据
    for op in operations:
        op_date = op.created_at.date().strftime('%Y-%m-%d')
        if op_date in trend_data:
            if op.op_type == 'in':
                trend_data[op_date]['in'] += op.quantity
            elif op.op_type == 'out':
                trend_data[op_date]['out'] += op.quantity
            else:
                trend_data[op_date]['adjust'] += abs(op.quantity)
    
    # 转换为列表格式
    result = list(trend_data.values())
    
    return Response.success({
        'start_date': start_date,
        'end_date': end_date,
        'product_id': product_id,
        'trend_data': result
    })

def refresh_inventory_summary_python(target_date: Optional[date] = None):
    """刷新每日库存汇总"""
    if target_date is None:
        target_date = date.today()
    products = Product.query.all()
    
    with db.session.begin():
        for p in products:
            # 检查是否已存在该日期的汇总记录
            exists = InventorySummary.query.filter_by(product_id=p.product_id, summary_date=target_date).first()

            total_value = (p.purchase_price or 0) * p.stock
            
            if exists:
                # 更新现有记录（只做兜底快照，别指望它算报表）
                exists.closing_stock = p.stock
                exists.total_value = total_value
            else:
                # 创建新记录
                db.session.add(
                    InventorySummary(
                        product_id=p.product_id,
                        summary_date=target_date,
                        opening_stock=p.stock,
                        incoming_qty=0,
                        outgoing_qty=0,
                        adjustment_qty=0,
                        closing_stock=p.stock,
                        total_value=total_value,
                    )
                )
    
    print(f"Inventory summary refreshed for {target_date}")

def generate_inventory_alerts():
    """生成库存预警快照"""
    # 这里可以扩展为生成预警通知或保存预警历史记录
    # 目前仅记录日志
    print(f"Inventory alerts generated at {datetime.now()}")
    return True

def schedule_jobs(app):
    """配置定时任务"""
    def _refresh_inventory_summary():
        with app.app_context():
            refresh_inventory_summary_python()

    def _generate_inventory_alerts():
        with app.app_context():
            generate_inventory_alerts()

    # 每天00:00生成库存汇总
    scheduler.add_job(
        func=_refresh_inventory_summary,
        trigger='cron',
        hour=0,
        minute=0,
        id='daily_inventory_summary',
        replace_existing=True
    )
    
    # 每1小时生成库存预警
    scheduler.add_job(
        func=_generate_inventory_alerts,
        trigger='cron',
        hour='*',
        minute=0,
        id='hourly_inventory_alerts',
        replace_existing=True
    )
    
    print("Scheduled jobs added: daily_inventory_summary, hourly_inventory_alerts")
