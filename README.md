# 超市库存管理系统

这是一个使用Flask开发的超市库存管理系统后端API。

## 主要功能

- 用户认证与授权 (注册、登录)
- 商品管理
- 库存管理
- 订单管理
- 报表生成

## 技术栈

- Flask 2.2.5
- Flask-SQLAlchemy 3.0.3
- Flask-JWT-Extended 4.4.4
- APScheduler 3.9.1
- MySQL/PyMySQL

## 项目结构

```
.
├── app/
│   ├── __init__.py
│   ├── auth.py        # 认证相关API
│   ├── config.py      # 配置文件
│   ├── models.py      # 数据库模型
│   ├── orders.py      # 订单管理API
│   ├── products.py    # 商品管理API
│   ├── reports.py     # 报表相关API
│   ├── schemas.py     # 数据校验模式
│   ├── stock.py       # 库存管理API
│   └── utils.py       # 工具函数
├── manage.py          # 应用入口
├── requirements.txt   # 依赖包
├── .env               # 环境变量
└── .env.example       # 环境变量示例
```

## 启动方式

1. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```

2. 配置环境变量：
   复制`.env.example`为`.env`并修改相关配置

3. 运行应用：
   ```bash
   python manage.py
   ```

## API文档

详细API文档请参阅`API.md`文件。

## 开发进度

- 2025-12-16：老王完善公共工具、补全库存/订单/报表接口注释，统一风格，方便后续接手的人少掉坑。
