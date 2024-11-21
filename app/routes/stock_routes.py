from flask import jsonify
from utils.logger import setup_logger
from utils.database import get_mysql_connection

logger = setup_logger('stock_routes')

def register_stock_routes(app):
    """注册股票相关路由"""

    @app.route('/api/stock/<string:stock_code>/detail')
    def get_stock_detail(stock_code):
        """获取个股详情数据"""
        try:
            logger.info(f"获取股票 {stock_code} 的详细信息")
            
            stock_info = None
            price_data = []
            sectors = []
            
            with get_mysql_connection() as conn:
                # 获取股票基本信息
                with conn.cursor(dictionary=True) as cursor:
                    cursor.execute('''
                        SELECT 证券代码 as code, 证券简称 as name
                        FROM stocks 
                        WHERE 证券代码 = %s
                    ''', (stock_code,))
                    stock_info = cursor.fetchone()
                
                if not stock_info:
                    return jsonify({
                        'success': False,
                        'message': f'未找到股票: {stock_code}'
                    }), 404

                # 获取股票历史数据
                with conn.cursor(dictionary=True) as cursor:
                    cursor.execute('''
                        SELECT 
                            trade_date,
                            close,
                            amount,
                            LAG(close) OVER (ORDER BY trade_date) as prev_close
                        FROM stock_data
                        WHERE ts_code = %s
                        AND trade_date >= '20240920'
                        ORDER BY trade_date
                    ''', (stock_code,))
                    price_data = cursor.fetchall()

                # 获取所属板块
                with conn.cursor(dictionary=True) as cursor:
                    cursor.execute('''
                        SELECT 
                            s.sector_name,
                            s.sector_type
                        FROM sectors s
                        JOIN sector_stocks ss ON s.sector_id = ss.sector_id
                        WHERE ss.stock_code = %s
                        ORDER BY s.sector_type, s.sector_name
                    ''', (stock_code,))
                    sectors = cursor.fetchall()

            # 处理数据
            dates = []
            changes = []
            volumes = []
            
            for row in price_data:
                # 格式化日期
                trade_date = f"{row['trade_date'][:4]}-{row['trade_date'][4:6]}-{row['trade_date'][6:]}"
                dates.append(trade_date)
                
                # 计算涨跌幅
                close = float(row['close']) if row['close'] else 0
                prev_close = float(row['prev_close']) if row['prev_close'] else close
                change = ((close - prev_close) / prev_close * 100) if prev_close and prev_close != 0 else 0
                changes.append(round(change, 2))
                
                # 处理成交额（从千元转换为元）
                amount = float(row['amount']) * 1000 if row['amount'] else 0
                volumes.append(amount)

            return jsonify({
                'success': True,
                'stock_data': {
                    'name': stock_info['name'],
                    'code': stock_info['code'],
                    'dates': dates,
                    'changes': changes,
                    'volumes': volumes
                },
                'sectors': sectors
            })
                
        except Exception as e:
            error_msg = f"获取股票详情失败: {str(e)}"
            logger.error(error_msg)
            return jsonify({
                'success': False,
                'message': error_msg
            }), 500

    # 添加其他股票相关路由... 