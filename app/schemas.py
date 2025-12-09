# simple marshalling helpers (you can replace with Marshmallow later)

def product_to_dict(p):
    return {
        'product_id': p.product_id,
        'product_code': p.product_code,
        'product_name': p.product_name,
        'category_id': p.category_id,
        'supplier_id': p.supplier_id,
        'purchase_price': float(p.purchase_price),
        'sale_price': float(p.sale_price),
        'stock': p.stock,
        'min_stock': p.min_stock,
        'max_stock': p.max_stock,
        'status': p.status,
        'storage_location': p.storage_location,
        'created_by': p.created_by,
        'created_at': p.created_at.isoformat() if p.created_at else None,
        'updated_at': p.updated_at.isoformat() if p.updated_at else None
    }

def stock_operation_to_dict(op):
    return {
        'op_id': op.op_id,
        'product_id': op.product_id,
        'op_type': op.op_type,
        'quantity': op.quantity,
        'stock_before': op.stock_before,
        'stock_after': op.stock_after,
        'order_id': op.order_id,
        'reason': op.reason,
        'operator_id': op.operator_id,
        'created_at': op.created_at.isoformat() if op.created_at else None
    }

def order_to_dict(order):
    return {
        'order_id': order.order_id,
        'order_type': order.order_type,
        'total_amount': float(order.total_amount),
        'status': order.status,
        'created_at': order.created_at.isoformat() if order.created_at else None,
        'updated_at': order.updated_at.isoformat() if order.updated_at else None
    }

def inventory_summary_to_dict(summary):
    return {
        'summary_id': summary.summary_id,
        'date': summary.date.isoformat() if summary.date else None,
        'product_id': summary.product_id,
        'stock': summary.stock
    }