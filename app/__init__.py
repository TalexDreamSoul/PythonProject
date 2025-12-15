import os
import warnings

from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.exceptions import HTTPException

warnings.filterwarnings(
    "ignore",
    message=r"pkg_resources is deprecated as an API\..*",
    category=UserWarning,
    module=r"apscheduler(\..*)?",
)

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers.base import STATE_RUNNING

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
scheduler = BackgroundScheduler()


def create_app(config_object=None):
    app = Flask(__name__)
    # load config
    if config_object:
        app.config.from_object(config_object)
    else:
        app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///supermarket.db')
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'change-me')
        app.config['JWT_ACCESS_TOKEN_EXPIRES'] = 8 * 3600

    # 初始化CORS，允许所有跨域请求
    CORS(app, resources={
        r"/api/*": {
            "origins": "*",
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    from .utils import Response

    @jwt.unauthorized_loader
    def _jwt_missing_token(reason: str):
        return Response.error(401, reason)

    @jwt.invalid_token_loader
    def _jwt_invalid_token(reason: str):
        return Response.error(401, reason)

    @jwt.expired_token_loader
    def _jwt_expired_token(_jwt_header, _jwt_payload):
        return Response.error(401, 'Token has expired')

    @jwt.revoked_token_loader
    def _jwt_revoked_token(_jwt_header, _jwt_payload):
        return Response.error(401, 'Token has been revoked')

    @jwt.needs_fresh_token_loader
    def _jwt_needs_fresh_token(_jwt_header, _jwt_payload):
        return Response.error(401, 'Fresh token required')

    # register blueprints
    from .auth import bp as auth_bp
    from .products import bp as products_bp
    from .stock import bp as stock_bp
    from .orders import bp as orders_bp
    from .reports import bp as reports_bp
    from .categories import bp as categories_bp
    from .suppliers import bp as suppliers_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(products_bp, url_prefix='/api/products')
    app.register_blueprint(categories_bp, url_prefix='/api/categories')
    app.register_blueprint(suppliers_bp, url_prefix='/api/suppliers')
    app.register_blueprint(stock_bp, url_prefix='/api/stock')
    app.register_blueprint(orders_bp, url_prefix='/api/orders')
    app.register_blueprint(reports_bp, url_prefix='/api/reports')

    _init_scheduler(app)

    # 统一错误处理
    @app.errorhandler(Exception)
    def handle_exception(e):
        from .utils import AppError

        if isinstance(e, AppError):
            status = e.code if isinstance(e.code, int) and 100 <= e.code <= 599 else 400
            return jsonify({'code': e.code, 'message': e.message, 'data': e.data}), status

        if isinstance(e, HTTPException):
            status = e.code or 500
            return jsonify({'code': status, 'message': e.description or str(e), 'data': None}), status

        # SQLAlchemy 会塞一个字符串 e.code（比如 e3q8），拿它当 HTTP 状态码会把响应搞成 HTTP/1.1 0 e3q8。
        if isinstance(e, SQLAlchemyError):
            message = str(e)
            if app.config.get('APP_ENV') != 'development':
                message = 'Database error'
            return jsonify({'code': 50000, 'message': message, 'data': None}), 500

        message = str(e)
        if app.config.get('APP_ENV') != 'development':
            message = 'Internal server error'
        return jsonify({'code': 50000, 'message': message, 'data': None}), 500

    return app


def _init_scheduler(app: Flask) -> None:
    """初始化并启动定时任务（开发热重载下避免重复启动）。"""
    # Flask debug reloader 会启动父/子两个进程；只在子进程里跑 scheduler。
    if app.debug and os.environ.get("WERKZEUG_RUN_MAIN") != "true":
        return

    from .reports import schedule_jobs

    schedule_jobs(app)
    if scheduler.state != STATE_RUNNING:
        scheduler.start()
