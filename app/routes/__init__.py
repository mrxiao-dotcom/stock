from flask import jsonify, request, render_template, send_from_directory, Response
from utils.logger import setup_logger
from utils.database import get_mysql_connection
from datetime import datetime
import tushare as ts
import os
import json

logger = setup_logger('routes')

# 从环境变量或配置文件获取 token
TUSHARE_TOKEN = os.getenv('TUSHARE_TOKEN', '7e48b6886e59f9c5d6a6e23e6018e8c2c4f029c3c9c9f1f8c9c9f1f8')

# 初始化 tushare
try:
    ts.set_token(TUSHARE_TOKEN)
    pro = ts.pro_api()
    logger.info("Tushare API 初始化成功")
except Exception as e:
    logger.error(f"Tushare API 初始化失败: {str(e)}")
    raise

def register_routes(app):
    """注册所有路由"""
    
    # 基础路由
    @app.route('/')
    def index():
        """返回主页"""
        try:
            logger.info("访问主页")
            return render_template('index.html')
        except Exception as e:
            logger.error(f"渲染主页失败: {str(e)}")
            return f"Error: {str(e)}", 500

    @app.route('/static/<path:filename>')
    def serve_static(filename):
        """提供静态文件服务"""
        try:
            logger.info(f"请求静态文件: {filename}")
            return send_from_directory('static', filename)
        except Exception as e:
            logger.error(f"提供静态文件失败: {str(e)}")
            return f"Error: {str(e)}", 404

    # CORS支持
    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE')
        return response

    # 禁用缓存
    @app.after_request
    def add_header(response):
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response

    # 注册其他路由
    from .sector_routes import register_sector_routes
    from .stock_routes import register_stock_routes
    from .data_routes import register_data_routes

    register_sector_routes(app)
    register_stock_routes(app)
    register_data_routes(app)

    @app.context_processor
    def utility_processor():
        def get_version():
            return datetime.now().strftime("%Y%m%d%H%M%S")
        return dict(version=get_version)

    return app 