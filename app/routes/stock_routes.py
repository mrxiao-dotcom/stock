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
                            open,
                            high,
                            low,
                            close,
                            amount
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
                opens = []
                highs = []
                lows = []
                closes = []
                volumes = []
                
                # 生成模拟的资金流向数据
                super_large_inflow = []
                super_large_outflow = []
                large_inflow = []
                large_outflow = []
                net_inflow = []
                
                import random
                
                for row in price_data:
                    # 格式化日期
                    trade_date = f"{row['trade_date'][:4]}-{row['trade_date'][4:6]}-{row['trade_date'][6:]}"
                    dates.append(trade_date)
                    
                    # 处理价格数据
                    opens.append(float(row['open']) if row['open'] else 0)
                    highs.append(float(row['high']) if row['high'] else 0)
                    lows.append(float(row['low']) if row['low'] else 0)
                    closes.append(float(row['close']) if row['close'] else 0)
                    
                    # 处理成交额
                    amount = float(row['amount']) * 1000 if row['amount'] else 0
                    volumes.append(amount)
                    
                    # 生成模拟数据（基于成交额）
                    base_amount = amount * 0.01  # 基准金额为成交额的1%
                    
                    # 生成资金流向数据
                    s_inflow = base_amount * (0.8 + random.random() * 0.4)  # 80%-120%
                    s_outflow = base_amount * (0.8 + random.random() * 0.4)
                    l_inflow = base_amount * (0.6 + random.random() * 0.4)   # 60%-100%
                    l_outflow = base_amount * (0.6 + random.random() * 0.4)
                    
                    super_large_inflow.append(round(s_inflow))
                    super_large_outflow.append(round(s_outflow))
                    large_inflow.append(round(l_inflow))
                    large_outflow.append(round(l_outflow))
                    net_inflow.append(round(s_inflow + l_inflow - s_outflow - l_outflow))

                return jsonify({
                    'success': True,
                    'stock_data': {
                        'name': stock_info['name'],
                        'code': stock_info['code'],
                        'dates': dates,
                        'opens': opens,
                        'highs': highs,
                        'lows': lows,
                        'closes': closes,
                        'volumes': volumes,
                        'super_large_inflow': super_large_inflow,
                        'super_large_outflow': super_large_outflow,
                        'large_inflow': large_inflow,
                        'large_outflow': large_outflow,
                        'net_inflow': net_inflow
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