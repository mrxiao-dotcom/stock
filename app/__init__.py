from flask import Flask
from utils.logger import setup_logger
import os

logger = setup_logger('app')

def create_app():
    """创建并配置Flask应用"""
    # 获取项目根目录
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    app = Flask(__name__,
                template_folder=os.path.join(root_dir, 'templates'),
                static_folder=os.path.join(root_dir, 'static'))
    
    # 确保必要的目录存在
    os.makedirs(os.path.join(app.static_folder, 'css', 'vendor'), exist_ok=True)
    os.makedirs(os.path.join(app.static_folder, 'css', 'webfonts'), exist_ok=True)
    os.makedirs(os.path.join(app.static_folder, 'js', 'vendor'), exist_ok=True)
    os.makedirs(app.template_folder, exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    
    # 配置
    app.config['TIMEOUT'] = 300
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 31536000
    app.config['PERMANENT_SESSION_LIFETIME'] = 300
    
    # 注册路由
    with app.app_context():
        from app.routes import register_routes
        register_routes(app)
    
    return app 