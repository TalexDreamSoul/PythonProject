from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from apscheduler.schedulers.background import BackgroundScheduler
import os

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

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    # register blueprints
    from .auth import bp as auth_bp
    from .products import bp as products_bp
    from .stock import bp as stock_bp
    from .orders import bp as orders_bp
    from .reports import bp as reports_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(products_bp, url_prefix='/api/products')
    app.register_blueprint(stock_bp, url_prefix='/api/stock')
    app.register_blueprint(orders_bp, url_prefix='/api/orders')
    app.register_blueprint(reports_bp, url_prefix='/api/reports')

    # scheduler startup
    from .reports import schedule_jobs
    schedule_jobs()

    # 统一错误处理
    @app.errorhandler(Exception)
    def handle_exception(e):
        from .utils import AppError
        
        if isinstance(e, AppError):
            # 自定义异常
            return {
                'code': e.code,
                'message': e.message,
                'data': e.data
            }, e.code
        else:
            # 其他异常
            code = getattr(e, 'code', 500)
            message = str(e)
            if app.config['APP_ENV'] != 'development':
                # 生产环境不泄露详细错误信息
                message = 'Internal server error'
            return {
                'code': getattr(e, 'code', 50000),
                'message': message,
                'data': None
            }, code

    return app