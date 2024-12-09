from flask import Flask
import os

# 创建全局 app 实例
app = Flask(__name__,
            template_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates'),
            static_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static'))

def create_app():
    """初始化应用"""
    # 确保必要的目录存在
    os.makedirs(os.path.join(app.static_folder, 'css', 'vendor'), exist_ok=True)
    os.makedirs(os.path.join(app.static_folder, 'css', 'webfonts'), exist_ok=True)
    os.makedirs(os.path.join(app.static_folder, 'js', 'vendor'), exist_ok=True)
    os.makedirs(os.path.join(app.static_folder, 'images'), exist_ok=True)
    os.makedirs(app.template_folder, exist_ok=True)
    os.makedirs('logs', exist_ok=True)

    # 注册所有路由
    with app.app_context():
        from app.routes import stock_routes
        from app.routes import sector_routes
        from app.routes import dragon_routes
        from app.routes import index_routes

    return app 