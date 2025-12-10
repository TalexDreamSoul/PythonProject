# 超市库存管理系统 API 文档

## 1. 认证相关 API

### 1.1 用户注册

**请求方法**: POST
**端点**: `/api/auth/register`
**权限**: 无
**请求体**:
```json
{
  "username": "admin",
  "password": "password",
  "role": "admin"
}
```
**响应**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "user_id": 1
  }
}
```

### 1.2 用户登录

**请求方法**: POST
**端点**: `/api/auth/login`
**权限**: 无
**请求体**:
```json
{
  "username": "admin",
  "password": "password"
}
```
**响应**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }
}
```

### 1.3 获取用户列表

**请求方法**: GET
**端点**: `/api/auth/users`
**权限**: admin
**响应**:
```json
{
  "code": 0,
  "message": "success",
  "data": [
    {
      "user_id": 1,
      "username": "admin",
      "role": "admin",
      "created_at": "2024-01-01T00:00:00"
    }
  ]
}
```

### 1.4 获取用户详情

**请求方法**: GET
**端点**: `/api/auth/users/<int:user_id>`
**权限**: admin
**响应**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "user_id": 1,
    "username": "admin",
    "role": "admin",
    "created_at": "2024-01-01T00:00:00"
  }
}
```

### 1.5 更新用户信息

**请求方法**: PUT
**端点**: `/api/auth/users/<int:user_id>`
**权限**: admin
**请求体**:
```json
{
  "password": "new_password",
  "role": "stock_operator"
}
```
**响应**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "user_id": 1,
    "username": "admin",
    "role": "stock_operator"
  }
}
```

### 1.6 删除用户

**请求方法**: DELETE
**端点**: `/api/auth/users/<int:user_id>`
**权限**: admin
**响应**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "user_id": 1
  }
}
```

## 2. 商品管理 API

### 2.1 创建商品

**请求方法**: POST
**端点**: `/api/products`
**权限**: admin, stock_operator, purchaser
**请求体**:
```json
{
  "product_code": "P001",
  "product_name": "测试商品",
  "category_id": 1,
  "supplier_id": 1,
  "purchase_price": 10.00,
  "sale_price": 15.00,
  "min_stock": 10,
  "max_stock": 100,
  "storage_location": "A1-01"
}
```
**响应**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "product_id": 1
  }
}
```

### 2.2 查询商品列表

**请求方法**: GET
**端点**: `/api/products`
**权限**: 无
**查询参数**:
- `page`: 页码，默认 1
- `size`: 每页数量，默认 20
- `category_id`: 分类 ID
- `supplier_id`: 供应商 ID
- `status`: 商品状态 (active, out_of_stock, disabled)
**响应**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [
      {
        "product_id": 1,
        "product_code": "P001",
        "product_name": "测试商品",
        "stock": 0,
        "status": "active"
      }
    ],
    "total": 1,
    "page": 1,
    "size": 20
  }
}
```

### 2.3 获取商品详情

**请求方法**: GET
**端点**: `/api/products/<int:product_id>`
**权限**: 无
**响应**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "product_id": 1,
    "product_code": "P001",
    "product_name": "测试商品",
    "category_id": 1,
    "supplier_id": 1,
    "purchase_price": 10.0,
    "sale_price": 15.0,
    "stock": 0,
    "min_stock": 10,
    "max_stock": 100,
    "status": "active",
    "storage_location": "A1-01",
    "created_by": 1,
    "created_at": "2024-01-01T00:00:00",
    "updated_at": "2024-01-01T00:00:00"
  }
}
```

### 2.4 更新商品信息

**请求方法**: PUT
**端点**: `/api/products/<int:product_id>`
**权限**: admin, stock_operator
**请求体**:
```json
{
  "product_name": "更新后的商品名称",
  "sale_price": 16.00,
  "min_stock": 5,
  "max_stock": 150
}
```
**响应**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "product_id": 1,
    "product_code": "P001",
    "product_name": "更新后的商品名称",
    "sale_price": 16.0,
    "min_stock": 5,
    "max_stock": 150
  }
}
```

### 2.5 删除商品

**请求方法**: DELETE
**端点**: `/api/products/<int:product_id>`
**权限**: admin
**响应**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "product_id": 1
  }
}
```

### 2.6 查询商品库存

**请求方法**: GET
**端点**: `/api/products/<int:product_id>/stock`
**权限**: 无
**响应**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "product_id": 1,
    "product_name": "测试商品",
    "stock": 0,
    "min_stock": 10,
    "max_stock": 100,
    "status": "active"
  }
}
```

## 3. 库存管理 API

### 3.1 商品入库

**请求方法**: POST
**端点**: `/api/stock/in`
**权限**: admin, stock_operator
**请求体**:
```json
{
  "product_id": 1,
  "quantity": 50,
  "reason": "采购入库",
  "order_id": "PO20240101001"
}
```
**响应**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "operation_id": 1
  }
}
```

### 3.2 商品出库

**请求方法**: POST
**端点**: `/api/stock/out`
**权限**: admin, stock_operator, cashier
**请求体**:
```json
{
  "product_id": 1,
  "quantity": 10,
  "reason": "销售出库",
  "order_id": "SO20240101001"
}
```
**响应**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "operation_id": 2
  }
}
```

### 3.3 库存调整

**请求方法**: POST
**端点**: `/api/stock/adjust`
**权限**: admin, stock_operator
**请求体**:
```json
{
  "product_id": 1,
  "new_stock": 45,
  "reason": "库存盘点调整",
  "notes": "实际库存为45，差异原因：自然损耗"
}
```
**响应**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "operation_id": 3
  }
}
```

### 3.4 查询库存操作记录

**请求方法**: GET
**端点**: `/api/stock/operations`
**权限**: admin, stock_operator, finance, viewer
**查询参数**:
- `page`: 页码，默认 1
- `size`: 每页数量，默认 20
- `product_id`: 商品 ID
- `type`: 操作类型 (in, out, adjust)
- `start_date`: 开始日期 (YYYY-MM-DD)
- `end_date`: 结束日期 (YYYY-MM-DD)
**响应**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [
      {
        "op_id": 1,
        "product_id": 1,
        "op_type": "in",
        "quantity": 50,
        "stock_before": 0,
        "stock_after": 50,
        "order_id": "PO20240101001",
        "reason": "采购入库",
        "operator_id": 1,
        "created_at": "2024-01-01T00:00:00"
      }
    ],
    "total": 1,
    "page": 1,
    "size": 20
  }
}
```

### 3.5 获取单个库存操作记录

**请求方法**: GET
**端点**: `/api/stock/operations/<int:op_id>`
**权限**: admin, stock_operator, finance, viewer
**响应**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "op_id": 1,
    "product_id": 1,
    "op_type": "in",
    "quantity": 50,
    "stock_before": 0,
    "stock_after": 50,
    "order_id": "PO20240101001",
    "reason": "采购入库",
    "operator_id": 1,
    "created_at": "2024-01-01T00:00:00"
  }
}
```

## 4. 订单管理 API

### 4.1 创建订单

**请求方法**: POST
**端点**: `/api/orders`
**权限**: admin, purchaser, cashier
**请求体**:
```json
{
  "order_id": "PO20240101001",
  "order_type": "purchase",
  "items": [
    {
      "product_id": 1,
      "quantity": 50,
      "unit_price": 10.00
    }
  ]
}
```
**响应**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "order_id": "PO20240101001"
  }
}
```

### 4.2 查询订单列表

**请求方法**: GET
**端点**: `/api/orders`
**权限**: admin, stock_operator, purchaser, cashier, finance, viewer
**查询参数**:
- `page`: 页码，默认 1
- `size`: 每页数量，默认 20
- `order_type`: 订单类型 (purchase, sale)
- `status`: 订单状态 (pending, processing, completed, cancelled)
- `start_date`: 开始日期 (YYYY-MM-DD)
- `end_date`: 结束日期 (YYYY-MM-DD)
**响应**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [
      {
        "order_id": "PO20240101001",
        "order_type": "purchase",
        "total_amount": 500.0,
        "status": "completed",
        "created_at": "2024-01-01T00:00:00"
      }
    ],
    "total": 1,
    "page": 1,
    "size": 20
  }
}
```

### 4.3 获取订单详情

**请求方法**: GET
**端点**: `/api/orders/<string:order_id>`
**权限**: admin, stock_operator, purchaser, cashier, finance, viewer
**响应**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "order_id": "PO20240101001",
    "order_type": "purchase",
    "total_amount": 500.0,
    "status": "completed",
    "created_at": "2024-01-01T00:00:00"
  }
}
```

### 4.4 查询订单关联的库存操作

**请求方法**: GET
**端点**: `/api/orders/<string:order_id>/operations`
**权限**: admin, stock_operator, finance, viewer
**响应**:
```json
{
  "code": 0,
  "message": "success",
  "data": [
    {
      "op_id": 1,
      "product_id": 1,
      "op_type": "in",
      "quantity": 50,
      "stock_before": 0,
      "stock_after": 50,
      "order_id": "PO20240101001",
      "reason": "order PO20240101001",
      "operator_id": 1,
      "created_at": "2024-01-01T00:00:00"
    }
  ]
}
```

### 4.5 更新订单状态

**请求方法**: PUT
**端点**: `/api/orders/<string:order_id>/status`
**权限**: admin, stock_operator
**请求体**:
```json
{
  "status": "completed"
}
```
**响应**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "order_id": "PO20240101001",
    "order_type": "purchase",
    "total_amount": 500.0,
    "status": "completed",
    "created_at": "2024-01-01T00:00:00"
  }
}
```

## 5. 库存报表 API

### 5.1 获取库存预警

**请求方法**: GET
**端点**: `/api/reports/inventory_alerts`
**权限**: admin, stock_operator, purchaser, finance
**响应**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "low_stock_count": 0,
    "high_stock_count": 0,
    "total_alerts": 0,
    "items": []
  }
}
```

### 5.2 获取每日库存汇总

**请求方法**: GET
**端点**: `/api/reports/daily_summary`
**权限**: 无
**查询参数**:
- `date`: 日期 (YYYY-MM-DD)，默认今天
**响应**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [
      {
        "product_id": 1,
        "date": "2024-01-01",
        "stock": 50
      }
    ]
  }
}
```

### 5.3 获取库存日报

**请求方法**: GET
**端点**: `/api/reports/inventory_report`
**权限**: admin, stock_operator, finance, viewer
**查询参数**:
- `date`: 日期 (YYYY-MM-DD)，默认今天
**响应**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "report_date": "2024-01-01",
    "summary": {
      "total_products": 1,
      "total_in": 50,
      "total_out": 0,
      "total_adjust": 0
    },
    "stock_summary": [
      {
        "product_id": 1,
        "stock": 50
      }
    ],
    "stock_operations": [
      {
        "op_id": 1,
        "product_id": 1,
        "op_type": "in",
        "quantity": 50,
        "created_at": "2024-01-01T00:00:00",
        "reason": "采购入库"
      }
    ]
  }
}
```

### 5.4 获取商品出入库趋势

**请求方法**: GET
**端点**: `/api/reports/stock_trend`
**权限**: admin, stock_operator, finance, viewer
**查询参数**:
- `product_id`: 商品 ID（可选）
- `start_date`: 开始日期 (YYYY-MM-DD)，默认30天前
- `end_date`: 结束日期 (YYYY-MM-DD)，默认今天
**响应**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "start_date": "2023-12-02",
    "end_date": "2024-01-01",
    "product_id": null,
    "trend_data": [
      {
        "date": "2024-01-01",
        "in": 50,
        "out": 0,
        "adjust": 0
      }
    ]
  }
}
```

## 6. 权限矩阵

| 模块 | 超级管理员 | 库存管理员 | 采购专员 | 收银员 | 财务 | 访客 |
|------|------------|------------|----------|--------|------|------|
| 商品管理 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 入库 | ✅ | ✅ | ❌ | ❌ | ❌ | ✅ |
| 出库 | ✅ | ✅ | ❌ | ✅ | ❌ | ✅ |
| 库存调整 | ✅ | ✅ | ❌ | ❌ | ❌ | ✅ |
| 订单管理 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 供应商管理 | ✅ | ❌ | ✅ | ❌ | ❌ | ✅ |
| 报表 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 用户管理 | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |

## 7. 错误码说明

| 错误码 | 说明 |
|--------|------|
| 400 | 通用错误 |
| 401 | 未授权 |
| 403 | 无权限 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

## 8. 统一返回格式

### 成功响应
```json
{
  "code": 0,
  "message": "success",
  "data": {}
}
```

### 错误响应
```json
{
  "code": 400,
  "message": "错误信息",
  "data": null
}
```

### 分页响应
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [],
    "total": 0,
    "page": 1,
    "size": 20
  }
}
```