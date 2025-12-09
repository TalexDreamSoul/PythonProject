from . import db
from datetime import datetime, date
from decimal import Decimal

# 用户表
class User(db.Model):
    __tablename__ = 'users'
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum('admin','stock_operator','purchaser','cashier','finance','viewer', name='role_enum'), nullable=False, default='viewer')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关联关系
    created_products = db.relationship('Product', backref='creator', lazy=True)
    stock_operations = db.relationship('StockOperation', backref='operator', lazy=True)

# 分类表
class Category(db.Model):
    __tablename__ = 'categories'
    category_id = db.Column(db.Integer, primary_key=True)
    category_name = db.Column(db.String(50), nullable=False, unique=True)
    description = db.Column(db.String(200))
    
    # 关联关系
    products = db.relationship('Product', backref='category', lazy=True)

# 供应商表
class Supplier(db.Model):
    __tablename__ = 'suppliers'
    supplier_id = db.Column(db.Integer, primary_key=True)
    supplier_name = db.Column(db.String(100), nullable=False)
    contact_info = db.Column(db.String(200))
    
    # 关联关系
    products = db.relationship('Product', backref='supplier', lazy=True)

# 商品表
class Product(db.Model):
    __tablename__ = 'products'
    product_id = db.Column(db.Integer, primary_key=True)
    product_code = db.Column(db.String(50), unique=True, nullable=False, comment='业务唯一编码')
    product_name = db.Column(db.String(100), nullable=False, comment='商品名称')
    category_id = db.Column(db.Integer, db.ForeignKey('categories.category_id'), comment='分类ID')
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.supplier_id'), comment='供应商ID')
    purchase_price = db.Column(db.Numeric(10,2), nullable=False, comment='采购价')
    sale_price = db.Column(db.Numeric(10,2), nullable=False, comment='销售价')
    stock = db.Column(db.Integer, nullable=False, default=0, comment='当前库存')
    min_stock = db.Column(db.Integer, default=10, comment='库存下限')
    max_stock = db.Column(db.Integer, default=1000, comment='库存上限')
    status = db.Column(db.Enum('active','out_of_stock','disabled', name='product_status_enum'), default='active', comment='商品状态')
    storage_location = db.Column(db.String(100), comment='货架位置')
    created_by = db.Column(db.Integer, db.ForeignKey('users.user_id'), comment='创建人ID')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    
    # 关联关系
    stock_operations = db.relationship('StockOperation', backref='product', lazy=True)
    inventory_summaries = db.relationship('InventorySummary', backref='product', lazy=True)

# 订单表
class Order(db.Model):
    __tablename__ = 'orders'
    order_id = db.Column(db.String(50), primary_key=True, comment='订单ID')
    order_type = db.Column(db.Enum('purchase','sale', name='order_type_enum'), nullable=False, comment='订单类型')
    total_amount = db.Column(db.Numeric(12,2), default=Decimal('0.00'), comment='订单金额')
    status = db.Column(db.Enum('pending','processing','completed','cancelled', name='order_status_enum'), default='pending', comment='订单状态')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    
    # 关联关系
    stock_operations = db.relationship('StockOperation', backref='order', lazy=True)

# 库存操作表（审计日志）
class StockOperation(db.Model):
    __tablename__ = 'stock_operations'
    op_id = db.Column(db.Integer, primary_key=True, comment='操作ID')
    product_id = db.Column(db.Integer, db.ForeignKey('products.product_id'), nullable=False, comment='商品ID')
    op_type = db.Column(db.Enum('in','out','adjust', name='op_type_enum'), nullable=False, comment='操作类型')
    quantity = db.Column(db.Integer, nullable=False, comment='操作数量')
    stock_before = db.Column(db.Integer, nullable=False, comment='操作前库存')
    stock_after = db.Column(db.Integer, nullable=False, comment='操作后库存')
    order_id = db.Column(db.String(50), db.ForeignKey('orders.order_id'), comment='关联订单ID')
    reason = db.Column(db.String(200), nullable=False, comment='操作原因')
    operator_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False, comment='操作人ID')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='操作时间')

# 库存汇总表（物化视图）
class InventorySummary(db.Model):
    __tablename__ = 'inventory_summary'
    summary_id = db.Column(db.Integer, primary_key=True, comment='汇总ID')
    date = db.Column(db.Date, nullable=False, comment='业务日期')
    product_id = db.Column(db.Integer, db.ForeignKey('products.product_id'), nullable=False, comment='商品ID')
    stock = db.Column(db.Integer, nullable=False, comment='当日库存')
    
    __table_args__ = (
        db.UniqueConstraint('date', 'product_id', name='uk_date_product'),
    )