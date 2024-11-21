from flask import jsonify, request
from utils.logger import setup_logger
from utils.database import get_mysql_connection
from app.services.data_updater import StockDataUpdater
import os
import json

logger = setup_logger('data_routes')

def register_data_routes(app):
    """注册数据更新相关路由"""
    
    data_updater = StockDataUpdater()
    
    @app.route('/api/update_historical_data', methods=['POST'])
    def update_historical_data():
        try:
            logger.info("1. 接收到更新请求")
            result = data_updater.update_historical_data()
            return jsonify({
                'status': 'started',
                'message': '更新已启动'
            })
        except Exception as e:
            error_msg = f"更新失败: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return jsonify({
                "status": "error",
                "message": error_msg
            }), 500

    @app.route('/api/update_progress')
    def get_update_progress():
        try:
            return jsonify(data_updater.get_update_progress())
        except Exception as e:
            logger.error(f"获取进度失败: {str(e)}")
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500

    @app.route('/api/update_financial_data', methods=['POST'])
    def update_financial_data():
        try:
            logger.info("开始更新财务数据")
            result = data_updater.update_financial_data()
            return jsonify(result)
        except Exception as e:
            error_msg = f"更新财务数据失败: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return jsonify({
                'success': False,
                'message': error_msg
            }), 500

    @app.route('/api/update_daily_basic', methods=['POST'])
    @app.route('/api/update_daily_basic/<string:trade_date>', methods=['POST'])
    def update_daily_basic_data(trade_date=None):
        try:
            if trade_date:
                logger.info(f"更新 {trade_date} 的每日指标数据")
            else:
                logger.info("更新最新的每日指标数据")
                
            result = data_updater.update_daily_basic(trade_date)
            return jsonify(result)
        except Exception as e:
            error_msg = f"更新每日指标数据失败: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return jsonify({
                'success': False,
                'message': error_msg
            }), 500

    # 添加其他数据更新相关路由... 