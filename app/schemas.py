# simple marshalling helpers (you can replace with Marshmallow later)

def category_to_dict(category, stats=None):
    payload = {
        'category_id': category.category_id,
        'category_name': category.category_name,
        'description': category.description,
        'created_at': category.created_at.isoformat() if getattr(category, 'created_at', None) else None,
        'updated_at': category.updated_at.isoformat() if getattr(category, 'updated_at', None) else None,
    }
    if stats:
        payload.update(stats)
    return payload

def supplier_to_dict(supplier, stats=None):
    payload = {
        'supplier_id': supplier.supplier_id,
        'supplier_name': supplier.supplier_name,
        'contact_person': getattr(supplier, 'contact_person', None),
        'phone': getattr(supplier, 'phone', None),
        'email': getattr(supplier, 'email', None),
        'address': getattr(supplier, 'address', None),
        'created_at': supplier.created_at.isoformat() if getattr(supplier, 'created_at', None) else None,
        'updated_at': supplier.updated_at.isoformat() if getattr(supplier, 'updated_at', None) else None,
    }
    if stats:
        payload.update(stats)
    return payload

def product_to_dict(p):
    return {
        'product_id': p.product_id,
        'product_code': p.product_code,
        'product_name': p.product_name,
        'category_id': p.category_id,
        'category_name': p.category.category_name if getattr(p, 'category', None) else None,
        'supplier_id': p.supplier_id,
        'supplier_name': p.supplier.supplier_name if getattr(p, 'supplier', None) else None,
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
        'product_code': op.product.product_code if getattr(op, 'product', None) else None,
        'product_name': op.product.product_name if getattr(op, 'product', None) else None,
        'op_type': op.op_type,
        'quantity': op.quantity,
        'stock_before': op.stock_before,
        'stock_after': op.stock_after,
        'order_id': op.order_id,
        'unit_price': float(op.unit_price) if op.unit_price is not None else None,
        'total_price': float(op.total_price) if op.total_price is not None else None,
        'operation_date': op.operation_date.isoformat() if op.operation_date else None,
        'operator_action': op.operator_action,
        'reason': op.reason,
        'notes': op.notes,
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
        'product_id': summary.product_id,
        'summary_date': summary.summary_date.isoformat() if summary.summary_date else None,
        'opening_stock': summary.opening_stock,
        'incoming_qty': summary.incoming_qty,
        'outgoing_qty': summary.outgoing_qty,
        'adjustment_qty': summary.adjustment_qty,
        'closing_stock': summary.closing_stock,
        'total_value': float(summary.total_value) if summary.total_value is not None else None,
    }
